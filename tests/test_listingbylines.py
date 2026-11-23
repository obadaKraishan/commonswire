"""Bylines from a paged story listing, with invented pages and names. No network."""

from __future__ import annotations

import json

from commonswire.cli import main
from commonswire.listingbylines import (
    LISTING_MARKUP,
    collect_listing_bylines,
    read_listing,
    translators_by_url,
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
    assert found[f"{GV}/2026/01/01/b"]["why_none"] == "not_a_person"  # an account
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


def teaser(slug):
    """A featured story on the home page: its title link, and no credit block."""
    return f"""<div class="post-summary"><div class="post-title">
      <a href="{GV}/2026/01/01/{slug}/">An invented featured title</a></div></div>"""


def test_a_story_first_seen_without_credits_takes_them_from_a_later_sighting(tmp_path):
    pages = [
        # The home page: two featured teasers with no credit block, then a credited story.
        page(teaser("e"), teaser("f"), story("g", ["Ana Invented"])),
        # "e" is listed again with its writer and translator; "g" again with no credits
        # (it keeps the first, credited sighting); "f" never comes back.
        page(story("e", ["Bo Made-Up"], ["Cy Invented"]), teaser("g")),
        page(story("e", ["Someone Else"]), story("h", ["Di Invented"], ["Guest Contributor"])),
    ]
    client, _ = make_test_client(tmp_path, site(pages))
    folder, mp = tmp_path / "listing", tmp_path / "map.json"
    st = collect_listing_bylines(client, "globalvoices", folder, mp, source_name="Global Voices")
    assert (st.stories, st.seen_again, st.credits_from_later_sighting) == (4, 3, 1)
    found = json.loads(mp.read_text())
    e = found[f"{GV}/2026/01/01/e"]
    assert (e["names"], e["translators"]) == (["Bo Made-Up"], ["Cy Invented"])  # 2nd, not 3rd
    assert found[f"{GV}/2026/01/01/g"]["names"] == ["Ana Invented"]
    assert found[f"{GV}/2026/01/01/f"] == {
        "names": [],
        "translators": [],
        "route": "listing",
        "why_none": "no_byline",
        "http_status": 200,
    }
    # An account is no translator either; it is counted, and the map keeps no counter field.
    assert found[f"{GV}/2026/01/01/h"]["translators"] == []
    assert st.translators_not_a_person == 1 and st.translated == 1
    assert st.why_none == {"no_byline": 1}
    summary = st.summary()
    assert summary["credits_from_later_sighting"] == 1 and summary["seen_again"] == 3
    assert translators_by_url(mp) == {f"{GV}/2026/01/01/e": ("Cy Invented",)}
    assert translators_by_url(tmp_path / "none.json") == {}
    # The replay of the same saved pages, with no request, gives the same map as the walk.
    calls = len(client.transport.calls)
    again = tmp_path / "again.json"
    collect_listing_bylines(None, "globalvoices", folder, again, source_name="Global Voices")
    assert len(client.transport.calls) == calls
    assert json.loads(again.read_text()) == found


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
    assert fetcher.byline_why_none == {f"{GV}/2026/01/01/b": "no_byline"}
    assert fetcher.page_translators == {}


def test_listing_credits_reads_only_the_pages_a_week_needs(tmp_path):
    from commonswire.listingbylines import listing_credits
    from commonswire.schema import canonical_url

    def dated(day, slug, writers=(), translators=()):
        html = story(slug, writers, translators)
        return html.replace("/2026/01/01/", f"/{day.replace('-', '/')}/")

    pages = [
        page(
            dated("2026-11-18", "a", ["Ana Invented"], ["Di Translator"]), dated("2026-11-17", "b")
        ),
        page(dated("2026-11-16", "c", ["Guest Contributor"])),
        page(dated("2026-10-01", "old", ["Bo Made-Up"])),
        page(dated("2026-09-01", "older", ["Bo Made-Up"])),
    ]
    wanted = {
        canonical_url(f"{GV}/2026/11/18/a/"): "2026-11-18",
        canonical_url(f"{GV}/2026/11/16/c/"): "2026-11-16",
        canonical_url(f"{GV}/2026/11/15/missing/"): "2026-11-15",
    }
    client, _ = make_test_client(tmp_path, site(pages))
    got, st = listing_credits(client, "globalvoices", wanted, source_name="Global Voices")
    a = got[canonical_url(f"{GV}/2026/11/18/a/")]
    assert a["names"] == ["Ana Invented"] and a["translators"] == ["Di Translator"]
    assert got[canonical_url(f"{GV}/2026/11/16/c/")]["why_none"] == "not_a_person"
    assert st.pages_fetched == 3 and "older than the wanted ones" in st.end
    assert (st.stories, st.with_writer, st.translated) == (2, 1, 1)
    # Every wanted story found: no further page; nothing wanted: no request at all.
    client, _ = make_test_client(tmp_path / "b", site(pages))
    got, st = listing_credits(client, "globalvoices", dict(list(wanted.items())[:1]))
    assert st.pages_fetched == 1 and st.end.startswith("every wanted story found")
    assert listing_credits(client, "globalvoices", {})[1].pages_fetched == 0
    # The cap, a 404, a page with no story, a refusal and an error each end the walk.
    client, _ = make_test_client(tmp_path / "c", site(pages[:2] * 3))
    _, st = listing_credits(client, "globalvoices", wanted, max_pages=2)
    assert st.end == "stopped after 2 pages"
    client, _ = make_test_client(tmp_path / "d", site(pages[:1]))
    _, st = listing_credits(client, "globalvoices", wanted)
    assert st.end.startswith("page 2 answered 404")
    client, _ = make_test_client(tmp_path / "e", site([page()]))
    assert listing_credits(client, "globalvoices", wanted)[1].end == "page 1 lists no story"
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "")).add(f"{GV}/page/1/", (403, "no"))
    client, _ = make_test_client(tmp_path / "f", t)
    assert listing_credits(client, "globalvoices", wanted)[1].stopped.startswith("Blocked")
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "")).add(f"{GV}/page/1/", (500, "x"))
    client, _ = make_test_client(tmp_path / "g", t)
    assert listing_credits(client, "globalvoices", wanted)[1].stopped == "page 1 answered HTTP 500"
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "")).add(f"{GV}/page/1/", CONNECTION_ERROR)
    client, _ = make_test_client(tmp_path / "h", t)
    assert listing_credits(client, "globalvoices", wanted)[1].stopped.startswith("error:")


def test_a_page_still_failing_after_the_clients_retries_is_asked_again_after_a_long_wait(tmp_path):
    from commonswire.listingbylines import LONG_PAUSES

    t = FakeTransport().add(f"{GV}/robots.txt", (404, ""))
    t.add(f"{GV}/page/1/", (200, page(story("one", ["Ana Invented"]))))
    t.add(f"{GV}/page/2/", *([(502, "busy")] * 4 + [(200, page(story("two", ["Bo Invented"])))]))
    t.add(f"{GV}/page/3/", (404, "none"))
    client, _ = make_test_client(tmp_path, t)
    waits = []
    st = collect_listing_bylines(
        client, "globalvoices", tmp_path / "pages", tmp_path / "map.json", sleep=waits.append
    )
    assert not st.stopped and st.stories == 2 and st.long_waits == 1
    assert waits == [LONG_PAUSES[0]]
