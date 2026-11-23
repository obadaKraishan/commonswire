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


def test_cli_census_and_rows_of_an_edition(tmp_path, monkeypatch, capsys):
    import bz2
    import gzip
    import json

    from commonswire import wikieditions
    from commonswire.cli import main
    from test_sources import row, write_csv

    root = tmp_path
    reg = write_csv(
        tmp_path,
        [
            row(
                source_id="wikinews_en",
                name="Wikinews",
                homepage="https://en.wikinews.org/",
                license="CC-BY-2.5",
                credit_line="{title}, {source} ({url}), {license}",
                access="dump",
            ),
            row(
                source_id="wikinews_ko",
                name="Wikinews (ko)",
                homepage="https://ko.wikinews.org/",
                languages="ko",
                edition_of="wikinews_en",
                license="CC-BY-2.5",
                credit_line="{title}, {source} ({url}), {license}",
                access="dump",
            ),
        ],
    )
    folder = root / "data" / "raw" / "backfill" / "wikinews_ko" / "R"
    folder.mkdir(parents=True)
    names = wikieditions.file_names("wikinews_ko")
    arts = dump(
        page(1, "옛 기사", "{{발행}} 가나다 라마바 사아자."),
        page(2, "기사", "{{발행}} 차카타 파하 가나."),
        page(3, "새 기사", "{{발행}} 다라마 바사 아자."),
        page(4, "초안", "가나다."),
    ).getvalue()
    (folder / names["articles"]).write_bytes(bz2.compress(arts))
    stubs = stub(
        (1, ["2004-05-01T00:00:00Z"]), (2, ["2010-05-01T00:00:00Z"]), (3, ["2020-05-01T00:00:00Z"])
    ).getvalue()
    (folder / names["stubs"]).write_bytes(gzip.compress(stubs))
    base = [
        "--root",
        str(root),
        "wikinews-edition",
        "wikinews_ko",
        "--run",
        "R",
        "--sources",
        str(reg),
    ]
    assert main([*base, "--census"]) == 0
    census = json.loads((root / "data/evidence/wikinews/wikinews_ko.census.json").read_text())
    assert census["article_pages"] == 4 and census["templates"]["발행"] == 3
    assert main(base) == 2  # no markers yet
    monkeypatch.setitem(
        wikieditions.EDITION_MARKERS,
        "wikinews_ko",
        EditionMarkers(published=re.compile(r"\{\{\s*발행")),
    )
    assert main(base) == 0
    rows = [
        json.loads(x)
        for x in (root / "data/interim/rows/wikinews_ko.jsonl").read_text().splitlines()
    ]
    by_title = {r["title"]: r for r in rows}
    assert by_title["옛 기사"]["license"] == "public-domain"
    assert by_title["기사"]["license"] == "CC-BY-2.5" and by_title["기사"]["releasable"]
    assert not by_title["새 기사"]["releasable"]
    assert by_title["새 기사"]["hold_reason"].startswith("license date not placed")
    assert all(r["language"] == "ko" for r in rows)
    info = json.loads((root / "data/evidence/backfill/wikinews_ko.build.json").read_text())
    assert info["held"] == 1 and info["skipped"] == {"not_marked_published": 1}
    assert info["by_license"]["held:license date not placed"] == 1
    assert "not_a_wikinews" not in capsys.readouterr().err
    other = [
        "--root",
        str(root),
        "wikinews-edition",
        "wikinews_en",
        "--run",
        "R",
        "--sources",
        str(reg),
    ]
    assert main(other) == 2


# ---- notices of a page's own ----

from commonswire.wikieditions import notice_differs, page_notices  # noqa: E402


def test_page_notices_name_the_licenses_of_templates_and_statements():
    assert page_notices("Mots inventés. {{w|Paris}}") == []
    assert page_notices("{{CC-BY-SA-4.0}} Mots.") == ["CC-BY-SA-4.0"]
    assert page_notices("{{cc-by-2.5|x}} Mots.") == ["CC-BY-2.5"]
    assert page_notices("{{GFDL}} Mots.") == ["unknown"]
    assert page_notices("{{PD-self}} Mots.") == ["public-domain"]
    assert page_notices("{{Domaine public}}") == ["public-domain"]
    assert page_notices("Ce texte est sous licence Creative Commons BY-SA 3.0.") == ["CC-BY-SA-3.0"]
    assert page_notices("Publié sous CC BY-NC-ND 4.0.") == ["CC-BY-NC-ND-4.0"]
    assert page_notices("© 2010 Une agence inventée. Tous droits réservés.") == ["rights-reserved"]
    assert page_notices("Copyright 2010 An invented agency.") == ["rights-reserved"]
    # a story about copyright is not a notice
    assert page_notices("The invented court ruled on a copyright case.") == []


