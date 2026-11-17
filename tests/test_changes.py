"""The record of changes, from invented published versions (no network)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from commonswire.changes import (
    CHANGE_FIELDS,
    counts,
    entries,
    history,
    read_changes,
    to_csv,
)
from commonswire.cli import main


def write_version(folder, version, rows, *, as_of, update=None, removed=0):
    folder.mkdir(parents=True)
    table = pa.Table.from_pylist(
        [
            {
                "id": rid,
                "source_id": src,
                "content_hash": h,
                "retrieved_at": datetime.fromisoformat(t).replace(tzinfo=timezone.utc),
            }
            for rid, src, h, t in rows
        ]
    )
    (folder / "data").mkdir()
    pq.write_table(table, folder / "data" / "a.parquet")
    manifest = {
        "version": version,
        "as_of": as_of,
        "configurations": {"by": ["data/a.parquet"]},
        "removed_rows_not_released": {"alpha": removed} if removed else {},
    }
    if update:
        manifest["update"] = update
    (folder / "manifest.json").write_text(json.dumps(manifest))
    return folder


def test_history_from_published_versions_splits_a_missing_version(tmp_path):
    v1 = write_version(
        tmp_path / "v1",
        "0.1.0",
        [
            ("cw_a", "alpha", "h1", "2026-01-01T00:00:00"),
            ("cw_b", "alpha", "h2", "2026-01-01T00:00:00"),
        ],
        as_of="2026-01-01T00:00:00Z",
    )
    # 0.1.1 is missing: 0.1.2 holds its row (retrieved before 0.1.2's own run) and its own.
    v3 = write_version(
        tmp_path / "v3",
        "0.1.2",
        [
            ("cw_a", "alpha", "h1", "2026-01-01T00:00:00"),
            ("cw_b", "alpha", "h2-edited", "2026-01-08T00:00:00"),
            ("cw_c", "beta", "h3", "2026-01-15T00:00:00"),
        ],
        as_of="2026-01-15T00:00:00Z",
        update={"from_version": "0.1.1"},
    )
    lines = history([v1, v3])
    assert [(r["id"], r["version"], r["change"]) for r in lines] == [
        ("cw_a", "0.1.0", "new"),
        ("cw_b", "0.1.0", "new"),
        ("cw_b", "0.1.1", "changed"),
        ("cw_c", "0.1.2", "new"),
    ]
    assert counts(lines) == {"0.1.0": {"new": 2}, "0.1.1": {"changed": 1}, "0.1.2": {"new": 1}}
    with pytest.raises(ValueError, match="is not the first"):
        history([v3])
    bad = write_version(tmp_path / "bad", "0.1.3", [], as_of="2026-01-20T00:00:00Z", removed=1)
    with pytest.raises(ValueError, match="whose ids its files do not hold"):
        history([v1, bad])


def test_entries_and_the_csv_round_trip(tmp_path):
    rows = {"cw_a": {"source_id": "alpha", "retrieved_at": "2026-02-01T00:00:00Z"}}
    lines = entries("0.3.1", rows, new=["cw_a"], removed=["cw_z"], as_of="2026-02-02T00:00:00Z")
    assert lines == [
        {
            "id": "cw_a",
            "source_id": "alpha",
            "version": "0.3.1",
            "change": "new",
            "date": "2026-02-01T00:00:00Z",
        },
        {
            "id": "cw_z",
            "source_id": "",
            "version": "0.3.1",
            "change": "removed",
            "date": "2026-02-02T00:00:00Z",
        },
    ]
    path = tmp_path / "changes.csv"
    path.write_bytes(to_csv(lines))
    assert read_changes(path) == lines
    path.write_text(",".join(CHANGE_FIELDS) + "\ncw_a,alpha,0.3.1,renamed,2026\n")
    with pytest.raises(ValueError, match="change must be one of"):
        read_changes(path)
    path.write_text("id,source\n")
    with pytest.raises(ValueError, match="the header must be"):
        read_changes(path)


def test_cli_changes(tmp_path, capsys):
    v1 = write_version(
        tmp_path / "v1",
        "0.1.0",
        [("cw_a", "alpha", "h1", "2026-01-01T00:00:00")],
        as_of="2026-01-01T00:00:00Z",
    )
    out = tmp_path / "out" / "changes.csv"
    assert main(["--root", str(tmp_path), "changes", str(v1), "--out", str(out)]) == 0
    assert "1 lines" in capsys.readouterr().out and out.exists()
    assert (
        main(["--root", str(tmp_path), "changes", str(tmp_path / "nowhere"), "--out", str(out)])
        == 2
    )
