"""The sample report: aggregates only, never article text or person-level rows.

For one source's sample (the kept articles and the fetch summary) it gives the articles per
day, the archive start, the languages, the length distribution, the share with a byline, the
share dropped as third-party, the missing fields, and an estimate of the full backfill.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from commonswire.schema import Article

QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)


def load_articles(path: Path) -> list[Article]:
    with Path(path).open(encoding="utf-8") as fh:
        return [Article.model_validate_json(line) for line in fh if line.strip()]


def quantiles(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    out: dict[str, float] = {"min": ordered[0], "max": ordered[-1]}
    out["mean"] = round(statistics.fmean(ordered), 1)
    for q in QUANTILES:
        # nearest-rank quantile, stable for small samples
        idx = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
        out[f"p{int(q * 100)}"] = ordered[idx]
    return out


def sample_report(
    articles: Iterable[Article],
    summary: dict[str, object],
    *,
    total_articles: int | None = None,
    archive_from: str | None = None,
) -> dict[str, object]:
    """Aggregate one source's sample. ``total_articles`` is the source's archive size, from its
    API, for the backfill estimate."""
    arts = list(articles)
    n = len(arts)
    seen = int(summary.get("seen", 0) or 0)
    dropped: dict[str, int] = dict(summary.get("dropped", {}) or {})  # type: ignore[arg-type]
    third = sum(v for k, v in dropped.items() if k.startswith("third_party"))
    chars = [len(a.text) for a in arts]
    words = [len(a.text.split()) for a in arts]
    record_bytes = [len(a.model_dump_json().encode("utf-8")) + 1 for a in arts]
    dates = sorted(a.published_at for a in arts)
    span_days = (dates[-1] - dates[0]).total_seconds() / 86400 if len(dates) > 1 else None
    per_day = round((n - 1) / span_days, 2) if span_days else None
    third_share = round(third / seen, 4) if seen else None
    backfill: dict[str, object] = {}
    if total_articles and record_bytes:
        keep_share = 1 - (third_share or 0)
        est_rows = round(total_articles * keep_share)
        mean_bytes = statistics.fmean(record_bytes)
        backfill = {
            "archive_articles": total_articles,
            "est_rows_after_third_party_drop": est_rows,
            "mean_record_bytes": round(mean_bytes),
            "est_jsonl_gb": round(est_rows * mean_bytes / 1e9, 3),
        }
    return {
        "source_id": summary.get("source_id"),
        "seen": seen,
        "kept": n,
        "dropped": dropped,
        "third_party_share": third_share,
        "sample_window": {
            "oldest": dates[0].date().isoformat() if dates else None,
            "newest": dates[-1].date().isoformat() if dates else None,
            "days": round(span_days, 1) if span_days else None,
        },
        "articles_per_day_in_sample": per_day,
        "archive_from": archive_from or summary.get("api_totals", {}).get("archive_from"),  # type: ignore[union-attr]
        "languages": dict(Counter(a.language for a in arts)),
        "licenses": dict(Counter(a.license for a in arts)),
        "length_chars": quantiles(chars),
        "length_words": quantiles(words),
        "share_with_byline": round(sum(1 for a in arts if a.authors) / n, 3) if n else None,
        "missing": {
            "authors": sum(1 for a in arts if not a.authors),
            "section": sum(1 for a in arts if not a.section),
            "updated_at": sum(1 for a in arts if a.updated_at is None),
        },
        "sample_bytes": sum(record_bytes),
        "backfill": backfill,
    }


def write_report(report: dict[str, object], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
