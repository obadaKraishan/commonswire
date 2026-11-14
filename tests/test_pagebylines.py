"""Bylines from article pages, with invented pages and names. Nothing here touches the network."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest

from commonswire.cli import main
from commonswire.daily import daily_wordpress, load_rows
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import GlobalVoicesFetcher
from commonswire.pagebylines import (
    SITE_MARKUP,
    PageBylineReader,
    byline_from_page,
    collect_page_bylines,
    is_person,
    load_page_bylines,
    names_by_url,
    page_file,
    source_credited,
    split_names,
)
from commonswire.schema import canonical_url
from fakes import FakeTransport, make_test_client
from test_backfill import backfill_post
from test_fetchers import gv_source

NOW = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)

PUBLIC_RECORD_PAGE = """<html><head>
<script type="application/ld+json">{"@graph": [
 {"@type": "Article", "@id": "#a", "author": {"@id": "#p1"}},
 {"@type": "Person", "@id": "#p1", "name": "Ivy Invented"}]}</script>
</head><body><header><div class="entry-meta"><span class="author-avatar"></span>
<span class="byline"><span>by</span> <span class="author vcard">
<a class="url fn n" href="/author/ivy/">Ivy Invented</a></span></span>
<span class="posted-on"><time>May 1, 2026</time></span></div></header>
<p>Invented body text.</p>
<aside><div class="entry-meta"><span class="byline"><a href="/author/x/">Other Writer</a></span>
</div></aside></body></html>"""

BALKAN_PAGE = """<html><head>
<script type="application/ld+json">{"@graph": [{"@type": "NewsArticle",
 "author": {"@type": "Person", "name": "Balkan Diskurs"}}]}</script></head><body>
