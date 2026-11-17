"""The weekly route of the page sources, on invented sitemaps, listings and pages. No network."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from commonswire import release as rel
from commonswire.cli import main
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.pages import AfricaIsACountryFetcher, SciDevNetFetcher
from commonswire.pageupdate import (
    MAX_SITEMAPS,
    page_state_from_backfill,
    run_route,
    sitemap_entries,
    update_pages,
)
from commonswire.release import collect, write_release
from commonswire.release_text import card, licenses_md
from commonswire.schema import article_id, canonical_url
from commonswire.sources import load_sources
from commonswire.update import read_version, run_update
from fakes import FakeTransport, make_test_client
from test_pagefetchers import (
    SD_CREDIT,
    SD_FOOTER,
    SD_OWN_BYLINE,
    aiac_page,
    scidev_page,
)
from test_sources import row, write_csv
from test_update import make_clients

NOW = datetime(2026, 11, 23, 6, tzinfo=timezone.utc)
BUILT = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
THROUGH = "2026-11-16T14:00:00Z"
SD = "https://www.scidev.net/global"
INDEX = f"{SD}/sitemap_index.xml"
AIAC = "https://africasacountry.com"
FRONT = f"{AIAC}/category/front-page"


def sd_url(slug, section="news"):
    return f"{SD}/{section}/{slug}/"


def sd_body(n, extra=""):
    return f"<p>Invented paragraph {n} of an invented report.</p>{extra}"


def sd_page(n, *, byline=SD_OWN_BYLINE, extra=""):
    return scidev_page(byline=byline, body=sd_body(n, extra)).replace(
        "</body>", f"{SD_FOOTER}</body>"
    )


def sitemap(*entries):
    urls = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in entries)
    return f'<?xml version="1.0"?><urlset>{urls}</urlset>'


def index(*maps):
    locs = "".join(f"<sitemap><loc>{SD}/{m}</loc></sitemap>" for m in maps)
    locs += f"<sitemap><loc>{SD}/page-sitemap.xml</loc></sitemap>"
    return f'<?xml version="1.0"?><sitemapindex>{locs}</sitemapindex>'


def registry(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return write_csv(
        tmp_path,
        [
            row(
                source_id="scidevnet",
                name="SciDev.Net",
                homepage=f"{SD}/",
                license="CC-BY-2.0",
                credit_line=SD_CREDIT,
                access="sitemap",
            ),
            row(
                source_id="africasacountry",
                name="Africa Is a Country",
                homepage=f"{AIAC}/",
                license="CC-BY-4.0",
                credit_line=SD_CREDIT,
                access="listing",
            ),
        ],
    )


def built(fetcher, url, html):
    art = fetcher.build(fetcher.item_from_page(url, html), BUILT)
    return json.loads(art.model_dump_json())


class SciDev:
    """A previous version's SciDev.Net rows and the site a week later."""

    def __init__(self, tmp_path):
        self.reg = load_sources(registry(tmp_path))
        self.transport = FakeTransport()
        self.client, _ = make_test_client(tmp_path, self.transport)
        self.f = SciDevNetFetcher(self.client, self.reg["scidevnet"], ReplayStore(tmp_path / "r"))
        self.urls = {k: sd_url(f"invented-{k}") for k in "abcdg"}
        self.prev = {
            article_id(self.urls[k]): built(self.f, self.urls[k], sd_page(k)) for k in "abcdg"
        }
        t = self.transport
        old, new = "2026-11-10T10:00:00+00:00", "2026-11-20T10:00:00+00:00"
        self.new = {
            "e": sd_url("invented-e"),  # new, with a byline
            "h": sd_url("invented-h"),  # new, no byline: held
            "s": sd_url("invented-s", "supported-content"),  # left out: another license
        }
        t.add(INDEX, (200, index("article-sitemap.xml", "article-sitemap2.xml")))
        # The first sitemap: older articles (read only by the removal check).
        t.add(
            f"{SD}/article-sitemap.xml",
            (200, sitemap((self.urls["a"], "2026-11-01T00:00:00+00:00"), (self.urls["d"], old))),
        )
        t.add(
            f"{SD}/article-sitemap2.xml",
            (
                200,
                sitemap(
                    (self.urls["a"], old),  # before the mark: never read
                    (self.urls["b"], new),  # edited: changed
                    (self.urls["c"], new),  # touched, same text: unchanged
                    (self.urls["g"], new),  # gone: removed
                    (self.new["e"], new),
                    (self.new["h"], new),
                    (self.new["s"], "2026-11-21T08:00:00+00:00"),
                ),
            ),
        )
        t.add(self.urls["b"], (200, sd_page("b, corrected")))
        t.add(self.urls["c"], (200, sd_page("c")))
        t.add(self.urls["g"], (404, "gone"))
        t.add(self.new["e"], (200, sd_page("e")))
        t.add(self.new["h"], (200, sd_page("h", byline="By:")))
        cc = '<p>Data under <a href="https://creativecommons.org/licenses/by-nc/4.0/">x</a>.</p>'
        t.add(self.new["s"], (200, sd_page("s", extra=cc)))

    def run(self, **kw):
        kw.setdefault("state", {"through": THROUGH})
        kw.setdefault("removals", False)
        return update_pages(self.f, self.client, self.prev, now=NOW, prev_as_of=THROUGH, **kw)


