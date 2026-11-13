"""Deduplication tests with invented texts."""

from __future__ import annotations

import numpy as np

from commonswire.dedup import (
    Row,
    candidate_pairs,
    exact_duplicates,
    histogram,
    jaccard,
    minhash,
    near_duplicates,
    normalize,
    shingles,
)

BASE = (
    "An invented report about a river flood in an invented valley, where invented officials "
    "said that the water rose quickly overnight and that invented families moved to higher "
    "ground while invented volunteers handed out food and blankets. "
) * 3


def row(i, source, text, day="2026-01-01", h=None, title="Invented river flood report"):
    return Row(
        id=i,
        source_id=source,
        published_at=f"{day}T00:00:00Z",
        content_hash=h or f"h{i}",
        text=text,
        title=title,
    )


def test_shingles_are_deterministic_and_jaccard_behaves():
    a, b = shingles(BASE), shingles(BASE)
    assert np.array_equal(a, b) and a.dtype == np.uint64
    assert jaccard(a, b) == 1.0
    other = shingles("A completely different invented text about a chess tournament result.")
    assert jaccard(a, other) < 0.1
    assert jaccard(np.array([], dtype=np.uint64), np.array([], dtype=np.uint64)) == 1.0
    assert shingles("ab").size == 1  # short texts still get one shingle
    assert normalize("  A\n B  ") == "a b"


def test_minhash_estimates_similarity():
    a = shingles(BASE)
    b = shingles(BASE.replace("blankets", "water"))
    est = float(np.mean(minhash(a) == minhash(b)))
    assert abs(est - jaccard(a, b)) < 0.25


def test_exact_duplicates_drop_repeated_urls_then_repeated_texts():
    rows = [
        row("a", "s1", BASE, "2026-01-02"),
        row("a", "s1", BASE, "2026-01-02"),
        row("b", "s2", BASE, "2026-01-03", h="hx"),
        row("c", "s1", BASE, "2026-01-01", h="hx"),
    ]
    res = exact_duplicates(rows, ["s1", "s2"])
    assert res.rows_in == 4 and res.kept_ids == ["c", "a"]
    assert res.dropped == {"b": "same_text_as:c"}
    assert res.dropped_by == {"same_url:s1": 1, "same_text:s2": 1}


def test_near_duplicates_are_flagged_with_title_overlap():
    rows = {
        "x": row("x", "s1", BASE),
        "y": row("y", "s2", BASE.replace("overnight", "during the night")),
        "z": row(
            "z",
            "s2",
            "An invented chess tournament ended in a draw after six hours. " * 5,
            title="Invented chess result",
        ),
    }
    pairs, oversized = near_duplicates(rows, ["x", "y", "z"])
    assert oversized == 0
    assert [(p[0], p[1]) for p in pairs] == [("x", "y")]
    assert pairs[0][4] > 0.8 and pairs[0][5] == 1.0
    hist = histogram(pairs, cross_source=True)
    assert hist and hist[-1]["pairs"] == 1
    assert histogram(pairs, cross_source=False) == []


def test_oversized_buckets_are_skipped():
    sig = np.zeros(64, dtype=np.uint64)
    sigs = {f"r{i}": sig for i in range(205)}
    pairs, oversized = candidate_pairs(sigs)
    assert pairs == set() and oversized == 16


def test_cli_dedup_writes_pairs_and_a_summary(tmp_path, capsys):
    import json

    import pyarrow.parquet as pq

    from commonswire.cli import main

    rows_dir = tmp_path / "data" / "interim" / "rows"
    rows_dir.mkdir(parents=True)

    def line(i, src, text, h):
        return (
            json.dumps(
                {
                    "id": i,
                    "source_id": src,
                    "published_at": "2026-01-01T00:00:00Z",
                    "content_hash": h,
                    "text": text,
                    "title": "Invented flood",
                }
            )
            + "\n"
        )

    (rows_dir / "s1.jsonl").write_text(line("x", "s1", BASE, "h1") + line("w", "s1", BASE, "h1"))
    (rows_dir / "s2.jsonl").write_text(line("y", "s2", BASE.replace("overnight", "at night"), "h2"))
    assert main(["--root", str(tmp_path), "dedup", "--threshold", "0.8"]) == 0
    assert "1 flagged" in capsys.readouterr().out
    summary = json.loads((tmp_path / "data" / "evidence" / "dedup" / "summary.json").read_text())
    assert summary["rows_in"] == 3 and summary["kept_after_exact"] == 2
    assert summary["flagged_by_source_pair"] == {"s1|s2": 1}
    table = pq.read_table(tmp_path / "data" / "interim" / "dedup" / "near_duplicates.parquet")
    assert table.num_rows == 1
