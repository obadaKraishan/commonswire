"""A new series' version from a published one plus new sources (invented rows, no network)."""

from __future__ import annotations

import json

import pytest

from commonswire import release as rel
from commonswire.cli import main
from commonswire.minor import build_from_previous, third_party_of
from commonswire.release import ReleaseError, collect, verify, write_release
from commonswire.release_text import card, licenses_md
from commonswire.sources import load_sources
from test_release import article, registry_csv

HELD_OLD = "cw_" + "cd" * 8


@pytest.fixture(autouse=True)
def series(monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 9), ("alpha", "beta"))
    monkeypatch.setitem(rel.SERIES, (9, 10), ("alpha", "beta", "gamma"))
    monkeypatch.setitem(rel.SERIES, (9, 11), ("alpha", "gamma"))


def world(tmp_path):
    reg_path = registry_csv(tmp_path)
    registry = load_sources(reg_path)
    takedowns = tmp_path / "takedowns.csv"
    takedowns.write_text("id,requested_on,basis\n")
    rows = {
        "alpha": [article("alpha", 1, "An invented first story."), article("alpha", 2, "Two.")],
        "beta": [article("beta", 1, "An invented beta story.", days=4)],
    }
    r = collect(tmp_path, "9.9.0", registry, rows=rows, takedowns_path=takedowns)
    prev = tmp_path / "prev"
    held = [{"id": HELD_OLD, "source_id": "beta", "published_on": "2026-09-02", "reason": "x"}]
    write_release(
        r,
        prev,
        reg_path,
        registry,
        card=card(r, registry, 0),
        licenses_md=licenses_md(r, registry),
        extra={"held_rows": held, "third_party_dropped": 3, "post_counts": {"beta": {"2026": 1}}},
    )
    rows_dir = tmp_path / "data" / "interim" / "rows"
    rows_dir.mkdir(parents=True)
    gamma = [
        article("gamma", 1, "An invented public record.", days=-30, authors=()),
        article("gamma", 2, "Two.", days=1, authors=()),  # the same text as alpha 2
        article(
            "gamma",
            3,
            "An invented held record.",
            authors=(),
            releasable=False,
            hold_reason="no byline: Gamma asks for the author's name",
        ),
    ]
    (rows_dir / "gamma.jsonl").write_text("".join(json.dumps(x) + "\n" for x in gamma))
    ev = tmp_path / "data" / "evidence" / "backfill"
    ev.mkdir(parents=True)
    (ev / "gamma.build.json").write_text(
        json.dumps({"dropped": {"third_party:elsewhere": 2, "answer:404": 5}})
    )
    return reg_path, registry, takedowns, prev


def test_a_new_series_keeps_the_published_rows_and_adds_the_new_sources(tmp_path):
    reg_path, registry, takedowns, prev = world(tmp_path)
    out = tmp_path / "out"
    manifest, problems = build_from_previous(
        tmp_path,
        prev,
        "9.10.0",
        out,
        registry_path=reg_path,
        registry=registry,
        takedowns_path=takedowns,
        baseline_path=tmp_path / "no-baseline.json",
        note="a test build",
    )
    assert problems == [] and verify(out) == []
    assert manifest["sources"] == ["alpha", "beta", "gamma"]
    assert manifest["built_from"] == {
        "from_version": "9.9.0",
        "new_sources": ["gamma"],
        "rows_from_previous": 3,
        "rows_of_new_sources": 3,
    }
    # alpha 1, alpha 2, beta 1, gamma 1; gamma 2 repeats alpha 2's text; gamma 3 is held.
    assert manifest["rows"] == 4
    assert manifest["exact_duplicates_dropped"] == {"same_text:gamma": 1}
    held = {h["id"]: h["source_id"] for h in manifest["held_rows"]}
    assert held[HELD_OLD] == "beta" and list(held.values()).count("gamma") == 1
    assert manifest["held_rows_not_released"] == {"beta": 1, "gamma": 1}
    assert manifest["third_party_dropped"] == 5
    assert manifest["post_counts"] == {"beta": {"2026": 1}}
    assert manifest["not_a_release"] == "a test build"
    assert third_party_of(tmp_path, "gamma") == 2 and third_party_of(tmp_path, "nobody") == 0


def test_build_from_refuses_what_it_must_not_do(tmp_path):
    reg_path, registry, takedowns, prev = world(tmp_path)
    kw = dict(
        registry_path=reg_path,
        registry=registry,
        takedowns_path=takedowns,
        baseline_path=tmp_path / "no-baseline.json",
    )
    full = tmp_path / "full"
    full.mkdir()
    (full / "x").write_text("x")
    with pytest.raises(ReleaseError, match="is not empty"):
        build_from_previous(tmp_path, prev, "9.10.0", full, **kw)
    with pytest.raises(ReleaseError, match="leaves out beta: a source is never dropped"):
        build_from_previous(tmp_path, prev, "9.11.0", tmp_path / "o2", **kw)
    (tmp_path / "data" / "interim" / "rows" / "gamma.jsonl").unlink()
    with pytest.raises(ReleaseError, match="no rows for gamma"):
        build_from_previous(tmp_path, prev, "9.10.0", tmp_path / "o3", **kw)
    (prev / "index.csv").write_text("changed\n")
    with pytest.raises(ReleaseError, match="fails its own check"):
        build_from_previous(tmp_path, prev, "9.10.0", tmp_path / "o4", **kw)


def test_cli_release_build_from(tmp_path, capsys):
    reg_path, _, takedowns, prev = world(tmp_path)
    out = tmp_path / "out"
    args = [
        "--root",
        str(tmp_path),
        "release",
        "build-from",
        "--from",
        str(prev),
        "--version",
        "9.10.0",
        "--out",
        str(out),
        "--sources",
        str(reg_path),
        "--takedowns",
        str(takedowns),
        "--baseline",
        str(tmp_path / "none.json"),
    ]
    assert main(args) == 0
    assert "version 9.10.0 from 9.9.0 plus gamma: 4 rows" in capsys.readouterr().out
    assert main(args) == 2
    assert "is not empty" in capsys.readouterr().err


def test_release_check_of_a_build_from_version_skips_the_corpus_report(tmp_path, capsys):
    reg_path, registry, takedowns, prev = world(tmp_path)
    out = tmp_path / "data" / "release" / "9.10.0-test"
    build_from_previous(
        tmp_path,
        prev,
        "9.10.0",
        out,
        registry_path=reg_path,
        registry=registry,
        takedowns_path=takedowns,
        baseline_path=tmp_path / "none.json",
    )
    assert main(["--root", str(tmp_path), "release", "check", "--version", "9.10.0-test"]) == 0
    got = capsys.readouterr().out
    assert "built by commonswire release build-from from 9.9.0" in got
    assert "all checks passed" in got
