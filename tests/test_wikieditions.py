"""Wikinews editions' dumps, invented. No network."""

from __future__ import annotations

import io
import re
from collections import Counter
from datetime import datetime, timezone

from commonswire.wikieditions import (
    EditionMarkers,
    file_names,
    file_url,
    first_revisions,
    read_edition,
    template_census,
    wiki_name,
)

NS = 'xmlns="http://www.mediawiki.org/xml/export-0.11/"'


def page(pid, title, text, ns=0, redirect=False, stamp="2020-05-01T10:00:00Z"):
    red = '<redirect title="x" />' if redirect else ""
    return (
        f"<page><title>{title}</title><ns>{ns}</ns><id>{pid}</id>{red}<revision><id>9{pid}</id>"
        f"<timestamp>{stamp}</timestamp><text>{text}</text></revision></page>"
    )


def dump(*pages):
    return io.BytesIO(f"<mediawiki {NS}>{''.join(pages)}</mediawiki>".encode())


def stub(*pages):
    body = ""
    for pid, stamps in pages:
        revs = "".join(
            f"<revision><id>{pid}{i}</id><timestamp>{s}</timestamp><contributor><id>5</id>"
            "</contributor></revision>"
            for i, s in enumerate(stamps)
        )
        body += f"<page><title>T{pid}</title><ns>0</ns><id>{pid}</id>{revs}</page>"
    return io.BytesIO(f"<mediawiki {NS}>{body}</mediawiki>".encode())


def test_names_and_addresses():
    assert wiki_name("wikinews_fr") == "frwikinews"
    assert file_names("wikinews_fr")["stubs"] == "frwikinews-latest-stub-meta-history.xml.gz"
    assert file_url("wikinews_ko", "x.gz") == "https://dumps.wikimedia.org/kowikinews/latest/x.gz"


def test_the_census_counts_templates_on_article_pages_once_each():
    pages, counts = template_census(
        dump(
            page(1, "A", "{{Publié}} words {{w|x}} {{w|y}}"),
            page(2, "B", "{{publié|2020}} words"),
            page(3, "Talk", "{{Publié}}", ns=1),
            page(4, "R", "{{Publié}}", redirect=True),
        )
    )
    assert pages == 2
    assert counts["publié"] == 2 and counts["w"] == 1


def test_first_revisions_take_each_pages_earliest_time():
    created = first_revisions(
        stub((1, ["2010-01-02T00:00:00Z", "2009-12-31T23:00:00Z"]), (2, ["2026-01-01T00:00:00Z"]))
    )
    assert created["1"] == datetime(2009, 12, 31, 23, tzinfo=timezone.utc)
    assert created["2"].year == 2026


def test_read_edition_keeps_published_articles_dated_by_their_creation():
    markers = EditionMarkers(
        published=re.compile(r"\{\{\s*publié", re.I),
        not_published=re.compile(r"\{\{\s*brouillon", re.I),
        closing=re.compile(r"^==\s*Sources\s*==", re.M),
    )
    created = {
        "1": datetime(2008, 3, 1, tzinfo=timezone.utc),
        "2": datetime(2009, 1, 1, tzinfo=timezone.utc),
    }
    skipped: Counter[str] = Counter()
    arts = list(
        read_edition(
            "wikinews_fr",
            dump(
                page(1, "Une histoire", "{{Publié}}\nDes mots inventés.\n== Sources ==\n* x"),
                page(2, "Brouillon", "{{Publié}}{{Brouillon}} Mots."),
                page(3, "Sans date", "{{Publié}} Mots."),
                page(4, "Non publié", "Mots."),
                page(5, "Discussion", "{{Publié}}", ns=1),
            ),
            created,
            skipped,
            markers,
        )
    )
    assert [a.title for a in arts] == ["Une histoire"]
    a = arts[0]
    assert a.published_at == datetime(2008, 3, 1, tzinfo=timezone.utc)
    assert a.url == "https://fr.wikinews.org/wiki/Une_histoire"
    assert "Sources" not in a.text and "inventés" in a.text
    assert skipped == Counter(
        {
            "marked_draft_or_under_review": 1,
            "no_first_revision": 1,
            "not_marked_published": 1,
            "not_an_article_namespace": 1,
        }
    )
