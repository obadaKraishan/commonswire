from __future__ import annotations

import csv
import json

from commonswire.pagebackfill import (
    PageProgress,
    PageRoute,
    check_pages,
    collect_urls,
    fetch_pages,
    listing_links,
    page_paths,
    sitemap_locs,
)
from commonswire.schema import article_id, canonical_url
from fakes import CONNECTION_ERROR, FakeTransport, make_test_client

HOST = "https://news.example"
ROBOTS = (200, "User-agent: *\nAllow: /\n")
SITEMAP = PageRoute(
    source_id="example",
    kind="sitemap",
    start=f"{HOST}/sitemap_index.xml",
    sitemap_pattern=rf"^{HOST}/article-sitemap\d*\.xml$",
    article_pattern=rf"^{HOST}/news/[^?#]+$",
)
LISTING = PageRoute(
    source_id="example",
    kind="listing",
    start=f"{HOST}/latest",
    next_page=HOST + "/latest?page={n}",
    article_pattern=rf"^{HOST}/\d{{4}}/\d{{2}}/[a-z0-9-]+$",
)


def index(*maps: str) -> str:
    items = "".join(f"<sitemap><loc>{m}</loc></sitemap>" for m in maps)
    return f'<?xml version="1.0"?><sitemapindex>{items}</sitemapindex>'


def urlset(*urls: str) -> str:
    items = "".join(f"<url><loc><![CDATA[{u}]]></loc><lastmod>2026</lastmod></url>" for u in urls)
    return f'<?xml version="1.0"?><urlset>{items}</urlset>'


def sitemap_site() -> FakeTransport:
    t = FakeTransport()
    t.add(f"{HOST}/robots.txt", ROBOTS)
    t.add(
        SITEMAP.start,
        (
            200,
            index(f"{HOST}/article-sitemap.xml", f"{HOST}/article-sitemap2.xml", f"{HOST}/x.xml"),
        ),
    )
    t.add(f"{HOST}/article-sitemap.xml", (200, urlset(f"{HOST}/news/a", f"{HOST}/news/b")))
    t.add(
        f"{HOST}/article-sitemap2.xml",
        (200, urlset(f"{HOST}/news/c", f"{HOST}/news/a/", f"{HOST}/about")),
    )
    t.add(f"{HOST}/news/a", (200, "<html>invented page a</html>"))
    t.add(f"{HOST}/news/b", (410, "gone"))
    t.add(f"{HOST}/news/c", (200, "<html>invented page c</html>"))
    return t


def test_sitemap_locs_and_listing_links():
    assert sitemap_locs(urlset("https://a.example/1", "https://a.example/2?x=1&amp;y=2")) == [
        "https://a.example/1",
        "https://a.example/2?x=1&y=2",
    ]
    html = (
        '<a href="/2026/01/one">1</a> <a href="/2026/01/one?ref=x">again</a>'
        '<a href="https://news.example/2026/02/two">2</a> <a href="/about">about</a>'
    )
    assert listing_links(html, f"{HOST}/latest", LISTING.article_pattern) == [
        f"{HOST}/2026/01/one",
        f"{HOST}/2026/02/two",
    ]


def test_a_sitemap_backfill_saves_each_page_once_and_logs_ids_not_addresses(tmp_path):
    t = sitemap_site()
    client, _ = make_test_client(tmp_path, t)
    folder = tmp_path / "run"
    prog = PageProgress("example", "r1")
    urls = collect_urls(client, SITEMAP, folder, prog)
    # The non-article sitemap and address are ignored; a/ and a are one article.
    assert urls == [f"{HOST}/news/a", f"{HOST}/news/b", f"{HOST}/news/c"]
    assert json.loads((folder / "urls.json").read_text()) == urls
    assert sorted(p.name for p in (folder / "lists").iterdir()) == [
        "index.xml",
        "sitemap-001.xml",
        "sitemap-002.xml",
    ]
    fetch_pages(client, SITEMAP, urls, folder, prog)
    assert prog.finished and prog.pages_saved == 2 and prog.by_status == {"200": 2, "410": 1}
    html_a, meta_a = page_paths(folder, f"{HOST}/news/a")
    assert html_a.read_bytes() == b"<html>invented page a</html>"
    assert json.loads(meta_a.read_text())["status"] == "200"
    html_b, meta_b = page_paths(folder, f"{HOST}/news/b")
    assert not html_b.exists() and json.loads(meta_b.read_text())["status"] == "410"
    with (tmp_path / "usage_log.csv").open() as fh:
        log = list(csv.DictReader(fh))
    page_rows = [r for r in log if r["note"] == "backfill:example"]
    assert len(page_rows) == 3
    assert {r["path"] for r in page_rows} == {
        article_id(canonical_url(f"{HOST}/news/{x}")) for x in "abc"
    }
    assert check_pages(folder)["complete"] is True

    # A rerun sends nothing: the lists and every page are saved.
    calls = len(t.calls)
    prog2 = PageProgress("example", "r1")
    urls2 = collect_urls(client, SITEMAP, folder, prog2)
    fetch_pages(client, SITEMAP, urls2, folder, prog2)
    assert len(t.calls) == calls and prog2.requests_this_run == 0 and prog2.finished


