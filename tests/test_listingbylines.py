"""Bylines from a paged story listing, with invented pages and names. No network."""

from __future__ import annotations

import json

from commonswire.cli import main
from commonswire.listingbylines import (
    LISTING_MARKUP,
    collect_listing_bylines,
    read_listing,
)
from commonswire.pagebylines import names_by_url
from fakes import CONNECTION_ERROR, FakeTransport, make_test_client

GV = "https://globalvoices.org"
MARKUP = LISTING_MARKUP["globalvoices"]


def story(slug, writers=(), translators=(), extra_link=False):
    links = "".join(f'<a class="user-link" href="{GV}/author/{w}/">{w}</a>, ' for w in writers)
    tr = "".join(f'<a class="user-link" href="{GV}/author/{t}/">{t}</a>' for t in translators)
    more = f'<a href="{GV}/2026/01/01/{slug}/#comments">0 comments</a>' if extra_link else ""
    credits = f"""<div class="text-credits-container"><div class="text-credits-section">
      <span class="credit-label">Written by</span> {links}</div>"""
    if translators:
        credits += f"""<div class="text-credits-section"><span class="credit-label">
          Translated by</span> {tr}</div>"""
    return f"""<div class="post-summary"><div class="post-title">
      <a href="{GV}/2026/01/01/{slug}/">An invented title</a>{more}</div>
      <p class="post-tagline">Invented tagline.</p>{credits}</div></div>"""


def page(*stories):
    return f"<html><body><main>{''.join(stories)}</main><br></body></html>"


def test_read_listing_takes_each_storys_writers_and_translators():
    html = page(
        story("a", ["Ana Invented"]),
        story("b", ["Bo Made-Up", "Cy Invented"], ["Di Translator"], extra_link=True),
        story("c"),
    )
    got = read_listing(html, MARKUP)
    assert [s.url.rsplit("/", 2)[-2] for s in got] == ["a", "b", "c"]
    assert got[0].credits == {"written by": ["Ana Invented"]}
    assert got[1].credits == {
        "written by": ["Bo Made-Up", "Cy Invented"],
        "translated by": ["Di Translator"],
    }
    assert got[2].credits == {}
    assert read_listing("</div><p>stray end tags</span>", MARKUP) == []


def site(pages):
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "User-agent: *\nCrawl-delay: 10\n"))
    for n, html in enumerate(pages, 1):
        t.add(f"{GV}/page/{n}/", (200, html))
    return t


def test_collect_walks_until_404_saves_once_and_resumes(tmp_path):
    pages = [
        page(story("a", ["Ana Invented"]), story("b", ["Guest Contributor"])),
        # A new story on the site pushed "b" onto the next page: it is kept once.
        page(story("b", ["Guest Contributor"]), story("c", ["Global Voices"])),
        page(story("d", ["Bo Made-Up", "Cy Invented"], ["Di Translator"])),
    ]
    t = site(pages)
    client, clock = make_test_client(tmp_path, t)
    folder, mp = tmp_path / "listing", tmp_path / "map.json"
    st = collect_listing_bylines(client, "globalvoices", folder, mp, source_name="Global Voices")
    assert st.end == "page 4 answered 404: past the last page"
    assert (st.pages_fetched, st.last_page, st.stories_seen, st.stories) == (4, 3, 5, 4)
    assert (st.with_writer, st.without_writer, st.translated) == (2, 2, 1)
    assert st.writers_per_story == {"0": 2, "1": 1, "2": 1}
    assert all(gap >= 10.0 for gap in clock.sleeps)  # the crawl-delay
    found = json.loads(mp.read_text())
    assert found[f"{GV}/2026/01/01/b"]["why_none"] == "no_byline"  # an account, not a person
    assert found[f"{GV}/2026/01/01/c"]["why_none"] == "source_itself"
    assert found[f"{GV}/2026/01/01/d"]["translators"] == ["Di Translator"]
    assert names_by_url(mp) == {
        f"{GV}/2026/01/01/a": ("Ana Invented",),
        f"{GV}/2026/01/01/d": ("Bo Made-Up", "Cy Invented"),
    }
    assert len(list(folder.glob("p*.html"))) == 3  # the 404 is not saved
    # A second run reads the saved pages and asks only for the page past the end.
    calls = len(t.calls)
    st = collect_listing_bylines(client, "globalvoices", folder, mp, source_name="Global Voices")
    assert (st.pages_fetched, st.pages_already_saved, st.stories) == (1, 3, 4)
    assert [u for u, _ in t.calls[calls:]] == [f"{GV}/page/4/"]
    # Replay sends nothing at all.
    st = collect_listing_bylines(None, "globalvoices", folder, mp, source_name="Global Voices")
    assert (st.pages_fetched, st.stories) == (0, 4)
    assert st.end == "page 4 is not saved (replay)"
    assert st.summary()["writers_per_story"] == {"0": 2, "1": 1, "2": 1}