def test_sitemap_entries_read_each_url_and_its_date():
    xml = sitemap(("https://x.example/a/", "2026-11-01T00:00:00+00:00"))
    xml = xml.replace("</urlset>", "<url><loc>https://x.example/b/</loc></url><url></url></urlset>")
    assert sitemap_entries(xml) == [
        ("https://x.example/a/", datetime(2026, 11, 1, tzinfo=timezone.utc)),
        ("https://x.example/b/", None),
    ]


def test_the_sitemap_route_reads_only_pages_changed_after_the_mark(tmp_path):
    w = SciDev(tmp_path)
    rows, upd, state = w.run()
    assert upd.status == "updated", upd.note
    asked = [u for u, _ in w.transport.calls]
    assert w.urls["a"] not in asked and w.urls["d"] not in asked
    assert f"{SD}/article-sitemap.xml" not in asked  # the newest one starts before the mark
    assert upd.new == 1 and upd.held == 1 and upd.changed == 1 and upd.removed == 1
    assert upd.route == {"route": "sitemap", "sitemaps_read": 1, "after_mark": 6, "unchanged": 1}
    assert upd.dropped == {"third_party:another license named outside an image's caption": 1}
    assert upd.third_party_new == 1
    assert rows[article_id(w.urls["b"])]["status"] == "changed"
    assert rows[article_id(w.urls["g"])]["status"] == "removed"
    assert rows[article_id(w.new["h"])]["releasable"] is False
    assert state == {"through": "2026-11-21T08:00:00Z"}
    assert upd.summary()["route"] == upd.route
    assert "not counted" in upd.count_line()
    log = (tmp_path / "usage_log.csv").read_text()
    assert "invented" not in log  # pages are logged by id
    assert article_id(w.new["e"]) in log


def test_no_state_takes_the_previous_versions_date_as_the_mark(tmp_path):
    w = SciDev(tmp_path)
    _rows, upd, state = w.run(state=None)
    assert upd.status == "updated" and state["through"] == "2026-11-21T08:00:00Z"
    _rows, upd, _ = SciDev(tmp_path / "b").run(state={"through": "not a date"})
    assert upd.status == "failed" and "no mark" in upd.note  # a broken state is never guessed
    w2 = SciDev(tmp_path / "c")
    _rows, upd, _ = update_pages(w2.f, w2.client, w2.prev, now=NOW, prev_as_of="", state=None)
    assert upd.status == "failed" and "no mark" in upd.note


