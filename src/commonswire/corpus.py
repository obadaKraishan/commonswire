"""The corpus report (aggregates only) and the Parquet store by source and year.

Both read the built rows (``data/interim/rows/<source>.jsonl``), leave out the exact duplicates
that ``commonswire dedup`` dropped, and attach its near-duplicate flags. Neither sends any
request. Needs the ``corpus`` extra (pyarrow).
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

from commonswire.licensing import license_class, license_url

LIVING_DAYS = 90


def _dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def _dropped(root: Path) -> dict[str, str]:
    path = root / "data" / "interim" / "dedup" / "dropped.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _flags(root: Path, threshold: float) -> dict[str, list[str]]:
    """Row id -> the ids of its near-duplicates in other sources, at or above ``threshold``."""
    path = root / "data" / "interim" / "dedup" / "near_duplicates.parquet"
    out: dict[str, list[str]] = defaultdict(list)
    if not path.exists():
        return out
    import pyarrow.parquet as pq

    t = pq.read_table(path).to_pylist()
    for p in t:
        if p["source_a"] != p["source_b"] and p["jaccard"] >= threshold:
            out[p["id_a"]].append(p["id_b"])
            out[p["id_b"]].append(p["id_a"])
    return out


def iter_rows(root: Path) -> Iterator[tuple[str, dict]]:
    dropped = _dropped(root)
    seen: set[str] = set()
    for path in sorted((root / "data" / "interim" / "rows").glob("*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                if d["id"] in dropped or d["id"] in seen:
                    continue
                seen.add(d["id"])
                yield path.stem, d


def corpus_report(
    root: Path, kinds: dict[str, str], threshold: float, now: datetime | None = None
) -> dict[str, object]:
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(days=LIVING_DAYS)).isoformat()
    builds = {}
    for p in (root / "data" / "evidence" / "backfill").glob("*.build.json"):
        builds[p.name.split(".")[0]] = json.loads(p.read_text())
    dedup_path = root / "data" / "evidence" / "dedup" / "summary.json"
    dedup = json.loads(dedup_path.read_text()) if dedup_path.exists() else {}
    flags = _flags(root, threshold)
    per: dict[str, dict] = defaultdict(lambda: {"words": [], "years": Counter()})
    for source, d in iter_rows(root):
        s = per[source]
        w = len(d["text"].split())
        s["words"].append(w)
        s["years"][d["published_at"][:4]] += 1
        s["rows"] = s.get("rows", 0) + 1
        s["releasable"] = s.get("releasable", 0) + int(d.get("releasable", True))
        s["bylines"] = s.get("bylines", 0) + int(bool(d["authors"]))
        s["first"] = min(s.get("first", d["published_at"]), d["published_at"])
        s["last"] = max(s.get("last", d["published_at"]), d["published_at"])
        s["recent"] = s.get("recent", 0) + int(d["published_at"] >= since)
        s["flagged"] = s.get("flagged", 0) + int(d["id"] in flags)
        s["classes"] = s.get("classes", Counter())
        s["classes"][license_class(d["license"])] += 1
    sources = {}
    for source, s in sorted(per.items()):
        b = builds.get(source, {})
        drops = b.get("dropped") or b.get("skipped") or {}
        third = sum(v for k, v in drops.items() if k.startswith("third_party"))
        dup = sum(v for k, v in dedup.get("dropped_exact", {}).items() if k.endswith(f":{source}"))
        raw = _dir_bytes(root / "data" / "raw" / "backfill" / source)
        rows_file = root / "data" / "interim" / "rows" / f"{source}.jsonl"
        sources[source] = {
            "kind": kinds.get(source, ""),
            "rows_kept": s["rows"],
            "dropped_third_party": third,
            "dropped_other": sum(drops.values()) - third,
            "exact_duplicates_dropped": dup,
            "near_duplicate_flags": s["flagged"],
            "first": s["first"][:10],
            "last": s["last"][:10],
            "articles_per_year": dict(sorted(s["years"].items())),
            "words_median": statistics.median(s["words"]),
            "words_total": sum(s["words"]),
            "share_with_byline": round(s["bylines"] / s["rows"], 3),
            "releasable_rows": s["releasable"],
            "license_classes": dict(s["classes"]),
            "raw_gb": round(raw / 1e9, 3),
            "rows_gb": round(rows_file.stat().st_size / 1e9, 3) if rows_file.exists() else 0,
            "per_day_last_90_days": round(s["recent"] / LIVING_DAYS, 2),
        }
    total = {
        "rows_kept": sum(v["rows_kept"] for v in sources.values()),
        "releasable_rows": sum(v["releasable_rows"] for v in sources.values()),
        "dropped_third_party": sum(v["dropped_third_party"] for v in sources.values()),
        "exact_duplicates_dropped": sum(v["exact_duplicates_dropped"] for v in sources.values()),
        "words_total": sum(v["words_total"] for v in sources.values()),
        "raw_gb": round(sum(v["raw_gb"] for v in sources.values()), 3),
        "rows_gb": round(sum(v["rows_gb"] for v in sources.values()), 3),
        "per_day_last_90_days": round(sum(v["per_day_last_90_days"] for v in sources.values()), 2),
        "license_classes": dict(
            sum((Counter(v["license_classes"]) for v in sources.values()), Counter())
        ),
    }
    return {
        "as_of": now.isoformat(timespec="seconds"),
        "near_duplicate_threshold": threshold,
        "sources": sources,
        "total": total,
    }


def write_parquet(root: Path, kinds: dict[str, str], threshold: float) -> dict[str, dict[str, int]]:
    """Parquet files by source and year under ``data/interim/parquet/``; returns the row counts."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    flags = _flags(root, threshold)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for source, d in iter_rows(root):
        row = {k: v for k, v in d.items() if k != "codings"}
        row["authors"] = list(d["authors"])
        row["kind"] = kinds.get(source, "")
        row["license_class"] = license_class(d["license"])
        row["license_url"] = license_url(d["license"])
        row["near_duplicates"] = sorted(flags.get(d["id"], []))
        groups[(source, d["published_at"][:4])].append(row)
    counts: dict[str, dict[str, int]] = defaultdict(dict)
    out = root / "data" / "interim" / "parquet"
    for (source, year), rows in sorted(groups.items()):
        path = out / source / f"{year}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(rows), path, compression="zstd")
        counts[source][year] = len(rows)
    return dict(counts)