<div class="single-meta d-flex"><div class="meta"><time>June 4th, 2014</time>
<p class="byline author vcard small m-0"><i class="fa fa-user-circle"></i>
<a href="/en/profile/ana/" rel="tag">Ana Invented</a> | <a href="/en/profile/bo/">Bo Made-Up</a>
</p></div></div><p>Invented body.</p>
<div class="card"><div class="card-footer clearfix"><time>2023</time>
<p class="byline author vcard small m-0 float-right"><a href="/en/profile/c/">Related Writer</a>
</p></div></div></body></html>"""

INFO360_PAGE = """<html><body><div class="post-meta-container">
<div class="post-meta-authors"><div class="post-authors"><span>Authors</span>
<strong>Dana Invented</strong><br>Invented University<br><br>
<strong>Eli Made-Up</strong><br>Another Invented Institute<br><br></div></div>
<div class="post-meta-editors"><div class="post-authors"><span>Editors</span>
<strong>Fay Editor</strong><br>Editor, 360info<br></div></div></div>
<div class="copy main-copy"><p>Invented body.</p></div></body></html>"""


def test_site_markup_reads_the_articles_own_byline_block_only():
    r = byline_from_page(PUBLIC_RECORD_PAGE, SITE_MARKUP["thepublicrecord"], "The Public Record")
    assert (r.names, r.route, r.jsonld_agrees) == (("Ivy Invented",), "site", True)
    # The shared account in JSON-LD is not a person; related posts are never read.
    r = byline_from_page(BALKAN_PAGE, SITE_MARKUP["balkandiskurs"], "Balkan Diskurs")
    assert (r.names, r.route) == (("Ana Invented", "Bo Made-Up"), "site")
    assert r.jsonld_agrees is None
    # Authors only, never the editors.
    r = byline_from_page(INFO360_PAGE, SITE_MARKUP["360info"], "360info")
    assert r.names == ("Dana Invented", "Eli Made-Up")


def test_fallbacks_jsonld_meta_and_written_by():
    page = """<script type="application/ld+json">{"bad": </script>
      <script type="application/ld+json">[{"@type": "Article", "author":
      [{"@type": ["Person"], "name": "Gil Invented"}, {"@type": "Organization", "name": "Org"}]}]
      </script>"""
    assert byline_from_page(page).names == ("Gil Invented",)
    meta = '<meta name="author" content="By Hal Invented and Io Made-Up">'
    assert byline_from_page(meta).names == ("Hal Invented", "Io Made-Up")
    page = (
        '<meta name="twitter:label1" content="Written by"><meta name="twitter:data1" content="Jo">'
    )
    r = byline_from_page(page)
    assert (r.names, r.route) == (("Jo",), "twitter")
    # The site's block is missing, so the next route is used.
    r = byline_from_page('<meta name="author" content="Kim Invented">', SITE_MARKUP["360info"])
    assert (r.names, r.route) == (("Kim Invented",), "meta")


def test_the_visible_byline_block_is_final_and_some_sources_have_no_fallback():
    poster = (
        '<script type="application/ld+json">{"author": {"@type": "Person", '
        '"name": "Poster Account"}}</script>'
    )
    own = (
        '<div class="single-meta"><p class="byline author vcard"><a href="/en/profile/bd/">'
        "Balkan Diskurs</a></p></div>"
    )
    # The page credits the source itself: its metadata does not overrule that.
    r = byline_from_page(poster + own, SITE_MARKUP["balkandiskurs"], "Balkan Diskurs")
    assert (r.names, r.route, r.why_none) == ((), "", "source_itself")
    # The source and an account together: no person and not the source alone, so held.
    mixed = own.replace("Balkan Diskurs</a>", "Balkan Diskurs</a> | <a href='/x/'>admin</a>")
    r = byline_from_page(mixed, SITE_MARKUP["balkandiskurs"], "Balkan Diskurs")
    assert r.why_none == "not_a_person"
    # No byline block, and this source's JSON-LD names the poster: no name.
    r = byline_from_page(poster, SITE_MARKUP["balkandiskurs"], "Balkan Diskurs")
    assert (r.names, r.why_none) == ((), "no_byline")
    # The same rule for a source that keeps its fallback: a block crediting the source wins.
    tpr = (
        '<div class="entry-meta"><span class="byline"><a href="/author/t/">The Public Record</a>'
        "</span></div>"
    )
    r = byline_from_page(poster + tpr, SITE_MARKUP["thepublicrecord"], "The Public Record")
    assert (r.names, r.why_none) == ((), "source_itself")
    r = byline_from_page(poster, SITE_MARKUP["thepublicrecord"], "The Public Record")
    assert (r.names, r.route) == (("Poster Account",), "jsonld")


@pytest.mark.parametrize(
    "page, why",
    [
        ("<p>No byline at all.</p>", "no_byline"),
        ('<meta name="author" content="admin">', "not_a_person"),
        ('<meta name="author" content="Editorial Team">', "not_a_person"),
        ('<meta name="author" content="The Public Record">', "not_a_person"),
        (
            '<script type="application/ld+json">{"author": {"@type": "Organization", '
            '"name": "An Invented Org"}}</script>',
            "not_a_person",
        ),
        ('<script type="application/ld+json">{"author": "Plain String"}</script>', "not_a_person"),
    ],
)
def test_pages_that_name_no_person_say_why(page, why):
    r = byline_from_page(page, None, "The Public Record")
    assert (r.names, r.route, r.why_none) == ((), "", why)


def test_split_names_and_is_person():
    assert split_names("By A. One, B. Two & C. Three") == ("A. One", "B. Two", "C. Three")
    assert split_names("written by: D. Four | E. Five") == ("D. Four", "E. Five")
    assert not is_person("Staff Writer")
    assert not is_person("12345")
    assert not is_person("x" * 81)
    assert is_person("Ana Invented", "Balkan Diskurs")


def test_page_file_is_the_same_for_every_form_of_a_url(tmp_path):
    a = page_file(tmp_path, "https://www.example.org/a/?utm_source=x")
    b = page_file(tmp_path, "http://example.org/a")
    assert a == b and a.suffix == ".html" and len(a.stem) == 20


SITE = "https://thepublicrecord.ca"


def _rows(tmp_path, urls, with_author=()):
    path = tmp_path / "rows.jsonl"
    lines = []
    for u in urls:
        authors = ["Someone"] if u in with_author else []
        lines.append(json.dumps({"url": u, "authors": authors, "status": "live"}))
    lines.append(json.dumps({"url": f"{SITE}/gone/", "authors": [], "status": "removed"}))
    path.write_text("\n".join(lines) + "\n")
    return path


def test_collect_fetches_each_page_once_and_records_why(tmp_path):
    urls = [f"{SITE}/{n}/" for n in ("a", "b", "c", "d")]
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(urls[0], (200, PUBLIC_RECORD_PAGE))
    t.add(urls[1], (200, "<p>No byline.</p>"))
    t.add(urls[2], (404, "gone"))
    client, clock = make_test_client(tmp_path, t)
    pages, mp = tmp_path / "pages", tmp_path / "map.json"
    rows = _rows(tmp_path, urls, with_author={urls[3]})
    reader = PageBylineReader(client, "thepublicrecord", pages, mp, source_name="The Public Record")
    st = collect_page_bylines(reader, rows)
    assert (st.rows, st.rows_without_byline, st.pages_fetched, st.with_person) == (5, 3, 3, 1)
    assert st.no_person == {"no_byline": 1, "http_404": 1}
    assert st.routes == {"site": 1} and st.jsonld_check == {"agrees": 1}
    assert len(list(pages.glob("*.html"))) == 2  # the 404 is not saved
    assert names_by_url(mp) == {"https://thepublicrecord.ca/a": ("Ivy Invented",)}
    assert load_page_bylines(mp)["https://thepublicrecord.ca/c"]["http_status"] == 404
    assert len(clock.sleeps) == 3 and all(gap >= 2.0 for gap in clock.sleeps)  # 2 s a request
    # A second run sends nothing: saved pages are read again, and the 404 is not retried.
    calls = len(t.calls)
    reader = PageBylineReader(client, "thepublicrecord", pages, mp, source_name="The Public Record")
    st = collect_page_bylines(reader, rows)
    assert len(t.calls) == calls
    assert (st.pages_fetched, st.pages_already_saved, st.with_person) == (0, 2, 1)
    assert st.summary()["no_person"] == {"http_404": 1, "no_byline": 1}


def test_collect_stops_on_a_block_and_honors_limit_and_replay(tmp_path):
    urls = [f"{SITE}/{n}/" for n in ("a", "b", "c")]
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(urls[0], (403, "no"))
    client, _ = make_test_client(tmp_path, t)
    reader = PageBylineReader(client, "thepublicrecord", tmp_path / "p", tmp_path / "m.json")
    st = collect_page_bylines(reader, _rows(tmp_path, urls))
    assert st.stopped.startswith("Blocked")
    assert st.no_person == {"not_fetched": 3}
    assert [u for u, _ in t.calls] == [f"{SITE}/robots.txt", urls[0]]
    # Replay: nothing is fetched.
    reader = PageBylineReader(None, "thepublicrecord", tmp_path / "p", tmp_path / "m.json")
    st = collect_page_bylines(reader, _rows(tmp_path, urls))
    assert st.no_person == {"not_fetched": 3} and not st.stopped
    # A limit of one page.
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    for u in urls:
        t.add(u, (200, PUBLIC_RECORD_PAGE))
    client, _ = make_test_client(tmp_path / "c2", t)
    reader = PageBylineReader(client, "thepublicrecord", tmp_path / "p2", tmp_path / "m2.json")
    st = collect_page_bylines(reader, _rows(tmp_path, urls), limit=1)
    assert (st.pages_fetched, st.with_person, st.no_person["not_fetched"]) == (1, 1, 2)


def test_a_network_error_is_counted_and_the_run_goes_on(tmp_path):
    from fakes import CONNECTION_ERROR

    urls = [f"{SITE}/a/", f"{SITE}/b/"]
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(urls[0], CONNECTION_ERROR)
    t.add(urls[1], (200, PUBLIC_RECORD_PAGE))
    client, _ = make_test_client(tmp_path, t, max_retries=0)
    said = []
    reader = PageBylineReader(
        client, "thepublicrecord", tmp_path / "p", tmp_path / "m.json", say=said.append
    )
    st = collect_page_bylines(reader, _rows(tmp_path, urls))
    assert st.no_person == {"fetch_error": 1} and st.with_person == 1
    assert said and "failed" in said[0]


def test_build_reads_page_bylines_by_canonical_url(tmp_path):
    client, _ = make_test_client(tmp_path, FakeTransport())
    fetcher = GlobalVoicesFetcher(client, gv_source(), ReplayStore(tmp_path / "raw"))
    post = backfill_post(1)
    item = fetcher.item_from_post(post)
    assert item.authors == ()
    assert not fetcher.build(item, NOW).releasable
    fetcher.page_bylines = {canonical_url(post["link"]): ("Lu Invented",)}
    post = dict(post, link=post["link"].replace("https://", "https://www."))
    item = fetcher.item_from_post(post)
    assert item.authors == ("Lu Invented",)
    assert fetcher.build(item, NOW).releasable
    fetcher.page_bylines = {"x": ("y",)}
    assert fetcher.item_from_post(dict(post, link="not a url")).authors == ()


GV = "https://globalvoices.org"


def test_daily_reads_the_page_of_a_new_post_with_no_byline(tmp_path):
    client, _ = make_test_client(tmp_path, FakeTransport())
    fetcher = GlobalVoicesFetcher(client, gv_source(), ReplayStore(tmp_path / "raw"))
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text(
        fetcher.build(fetcher.item_from_post(backfill_post(1)), NOW).model_dump_json() + "\n"
    )
    newest = max(r["published_at"] for r in load_rows(rows_path).values())[:19]
    fields = fetcher.backfill_fields

    def url(**params):
        q = urlencode({"per_page": "100", "page": "1", **params})
        return f"{GV}/wp-json/wp/v2/posts?{q}"

    new = [backfill_post(5), backfill_post(6)]
    t = FakeTransport().add(f"{GV}/robots.txt", (404, ""))
    t.add(url(after=newest, orderby="date", order="asc", _fields=fields), (200, json.dumps(new)))
    t.add(url(modified_after=newest, _fields=fields), (200, "[]"))
    t.add(url(after="2026-10-14T12:00:00", _fields="id,link"), (200, json.dumps(new)))
    t.add(new[0]["link"], (200, '<meta name="author" content="Mo Invented">'))
    t.add(new[1]["link"], (200, "<p>no byline</p>"))
    client, _ = make_test_client(tmp_path / "c", t)
    fetcher.client = client
    reader = PageBylineReader(client, "globalvoices", tmp_path / "pages", tmp_path / "m.json")
    res = daily_wordpress(fetcher, client, rows_path, tmp_path / "d", {}, NOW, page_bylines=reader)
    assert (res.new, res.held, res.page_bylines) == (2, 1, 1)
    assert "2 new" in res.line() and "1 new rows held, 1 bylines from article pages" in res.line()
    rows = load_rows(rows_path)
    assert sorted(r["releasable"] for r in rows.values()) == [False, False, True]
    assert ["Mo Invented"] in [r["authors"] for r in rows.values()]


def test_cli_page_bylines_checks_its_inputs_and_replays(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "page-bylines", "factly"]) == 2
    assert "no byline markup is known for factly" in capsys.readouterr().err
    assert main(["--root", str(tmp_path), "page-bylines", "thepublicrecord"]) == 2
    assert "data/raw is missing" in capsys.readouterr().err
    (tmp_path / "data" / "raw").mkdir(parents=True)
    assert main(["--root", str(tmp_path), "page-bylines", "thepublicrecord"]) == 2
    assert "no rows yet" in capsys.readouterr().err


BD = "https://balkandiskurs.com/en"
OWN_PAGE = (
    '<div class="single-meta"><p class="byline author vcard"><a href="/en/profile/bd/">'
    "Balkan Diskurs</a></p></div><p>Invented body.</p>"
)


def _bd_fetcher(tmp_path):
    from commonswire.fetchers.wordpress import BalkanDiskursFetcher
    from commonswire.sources import parse_row
    from test_sources import row

    src = parse_row(
        row(
            source_id="balkandiskurs",
            name="Balkan Diskurs",
            license="CC-BY-3.0",
            credit_line=(
                "{title}, by {authors}, originally published by {source} ({url}), {license}"
            ),
        )
    )
    client, _ = make_test_client(tmp_path, FakeTransport())
    return BalkanDiskursFetcher(client, src, ReplayStore(tmp_path / "raw"))


def test_a_page_that_credits_the_source_itself_is_released_naming_the_source(tmp_path):
    urls = [f"{BD}/a/", f"{BD}/b/", f"{BD}/c/"]
    t = FakeTransport().add(f"{BD.rsplit('/', 1)[0]}/robots.txt", (404, ""))
    t.add(urls[0], (200, OWN_PAGE))
    t.add(urls[1], (200, BALKAN_PAGE))
    t.add(urls[2], (200, "<p>No byline.</p>"))
    client, _ = make_test_client(tmp_path, t)
    mp = tmp_path / "m.json"
    reader = PageBylineReader(
        client, "balkandiskurs", tmp_path / "p", mp, source_name="Balkan Diskurs"
    )
    st = collect_page_bylines(reader, _rows(tmp_path, urls))
    assert st.no_person == {"source_itself": 1, "no_byline": 1} and st.with_person == 1
    assert reader.credits_source(urls[0]) and not reader.credits_source(urls[2])
    assert source_credited(mp) == {f"{BD}/a"}
    assert source_credited(tmp_path / "missing.json") == set()

    fetcher = _bd_fetcher(tmp_path / "f")
    fetcher.page_bylines = names_by_url(mp)
    fetcher.source_credited = source_credited(mp)
    built = {}
    for n, u in enumerate(urls):
        post = dict(backfill_post(n + 1), link=u)
        built[u] = fetcher.build(fetcher.item_from_post(post), NOW)
    own = built[urls[0]]
    assert own.releasable and own.authors == () and not own.hold_reason
    assert own.credit_line.startswith(f"{own.title}, by Balkan Diskurs, originally published by")
    assert built[urls[1]].authors == ("Ana Invented", "Bo Made-Up")
    assert not built[urls[2]].releasable  # an empty byline stays held
    assert built[urls[2]].hold_reason.startswith("no byline")


def test_daily_releases_a_new_post_whose_page_credits_the_source(tmp_path):
    fetcher = _bd_fetcher(tmp_path)
    rows_path = tmp_path / "rows.jsonl"
    first = dict(backfill_post(1), link=f"{BD}/old/")
    rows_path.write_text(fetcher.build(fetcher.item_from_post(first), NOW).model_dump_json() + "\n")
    newest = max(r["published_at"] for r in load_rows(rows_path).values())[:19]
    fields = fetcher.backfill_fields

    def url(**params):
        q = urlencode({"per_page": "100", "page": "1", **params})
        return f"{BD}/wp-json/wp/v2/posts?{q}"

    new = [dict(backfill_post(5), link=f"{BD}/own/")]
    t = FakeTransport().add("https://balkandiskurs.com/robots.txt", (404, ""))
    t.add(url(after=newest, orderby="date", order="asc", _fields=fields), (200, json.dumps(new)))
    t.add(url(modified_after=newest, _fields=fields), (200, "[]"))
    t.add(url(after="2026-10-14T12:00:00", _fields="id,link"), (200, json.dumps(new)))
    t.add(f"{BD}/own/", (200, OWN_PAGE))
    client, _ = make_test_client(tmp_path / "c", t)
    fetcher.client = client
    reader = PageBylineReader(
        client,
        "balkandiskurs",
        tmp_path / "pages",
        tmp_path / "m.json",
        source_name="Balkan Diskurs",
    )
    res = daily_wordpress(fetcher, client, rows_path, tmp_path / "d", {}, NOW, page_bylines=reader)
    assert (res.new, res.held, res.page_bylines) == (1, 0, 0)
    got = next(r for r in load_rows(rows_path).values() if r["url"].endswith("/own/"))
    assert got["releasable"] and got["authors"] == []
