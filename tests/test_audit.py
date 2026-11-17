from __future__ import annotations

import csv
import json

import pytest

from commonswire.audit import (
    COMPARISON_FIELDS,
    OTHER_LIST_FIELDS,
    compare,
    counts,
    read_other_lists,
    registry_class,
    tag_class,
    tagged_open,
)
from commonswire.cli import main
from commonswire.sources import load_sources, parse_row
from test_sources import row, write_csv

T = "2026-11-17T02:05:00Z"


def registry(tmp_path):
    rows = [
        row(source_id="alpha", name="Alpha", homepage="https://alpha.example/"),
        row(
            source_id="beta",
            name="Beta",
            homepage="https://beta.example/",
            license="CC-BY-ND-4.0",
            status="exclude",
            reason_code="bulk_clause",
            reason="no wholesale use",
            bulk_clause="forbids",
            quote_bulk="Do not republish our stories as a whole.",
        ),
        row(
            source_id="gamma",
            name="Gamma",
            homepage="https://gamma.example/",
            license="NOASSERTION",
            license_url="",
            quote_license="",
            robots="blocked",
            status="pending",
            reason_code="refused_requests",
            reason="Can the maintainer read it?",
        ),
        row(source_id="delta", name="Delta", homepage="https://delta.example/"),
    ]
    return write_csv(tmp_path, rows)


def fact(lst, sid, tag, **over):
    base = {
        "list": lst,
        "source_id": sid,
        "publisher": sid.title(),
        "list_homepage": f"https://{sid}.example/",
        "tag": tag,
        "tag_from": "code" if lst == "common_pile" else "feeds.csv",
        "documents": "",
        "named_in": "card;code;data" if lst == "common_pile" else "English",
        "active": "" if lst == "common_pile" else "1",
        "read_from": "https://lists.example/x",
        "read_at": T,
    }
    base.update(over)
    return base


def write_lists(tmp_path, rows, fields=OTHER_LIST_FIELDS):
    path = tmp_path / "other_lists.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.mark.parametrize(
    ("tag", "cls"),
    [
        ("CC BY", "by"),
        ("CC-BY", "by"),
        ("CC BY-SA", "by-sa"),
        ("CC-BY-SA", "by-sa"),
        ("Public Domain", "pd"),
        ("public-domain", "pd"),
        ("CC0", "pd"),
        ("CC BY-NC-ND", "nc-nd"),
        ("CC BY-ND", "nc-nd"),
        ("CC BY-NC-SA", "nc-nd"),
        ("Attribution+", "other"),
    ],
)
def test_tag_class(tag, cls):
    assert tag_class(tag) == cls


def test_registry_class():
    assert registry_class(parse_row(row())) == "by"
    assert registry_class(parse_row(row(license="CC-BY-SA-3.0"))) == "by-sa"
    assert registry_class(parse_row(row(license="public-domain"))) == "pd"
    assert registry_class(parse_row(row(license="CC-BY-NC-ND-4.0"))) == "nc-nd"
    assert registry_class(parse_row(row(license="NOASSERTION"))) == "none"
    assert registry_class(parse_row(row(license="LicenseRef-all-rights-reserved"))) == "closed"


def test_compare_says_what_each_list_gives_and_whether_it_agrees(tmp_path):
    reg = load_sources(registry(tmp_path))
    other = [
        fact("common_pile", "alpha", "CC-BY", documents="120"),
        fact("open_newswire", "alpha", "CC BY"),
        fact("common_pile", "beta", "CC-BY", documents="7"),
        fact("open_newswire", "beta", "CC BY-ND", active="0"),
        fact("open_newswire", "gamma", "CC BY"),
    ]
    rows = {r["source_id"]: r for r in compare(reg, other)}
    assert list(rows) == ["alpha", "beta", "delta", "gamma"]
    assert all(list(r) == COMPARISON_FIELDS for r in rows.values())
    a, b, g, d = rows["alpha"], rows["beta"], rows["gamma"], rows["delta"]
    assert a["common_pile_tag"] == "CC-BY" and a["common_pile_documents"] == "120"
    assert a["common_pile_named_in"] == "card;code;data" and a["lists_agree"] == "yes"
    assert b["open_newswire_tag"] == "CC BY-ND" and b["open_newswire_active"] == "0"
    assert b["class_here"] == "nc-nd" and b["lists_agree"] == "no"
    assert g["class_here"] == "none" and g["lists_agree"] == "unread"
    assert d["lists_agree"] == "" and d["common_pile_tag"] == "" and d["open_newswire_tag"] == ""
    assert tagged_open(a) and tagged_open(b) and not tagged_open(d)
    assert tagged_open(b, ["common_pile"]) and not tagged_open(b, ["open_newswire"])

    c = counts(rows.values())
    assert c["registry"]["publishers"] == 4
    assert c["registry"]["by_status"] == {"exclude": 1, "include": 2, "pending": 1}
    either = c["tagged_open_by_either"]
    assert either["publishers"] == 3 and either["lists_disagree"] == 1
    assert either["by_status_and_reason"] == {
        "exclude:bulk_clause": 1,
        "include:license_allows": 1,
        "pending:refused_requests": 1,
    }
    assert c["tagged_open_by_open_newswire"]["publishers"] == 2


@pytest.mark.parametrize(
    ("over", "message"),
    [
        ({"list": "somewhere"}, "list must be common_pile or open_newswire"),
        ({"source_id": "omega"}, "'omega' is not in the registry"),
        ({"documents": "many"}, "documents must be a whole number"),
        ({"read_at": "yesterday"}, "read_at must be a time"),
    ],
)
def test_other_lists_are_checked_line_by_line(tmp_path, over, message):
    reg = load_sources(registry(tmp_path))
    rows = [fact("common_pile", "alpha", "CC-BY"), fact("common_pile", "alpha", "CC-BY")]
    rows[1].update(over)
    path = write_lists(tmp_path, rows)
    with pytest.raises(ValueError, match=f"line 3: {message}"):
        read_other_lists(path, reg)


def test_other_lists_header_must_match(tmp_path):
    reg = load_sources(registry(tmp_path))
    path = write_lists(tmp_path, [], fields=["list", "source_id"])
    with pytest.raises(ValueError, match="the header must be list, source_id, publisher"):
        read_other_lists(path, reg)


def test_cli_audit_compare_writes_the_table_and_prints_counts(tmp_path, capsys):
    reg = registry(tmp_path)
    lists = write_lists(tmp_path, [fact("common_pile", "alpha", "CC-BY", documents="3")])
    out = tmp_path / "audit" / "comparison.csv"
    args = ["audit", "compare", "--sources", str(reg), "--lists", str(lists), "--out", str(out)]
    assert main(args) == 0
    printed = capsys.readouterr().out
    assert "4 publishers, 1 facts from other lists" in printed
    numbers = json.loads(printed[printed.index("{") :])
    assert numbers["tagged_open_by_common_pile"]["publishers"] == 1
    with out.open(newline="", encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert [r["source_id"] for r in got] == ["alpha", "beta", "delta", "gamma"]