def test_the_walk_goes_back_while_a_sitemap_starts_after_the_mark(tmp_path):
    w = SciDev(tmp_path)
    late = "2026-11-22T00:00:00+00:00"
    w.transport.routes[f"{SD}/article-sitemap2.xml"] = [
        (200, sitemap((sd_url("invented-n"), late)))
    ]
    w.transport.routes[f"{SD}/article-sitemap.xml"] = [
        (200, sitemap((w.urls["a"], "2026-11-01T00:00:00+00:00"), (w.urls["c"], late)))
    ]
    w.transport.add(sd_url("invented-n"), (200, sd_page("n")))
    _rows, upd, state = w.run()
    assert upd.status == "updated" and upd.route["sitemaps_read"] == 2
    assert (
        upd.new == 1 and upd.route["unchanged"] == 1 and state["through"] == "2026-11-22T00:00:00Z"
    )
    # Every sitemap the route may read starts after the mark: the mark looks wrong.
    maps = [f"article-sitemap{n}.xml" for n in range(1, MAX_SITEMAPS + 2)]
    w2 = SciDev(tmp_path / "b")
    w2.transport.routes[INDEX] = [(200, index(*maps))]
    for m in maps:
        w2.transport.routes[f"{SD}/{m}"] = [(200, sitemap((sd_url(f"x-{m[:-4]}"), late)))]
    rows, upd, state = w2.run()
    assert upd.status == "failed" and "the mark looks wrong" in upd.note
    assert rows == w2.prev and state == {"through": THROUGH}


def test_more_pages_than_the_limit_stop_before_any_page_is_read(tmp_path):
    w = SciDev(tmp_path)
    rows, upd, state = w.run(max_requests=5)
    assert upd.status == "over_budget" and "more than the limit of 5" in upd.note
    asked = {u for u, _ in w.transport.calls}
    assert not asked & set(w.new.values()) and rows == w.prev
    assert upd.route["route"] == "sitemap" and state == {"through": THROUGH}


@pytest.mark.parametrize(
    ("answer", "status"),
    [((403, "no"), "refused"), ((500, "down"), "failed"), ((404, "none"), "failed")],
)
def test_a_refusing_or_failing_sitemap_skips_the_source(tmp_path, answer, status):
    w = SciDev(tmp_path)
    w.transport.routes[INDEX] = [answer]
    rows, upd, _state = w.run()
    assert upd.status == status and rows == w.prev


def test_an_index_with_no_article_sitemap_or_a_failing_page_stops(tmp_path):
    w = SciDev(tmp_path)
    w.transport.routes[INDEX] = [(200, index())]
    assert w.run()[1].status == "failed"
    w2 = SciDev(tmp_path / "b")
    w2.transport.routes[w2.urls["b"]] = [(502, "bad gateway")]
    _rows, upd, _ = w2.run()
    assert upd.status == "failed"
    w3 = SciDev(tmp_path / "c")
    w3.transport.routes[f"{SD}/article-sitemap2.xml"] = [(404, "gone")]
    assert w3.run()[1].status == "failed"


def test_pages_that_are_not_articles_or_invalid_are_counted(tmp_path):
    w = SciDev(tmp_path)
    w.transport.routes[w.new["e"]] = [(200, "<html><body>no article</body></html>")]
    w.transport.routes[w.new["h"]] = [(404, "gone")]
    _rows, upd, _ = w.run()
    assert upd.dropped["not_an_article"] == 1 and upd.dropped["answer:404"] == 1


def aiac(tmp_path, n_old=3):
    reg = load_sources(registry(tmp_path))
    transport = FakeTransport()
    client, _ = make_test_client(tmp_path, transport)
    f = AfricaIsACountryFetcher(client, reg["africasacountry"], ReplayStore(tmp_path / "r"))
    olds = [f"{AIAC}/2026/07/invented-old-{i}" for i in range(n_old)]
    prev = {
        article_id(u): built(f, u, aiac_page(body=f'<p class="po-bo__paragraph">Old {i}.</p>'))
        for i, u in enumerate(olds)
    }
    return f, client, transport, prev, olds


def listing(*links):
    return "<html><body>" + "".join(f'<a href="{u}">t</a>' for u in links) + "</body></html>"


def test_the_listing_route_reads_new_stories_only(tmp_path):
    f, client, t, prev, olds = aiac(tmp_path)
    new = f"{AIAC}/2026/11/invented-new"
    republished = f"{AIAC}/2026/11/invented-republished"
    t.add(FRONT, (200, listing(new, republished, olds[0])))
    t.add(f"{FRONT}?page=2", (200, listing(olds[1], olds[2])))
    t.add(new, (200, aiac_page(date="11.18.2026")))
    seen = [article_id(republished)]
    rows, upd, state = update_pages(
        f, client, prev, now=NOW, prev_as_of=THROUGH, state={"seen": seen}, removals=False
    )
    assert upd.status == "updated" and upd.new == 1 and upd.listed == 1
    assert upd.route == {"route": "listing", "listing_pages_read": 2, "reread": 0, "unchanged": 0}
    assert republished not in [u for u, _ in t.calls]  # seen last time: not read again
    assert state["seen"] == sorted(article_id(u) for u in [new, republished, *olds])
    assert article_id(new) in rows