def test_collect_stops_on_refusal_errors_empty_pages_and_limits(tmp_path):
    t = FakeTransport().add(f"{GV}/robots.txt", (404, "")).add(f"{GV}/page/1/", (403, "no"))
    client, _ = make_test_client(tmp_path, t)
    st = collect_listing_bylines(client, "globalvoices", tmp_path / "a", tmp_path / "a.json")
    assert st.stopped.startswith("Blocked") and st.stories == 0
    t = FakeTransport().add(f"{GV}/robots.txt", (404, "")).add(f"{GV}/page/1/", (500, "down"))
    client, _ = make_test_client(tmp_path / "b", t, max_retries=0)
    st = collect_listing_bylines(client, "globalvoices", tmp_path / "b", tmp_path / "b.json")
    assert st.stopped == "page 1 answered HTTP 500"
    t = FakeTransport().add(f"{GV}/robots.txt", (404, "")).add(f"{GV}/page/1/", CONNECTION_ERROR)
    client, _ = make_test_client(tmp_path / "c", t, max_retries=0)
    st = collect_listing_bylines(client, "globalvoices", tmp_path / "c", tmp_path / "c.json")
    assert st.stopped.startswith("error:")
    t = site([page(story("a", ["Ana Invented"])), "<p>No stories here.</p>"])
    client, _ = make_test_client(tmp_path / "d", t)
    st = collect_listing_bylines(client, "globalvoices", tmp_path / "d", tmp_path / "d.json")
    assert st.end == "page 2 lists no story" and st.stories == 1
    t = site([page(story(x, ["Ana Invented"])) for x in "abc"])
    client, _ = make_test_client(tmp_path / "e", t)
    st = collect_listing_bylines(
        client, "globalvoices", tmp_path / "e", tmp_path / "e.json", max_pages=2
    )
    assert (st.pages_fetched, st.stories, st.end) == (2, 2, "")


def test_cli_listing_bylines_checks_inputs_replays_and_feeds_build(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "listing-bylines", "factly"]) == 2
    assert "no listing markup is known for factly" in capsys.readouterr().err
    assert main(["--root", str(tmp_path), "listing-bylines", "globalvoices"]) == 2
    assert "data/raw is missing" in capsys.readouterr().err
    folder = tmp_path / "data" / "raw" / "pages" / "globalvoices" / "listing" / "r1"
    folder.mkdir(parents=True)
    (folder / "p00001.html").write_text(page(story("a", ["Ana Invented"]), story("b")))
    args = ["--root", str(tmp_path), "listing-bylines", "globalvoices", "--run", "r1"]
    assert main([*args, "--replay"]) == 0
    out = capsys.readouterr().out
    assert "1 listing pages (0 fetched, 1 already saved" in out and "2 stories, 1 with" in out
    ev = json.loads((tmp_path / "data/evidence/bylines/globalvoices.listing.json").read_text())
    assert ev["run"] == "r1" and ev["with_writer"] == 1
    # build reads the listing names (article-page names, if any, come first).
    from commonswire.cli import _load_bylines
    from commonswire.fetchers.base import ReplayStore
    from commonswire.fetchers.wordpress import GlobalVoicesFetcher
    from test_fetchers import gv_source

    client, _ = make_test_client(tmp_path / "x", FakeTransport())
    fetcher = GlobalVoicesFetcher(client, gv_source(), ReplayStore(tmp_path / "raw"))
    _load_bylines(tmp_path, fetcher)
    assert fetcher.page_bylines == {f"{GV}/2026/01/01/a": ("Ana Invented",)}