def test_a_refusal_stops_the_run_and_a_failure_is_tried_again_next_run(tmp_path):
    t = sitemap_site()
    t.routes[f"{HOST}/news/a"] = [CONNECTION_ERROR]
    t.routes[f"{HOST}/news/c"] = [(403, "forbidden")]
    client, _ = make_test_client(tmp_path, t)
    folder = tmp_path / "run"
    prog = PageProgress("example", "r1")
    urls = collect_urls(client, SITEMAP, folder, prog)
    fetch_pages(client, SITEMAP, urls, folder, prog)
    assert "refused page 3 (HTTP 403" in prog.stopped and not prog.finished
    assert prog.retry_later == 1 and prog.by_status == {"410": 1}
    r = check_pages(folder)
    assert r["complete"] is False and r["not_yet_recorded"] == 2
    assert r["first_not_recorded"][0] == page_paths(folder, f"{HOST}/news/a")[1].stem

    t.routes[f"{HOST}/news/a"] = [(200, "<html>a at last</html>")]
    t.routes[f"{HOST}/news/c"] = [(200, "<html>c at last</html>")]
    client2, _ = make_test_client(tmp_path / "second", t)
    prog2 = PageProgress("example", "r1")
    fetch_pages(client2, SITEMAP, urls, folder, prog2)
    assert prog2.finished and prog2.requests_this_run == 2
    assert check_pages(folder) == {
        "urls": 3,
        "recorded": 3,
        "by_status": {"200": 2, "410": 1},
        "not_yet_recorded": 0,
        "first_not_recorded": [],
        "pages_not_on_disk_at_their_size": [],
        "complete": True,
    }


def test_a_page_cut_short_on_disk_is_named(tmp_path):
    client, _ = make_test_client(tmp_path, sitemap_site())
    folder = tmp_path / "run"
    prog = PageProgress("example", "r1")
    fetch_pages(client, SITEMAP, collect_urls(client, SITEMAP, folder, prog), folder, prog)
    html_c, meta_c = page_paths(folder, f"{HOST}/news/c")
    html_c.write_bytes(b"cut")
    r = check_pages(folder)
    assert r["complete"] is False and r["pages_not_on_disk_at_their_size"] == [meta_c.stem]


def test_the_request_limit_and_the_byte_budget_stop_the_run(tmp_path):
    client, _ = make_test_client(tmp_path, sitemap_site())
    folder = tmp_path / "run"
    prog = PageProgress("example", "r1")
    urls = collect_urls(client, SITEMAP, folder, prog)
    prog.requests_this_run = 0
    fetch_pages(client, SITEMAP, urls, folder, prog, max_requests=1)
    assert prog.stopped.startswith("the request limit of 1") and prog.recorded == 1
    client2, _ = make_test_client(tmp_path / "b", sitemap_site(), byte_budget=1)
    client2.bytes_used = 5
    prog2 = PageProgress("example", "r1")
    fetch_pages(client2, SITEMAP, urls, folder, prog2)
    assert prog2.stopped.startswith("the byte budget is used up")


def test_robots_that_disallow_a_page_is_recorded(tmp_path):
    t = sitemap_site()
    t.routes[f"{HOST}/robots.txt"] = [(200, "User-agent: *\nDisallow: /news/c\n")]
    client, _ = make_test_client(tmp_path, t)
    folder = tmp_path / "run"
    prog = PageProgress("example", "r1")
    fetch_pages(client, SITEMAP, collect_urls(client, SITEMAP, folder, prog), folder, prog)
    assert prog.finished and prog.by_status == {"200": 1, "410": 1, "disallowed": 1}


def test_a_listing_is_read_until_a_page_brings_nothing_new_or_answers_404(tmp_path):
    t = FakeTransport()
    t.add(f"{HOST}/robots.txt", ROBOTS)
    t.add(f"{HOST}/latest", (200, '<a href="/2026/03/three">3</a><a href="/2026/02/two">2</a>'))
    t.add(f"{HOST}/latest?page=2", (200, '<a href="/2026/02/two">2</a><a href="/2026/01/one">'))
    t.add(f"{HOST}/latest?page=3", (200, '<a href="/2026/01/one">1</a><a href="/about">a</a>'))
    client, _ = make_test_client(tmp_path, t)
    prog = PageProgress("example", "r1")
    urls = collect_urls(client, LISTING, tmp_path / "run", prog)
    assert urls == [f"{HOST}/2026/03/three", f"{HOST}/2026/02/two", f"{HOST}/2026/01/one"]
    assert prog.list_pages == 3

    t2 = FakeTransport()
    t2.add(f"{HOST}/robots.txt", ROBOTS)
    t2.add(f"{HOST}/latest", (200, '<a href="/2026/03/three">3</a>'))
    client2, _ = make_test_client(tmp_path / "b", t2)
    prog2 = PageProgress("example", "r2")
    assert collect_urls(client2, LISTING, tmp_path / "run2", prog2) == [f"{HOST}/2026/03/three"]