def test_the_listing_reads_on_until_it_meets_a_known_story_or_stops(tmp_path):
    f, client, t, prev, olds = aiac(tmp_path)
    fresh = [f"{AIAC}/2026/11/invented-{i}" for i in range(4)]
    t.add(FRONT, (200, listing(fresh[0])))
    t.add(f"{FRONT}?page=2", (200, listing(fresh[1])))
    t.add(f"{FRONT}?page=3", (200, listing(fresh[2], olds[0])))
    for i, u in enumerate(fresh[:3]):
        t.add(u, (200, aiac_page(date="11.18.2026", body=f"<p>Fresh {i}.</p>")))
    _rows, upd, _state = update_pages(
        f, client, prev, now=NOW, prev_as_of=THROUGH, state=None, removals=False
    )
    assert upd.status == "updated" and upd.route["listing_pages_read"] == 3 and upd.new == 3
    # No page up to the cap shares a story with the previous version.
    f2, client2, t2, prev2, _ = aiac(tmp_path / "b")
    for n in range(1, 7):
        t2.add(FRONT if n == 1 else f"{FRONT}?page={n}", (200, listing(f"{AIAC}/2026/11/z-{n}")))
    rows, upd, state = update_pages(
        f2, client2, prev2, now=NOW, prev_as_of=THROUGH, state={"seen": ["cw_x"]}, removals=False
    )
    assert upd.status == "failed" and "share no story" in upd.note
    assert rows == prev2 and state == {"seen": ["cw_x"]}


def test_a_listing_that_ends_early_is_read_to_its_end(tmp_path):
    f, client, t, prev, olds = aiac(tmp_path)
    t.add(FRONT, (200, listing(olds[0])))
    _rows, upd, state = update_pages(
        f, client, prev, now=NOW, prev_as_of=THROUGH, state=None, removals=False
    )
    assert upd.status == "updated" and upd.route["listing_pages_read"] == 2
    assert state == {"seen": [article_id(olds[0])]}


def test_page_state_from_a_saved_backfill(tmp_path):
    sd = tmp_path / "sd"
    (sd / "lists").mkdir(parents=True)
    (sd / "lists" / "sitemap-001.xml").write_text(
        sitemap(
            (sd_url("x"), "2026-01-01T00:00:00+00:00"), ("https://else.example/y", "2027-01-01")
        )
    )
    (sd / "lists" / "sitemap-002.xml").write_text(
        sitemap((sd_url("y"), "2026-11-16T14:10:04+00:00"))
    )
    assert page_state_from_backfill("scidevnet", sd) == {"through": "2026-11-16T14:10:04Z"}
    a = tmp_path / "a"
    (a / "lists").mkdir(parents=True)
    links = [f"{AIAC}/2026/11/s-{i}" for i in range(3)]
    (a / "lists" / "listing-p00001.html").write_text(listing(links[0], links[1]))
    (a / "lists" / "listing-p00002.html").write_text(listing(links[2], links[0]))
    with pytest.raises(Exception, match=r"urls\.json"):
        page_state_from_backfill("africasacountry", a)
    (a / "urls.json").write_text(json.dumps(links))
    assert page_state_from_backfill("africasacountry", a) == {
        "seen": sorted(article_id(canonical_url(u)) for u in links)
    }
    empty = tmp_path / "e"
    (empty / "lists").mkdir(parents=True)
    for sid in ("scidevnet", "africasacountry"):
        with pytest.raises(Exception, match="holds no"):
            page_state_from_backfill(sid, empty)


