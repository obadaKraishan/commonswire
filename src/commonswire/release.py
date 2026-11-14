"""The release build: one dataset version, written from the built rows with no request.

``commonswire release build --version 0.1.0`` writes ``data/release/<version>/``:

- ``data/<configuration>/train-NNNNN-of-NNNNN.parquet``: one configuration per license class
  (``pd``, ``by``, ``by-sa``), releasable rows only, sorted by publication time and id;
- ``index.csv``: one line per released row (id, source, configuration, URL, license, content
  hash, publication time), with no text;
- ``sources.csv``: the source registry as it is (every source, its evidence and its status);
- ``LICENSES.md`` and ``README.md`` (the dataset card);
- ``manifest.json``: row counts, and the size and SHA-256 of every other file.

Each version series has a fixed list of sources (:data:`SERIES`), so a source collected later
does not slip into an older series. Inside that list, exact duplicates are dropped and
near-duplicates flagged by the same rules as ``commonswire dedup``, computed here from the rows
alone, so the files depend only on the rows and the registry: the same input gives the same
bytes. Before anything is written, every row is checked: it validates against the schema, it is
releasable and not third-party, it is not a removed row, and its credit line is exactly the
source's template filled in for it.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from commonswire.dedup import Row, exact_duplicates, near_duplicates
from commonswire.licensing import CLASS_NC_ND, license_class, license_url
from commonswire.schema import Article
from commonswire.sources import Source, license_label, render_credit

#: The sources of each version series, (major, minor) -> source ids.
SERIES: dict[tuple[int, int], tuple[str, ...]] = {
    (0, 1): ("wikinews_en", "360info", "thepublicrecord", "balkandiskurs", "factly", "altnews"),
}
#: The order configurations are listed in; ``by`` is the default.
CONFIGURATIONS = ("by", "by-sa", "pd")
NEAR_DUPLICATE_THRESHOLD = 0.6
ROWS_PER_SHARD = 50_000
ROW_GROUP = 2_000
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

#: The released columns, in order.
COLUMNS = (
    "id",
    "source_id",
    "kind",
    "title",
    "authors",
    "published_at",
    "updated_at",
    "retrieved_at",
    "language",
    "section",
    "url",
    "license",
    "license_url",
    "credit_line",
    "text",
    "content_hash",
    "status",
    "near_duplicates",
)


class ReleaseError(ValueError):
    """The release cannot be built as asked; the message says what to fix."""


def series_sources(version: str) -> tuple[str, ...]:
    """The sources of a version: ``0.1.0`` and ``0.1.7`` share the list of series 0.1."""
    m = _VERSION.match(version)
    if not m:
        raise ReleaseError(f"version {version!r} is not of the form 0.1.0")
    key = (int(m.group(1)), int(m.group(2)))
    if key not in SERIES:
        known = ", ".join(f"{a}.{b}.x" for a, b in SERIES)
        raise ReleaseError(
            f"version {version} belongs to series {key[0]}.{key[1]}, which has no source list; "
            f"known series: {known}. Add its sources to SERIES in release.py first."
        )
    return SERIES[key]


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class Checks:
    """What the checks before writing found (all must be zero but ``held`` and ``removed``)."""

    rows_in: int = 0
    exact_duplicates: Counter[str] = field(default_factory=Counter)
    held: Counter[str] = field(default_factory=Counter)
    removed: Counter[str] = field(default_factory=Counter)
    invalid: list[str] = field(default_factory=list)
    credit_mismatch: list[str] = field(default_factory=list)
    third_party: list[str] = field(default_factory=list)
    unreleasable_class: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.invalid or self.credit_mismatch or self.third_party or self.unreleasable_class
        )

    def problems(self) -> list[str]:
        out = []
        for name in ("invalid", "credit_mismatch", "third_party", "unreleasable_class"):
            items = getattr(self, name)
            if items:
                out.append(f"{len(items)} rows {name.replace('_', ' ')}: {', '.join(items[:5])}")
        return out


@dataclass
class Release:
    version: str
    sources: tuple[str, ...]
    rows: dict[str, list[dict]]  # configuration -> rows, in release order
    checks: Checks
    near_duplicate_pairs: int = 0

    def counts(self) -> dict[str, object]:
        by_source: dict[str, Counter[str]] = defaultdict(Counter)
        by_license: Counter[str] = Counter()
        for config, rows in self.rows.items():
            for r in rows:
                by_source[r["source_id"]][config] += 1
                by_license[r["license"]] += 1
        return {
            "rows": sum(len(v) for v in self.rows.values()),
            "rows_by_configuration": {c: len(self.rows[c]) for c in CONFIGURATIONS},
            "rows_by_source": {s: dict(sorted(by_source[s].items())) for s in self.sources},
            "rows_by_license": dict(sorted(by_license.items())),
        }


def _flags(rows: dict[str, Row], kept: list[str], threshold: float) -> tuple[dict, int]:
    pairs, _ = near_duplicates(rows, kept)
    flags: dict[str, list[str]] = defaultdict(list)
    n = 0
    for a, b, sa, sb, j, _t in pairs:
        if sa != sb and j >= threshold:
            flags[a].append(b)
            flags[b].append(a)
            n += 1
    return {k: sorted(v) for k, v in flags.items()}, n


def collect(
    root: Path,
    version: str,
    registry: dict[str, Source],
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> Release:
    """Read, deduplicate, check and group the rows of a version (nothing is written)."""
    sources = series_sources(version)
    rows_dir = root / "data" / "interim" / "rows"
    missing = [s for s in sources if not (rows_dir / f"{s}.jsonl").exists()]
    if missing:
        raise ReleaseError(
            f"no rows for {', '.join(missing)} in {rows_dir}; build them first "
            "(commonswire build SOURCE, or commonswire wikinews-dump)"
        )
    unknown = [s for s in sources if s not in registry]
    if unknown:
        raise ReleaseError(f"{', '.join(unknown)} not in the registry (data/sources.csv)")
    checks = Checks()
    data: dict[str, dict] = {}
    rows: dict[str, Row] = {}
    order = sorted(sources)
    for source in order:
        with (rows_dir / f"{source}.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                checks.rows_in += 1
                if d["source_id"] != source:
                    checks.invalid.append(f"{d['id']} (source_id {d['source_id']!r})")
                    continue
                if d["id"] in data:
                    checks.exact_duplicates[f"same_url:{source}"] += 1
                    continue
                data[d["id"]] = d
                rows[d["id"]] = Row(
                    id=d["id"],
                    source_id=source,
                    published_at=d["published_at"],
                    content_hash=d["content_hash"],
                    text=d["text"],
                    title=d.get("title", ""),
                )
    exact = exact_duplicates(rows.values(), order)
    checks.exact_duplicates.update(exact.dropped_by)
    flags, n_pairs = _flags(rows, exact.kept_ids, threshold)
    grouped: dict[str, list[dict]] = {c: [] for c in CONFIGURATIONS}
    for rid in exact.kept_ids:
        d = data[rid]
        src = registry[d["source_id"]]
        if d.get("status") == "removed":
            checks.removed[d["source_id"]] += 1
            continue
        if not d.get("releasable", True):
            checks.held[d["source_id"]] += 1
            continue
        if d.get("third_party"):
            checks.third_party.append(rid)
            continue
        try:
            Article.model_validate(d)
        except ValueError as exc:
            checks.invalid.append(f"{rid} ({str(exc).splitlines()[0][:60]})")
            continue
        expected = render_credit(
            src.credit_line,
            title=d["title"],
            authors=d["authors"],
            source=src.name,
            url=d["url"],
            license=d["license"],
        )
        if d["credit_line"] != expected:
            checks.credit_mismatch.append(rid)
            continue
        config = license_class(d["license"])
        if config == CLASS_NC_ND or config not in grouped:
            checks.unreleasable_class.append(f"{rid} ({d['license']})")
            continue
        grouped[config].append(
            {
                "id": rid,
                "source_id": d["source_id"],
                "kind": src.kind,
                "title": d["title"],
                "authors": list(d["authors"]),
                "published_at": _ts(d["published_at"]),
                "updated_at": _ts(d.get("updated_at")),
                "retrieved_at": _ts(d["retrieved_at"]),
                "language": d["language"],
                "section": d.get("section", ""),
                "url": d["url"],
                "license": d["license"],
                "license_url": license_url(d["license"]),
                "credit_line": d["credit_line"],
                "text": d["text"],
                "content_hash": d["content_hash"],
                "status": d.get("status", "live"),
                "near_duplicates": flags.get(rid, []),
            }
        )
    for config in grouped.values():
        config.sort(key=lambda r: (r["published_at"], r["id"]))
    return Release(
        version=version, sources=sources, rows=grouped, checks=checks, near_duplicate_pairs=n_pairs
    )


def _schema():  # type: ignore[no-untyped-def]
    import pyarrow as pa

    ts = pa.timestamp("s", tz="UTC")
    text = pa.string()
    types = {
        "authors": pa.list_(text),
        "near_duplicates": pa.list_(text),
        "published_at": ts,
        "updated_at": ts,
        "retrieved_at": ts,
    }
    return pa.schema([pa.field(c, types.get(c, text), nullable=c == "updated_at") for c in COLUMNS])


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _parquet_bytes(rows: list[dict]) -> bytes:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist(rows, schema=_schema())
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="zstd", row_group_size=ROW_GROUP)
    return sink.getvalue()


def _csv_bytes(header: list[str], lines: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(lines)
    return buf.getvalue().encode("utf-8")


def _iso(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_table(release: Release, registry: dict[str, Source]) -> list[dict[str, object]]:
    """One line per source of the release: kind, licenses, rows, dates, credit template."""
    out = []
    for s in release.sources:
        src = registry[s]
        rows = [r for config in release.rows.values() for r in config if r["source_id"] == s]
        licenses = Counter(r["license"] for r in rows)
        dates = [r["published_at"] for r in rows]
        out.append(
            {
                "source_id": s,
                "name": src.name,
                "kind": src.kind,
                "homepage": src.homepage,
                "licenses": {license_label(k): v for k, v in sorted(licenses.items())},
                "rows": len(rows),
                "first": min(dates).date().isoformat() if dates else "",
                "last": max(dates).date().isoformat() if dates else "",
                "credit_template": src.credit_line,
                "held": release.checks.held.get(s, 0),
                "removed": release.checks.removed.get(s, 0),
            }
        )
    return out


def write_release(
    release: Release,
    out: Path,
    registry_path: Path,
    registry: dict[str, Source],
    *,
    card: str,
    licenses_md: str,
) -> dict[str, object]:
    """Write the files of a checked release under ``out`` and return the manifest."""
    if not release.checks.ok:
        raise ReleaseError("the checks failed: " + "; ".join(release.checks.problems()))
    files: dict[str, bytes] = {}
    shards: dict[str, list[str]] = {}
    for config in CONFIGURATIONS:
        rows = release.rows[config]
        n = max(1, -(-len(rows) // ROWS_PER_SHARD))
        shards[config] = []
        for i in range(n):
            name = f"data/{config}/train-{i:05d}-of-{n:05d}.parquet"
            files[name] = _parquet_bytes(rows[i * ROWS_PER_SHARD : (i + 1) * ROWS_PER_SHARD])
            shards[config].append(name)
    index = [
        [
            r["id"],
            r["source_id"],
            config,
            r["url"],
            r["license"],
            r["content_hash"],
            _iso(r["published_at"]),
        ]
        for config in CONFIGURATIONS
        for r in release.rows[config]
    ]
    index.sort(key=lambda x: (x[6], x[0]))
    files["index.csv"] = _csv_bytes(
        ["id", "source_id", "configuration", "url", "license", "content_hash", "published_at"],
        index,
    )
    files["sources.csv"] = registry_path.read_bytes()
    files["LICENSES.md"] = licenses_md.encode("utf-8")
    files["README.md"] = card.encode("utf-8")
    all_rows = [r for config in release.rows.values() for r in config]
    as_of = max((r["retrieved_at"] for r in all_rows), default=None)
    out.mkdir(parents=True, exist_ok=True)
    for name, body in sorted(files.items()):
        _write_atomic(out / name, body)
    manifest = {
        "name": "CommonsWire",
        "version": release.version,
        "as_of": _iso(as_of),
        "sources": list(release.sources),
        "configurations": {c: shards[c] for c in CONFIGURATIONS},
        **release.counts(),
        "held_rows_not_released": dict(sorted(release.checks.held.items())),
        "removed_rows_not_released": dict(sorted(release.checks.removed.items())),
        "exact_duplicates_dropped": dict(sorted(release.checks.exact_duplicates.items())),
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "near_duplicate_pairs_across_sources": release.near_duplicate_pairs,
        "files": [
            {"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            for name, body in sorted(files.items())
        ],
    }
    _write_atomic(out / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


def verify(out: Path, corpus_report: dict | None = None) -> list[str]:
    """Check a written release against its manifest (and the corpus report, if given):
    every file's size and hash, the row counts in the Parquet files, and every row's id, license
    class and credit line filled in. Returns the problems found (empty when all is well)."""
    import pyarrow.parquet as pq

    problems: list[str] = []
    manifest = json.loads((out / "manifest.json").read_text())
    for f in manifest["files"]:
        path = out / f["path"]
        if not path.exists():
            problems.append(f"{f['path']} is missing")
            continue
        if path.stat().st_size != f["bytes"] or sha256(path) != f["sha256"]:
            problems.append(f"{f['path']} differs from the manifest")
    listed = {f["path"] for f in manifest["files"]} | {"manifest.json"}
    for path in sorted(out.rglob("*")):
        if path.is_file() and str(path.relative_to(out)) not in listed:
            problems.append(f"{path.relative_to(out)} is not in the manifest")
    seen: set[str] = set()
    by_source: Counter[str] = Counter()
    for config, names in manifest["configurations"].items():
        n = 0
        for name in names:
            table = pq.read_table(out / name, columns=["id", "source_id", "license", "credit_line"])
            for r in table.to_pylist():
                n += 1
                by_source[r["source_id"]] += 1
                if r["id"] in seen:
                    problems.append(f"{r['id']} is in the release twice")
                seen.add(r["id"])
                if license_class(r["license"]) != config:
                    problems.append(f"{r['id']} ({r['license']}) is in the {config} configuration")
                if not r["credit_line"] or "{" in r["credit_line"]:
                    problems.append(f"{r['id']} has an unfilled credit line")
        if n != manifest["rows_by_configuration"][config]:
            problems.append(
                f"{config}: {n} rows in the files, {manifest['rows_by_configuration'][config]} in "
                "the manifest"
            )
    if corpus_report is not None:
        for s in manifest["sources"]:
            v = corpus_report["sources"].get(s, {})
            removed = manifest["removed_rows_not_released"].get(s, 0)
            want = v.get("releasable_rows", 0) - removed
            if by_source[s] != want:
                problems.append(
                    f"{s}: {by_source[s]} rows released, but the corpus report has {want} "
                    "releasable rows (run commonswire dedup and corpus-report again?)"
                )
    return problems