def test_an_images_notice_is_not_the_pages_own():
    text = (
        "Mots inventés. [[Fichier:Photo inventée.jpg|vignette|© Un photographe, CC BY-SA 4.0]]"
        "<gallery>Image:Autre.png|© Quelqu'un</gallery> Fin."
    )
    assert page_notices(text) == []


def test_a_page_is_held_only_when_its_own_notice_differs_from_the_table():
    assert not notice_differs("Mots.", "CC-BY-2.5")
    assert not notice_differs("{{CC-BY-2.5}} Mots.", "CC-BY-2.5")
    assert notice_differs("{{CC-BY-SA-4.0}} Mots.", "CC-BY-2.5")
    assert notice_differs("{{Copyright}} Mots.", "CC-BY-2.5")
    assert notice_differs("© Agence inventée.", "public-domain")
    assert not notice_differs("{{PD}} Mots.", "public-domain")
    # one agreeing and one differing notice: held
    assert notice_differs("{{CC-BY-2.5}} Extrait sous CC BY-SA 3.0.", "CC-BY-2.5")


def test_the_edition_command_holds_and_counts_pages_with_their_own_differing_notice(
    tmp_path, monkeypatch
):
    import bz2
    import gzip
    import json

    from commonswire import wikieditions
    from commonswire.cli import main
    from test_sources import row, write_csv

    reg = write_csv(
        tmp_path,
        [
            row(
                source_id="wikinews_en",
                name="Wikinews",
                homepage="https://en.wikinews.org/",
                license="CC-BY-2.5",
                credit_line="{title}, {source} ({url}), {license}",
            ),
            row(
                source_id="wikinews_fr",
                name="Wikinews (fr)",
                homepage="https://fr.wikinews.org/",
                languages="fr",
                edition_of="wikinews_en",
                license="CC-BY-2.5",
                credit_line="{title}, {source} ({url}), {license}",
                access="dump",
            ),
        ],
    )
    folder = tmp_path / "data" / "raw" / "backfill" / "wikinews_fr" / "R"
    folder.mkdir(parents=True)
    names = wikieditions.file_names("wikinews_fr")
    arts = dump(
        page(1, "Sans avis", "{{Publié}} Des mots inventés, un."),
        page(2, "Avis égal", "{{Publié}}{{CC-BY-2.5}} Des mots inventés, deux."),
        page(3, "Avis autre", "{{Publié}} Des mots inventés, trois. Texte sous CC BY-SA 3.0."),
        page(4, "Droits", "{{Publié}} Des mots inventés, quatre. © Une agence inventée."),
    ).getvalue()
    (folder / names["articles"]).write_bytes(bz2.compress(arts))
    stubs = stub(*[(i, ["2010-05-01T00:00:00Z"]) for i in (1, 2, 3, 4)]).getvalue()
    (folder / names["stubs"]).write_bytes(gzip.compress(stubs))
    monkeypatch.setitem(
        wikieditions.EDITION_MARKERS,
        "wikinews_fr",
        EditionMarkers(published=re.compile(r"\{\{\s*publié", re.I)),
    )
    base = [
        "--root",
        str(tmp_path),
        "wikinews-edition",
        "wikinews_fr",
        "--run",
        "R",
        "--sources",
        str(reg),
    ]
    assert main(base) == 0
    rows = {
        r["title"]: r
        for r in map(
            json.loads, (tmp_path / "data/interim/rows/wikinews_fr.jsonl").read_text().splitlines()
        )
    }
    assert rows["Sans avis"]["releasable"] and rows["Avis égal"]["releasable"]
    assert not rows["Avis autre"]["releasable"] and not rows["Droits"]["releasable"]
    assert rows["Droits"]["hold_reason"].startswith("own notice differs")
    info = json.loads((tmp_path / "data/evidence/backfill/wikinews_fr.build.json").read_text())
    assert info["by_license"] == {"CC-BY-2.5": 2, "held:own notice differs": 2}