def write_version(tmp_path, rows, *, page_state=None, held=()):
    reg_path = registry(tmp_path)
    reg = load_sources(reg_path)
    takedowns = tmp_path / "takedowns.csv"
    takedowns.write_text("id,requested_on,basis\n")
    r = collect(tmp_path, "9.8.0", reg, rows=rows, takedowns_path=takedowns)
    out = tmp_path / "prev"
    extra = {"third_party_dropped": 0, "held_rows": list(held), "post_counts": {}}
    if page_state:
        extra["page_state"] = page_state
    write_release(
        r,
        out,
        reg_path,
        reg,
        card=card(r, reg, 0),
        licenses_md=licenses_md(r, reg),
        extra=extra,
    )
    return out, reg_path, takedowns


@pytest.fixture
def page_series(monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 8), ("scidevnet", "africasacountry"))


def two_sources(tmp_path):
    w = SciDev(tmp_path / "site")
    _f, _c, t, prev_a, olds = aiac(tmp_path / "aiac")
    rows = {"scidevnet": list(w.prev.values()), "africasacountry": list(prev_a.values())}
    out, reg_path, takedowns = write_version(
        tmp_path,
        rows,
        page_state={
            "scidevnet": {"through": THROUGH},
            "africasacountry": {"seen": [article_id(u) for u in olds]},
        },
    )
    for url, answers in t.routes.items():
        w.transport.routes[url] = answers
    w.transport.add(FRONT, (200, listing(*olds)))
    return w, out, reg_path, takedowns


def test_run_route_dry_run_then_an_offline_replay(tmp_path, page_series, capsys):
    w, out, reg_path, _ = two_sources(tmp_path)
    work = tmp_path / "work"
    s1 = run_route(
        tmp_path,
        out,
        "scidevnet",
        work,
        clients=make_clients(w.transport),
        registry_path=reg_path,
        now=NOW,
    )
    assert s1["update"]["status"] == "updated"
    assert s1["state_after"] == {
        "through": "2026-11-21T08:00:00Z",
        "removals_checked": "2026-11-23",
    }
    assert s1["update"]["route"]["removal_check"] == {
        "listed": 8,
        "rows_not_listed": 0,
        "confirmed_removed": 0,
        "still_answer": 0,
    }
    assert s1["rows_before"] == 5 and s1["new_ids"] == [article_id(w.new["e"])]
    calls = len(w.transport.calls)
    replay = tmp_path / "work2"
    args = [
        "--root", str(tmp_path), "update-route", "scidevnet", "--from", str(out), "--work",
        str(replay), "--answers", str(work / "answers"), "--offline", "--sources", str(reg_path),
    ]  # fmt: skip
    assert main(args) == 0
    assert "offline replay" in capsys.readouterr().out
    s2 = json.loads((replay / "route-summary.json").read_text())
    assert len(w.transport.calls) == calls  # nothing sent
    for key in ("state_after", "new_ids", "changed_ids", "removed_ids", "now"):
        assert s2[key] == s1[key]
    assert s1["answers_served_from_disk"] == 0 and s2["answers_served_from_disk"] > 0


def test_run_route_refuses_what_it_cannot_do(tmp_path, page_series, capsys):
    _w, out, reg_path, _ = two_sources(tmp_path)
    base = ["--root", str(tmp_path), "update-route"]
    tail = ["--from", str(out), "--work", str(tmp_path / "w"), "--sources", str(reg_path)]
    assert main([*base, "factly", *tail]) == 2
    assert main([*base, "scidevnet", *tail[:2], "--work", str(tmp_path / "w2"), "--offline"]) == 2
    assert main([*base, "scidevnet", "--from", str(tmp_path / "nowhere"), *tail[2:]]) == 2
    with pytest.raises(rel.ReleaseError, match="has no"):
        other = tmp_path / "o"
        other.mkdir()
        m = json.loads((out / "manifest.json").read_text())
        m["sources"] = ["scidevnet"]
        (other / "manifest.json").write_text(json.dumps(m))
        run_route(tmp_path, other, "africasacountry", tmp_path / "w3", registry_path=reg_path)
    err = capsys.readouterr().err
    assert "no page route" in err and "nothing to replay" in err


