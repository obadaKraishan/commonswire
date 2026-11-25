"""Wikinews dump tests with an invented mini dump. Nothing here touches the network."""

from __future__ import annotations

import bz2
import csv
import io
import json
from collections import Counter

import pytest

from commonswire import cli
from commonswire.sources import SOURCE_FIELDS
from commonswire.wikidump import (
    DUMP_URL,
    MD5_URL,
    expected_md5,
    md5_of,
    parse_date,
    read_dump,
    wiki_to_text,
)
from fakes import FakeTransport, make_test_client
from test_sources import row

WIKI = """{{date|May 1, 2026}}
<!-- a hidden comment -->
'''Invented''' town elects a council, says [[w:Invented Town|the town]]'s clerk.<ref>A ref</ref>
{{Infobox|nested={{inner|x}}}}
[[File:Invented.jpg|thumb|A caption that must go]]
{| class="wikitable"
| a table cell
|}
* An invented list item with [[Invented link]] and [http://example.org an external link].

== Reactions ==
An invented reaction.<br/>
{{publish}}
[[Category:Invented]]
[[fr:Ville inventée]]

== Sources ==
* {{source|url=http://example.org|title=Invented source}}
"""


def test_wiki_to_text_strips_markup_and_stops_at_sources():
    assert wiki_to_text(WIKI) == (
        "Invented town elects a council, says the town's clerk.\n\n"
        "An invented list item with Invented link and an external link.\n\n"
        "Reactions\n\nAn invented reaction."
    )


def test_parse_date():
    assert parse_date("May 1, 2026").day == 1
    assert parse_date("1 May 2026").month == 5
    assert parse_date("2026-05-01").year == 2026
    assert parse_date("sometime") is None


def page(title, ns, text, ts="2026-05-02T10:00:00Z", redirect=False):
    red = '<redirect title="x"/>' if redirect else ""
    return (
        f"<page><title>{title}</title><ns>{ns}</ns><id>1</id>{red}<revision><id>2</id>"
        f"<timestamp>{ts}</timestamp><text>{text}</text></revision></page>"
    )


def dump_bytes():
    esc = WIKI.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    pages = [
        page("Invented town elects council", 0, esc),
        page("Talk:Something", 1, "talk"),
        page("Old name", 0, "#REDIRECT [[Invented town elects council]]", redirect=True),
        page("Draft story", 0, "{{date|May 2, 2026}} {{develop}} {{publish}} text"),
        page("Unmarked", 0, "{{date|May 3, 2026}} text"),
        page("Undated", 0, "{{publish}} text"),
        page("Only markup", 0, "{{date|May 4, 2026}}{{publish}}{{infobox}}"),
        page(
            "Early story",
            0,
            "{{date|January 9, 2005}}{{archive}}Invented 2005 text.",
            ts="2004-01-01T00:00:00Z",
        ),
        page("Wire story", 0, "{{date|May 5, 2026}}{{publish}}Invented wire text. © 2026 Wire"),
    ]
    xml = (
        '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
        + "".join(pages)
        + "</mediawiki>"
    )
    return bz2.compress(xml.encode("utf-8"))


def test_read_dump_keeps_published_articles_and_counts_every_skip():
    skipped = Counter()
    arts = list(read_dump(bz2.BZ2File(io.BytesIO(dump_bytes())), skipped))
    assert [a.title for a in arts] == ["Invented town elects council", "Early story", "Wire story"]
    assert arts[0].url == "https://en.wikinews.org/wiki/Invented_town_elects_council"
    assert arts[1].last_edit is None  # an edit time before the date line is not an update
    assert skipped == {
        "not_an_article_namespace": 1,
        "redirect": 1,
        "marked_draft_review_or_abandoned": 1,
        "not_marked_published": 1,
        "no_date": 1,
        "empty_text": 1,
    }


def test_expected_md5():
    sums = "abc  enwikinews-20261101-pages-articles.xml.bz2\n"
    sums += "xyz  enwikinews-20261101-pages-meta.xml.bz2\n"
    assert expected_md5(sums) == "abc"
    assert expected_md5("nothing here") is None


