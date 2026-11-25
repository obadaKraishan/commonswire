"""Other-language versions from saved pages and link files, invented. No network."""

from __future__ import annotations

import json

from commonswire.cli import main
from commonswire.lingua import write_links
from commonswire.schema import canonical_url
from commonswire.versions import (
    global_voices_versions,
    hreflang_groups,
    hreflang_links,
    hreflang_versions,
    lingua_source,
    load_versions,
)

BS = "https://balkandiskurs.com/invented-prica/"
EN = "https://balkandiskurs.com/en/invented-story/"


def page(own, other, own_lang="bs", other_lang="en"):
    return f"""<html><head>
      <link rel="alternate" hreflang="{own_lang}" href="{own}" />
      <link rel='alternate' hreflang='{other_lang}' href='{other}' />
      <link rel="alternate" hreflang="x-default" href="{own}" />
      <link rel="alternate" type="application/rss+xml" href="https://balkandiskurs.com/feed/" />
      <link rel="canonical" href="{own}" />
      </head><body><a hreflang="fr" href="https://example.org/">not in the head</a></body></html>"""


def test_hreflang_links_read_the_head_only_and_skip_x_default():
    assert hreflang_links(page(BS, EN)) == {"bs": BS, "en": EN}
    assert hreflang_links("<html><head></head><body></body></html>") == {}
    bad = '<head><link rel="alternate" hreflang="en" href="not a url"></head>'
    assert hreflang_links(bad) == {}


def test_hreflang_groups_pair_the_editions():
    groups = hreflang_groups([page(BS, EN), page(EN, BS, "en", "bs"), "<head></head>"])
    assert groups[canonical_url(BS)] == (EN,)
    assert groups[canonical_url(EN)] == (BS,)


def test_hreflang_versions_by_source(tmp_path):
    for sid, (own, other, lo, lt) in {
        "balkandiskurs_bs": (BS, EN, "bs", "en"),
        "balkandiskurs": (EN, BS, "en", "bs"),
    }.items():
        folder = tmp_path / sid
        folder.mkdir()
        (folder / "a.html").write_text(page(own, other, lo, lt))
    out, counts = hreflang_versions(tmp_path)
    assert out["balkandiskurs_bs"][canonical_url(BS)]["other_versions"] == [EN]
    assert out["balkandiskurs"][canonical_url(EN)]["other_versions"] == [BS]
    assert counts["balkandiskurs_bs:rows_with_versions"] == 1


def test_lingua_source_of_an_address():
    assert lingua_source("https://globalvoices.org/2020/01/01/x/") == "globalvoices"
    assert lingua_source("https://zht.globalvoices.org/2020/01/01/1/") == "globalvoices_zht"


def test_global_voices_versions_and_the_cli(tmp_path, capsys):
    en = "https://globalvoices.org/2020/01/01/an-invented-story/"
    fr = "https://fr.globalvoices.org/2020/01/02/une-histoire/"
    interim = tmp_path / "data" / "interim"
    write_links(
        interim / "lingua" / "globalvoices_fr.links.json",
        {canonical_url(fr): {"url": fr, "en": en}},
    )
    by = interim / "bylines"
    by.mkdir(parents=True)
    (by / "globalvoices_fr.listing.json").write_text(
        json.dumps({canonical_url(fr): {"names": ["A"], "translators": ["T"]}})
    )
    out, counts = global_voices_versions(interim / "lingua", by)
    assert out["globalvoices_fr"][canonical_url(fr)] == {"other_versions": [en], "original_url": en}
    assert out["globalvoices"][canonical_url(en)]["original_url"] == ""
    assert counts["globalvoices_fr:with_original_url"] == 1
    (tmp_path / "data" / "raw" / "pages").mkdir(parents=True)
    assert main(["--root", str(tmp_path), "versions"]) == 0
    assert "globalvoices_fr:rows_with_versions: 1" in capsys.readouterr().out
    assert (
        load_versions(interim / "versions", "globalvoices_fr")[canonical_url(fr)]["original_url"]
        == en
    )
    assert load_versions(interim / "versions", "factly") == {}