def test_the_weekly_update_takes_the_page_route_and_keeps_its_state(tmp_path, page_series):
    w, out, reg_path, takedowns = two_sources(tmp_path)

    res = run_update(
        tmp_path,
        out,
        tmp_path / "next",
        tmp_path / "work",
        registry_path=reg_path,
        takedowns_path=takedowns,
        baseline_path=tmp_path / "baseline.json",
        now=NOW,
        dry_run=True,
        clients=make_clients(w.transport),
    )
    assert res.status == "ready", res.stop_reasons
    sd, aa = res.sources["scidevnet"], res.sources["africasacountry"]
    assert (sd.new, sd.changed, sd.removed, sd.held) == (1, 1, 1, 1)
    assert aa.status == "updated" and aa.new == 0
    manifest = json.loads((tmp_path / "next" / "manifest.json").read_text())
    assert manifest["page_state"]["scidevnet"] == {
        "through": "2026-11-21T08:00:00Z",
        "removals_checked": "2026-11-23",
    }
    assert manifest["page_state"]["africasacountry"]["full_walk"] == "2026-11-23"
    assert manifest["update"]["sources"]["scidevnet"]["route"]["route"] == "sitemap"
    held = {h["id"] for h in manifest["held_rows"]}
    assert article_id(w.new["h"]) in held
    _m, rows = read_version(tmp_path / "next")
    assert article_id(w.new["e"]) in rows["scidevnet"]


def test_a_wordpress_only_update_writes_no_page_state(tmp_path, monkeypatch):
    from test_update import SOURCES, World

    monkeypatch.setitem(rel.SERIES, (9, 9), SOURCES)
    world = World(tmp_path)
    res = world.run()
    assert res.status == "ready", res.stop_reasons
    manifest = json.loads((tmp_path / "next" / "manifest.json").read_text())
    assert "page_state" not in manifest
    assert all("route" not in s for s in manifest["update"]["sources"].values())


def test_the_removal_check_confirms_each_missing_row_by_its_own_page(tmp_path):
    w = SciDev(tmp_path)
    # Row d leaves the sitemaps and its page answers 404 (the fake site's default): removed.
    w.transport.routes[f"{SD}/article-sitemap.xml"] = [(200, sitemap())]
    rows, upd, state = w.run(removals=True)
    assert upd.status == "updated", upd.note
    check = upd.route["removal_check"]
    assert check["rows_not_listed"] == 1 and check["confirmed_removed"] == 1
    assert check["still_answer"] == 0 and upd.route["sitemaps_read"] == 2
    assert rows[article_id(w.urls["d"])]["status"] == "removed" and upd.removed == 2  # and g
    assert state["removals_checked"] == "2026-11-23"
    log = (tmp_path / "usage_log.csv").read_text()
    assert article_id(w.urls["d"]) in log and "invented-d" not in log
    # A row that left the sitemaps but whose page still answers stays.
    w2 = SciDev(tmp_path / "b")
    w2.transport.routes[f"{SD}/article-sitemap.xml"] = [(200, sitemap())]
    w2.transport.add(w2.urls["d"], (200, sd_page("d")))
    rows2, upd2, _ = w2.run(removals=True)
    assert upd2.route["removal_check"]["still_answer"] == 1
    assert rows2[article_id(w2.urls["d"])] is w2.prev[article_id(w2.urls["d"])]
    # Any other answer is a failure, never a removal.
    w3 = SciDev(tmp_path / "c")
    w3.transport.routes[f"{SD}/article-sitemap.xml"] = [(200, sitemap())]
    w3.transport.add(w3.urls["d"], (500, "down"))
    assert w3.run(removals=True)[1].status == "failed"


def test_more_missing_rows_than_the_ceiling_stop_the_source(tmp_path, monkeypatch):
    from commonswire import pageupdate

    monkeypatch.setattr(pageupdate, "MAX_REMOVAL_CONFIRMATIONS", 0)
    w = SciDev(tmp_path)
    w.transport.routes[f"{SD}/article-sitemap.xml"] = [(200, sitemap())]
    rows, upd, state = w.run(removals=True)
    assert upd.status == "over_ceiling" and "more than the 0 pages" in upd.note
    assert rows == w.prev and state == {"through": THROUGH}
    asked = {u for u, _ in w.transport.calls}
    assert w.urls["d"] not in asked  # nothing confirmed past the ceiling
    monkeypatch.setattr(pageupdate, "MAX_REMOVAL_CONFIRMATIONS", 25)
    # The weekly page limit counts the confirmations too (6 changed pages and 1 to confirm).
    w2 = SciDev(tmp_path / "b")
    w2.transport.routes[f"{SD}/article-sitemap.xml"] = [(200, sitemap())]
    assert w2.run(removals=True, max_pages=6)[1].status == "over_budget"