def test_cli_downloads_once_checks_md5_and_builds(tmp_path, monkeypatch, capsys):
    reg = tmp_path / "sources.csv"
    with reg.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerow(
            row(
                source_id="wikinews_en",
                name="Wikinews",
                homepage="https://en.wikinews.org/",
                license="CC-BY-2.5",
                access="dump",
                credit_line="{title}, Wikinews ({url}), {license}",
            )
        )
    data = dump_bytes()
    (tmp_path / "probe.bz2").write_bytes(data)
    digest = md5_of(tmp_path / "probe.bz2")
    t = FakeTransport().add(
        "https://dumps.wikimedia.org/robots.txt", (200, "User-agent: *\nAllow: /\n")
    )
    t.add(MD5_URL, (200, f"{digest}  enwikinews-20261101-pages-articles.xml.bz2\n"))
    t.add(DUMP_URL, (200, data))

    def fake_make_client(root, *, byte_budget=None, transport=None):
        client, _ = make_test_client(root / "data", t, byte_budget=byte_budget)
        return client

    monkeypatch.setattr("commonswire.http.make_client", fake_make_client)
    root = ["--root", str(tmp_path)]
    assert cli.main([*root, "wikinews-dump", "--run", "r", "--sources", str(reg)]) == 2
    (tmp_path / "data" / "raw").mkdir(parents=True)
    assert (
        cli.main([*root, "wikinews-dump", "--run", "r", "--download", "--sources", str(reg)]) == 0
    )
    out = capsys.readouterr().out
    assert "kept 3 (1 held" in out and "validate: 0 errors" in out
    rows = (tmp_path / "data" / "interim" / "rows" / "wikinews_en.jsonl").read_text().splitlines()
    assert '"license":"CC-BY-4.0"' in rows[0] and '"license":"public-domain"' in rows[1]
    # Its own copyright notice differs from its date's license: held, counted by kind.
    wire = json.loads(rows[2])
    assert not wire["releasable"]
    assert wire["hold_reason"].startswith("own notice differs (a third party's copyright): ")
    info = json.loads(
        (tmp_path / "data" / "evidence" / "backfill" / "wikinews_en.build.json").read_text()
    )
    assert info["held"] == {"own notice differs (a third party's copyright)": 1}
    calls = len(t.calls)
    assert (
        cli.main([*root, "wikinews-dump", "--run", "r", "--download", "--sources", str(reg)]) == 0
    )
    assert len(t.calls) == calls  # downloaded once
    sums = tmp_path / "data" / "raw" / "backfill" / "wikinews_en" / "r" / "md5sums.txt"
    sums.chmod(0o644)
    sums.write_text("0000  enwikinews-20261101-pages-articles.xml.bz2\n")
    assert cli.main([*root, "wikinews-dump", "--run", "r", "--sources", str(reg)]) == 1


@pytest.mark.parametrize(
    "wikitext, text",
    [
        # Templates that show words keep them; named parameters are left out.
        ("Said {{w|Invented Town}} today.", "Said Invented Town today."),
        ("Said {{w|Invented Town|the town|nocat=1}}.", "Said the town."),
        ("A {{wikt|neologism}} and {{W|Place|}}.", "A neologism and Place."),
        ("On {{nowrap|1 May}}.", "On 1 May."),
        (
            "He said {{translated quote|xx|Invented language|Original words|Invented words}}.",
            'He said "Invented words".',
        ),
        # Every other template goes, with any template inside it.
        ("A {{image|caption={{w|Invented}} here|x=1}}B.", "A B."),
        ("A {{q|An invented pull-quote}}B.", "A B."),
        # A template that is never closed removes only its opener, not the rest of the text.
        (
            "{{Infobox\n| name = Invented\n| size = 9.9\nThe invented story goes on.",
            "The invented story goes on.",
        ),
        # Slips in the wikitext.
        ("A {[w|Invented Place}} b.", "A Invented Place b."),
        ("A {{w|Invented Place} b.", "A Invented Place b."),
        ("A {w|Invented Place}} b.", "A Invented Place b."),
        ("A {w|Invented Place|the place} b.", "A the place b."),
        ("A {{w|Invented Place]] b.", "A Invented Place b."),
        ("A [[w|Invented Place}} b.", "A Invented Place b."),
        ("A {{coord|9.9|lat=1} b.", "A b."),
        # Links: innermost first; a file whose caption holds links and an external link goes.
        (
            "A [[File:Invented.jpg|thumb|Caption [[Invented]] [http://example.org ext]]] B.",
            "A B.",
        ),
        ("A [[w:Invented Target|the label|]] B.", "A the label B."),
        ("A [[Invented Target|label] B.", "A label B."),
        ("A [Invented Target|label]] B.", "A label B."),
        ("A stray ]] and [[ B.", "A stray and B."),
        # Editorial brackets in quotes are text and stay.
        ('"[T]he invented [...] plan," she said.', '"[T]he invented [...] plan," she said.'),
        # Character references are decoded; a bare ampersand is left alone.
        ("A&nbsp;B &mdash; C &#8212; D &#x2014; AT&T &amp;ndash;", "A B — C — D — AT&T &ndash;"),
        # Map and chart JSON is not text; a line break is a break.
        ('A <mapframe width="200">{"type": "Feature", "x": [1, 2]}</mapframe>B.', "A B."),
        ('A <maplink zoom="5"/>B.', "A B."),
        ("Line one<br />Line two", "Line one\n\nLine two"),
        # Apostrophes: italic, bold, both, and a real one before bold.
        ("''Invented'' '''Bold''' '''''Both''''' ''''Quoted'''", "Invented Bold Both 'Quoted"),
        # Leftover table and parameter lines go; a closed table goes whole.
        ("Text.\n{|\n| cell\n|-\n| cell\n|}\nMore.", "Text.\n\nMore."),
        ("Text.\n|-\n| key = value\n!head | cell\nMore.", "Text.\n\nMore."),
    ],
)
def test_wiki_to_text_markup_cases(wikitext, text):
    assert wiki_to_text(wikitext) == text
