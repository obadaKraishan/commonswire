from __future__ import annotations

import csv

from commonswire.cli import blocked_pages, main
from commonswire.evidence import PAGE_FIELDS, ROBOTS_FIELDS
from commonswire.render import render_sources_md
from commonswire.sources import SOURCE_FIELDS, parse_row
from test_sources import row


def test_render_groups_by_status_and_quotes_the_evidence():
    inc = parse_row(row())
    pend = parse_row(
        row(
            source_id="b_news",
            name="B News",
            homepage="https://b.example.org/",
            license="NOASSERTION",
            license_url="",
            quote_license="",
            status="pending",
            reason="Does B News allow automatic republishing?",
            notes="robots shuts out CCBot",
        )
    )
    exc = parse_row(
        row(
            source_id="c_news",
            name="C News",
            homepage="https://c.example.org/",
            bulk_clause="forbids",
            quote_bulk="Do not republish automatically.",
            tracking_required="yes",
            status="exclude",
            reason="Forbids automatic republishing.",
            terms_url="",
            quote_attribution="",
        )
    )
    text = render_sources_md(
        [exc, pend, inc],
        [
            {
                "source_id": "c_news",
                "url": "https://c.example.org/x",
                "status": "403",
                "outcome": "blocked",
                "answer": "HTTP 403",
            },
            {
                "source_id": "c_news",
                "url": "https://c.example.org/y",
                "status": "",
                "outcome": "error",
            },
        ],
    )
    assert "3 sources checked: 1 include, 1 pending, 1 exclude." in text
    assert text.index("## Included") < text.index("## Pending") < text.index("## Excluded")
    assert '"All our stories are published under CC BY 4.0."' in text
    assert "no license named" in text and "Does B News allow automatic republishing?" in text
    assert "a tracking pixel or counter is required" in text
    assert "| c_news | <https://c.example.org/x> | HTTP 403 |" in text
    assert "| c_news | <https://c.example.org/y> | error |" in text
    assert "**Notes:** robots shuts out CCBot" in text
    assert "(no terms of use page found)" in text
    closed = parse_row(
        row(
            license="LicenseRef-all-rights-reserved",
            status="exclude",
            reason="No license.",
            license_url="",
        )
    )
    assert "all rights reserved" in render_sources_md([closed])


def _write(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def test_blocked_pages_and_the_render_command(tmp_path, capsys):
    ev = tmp_path / "data" / "evidence"
    base = {f: "" for f in PAGE_FIELDS}
    _write(
        ev / "pages.csv",
        PAGE_FIELDS,
        [
            {
                **base,
                "source_id": "a",
                "url": "https://a.org/",
                "outcome": "blocked",
                "status": "403",
            },
            {**base, "source_id": "b", "url": "https://b.org/", "outcome": "disallowed"},
            {**base, "source_id": "c", "url": "https://c.org/", "outcome": "disallowed"},
            {**base, "source_id": "d", "url": "https://d.org/", "outcome": "ok"},
            {**base, "source_id": "e", "url": "https://e.org/", "outcome": "blocked"},
            {
                **base,
                "source_id": "f",
                "url": "https://f.org/",
                "outcome": "blocked",
                "status": "200",
            },
            {**base, "source_id": "g", "url": "https://g.org/", "outcome": "disallowed"},
        ],
    )
    rb = {f: "" for f in ROBOTS_FIELDS}
    _write(
        ev / "robots.csv",
        ROBOTS_FIELDS,
        [
            {**rb, "source_id": "b", "state": "blocked", "robots_status": "403"},
            {**rb, "source_id": "c", "state": "present"},
            {**rb, "source_id": "g", "state": "unreachable"},
        ],
    )
    answers = [r["answer"] for r in blocked_pages(tmp_path)]
    assert answers == [
        "HTTP 403",
        "robots.txt answered HTTP 403",
        "robots.txt disallows the CommonsWire user agent",
        "a bot check page",
        "a bot check page",
        "robots.txt could not be reached",
    ]
    reg = tmp_path / "sources.csv"
    _write(reg, SOURCE_FIELDS, [row()])
    out = tmp_path / "sources.md"
    assert (
        main(
            ["--root", str(tmp_path), "sources", "render", "--sources", str(reg), "--out", str(out)]
        )
        == 0
    )
    assert out.read_text().startswith("# Sources")


def test_the_reason_code_is_shown_when_the_registry_has_one():
    from commonswire.render import paragraph

    coded = parse_row(row())
    assert "**Status: include.** Reason code `license_allows`." in paragraph(coded)
    legacy = parse_row({k: v for k, v in row().items() if k != "reason_code"})
    assert "Reason code" not in paragraph(legacy)
