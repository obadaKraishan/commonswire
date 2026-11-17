"""The page fetchers, on invented pages in each source's markup (no network)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from commonswire.cli import main
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.pages import (
    AfricaIsACountryFetcher,
    SciDevNetFetcher,
    jsonld_nodes,
)
from commonswire.html import element_html
from commonswire.pagebackfill import URLS_FILE, build_page_rows, page_paths
from commonswire.sources import parse_row
from fakes import FakeTransport, make_test_client
from test_sources import row

SD_CREDIT = "{title}, by {authors}, {source} ({url}), {license}"


def scidev_source():
    return parse_row(
        row(
            source_id="scidevnet",
            name="SciDev.Net",
            homepage="https://www.scidev.net/global/",
            license="CC-BY-2.0",
            credit_line=SD_CREDIT,
            access="sitemap",
        )
    )


def aiac_source():
    return parse_row(
        row(
            source_id="africasacountry",
            name="Africa Is a Country",
            homepage="https://africasacountry.com/",
            license="CC-BY-4.0",
            credit_line=SD_CREDIT,
            access="listing",
        )
    )


LICENSE_FOOTER = (
    "<footer><p>All site content, except where otherwise noted, is licensed under a "
    '<a href="https://www.scidev.net/global/content/media.html">Creative Commons Attribution '
    "License</a></p></footer>"
)


def scidev_page(
    *,
    byline='By: <a href="/global/x/">Ana Invented</a>',
    body=None,
    ld_date=True,
    footer=LICENSE_FOOTER,
):
    body = body or (
        "<p>An invented first paragraph about a made-up study.</p>"
        "<figure><img src='x.jpg'><figcaption>© Someone Else 2026</figcaption></figure>"
        "<p>An invented second paragraph.</p><p>© SciDev.Net 2026</p>"
    )
    page = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "datePublished": "2026-11-14T10:00:00+00:00" if ld_date else "",
                "dateModified": "2026-11-15T09:00:00+00:00",
            }
        ],
    }
    art = {
        "@type": "Article",
        "headline": "An invented headline &amp; more",
        "datePublished": "2026-11-14 10:00:00",
        "author": {"@type": "Person", "name": "The Account That Posted"},
    }
    return (
        "<html><head>"
        f'<script type="application/ld+json">{json.dumps(page)}</script>'
        f'<script type="application/ld+json">{json.dumps(art)}</script>'
        "</head><body>"
        '<h4 class="fl-heading"><span>14/11/26</span></h4>'
        '<h4 class="share-widget-heading">Share this:</h4>'
        f"<div class='fl-html'><h4><strong>{byline}</strong></h4></div>"
        '<div class="fl-module fl-module-fl-post-content fl-node-1">'
        f'<div class="fl-module-content">{body}</div></div>'
        '<div class="republish-popup"><textarea>&lt;p&gt;copy&lt;/p&gt;</textarea></div>'
        f"{footer}</body></html>"
    )


def aiac_page(*, date="07.15.2026", authors=("Ana Invented",), body=None):
    names = "".join(
        f'<dd class="po-hr-cn__author"><a class="po-hr-cn__author-link" href="/a">{a}</a></dd>'
        for a in authors
    )
    body = body or (
        '<p class="po-bo__paragraph">An invented essay paragraph.</p>'
        '<p class="po-bo__paragraph">Another invented paragraph.</p>'
    )
    return (
        '<html><body><article class="po__article"><header class="po-hr">'
        f'<footer class="po-hr-fl"><time class="po-hr-fl__date" datetime="undefined">{date}</time>'
        "</footer>"
        '<section class="po-hr-cn"><h1 class="po-hr-cn__title">An invented title</h1>'
        '<div class="po-hr-cn__contributors"><dl class="po-hr-cn__authors">'
        f'<dt class="po-hr-cn__byline">By</dt>{names}</dl></div></section></header>'
        f'<div class="po__main"><div class="po-bo__content"><div class="po-bo__content">{body}'
        '</div></div><footer class="po-fr"><section class="po-fr__bios"><p>A bio.</p>'
        "</section></footer></div></article></body></html>"
    )


def fetcher(cls, source, tmp_path):
    client, _ = make_test_client(tmp_path, FakeTransport())
    return cls(client, source, ReplayStore(tmp_path / "rs"))


def test_element_html_takes_the_whole_nested_element():
    html = '<div class="a"><div class="b x">in <div>deeper</div> b</div> after</div><p>z</p>'
    assert element_html(html, "b") == '<div class="b x">in <div>deeper</div> b</div>'
    assert element_html(html, "a").endswith("after</div>")
    assert element_html(html, "missing") is None
    assert element_html('<span class="b">s</span><div class="b">d</div>', "b", "div") == (
        '<div class="b">d</div>'
    )


def test_jsonld_nodes_reads_graphs_and_skips_broken_blocks():
    page = scidev_page() + '<script type="application/ld+json">{broken</script>'
    types = [n.get("@type") for n in jsonld_nodes(page)]
    assert types == ["WebPage", "Article"]


def test_scidev_reads_the_visible_byline_never_the_posting_account(tmp_path):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    url = "https://www.scidev.net/global/news/an-invented-story/"
    item = f.item_from_page(url, scidev_page())
    assert item.authors == ("Ana Invented",)
    assert item.title == "An invented headline & more"
    assert item.published_at == datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
    assert item.updated_at == datetime(2026, 11, 15, 9, tzinfo=timezone.utc)
    assert item.section == "news" and f.third_party_reason(item) is None
    art = f.build(item, datetime(2026, 11, 17, tzinfo=timezone.utc))
    assert art.releasable and art.license == "CC-BY-2.0"
    assert (
        art.text
        == "An invented first paragraph about a made-up study.\n\nAn invented second paragraph."
    )
    assert "by Ana Invented, SciDev.Net" in art.credit_line
    two = scidev_page(byline='By: <a href="/a">Ana Invented</a> and <a href="/b">Bo Made</a>')
    assert f.item_from_page(url, two).authors == ("Ana Invented", "Bo Made")


def test_scidev_with_no_byline_is_held_and_the_source_itself_is_released(tmp_path):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    url = "https://www.scidev.net/global/news/x/"
    none = f.build(f.item_from_page(url, scidev_page(byline="")), datetime.now(timezone.utc))
    assert not none.releasable and "asks for the author's name" in none.hold_reason
    own = f.item_from_page(url, scidev_page(byline='By: <a href="/s">SciDev.Net</a>'))
    assert own.authors == () and own.hints["byline_is_source"]
    assert f.build(own, datetime.now(timezone.utc)).releasable


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("<p>Invented text.</p><p>© Another Outlet 2025</p>", "another holder's copyright"),
        ("<p>This article was originally published by an invented outlet.</p>", "elsewhere"),
        ("<p>Invented text.</p><p>Header image: © Somebody/Agency</p>", None),
    ],
)
def test_scidev_third_party_rules(tmp_path, body, reason):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    item = f.item_from_page("https://www.scidev.net/global/news/x/", scidev_page(body=body))
    got = f.third_party_reason(item)
    assert (got is None) if reason is None else (reason in got)


def test_scidev_pages_that_are_not_articles_are_refused(tmp_path):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    with pytest.raises(ValueError, match="no title or no dated JSON-LD"):
        f.item_from_page("https://www.scidev.net/global/x/", scidev_page(ld_date=False))
    with pytest.raises(ValueError, match="no post-content module"):
        no_body = (
            '<meta property="og:title" content="An invented title">'
            "<script type='application/ld+json'>"
            '{"@type": "WebPage", "datePublished": "2026-01-01T00:00:00+00:00"}</script>'
        )
        f.item_from_page("https://www.scidev.net/global/x/", no_body)
    with pytest.raises(NotImplementedError, match="backfill-pages"):
        next(f.items(1))


def test_africa_is_a_country_reads_its_header_and_body(tmp_path):
    f = fetcher(AfricaIsACountryFetcher, aiac_source(), tmp_path)
    url = "https://africasacountry.com/2026/07/an-invented-essay"
    item = f.item_from_page(url, aiac_page(authors=("Ana Invented", "Bo Made")))
    assert item.title == "An invented title"
    assert item.published_at == datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert item.authors == ("Ana Invented", "Bo Made")
    art = f.build(item, datetime(2026, 11, 17, tzinfo=timezone.utc))
    assert art.text == "An invented essay paragraph.\n\nAnother invented paragraph."
    assert art.releasable and "A bio." not in art.text
    none = f.build(f.item_from_page(url, aiac_page(authors=())), datetime.now(timezone.utc))
    assert none.releasable and "by Africa Is a Country, Africa Is a Country" in none.credit_line
    with pytest.raises(ValueError, match="does not match the year and month"):
        f.item_from_page(url, aiac_page(date="08.15.2026"))
    with pytest.raises(ValueError, match="no title, date or body"):
        f.item_from_page(url, "<html><body>nothing here</body></html>")
    first = aiac_page(body='<p class="po-bo__paragraph">This essay first appeared in a zine.</p>')
    assert "elsewhere" in f.third_party_reason(f.item_from_page(url, first))


def test_build_page_rows_and_the_cli(tmp_path, capsys):
    import csv

    from commonswire.sources import SOURCE_FIELDS

    folder = tmp_path / "data" / "raw" / "backfill" / "scidevnet" / "r1"
    urls = [f"https://www.scidev.net/global/news/story-{i}/" for i in range(4)]
    (folder / "pages").mkdir(parents=True)
    (folder / URLS_FILE).write_text(json.dumps(urls))
    pages = [scidev_page(), scidev_page(byline=""), "<html>not an article</html>", None]
    for url, page in zip(urls, pages, strict=True):
        html_path, meta_path = page_paths(folder, url)
        status = "200" if page else "404"
        if page:
            html_path.write_text(page)
        meta_path.write_text(
            json.dumps({"url": url, "status": status, "retrieved_at": "2026-11-17T03:00:00+00:00"})
        )
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    out = tmp_path / "rows.jsonl"
    res = build_page_rows(f, folder, out)
    assert (res.seen, res.kept, res.releasable) == (3, 2, 1)
    assert res.dropped["answer:404"] == 1 and sum(res.dropped.values()) == 2
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    assert rows[0]["retrieved_at"].startswith("2026-11-17T03:00")

    reg = tmp_path / "sources.csv"
    with reg.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerow(
            row(
                **{k: getattr(scidev_source(), k) for k in ("source_id", "name")},
                homepage="https://www.scidev.net/global/",
                license="CC-BY-2.0",
                credit_line=SD_CREDIT,
                access="sitemap",
            )
        )
    args = ["--root", str(tmp_path), "build", "scidevnet", "--run", "r1", "--sources", str(reg)]
    assert main(args) == 0
    printed = capsys.readouterr().out
    assert "3 pages read, 2 rows kept (1 releasable" in printed and "0 errors" in printed
    summary = json.loads((tmp_path / "data/evidence/backfill/scidevnet.build.json").read_text())
    assert summary["kept"] == 2 and summary["run"] == "r1"


def test_only_a_republication_note_counts_not_a_sentence_in_the_essay():
    from commonswire.fetchers.pages import published_elsewhere

    long = "An invented sentence about invented things. " * 12
    middle = "\n\n".join(
        [long, long, f"{long} The invented novel first appeared in 1958, she said.", long, long]
    )
    assert not published_elsewhere(middle)
    assert published_elsewhere(f"{long}\n\n{long}\n\nThis essay first appeared in a zine.")
    assert published_elsewhere(
        f"A version of this piece was originally published elsewhere.\n\n{long}"
    )
    end = f"{long}\n\n{long}\n\n{long} It was first published in an invented journal."
    assert published_elsewhere(end)
    assert not published_elsewhere(f"{long}\n\n{long} which was first published in 1965.")


SD_FOOTER = LICENSE_FOOTER
SD_SUPPORTED = "https://www.scidev.net/global/supported-content/an-invented-piece/"
SD_OWN_BYLINE = (
    'By: <a href="https://www.scidev.net/global/author.ana-invented.html">Ana Invented</a>'
)


def supported_page(*, byline=SD_OWN_BYLINE, footer=SD_FOOTER, body=None):
    body = body or (
        "<p>An invented paragraph about an invented project.</p>"
        "<p><em>This article was supported by the Invented Fund.</em></p>"
    )
    return scidev_page(byline=byline, body=body, footer=footer)


def test_licenses_outside_captions():
    from commonswire.fetchers.pages import licenses_outside_captions

    cc = '<a href="https://creativecommons.org/licenses/by-nc/2.0/">CC BY-NC</a>'
    assert licenses_outside_captions(f"<p>Invented data, under {cc}.</p>") == 1
    assert licenses_outside_captions(f'<p class="wp-caption-text">A view. {cc}</p>') == 0
    assert licenses_outside_captions(f"<figure><img src='x'><p>{cc}</p></figure>") == 0
    assert licenses_outside_captions(f"<p>Photo: Someone / Flickr ({cc})</p>") == 0
    assert licenses_outside_captions("<p>No license link here.</p>") == 0


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({}, None),
        ({"byline": "By:"}, "supported content without a byline of its own"),
        (
            {"byline": 'By: <a href="https://partner.example/team/">Ana Invented</a>'},
            "supported content without a byline of its own",
        ),
        (
            {
                "byline": SD_OWN_BYLINE
                + ' and <a href="https://partner.example/b/">Ben Invented</a>'
            },
            "supported content without a byline of its own",
        ),
        ({"footer": ""}, "no site license line on the page"),
        (
            {
                "body": "<p>An invented paragraph.</p><p><em>This piece uses invented data, "
                'under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA'
                "</a>.</em></p>"
            },
            "another license named outside an image's caption",
        ),
        (
            {
                "body": "<p>An invented paragraph.</p><p>Photo: Invented / Flickr "
                '(<a href="https://creativecommons.org/licenses/by/2.0/">CC BY</a>)</p>'
            },
            None,
        ),
    ],
)
def test_supported_content_is_kept_only_when_it_is_scidevnets_own(tmp_path, kwargs, reason):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    item = f.item_from_page(SD_SUPPORTED, supported_page(**kwargs))
    assert item.section == "supported-content"
    assert f.third_party_reason(item) == reason


def test_the_license_checks_hold_for_every_section_the_byline_check_for_supported(tmp_path):
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    news = "https://www.scidev.net/global/news/an-invented-story/"
    item = f.item_from_page(news, supported_page(byline="By:", footer=""))
    assert not item.hints["license_line"] and not item.hints["byline_own"]
    assert f.third_party_reason(item) == "no site license line on the page"
    held = f.item_from_page(news, supported_page(byline="By:"))
    assert f.third_party_reason(held) is None  # held for no byline, not dropped
    cc = '<p>Data <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC</a>.</p>'
    other = f.item_from_page(news, supported_page(body=f"<p>An invented paragraph.</p>{cc}"))
    assert f.third_party_reason(other) == "another license named outside an image's caption"
    view = "https://www.scidev.net/global/opinions/an-invented-view/"
    assert f.item_from_page(view, supported_page()).hints["byline_own"] is True


def test_legacy_brackets_and_escaped_embed_code_are_cleaned(tmp_path):
    from commonswire.fetchers.pages import clean_legacy_body

    body = (
        '<p>An invented paragraph.</p><p>&lt;<a href="/x">An invented link</a>&gt;</p>'
        '<p><<a href="/y">A second invented link</a>></p>'
        "<td>&LT;div id=&#8217;player-1&#8242;&GT;&LT;/div&GT;&LT;script&GT;&LT;/script&GT;</td>"
        "<p>A sentence with 3 &lt; 4 in it.</p>"
    )
    cleaned = clean_legacy_body(body)
    assert '<a href="/x">An invented link</a>' in cleaned and "<<a" not in cleaned
    assert "player" not in cleaned and "An invented paragraph." in cleaned
    assert "3 &lt; 4" in cleaned  # one escaped bracket in a sentence is text, kept
    f = fetcher(SciDevNetFetcher, scidev_source(), tmp_path)
    url = "https://www.scidev.net/global/opinions/an-invented-view/"
    art = f.build(f.item_from_page(url, scidev_page(body=body)), datetime.now(timezone.utc))
    assert "An invented link" in art.text and "A second invented link" in art.text
    assert "player" not in art.text and "3 < 4" in art.text