def test_only_removals_reads_every_sitemap_and_no_changed_page(tmp_path):
    w = SciDev(tmp_path)
    _rows, upd, state = w.run(removals=True, only_removals=True)
    assert upd.status == "updated" and upd.listed == 0 and upd.route["sitemaps_read"] == 2
    assert {u for u, _ in w.transport.calls} & set(w.new.values()) == set()
    assert state["removals_checked"] == "2026-11-23"
    assert state["through"] == THROUGH  # the changed pages were not read: the mark stays


def test_a_listing_is_walked_in_full_once_a_month_and_recent_stories_reread(tmp_path):
    f, client, t, prev, olds = aiac(tmp_path)
    recent = f"{AIAC}/2026/11/invented-recent"
    prev[article_id(recent)] = built(
        f, recent, aiac_page(date="11.10.2026", body='<p class="po-bo__paragraph">Recent.</p>')
    )
    t.add(FRONT, (200, listing(recent, olds[0])))
    t.add(f"{FRONT}?page=2", (200, listing(olds[1])))
    t.add(f"{FRONT}?page=3", (200, listing(olds[1])))  # brings nothing new: the walk ends
    t.add(recent, (200, aiac_page(date="11.10.2026", body="<p>Recent, corrected.</p>")))
    t.add(olds[2], (410, "gone"))
    state = {"seen": [], "full_walk": "2026-10-01"}
    rows, upd, new_state = update_pages(f, client, prev, now=NOW, prev_as_of=THROUGH, state=state)
    assert upd.status == "updated", upd.note
    assert upd.route["reread"] == 1 and upd.changed == 1  # the recent story was edited
    assert upd.route["walk_pages_read"] == 3
    assert upd.route["removal_check"]["confirmed_removed"] == 1
    assert rows[article_id(olds[2])]["status"] == "removed"
    assert new_state["full_walk"] == "2026-11-23"
    # Walked less than four weeks ago: no walk this week.
    f2, client2, t2, prev2, olds2 = aiac(tmp_path / "b")
    t2.add(FRONT, (200, listing(*olds2)))
    _rows, upd2, st2 = update_pages(
        f2, client2, prev2, now=NOW, prev_as_of=THROUGH, state={"full_walk": "2026-11-10"}
    )
    assert "walk_pages_read" not in upd2.route and st2["full_walk"] == "2026-11-10"
    # A listing with more pages than the walk reads stops the source.
    from commonswire import pageupdate

    f3, client3, t3, prev3, olds3 = aiac(tmp_path / "c")
    for n in range(1, 5):
        t3.add(
            FRONT if n == 1 else f"{FRONT}?page={n}", (200, listing(*olds3, f"{AIAC}/2026/01/p{n}"))
        )
    old_max = pageupdate.MAX_WALK_PAGES
    pageupdate.MAX_WALK_PAGES = 3
    try:
        _r, upd3, _s = update_pages(f3, client3, prev3, now=NOW, prev_as_of=THROUGH, state=None)
    finally:
        pageupdate.MAX_WALK_PAGES = old_max
    assert upd3.status == "failed" and "more than 3 pages" in upd3.note


def test_only_removals_on_a_listing_walks_and_confirms_nothing_else(tmp_path, page_series, capsys):
    w, out, reg_path, _ = two_sources(tmp_path)
    args = [
        "--root", str(tmp_path), "update-route", "africasacountry", "--from", str(out), "--work",
        str(tmp_path / "w"), "--sources", str(reg_path), "--only-removals",
    ]  # fmt: skip
    from commonswire import pageupdate

    real = pageupdate.default_clients
    pageupdate.default_clients = lambda root, locks: make_clients(w.transport)
    try:
        assert main(args) == 0
    finally:
        pageupdate.default_clients = real
    summary = json.loads((tmp_path / "w" / "route-summary.json").read_text())
    assert summary["only_removals"] is True and summary["update"]["new"] == 0
    assert summary["update"]["route"]["walk_pages_read"] == 2
    assert summary["update"]["route"]["removal_check"]["rows_not_listed"] == 0
