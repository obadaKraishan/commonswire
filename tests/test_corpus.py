"""Corpus report and Parquet store tests with invented rows."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq

from commonswire.cli import main
from commonswire.corpus import corpus_report, write_parquet
from commonswire.sources import SOURCE_FIELDS
from test_schema import art
from test_sources import row

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


def setup(tmp_path):
    rows = tmp_path / "data" / "interim" / "rows"
    rows.mkdir(parents=True)
    a = art(
        url="https://news.example.org/a", published_at=datetime(2026, 11, 1, tzinfo=timezone.utc)
    )
    b = art(
        url="https://news.example.org/b",
        authors=("A. Writer",),
        published_at=datetime(2019, 5, 1, tzinfo=timezone.utc),
        license="CC-BY-SA-4.0",
        text="Another invented paragraph about a library opening.",
    )
    c = art(
        url="https://news.example.org/c",
        releasable=False,
        hold_reason="no byline",
        published_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        text="A third invented text.",
    )
    (rows / "example_news.jsonl").write_text("".join(x.model_dump_json() + "\n" for x in (a, b, c)))
    dd = tmp_path / "data" / "interim" / "dedup"
    dd.mkdir(parents=True)
    (dd / "dropped.json").write_text(json.dumps({c.id: "same_text_as:x"}))
    pq.write_table(
        pa.table(
            {
                "id_a": [a.id],
                "id_b": ["cw_other"],
                "source_a": ["example_news"],
                "source_b": ["other"],
                "jaccard": [0.9],
                "title_overlap": [1.0],
            }
        ),
        dd / "near_duplicates.parquet",
    )
    ev = tmp_path / "data" / "evidence" / "backfill"
    ev.mkdir(parents=True)
    (ev / "example_news.build.json").write_text(
        json.dumps({"dropped": {"third_party:x": 4, "invalid:y": 1}})
    )
    (tmp_path / "data" / "evidence" / "dedup").mkdir(parents=True)
    (tmp_path / "data" / "evidence" / "dedup" / "summary.json").write_text(
        json.dumps({"dropped_exact": {"same_text:example_news": 1}})
    )
    raw = tmp_path / "data" / "raw" / "backfill" / "example_news"
    raw.mkdir(parents=True)
    (raw / "p.json").write_bytes(b"x" * 100)
    return a, b, c


def test_corpus_report_aggregates_without_text(tmp_path):
    setup(tmp_path)
    rep = corpus_report(tmp_path, {"example_news": "news"}, 0.8, now=NOW)
    s = rep["sources"]["example_news"]
    assert s["rows_kept"] == 2 and s["releasable_rows"] == 2
    assert s["dropped_third_party"] == 4 and s["dropped_other"] == 1
    assert s["exact_duplicates_dropped"] == 1 and s["near_duplicate_flags"] == 1
    assert s["articles_per_year"] == {"2019": 1, "2026": 1}
    assert s["share_with_byline"] == 0.5 and s["license_classes"] == {"by": 1, "by-sa": 1}
    assert s["per_day_last_90_days"] == round(1 / 90, 2) and s["kind"] == "news"
    assert rep["total"]["rows_kept"] == 2
    assert "invented" not in json.dumps(rep).lower()


def test_parquet_by_source_and_year_with_release_columns(tmp_path):
    setup(tmp_path)
    counts = write_parquet(tmp_path, {"example_news": "news"}, 0.8)
    assert counts == {"example_news": {"2019": 1, "2026": 1}}
    t = pq.read_table(tmp_path / "data" / "interim" / "parquet" / "example_news" / "2026.parquet")
    r = t.to_pylist()[0]
    assert r["kind"] == "news" and r["license_class"] == "by"
    assert r["license_url"] == "https://creativecommons.org/licenses/by/4.0/"
    assert r["near_duplicates"] == ["cw_other"] and "codings" not in r


def test_cli_corpus_report_and_store(tmp_path, capsys):
    setup(tmp_path)
    reg = tmp_path / "sources.csv"
    with reg.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerow(row())
    root = ["--root", str(tmp_path)]
    assert main([*root, "corpus-report", "--sources", str(reg)]) == 0
    assert "total: 2 rows" in capsys.readouterr().out
    assert main([*root, "store", "--sources", str(reg)]) == 0
    assert (tmp_path / "data" / "evidence" / "corpus" / "parquet_counts.json").exists()
