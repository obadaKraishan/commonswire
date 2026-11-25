"""The weekly update, with invented sources, posts, pages and listings. No network."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit

import pyarrow.parquet as pq
import pytest

from commonswire import release as rel
from commonswire.cli import main
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import (
    FactlyFetcher,
    GlobalVoicesFetcher,
    PublicRecordFetcher,
)
from commonswire.http import Pacer, PoliteClient, RawResponse
from commonswire.release import ReleaseError, collect, write_release
from commonswire.release_text import card, licenses_md
from commonswire.schema import article_id, canonical_url, make_article
from commonswire.sources import load_sources, render_credit
from commonswire.update import (
    baseline,
    carried_state,
    next_version,
    read_version,
    redact,
    run_update,
)
from fakes import FakeClock
from test_sources import row, write_csv

NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
BUILT = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)  # the previous version's as_of
SECRET_TEXT = "Invented paragraph"  # every invented body starts with this
NAMES = ("Ana Invented", "Bo Invented", "Cy Translator", "Di Invented", "Ed Invented")
GV = "https://globalvoices.org"
FACTLY = "https://factly.in"
TPR = "https://thepublicrecord.ca"
SOURCES = ("wikinews_en", "thepublicrecord", "factly", "globalvoices")


@pytest.fixture(autouse=True)
def series(monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 9), SOURCES)


def registry(tmp_path):
    return write_csv(
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
                source_id="thepublicrecord",
                name="The Public Record",
                homepage=f"{TPR}/",
                license="CC-BY-SA-4.0",
                credit_line="{title}, by {authors}, {source} ({url}), {license}",
            ),
            row(
                source_id="factly",
                name="Factly",
                kind="fact-check",
                homepage=f"{FACTLY}/",
                license="CC-BY-4.0",
                credit_line="{title}, by {authors}, {source} ({url}), {license}",
            ),
            row(
                source_id="globalvoices",
                name="Global Voices",
                homepage=f"{GV}/",
                license="CC-BY-3.0",
                credit_line="{title}, by {authors} for {source} ({url}), {license}",
            ),
        ],
    )


def post(base, n, day, *, body=None, modified=None, author=None, cats=(1,)):
    """A WordPress post as a backfill-style answer gives it (no embedded names)."""
    link = f"{base}/{day[:4]}/{day[5:7]}/{day[8:10]}/invented-{n}/"
    p = {
        "id": n,
        "link": link,
        "title": {"rendered": f"Invented headline {n}"},
        "content": {"rendered": body or f"<p>{SECRET_TEXT} {n} of an invented story.</p>"},
        "date_gmt": f"{day}T08:00:00",
        "modified_gmt": f"{modified or day}T09:00:00",
        "type": "post",
        "author": 7,
        "categories": list(cats),
    }
    if author:
        p["yoast_head_json"] = {"author": author}
    return p


class Site:
    """Answers like the invented sites: their WordPress API by path and query, article pages,
    and Global Voices' listing pages. Records every URL asked for."""

    def __init__(self):
        self.calls: list[str] = []
        self.recent: dict[str, list[dict]] = {"factly": [], "globalvoices": [], "tpr": []}
        self.edited: dict[str, list[dict]] = {"factly": [], "globalvoices": [], "tpr": []}
        self.pages: dict[str, tuple[int, str]] = {}
        self.listing: dict[int, str] = {}
        self.refuse: set[str] = set()
        #: Post counts per year (5 if not set) and the links a year's listing gives.
        self.counts: dict[str, dict[int, int]] = {"factly": {}, "globalvoices": {}, "tpr": {}}
        self.year_links: dict[str, dict[int, list[str]]] = {
            "factly": {},
            "globalvoices": {},
            "tpr": {},
        }
        self.refuse_counts: set[str] = set()

    def __call__(self, url, headers, timeout, max_bytes):
        self.calls.append(url)
        parts = urlsplit(url)
        host, path = parts.hostname, parts.path
        q = dict(parse_qsl(parts.query))
        sid = {"factly.in": "factly", "globalvoices.org": "globalvoices"}.get(host, "tpr")

        def answer(status, body, hdrs=None):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            return RawResponse(url=url, status=status, headers=hdrs or {}, body=data)

        if path == "/robots.txt":
            return answer(200, "User-agent: *\nCrawl-delay: 10\n" if sid == "globalvoices" else "")
        if "/wp-json/wp/v2/" in path:
            if host in self.refuse:
                return answer(403, "no")
            if q.get("per_page") == "1" and q.get("_fields") == "id":  # a post count
                if host in self.refuse_counts:
                    return answer(403, "no")
                n = self.counts[sid].get(int(q["after"][:4]) + 1, 5)
                return answer(200, '[{"id": 1}]' if n else "[]", {"X-WP-Total": str(n)})
            if q.get("_fields") == "link":  # a year's listing, links only
                links = self.year_links[sid].get(int(q["after"][:4]) + 1, [])
                page = int(q["page"])
                chunk = links[(page - 1) * 100 : page * 100]
                if page > 1 and not chunk:
                    return answer(400, "{}")
                pages = str(max(1, -(-len(links) // 100)))
                body = json.dumps([{"link": x} for x in chunk])
                return answer(200, body, {"X-WP-TotalPages": pages})
            if q.get("page") != "1":
                return answer(400, "{}")
            if path.endswith("/categories"):
                cats = [{"id": 1, "name": "World"}, {"id": 2, "name": "Partner content"}]
                return answer(200, json.dumps(cats))
            if path.endswith("/users"):
                return answer(200, json.dumps([{"id": 7, "name": "Ana Invented"}]))
            if "after" in q:
                return answer(200, json.dumps(self.recent[sid]))
            if "modified_after" in q:
                assert "before" in q
                return answer(200, json.dumps(self.edited[sid]))
        if path.startswith("/page/"):
            n = int(path.split("/")[2])
            if n in self.listing:
                return answer(200, self.listing[n])
            return answer(404, "none")
        if url in self.pages:
            return answer(*self.pages[url])
        return answer(404, "not found")


def listing_story(link, writers=(), translators=(), credits=True):
    links = "".join(f'<a class="user-link" href="{GV}/author/x/">{w}</a>, ' for w in writers)
    tr = "".join(f'<a class="user-link" href="{GV}/author/y/">{t}</a>' for t in translators)
    block = ""
    if credits:
        block = (
            '<div class="text-credits-container"><div class="text-credits-section">'
            f'<span class="credit-label">Written by</span> {links}</div>'
        )
        if translators:
            block += (
                '<div class="text-credits-section"><span class="credit-label">Translated by'
                f"</span> {tr}</div>"
            )
        block += "</div>"
    return (
        f'<div class="post-summary"><div class="post-title"><a href="{link}">An invented '
        f"title</a></div>{block}</div>"
    )


def listing_page(*stories):
    return f"<html><body><main>{''.join(stories)}</main></body></html>"


def make_clients(site, clock=None):
    clock = clock or FakeClock()

    def make(budget, log, cache):
        return PoliteClient(
            usage_log=log,
            pacer=Pacer(log.path.parent / "locks", clock=clock.time, sleep=clock.sleep),
            transport=site,
            sleep=clock.sleep,
            jitter=lambda: 0.0,
            byte_budget=budget,
            cache=cache,
        )

    return make


def built_row(fetcher, p, *, authors=(), translators=(), credited=False):
    key = canonical_url(p["link"])
    if authors:
        fetcher.page_bylines[key] = tuple(authors)
    if translators:
        fetcher.page_translators[key] = tuple(translators)
    if credited:
        fetcher.source_credited.add(key)
    art = fetcher.build(fetcher.item_from_post(p), BUILT)
    return json.loads(art.model_dump_json())


def wikinews_row(n):
    url = f"https://en.wikinews.org/wiki/Invented_{n}"
    title = f"Invented wiki story {n}"
    a = make_article(
        source_id="wikinews_en",
        url=url,
        title=title,
        text=f"{SECRET_TEXT} {n} of a closed wiki.",
        published_at=datetime(2010, 1, n, tzinfo=timezone.utc),
        retrieved_at=BUILT,
        language="en",
        license="CC-BY-2.5",
        credit_line=render_credit(
            "{title}, {source} ({url}), {license}",
            title=title,
            authors=(),
            source="Wikinews",
            url=url,
            license="CC-BY-2.5",
        ),
    )
    return json.loads(a.model_dump_json())


class World:
    """A previous version (9.9.0) of four invented sources, and the site as it is a week later."""

    def __init__(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        self.tmp = tmp_path
        self.reg_path = registry(tmp_path)
        self.registry = load_sources(self.reg_path)
        self.takedowns = tmp_path / "takedowns.csv"
        self.takedowns.write_text("id,requested_on,basis\n")
        self.site = Site()
        client = make_clients(self.site)(10**9, _log(tmp_path / "unused"), None)
        reg = self.registry
        fa = FactlyFetcher(client, reg["factly"], ReplayStore(tmp_path / "x"))
        fa.category_names = {1: "World", 2: "Partner content"}
        gv = GlobalVoicesFetcher(client, reg["globalvoices"], ReplayStore(tmp_path / "x"))
        tp = PublicRecordFetcher(client, reg["thepublicrecord"], ReplayStore(tmp_path / "x"))
        # Factly: f1 stays, f2 is edited, f3 is removed at its source, f4 is missing from the
        # listing but still answers, f5 is old and edited, f0 is old and untouched.
        self.f = {
            0: post(FACTLY, 100, "2024-03-01", author="Ana Invented"),
            1: post(FACTLY, 101, "2026-11-01", author="Ana Invented"),
            2: post(FACTLY, 102, "2026-11-05", author="Ana Invented"),
            3: post(FACTLY, 103, "2026-11-08", author="Ana Invented"),
            4: post(FACTLY, 104, "2026-11-09", author="Ana Invented"),
            5: post(FACTLY, 105, "2025-06-01", author="Ana Invented"),
        }
        # Global Voices: g1 stays; g6 is old, with a translator, and edited; g7 is old,
        # credited to the source itself, and edited; g8 was held and is outside the window.
        self.g = {
            1: post(GV, 201, "2026-11-10"),
            6: post(GV, 206, "2025-01-10"),
            7: post(GV, 207, "2024-05-10"),
        }
        self.t = {1: post(TPR, 301, "2026-11-02")}
        rows = {
            "wikinews_en": [wikinews_row(1), wikinews_row(2)],
            "factly": [built_row(fa, p) for p in self.f.values()],
            "globalvoices": [
                built_row(gv, self.g[1], authors=("Bo Invented",)),
                built_row(gv, self.g[6], authors=("Bo Invented",), translators=("Cy Translator",)),
                built_row(gv, self.g[7], credited=True),
            ],
            "thepublicrecord": [built_row(tp, self.t[1], authors=("Di Invented",))],
        }
        self.held_old = "cw_" + "ab" * 8
        self.g4 = post(GV, 204, "2026-11-15")
        self.held = {
            self.held_old: {
                "source_id": "globalvoices",
                "published_on": "2020-01-01",
                "reason": "credited to an account, not a person",
            },
            article_id(self.g4["link"]): {
                "source_id": "globalvoices",
                "published_on": "2026-11-15",
                "reason": "credited to an account, not a person",
            },
        }
        self.prev = self.write_prev(rows, extra={"held_rows": self.held_list()})
        self.week_later()

    def held_list(self):
        return [{"id": k, **v} for k, v in sorted(self.held.items())]

    def write_prev(self, rows, extra, name="prev"):
        r = collect(self.tmp, "9.9.0", self.registry, rows=rows, takedowns_path=self.takedowns)
        out = self.tmp / name
        write_release(
            r,
            out,
            self.reg_path,
            self.registry,
            card=card(r, self.registry, 3),
            licenses_md=licenses_md(r, self.registry),
            extra={"third_party_dropped": 3, **extra},
        )
        return out

    def week_later(self):
        s, f, g = self.site, self.f, self.g
        edited_body = f"<p>{SECRET_TEXT} 102, corrected.</p>"
        s.recent["factly"] = [
            f[1],
            post(FACTLY, 102, "2026-11-05", body=edited_body, author="Ana Invented"),
            post(FACTLY, 106, "2026-11-18", author="Ed Invented"),  # new
            post(FACTLY, 107, "2026-11-19", author="Ed Invented", cats=(2,)),  # partner: dropped
        ]
        s.edited["factly"] = [
            post(
                FACTLY,
                105,
                "2025-06-01",
                body=f"<p>{SECRET_TEXT} 105, corrected.</p>",
                author="Ana Invented",
            )
        ]
        s.pages[f[3]["link"]] = (404, "gone")
        s.pages[f[4]["link"]] = (200, "<html><body>still here</body></html>")
        self.g2 = post(GV, 202, "2026-11-17")  # credited on listing page 1, with a translator
        self.g3 = post(GV, 203, "2026-11-16")  # a teaser on page 1, credited on page 2
        self.g5 = post(GV, 205, "2026-11-14")  # in no listing page: held
        s.recent["globalvoices"] = [g[1], self.g2, self.g3, self.g4, self.g5]
        s.edited["globalvoices"] = [
            post(GV, 206, "2025-01-10", body=f"<p>{SECRET_TEXT} 206, corrected.</p>"),
            post(GV, 207, "2024-05-10", body=f"<p>{SECRET_TEXT} 207, corrected.</p>"),
        ]
        s.listing[1] = listing_page(
            listing_story(self.g3["link"], credits=False),
            listing_story(self.g2["link"], ["Bo Invented"], ["Cy Translator", "Guest Contributor"]),
            listing_story(self.g4["link"], ["Guest Contributor"]),
            listing_story(g[1]["link"], ["Bo Invented"]),
        )
        s.listing[2] = listing_page(listing_story(self.g3["link"], ["Ed Invented"]))
        s.listing[3] = listing_page(listing_story(f"{GV}/2026/10/01/older/", ["Bo Invented"]))
        s.listing[4] = listing_page(listing_story(f"{GV}/2026/09/01/oldest/", ["Bo Invented"]))
        self.t2 = post(TPR, 302, "2026-11-18")  # new, its byline only on its page
        s.recent["tpr"] = [self.t[1], self.t2]
        s.pages[self.t2["link"]] = (
            200,
            '<html><body><div class="entry-meta"><span class="byline"><a href="/author/e/">'
            "Ed Invented</a></span></div></body></html>",
        )

    def run(self, out="next", **kw):
        kw.setdefault("clients", make_clients(self.site))
        kw.setdefault("now", NOW)
        kw.setdefault("dry_run", False)
        return run_update(
            self.tmp,
            kw.pop("prev", self.prev),
            self.tmp / out,
            kw.pop("work", self.tmp / "work"),
            registry_path=kw.pop("registry_path", self.reg_path),
            takedowns_path=self.takedowns,
            baseline_path=kw.pop("baseline_path", self.tmp / "baseline.json"),
            **kw,
        )


def _log(path):
    from commonswire.http import UsageLog

    return UsageLog(path / "usage_log.csv")


def released(out):
    m = json.loads((out / "manifest.json").read_text())
    rows = {}
    for names in m["configurations"].values():
        for name in names:
            for r in pq.read_table(out / name).to_pylist():
                rows[r["id"]] = r
    return m, rows


def test_a_week_of_new_changed_removed_and_credited_rows(tmp_path):
    w = World(tmp_path)
    res = w.run()
    assert res.status == "ready" and res.ready_to_deliver and not res.stop_reasons
    fa, gv, tp = (res.sources[s] for s in ("factly", "globalvoices", "thepublicrecord"))
    assert res.sources["wikinews_en"].status == "closed"
    assert (fa.new, fa.changed, fa.removed, fa.removal_checks) == (1, 2, 1, 2)
    assert fa.third_party_new == 1 and fa.dropped == {"third_party:partner_category": 1}
    assert (gv.new, gv.changed, gv.removed, gv.held) == (2, 2, 0, 2)
    assert gv.listing["wanted"] == 4 and gv.listing["with_writer"] == 2
    assert gv.listing["with_translators"] == 1 and gv.listing["not_found"] == 1
    assert gv.listing["pages"] == 3  # page 3 lists only older stories: no page 4
    assert (tp.new, tp.page_bylines) == (1, 1)
    m, rows = released(tmp_path / "next")
    ids = {k: article_id(v["link"]) for k, v in w.f.items()}
    assert ids[3] not in rows and ids[4] in rows and ids[0] in rows
    assert rows[ids[2]]["status"] == "changed" and rows[ids[5]]["status"] == "changed"
    assert rows[ids[2]]["retrieved_at"] == NOW and rows[ids[1]]["retrieved_at"] == BUILT
    g2 = rows[article_id(w.g2["link"])]
    assert g2["authors"] == ["Bo Invented"] and g2["translators"] == ["Cy Translator"]
    assert "translated by Cy Translator" in g2["credit_line"]
    assert rows[article_id(w.g3["link"])]["authors"] == ["Ed Invented"]
    # Edited old rows keep the bylines of the previous version, with no listing or page read.
    g6, g7 = rows[article_id(w.g[6]["link"])], rows[article_id(w.g[7]["link"])]
    assert g6["translators"] == ["Cy Translator"] and g6["status"] == "changed"
    assert g7["authors"] == [] and "for Global Voices" in g7["credit_line"]
    assert rows[article_id(w.t2["link"])]["authors"] == ["Ed Invented"]
    # Held: g4 (an account) again, g5 (no listing), and the old held row carried over.
    held = {h["id"]: h for h in m["held_rows"]}
    assert set(held) == {w.held_old, article_id(w.g4["link"]), article_id(w.g5["link"])}
    assert held[article_id(w.g5["link"])]["reason"] == "no byline"
    assert m["held_rows_not_released"] == {"globalvoices": 3}
    assert m["third_party_dropped"] == 4  # 3 carried, 1 new
    assert m["removed_rows_not_released"] == {"factly": 1}
    assert m["update"]["from_version"] == "9.9.0" and m["update"]["new"] == 4
    assert set(m["update"]["requests"]) == {"factly.in", "globalvoices.org", "thepublicrecord.ca"}
    assert res.rows_after == res.rows_before + 4 - 1
    readme = (tmp_path / "next" / "README.md").read_text()
    assert "## This update" in readme and "4 new rows, 4 changed, 1 removed" in readme
    assert "3 more rows are held back" in readme and "4 were dropped" in readme
    # No request to the closed source; the removal checks are logged by id, not address.
    assert not [c for c in w.site.calls if "wikinews" in c]
    with (tmp_path / "work" / "usage_log.csv").open(encoding="utf-8") as fh:
        logged = list(csv.DictReader(fh))
    assert ids[3] in {r["path"] for r in logged}
    assert not any(r["path"].startswith("/2026/") for r in logged if r["host"] == "factly.in")
    # What a public log or pull request would show: counts, ids and hosts, no text or names.
    shown = json.dumps(res.summary()) + res.markdown()
    assert SECRET_TEXT not in shown and "Invented headline" not in shown
    assert not any(n in shown for n in NAMES)
    assert "/2026/" not in shown


def test_an_offline_replay_sends_nothing_and_builds_the_same_rows(tmp_path):
    w = World(tmp_path)
    first = w.run(out="a")
    sent = len(w.site.calls)
    assert sent > 0
    again = w.run(out="b", offline=True, now=None)
    assert len(w.site.calls) == sent  # nothing was sent
    assert again.status == first.status == "ready"
    assert again.requests == {}
    for f in ("data/by/train-00000-of-00001.parquet", "index.csv", "README.md"):
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes()
    with pytest.raises(ReleaseError, match="nothing to replay"):
        w.run(out="c", offline=True, work=tmp_path / "empty-work")


def test_a_dry_run_is_never_ready_to_deliver(tmp_path):
    w = World(tmp_path)
    # A download's own files (Hugging Face's .gitattributes and .cache/) are not the release's.
    (w.prev / ".gitattributes").write_text("*.parquet filter=lfs\n")
    (w.prev / ".cache" / "huggingface").mkdir(parents=True)
    (w.prev / ".cache" / "huggingface" / "x.lock").write_text("")
    res = w.run(dry_run=True)
    assert res.status == "ready" and not res.ready_to_deliver
    assert res.summary()["ready_to_deliver"] is False and "(dry run)" in res.markdown()


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("registry", "registry change needs the maintainer"),
        ("takedowns", "takedown request(s) are open"),
        ("prs", "pull request(s) on the dataset are still open"),
        ("source", "a new source needs the maintainer"),
        ("series", "has no source list"),
        ("out", "is not empty"),
        ("tampered", "fails its own check"),
        ("no_held", "carries no list of held rows"),
    ],
)
def test_stops_before_any_request(tmp_path, monkeypatch, change, reason):
    w = World(tmp_path)
    kw = {}
    if change == "registry":
        other = tmp_path / "other"
        other.mkdir()
        p = registry(other)
        p.write_text(p.read_text() + "\n")
        kw["registry_path"] = p
    elif change == "takedowns":
        kw["open_takedowns"] = 1
    elif change == "prs":
        kw["open_dataset_prs"] = 2
    elif change == "source":
        monkeypatch.setitem(rel.SERIES, (9, 9), (*SOURCES, "altnews"))
    elif change == "series":
        kw["version"] = "9.8.1"
    elif change == "out":
        (tmp_path / "next").mkdir()
        (tmp_path / "next" / "old.txt").write_text("x")
    elif change == "tampered":
        (w.prev / "index.csv").write_text("id\n")
    elif change == "no_held":
        m = json.loads((w.prev / "manifest.json").read_text())
        del m["held_rows"]
        (w.prev / "manifest.json").write_text(json.dumps(m))
    res = w.run(**kw)
    assert res.status == "stopped"
    assert any(reason in r for r in res.stop_reasons), res.stop_reasons
    assert w.site.calls == []


def test_the_registry_is_the_series_own(tmp_path, monkeypatch):
    """A series whose registry is frozen updates with its copy, so data/sources.csv can hold
    the next series' registry; the published version's number picks the series."""
    from commonswire.update import FROZEN_REGISTRIES, registry_for

    assert registry_for(tmp_path, "0.2.4") == tmp_path / FROZEN_REGISTRIES[(0, 2)]
    assert registry_for(tmp_path, "0.3.1") == tmp_path / "data" / "sources.csv"
    w = World(tmp_path)
    frozen = tmp_path / "frozen" / "sources.csv"
    frozen.parent.mkdir()
    frozen.write_bytes(w.reg_path.read_bytes())
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "sources.csv").write_text("source_id\nnext_series_only\n")
    monkeypatch.setitem(FROZEN_REGISTRIES, (9, 9), "frozen/sources.csv")
    res = w.run(registry_path=None)
    assert res.status == "ready", res.stop_reasons
    assert (tmp_path / "next" / "sources.csv").read_bytes() == frozen.read_bytes()


def test_the_registry_of_the_next_series_stops_a_frozen_series(tmp_path, monkeypatch):
    from commonswire.update import FROZEN_REGISTRIES

    w = World(tmp_path)
    (tmp_path / "frozen").mkdir()
    (tmp_path / "frozen" / "sources.csv").write_text("source_id\nnext_series_only\n")
    monkeypatch.setitem(FROZEN_REGISTRIES, (9, 9), "frozen/sources.csv")
    res = w.run(registry_path=None)
    assert any("frozen/sources.csv) differs" in r for r in res.stop_reasons), res.stop_reasons
    assert w.site.calls == []


def test_an_update_never_begins_a_series(tmp_path, monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 10), SOURCES)
    w = World(tmp_path)
    res = w.run(version="9.10.0")
    assert res.status == "stopped"
    assert any("begins a new series" in r for r in res.stop_reasons), res.stop_reasons
    assert w.site.calls == []


def test_a_released_row_that_would_become_a_copy_stops_the_run(tmp_path, monkeypatch):
    """A weekly run never drops a released row as a copy of another source's row (series 0.3's
    republished-copies rule): it stops for the maintainer."""
    w = World(tmp_path)
    w.week_later()
    monkeypatch.setattr(rel, "REPUBLISHED_COPIES", {"factly": "globalvoices"})
    res = w.run()
    assert res.status == "stopped"
    assert any("left out as copies" in r for r in res.stop_reasons), res.stop_reasons


def test_a_runs_request_cap_skips_the_sources_past_it(tmp_path):
    w = World(tmp_path)
    w.week_later()
    res = w.run(max_requests=3)
    assert res.status == "stopped"
    over = [s for s, u in res.sources.items() if u.status == "over_budget"]
    assert over and all("request budget" in res.sources[s].note for s in over)
    assert len(w.site.calls) <= 3


def test_a_refusing_source_is_skipped_and_named(tmp_path):
    w = World(tmp_path)
    w.site.refuse.add("factly.in")
    res = w.run()
    fa = res.sources["factly"]
    assert fa.status == "refused" and "factly.in/..." in fa.note
    assert res.status == "stopped" and any("factly was refused" in r for r in res.stop_reasons)
    _, rows = released(tmp_path / "next")
    assert article_id(w.f[3]["link"]) in rows  # its rows carried over unchanged
    assert not [c for c in w.site.calls if "factly.in/2026" in c]  # never worked around
    again = World(tmp_path / "b")
    again.site.refuse.add("factly.in")
    ok = again.run(allow_skipped=frozenset({"factly"}))
    assert ok.status == "ready" and any("skipped, as allowed" in n for n in ok.notes)


def test_a_failing_listing_or_budget_stops_the_source(tmp_path):
    w = World(tmp_path)
    w.site.listing[1] = "<html>an error page</html>"  # lists no story: the walk ends
    w.site.pages[w.f[3]["link"]] = (500, "busy")  # retried, then kept (not removed)
    res = w.run()
    assert res.sources["globalvoices"].listing["found"] == 0
    assert res.sources["factly"].removed == 0
    tight = World(tmp_path / "b").run(max_mb=0)
    assert all(u.status == "over_budget" for s, u in tight.sources.items() if s != "wikinews_en")
    assert tight.status == "stopped"


def test_too_many_rows_missing_from_a_listing_stops_the_source(tmp_path, monkeypatch):
    from commonswire import update as up

    monkeypatch.setattr(up, "MAX_REMOVAL_CHECKS", 0)
    res = World(tmp_path).run()
    assert res.sources["factly"].status == "failed"
    assert "the listing looks wrong" in res.sources["factly"].note


def test_a_version_that_shrinks_too_much_stops(tmp_path):
    w = World(tmp_path)
    w.site.recent["factly"] = [w.f[1]]  # f2 and f4 vanish from the listing too
    w.site.pages[w.f[2]["link"]] = (410, "gone")
    w.site.pages[w.f[4]["link"]] = (404, "gone")
    w.site.recent["globalvoices"] = [w.g[1]]
    w.site.recent["tpr"] = [w.t[1]]
    res = w.run(max_shrink=0.01)
    assert res.status == "stopped"
    assert any("would shrink" in r for r in res.stop_reasons)


def test_nothing_new_is_unchanged_and_a_takedown_is_applied(tmp_path):
    w = World(tmp_path)
    s = w.site
    s.recent = {"factly": [w.f[1], w.f[2]], "globalvoices": [w.g[1]], "tpr": [w.t[1]]}
    s.edited = {"factly": [], "globalvoices": [], "tpr": []}
    s.pages[w.f[3]["link"]] = (200, "<html>here</html>")
    res = w.run()
    assert res.status == "unchanged"
    w.takedowns.write_text(f"id,requested_on,basis\n{article_id(w.f[1]['link'])},2026-11-19,x\n")
    res = w.run(out="next2", work=tmp_path / "work2", max_shrink=0.5)  # 1 of 12 rows
    assert res.status == "ready" and res.summary()["ids"]["taken_down"]
    m, rows = released(tmp_path / "next2")
    assert article_id(w.f[1]["link"]) not in rows
    assert m["taken_down_rows_not_released"] == {"factly": 1}


def test_carried_state_from_the_baseline_file(tmp_path):
    w = World(tmp_path)
    m = json.loads((w.prev / "manifest.json").read_text())
    held, third = carried_state(m, w.prev, tmp_path / "none.json")
    assert set(held) == set(w.held) and third == 3
    del m["held_rows"]
    (w.prev / "manifest.json").write_text(json.dumps(m))
    path = tmp_path / "baseline.json"
    assert carried_state(m, w.prev, path) is None
    from commonswire.release import sha256

    base = {
        "version": "9.9.0",
        "manifest_sha256": sha256(w.prev / "manifest.json"),
        "third_party_dropped": 5,
        "held_rows": w.held_list(),
    }
    path.write_text(json.dumps(base))
    held, third = carried_state(m, w.prev, path)
    assert third == 5 and set(held) == set(w.held)
    path.write_text(json.dumps({**base, "manifest_sha256": "0" * 64}))
    assert carried_state(m, w.prev, path) is None
    path.write_text(json.dumps({**base, "version": "9.9.7"}))
    assert carried_state(m, w.prev, path) is None


def test_read_version_gives_stored_rows_back(tmp_path):
    w = World(tmp_path)
    manifest, rows = read_version(w.prev)
    assert manifest["version"] == "9.9.0" and set(rows) == set(SOURCES)
    r = rows["factly"][article_id(w.f[1]["link"])]
    assert r["releasable"] is True and r["published_at"] == "2026-11-01T08:00:00Z"
    assert "kind" not in r and "near_duplicates" not in r


def test_baseline_from_stored_rows(tmp_path):
    w = World(tmp_path)
    rows_dir = tmp_path / "data" / "interim" / "rows"
    rows_dir.mkdir(parents=True)
    _, stored = read_version(w.prev)
    held_row = {**stored["factly"][article_id(w.f[0]["link"])]}
    held_row.update(releasable=False, hold_reason="no byline: Factly asks for it")
    stored["factly"][held_row["id"]] = held_row
    for s, rows in stored.items():
        (rows_dir / f"{s}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    (tmp_path / "data" / "takedowns.csv").write_text("id,requested_on,basis\n")
    release_dir = tmp_path / "data" / "release" / "9.9.0"
    release_dir.mkdir(parents=True)
    m = json.loads((w.prev / "manifest.json").read_text())
    m["held_rows_not_released"] = {"factly": 1}
    (release_dir / "manifest.json").write_text(json.dumps(m))
    ev = tmp_path / "data" / "evidence" / "backfill"
    ev.mkdir(parents=True)
    (ev / "factly.build.json").write_text(json.dumps({"dropped": {"third_party:x": 2, "y": 1}}))
    b = baseline(tmp_path, "9.9.0", w.registry)
    assert b["third_party_dropped"] == 2
    assert b["held_rows"] == [
        {
            "id": held_row["id"],
            "source_id": "factly",
            "published_on": "2024-03-01",
            "reason": "no byline",
        }
    ]
    m["held_rows_not_released"] = {}
    (release_dir / "manifest.json").write_text(json.dumps(m))
    with pytest.raises(ReleaseError, match="the rows changed since the build"):
        baseline(tmp_path, "9.9.0", w.registry)


def test_cli_update_offline_writes_the_summary(tmp_path, capsys):
    w = World(tmp_path)
    w.run(out="live")
    argv = [
        "--root",
        str(tmp_path),
        "update",
        "--from",
        str(w.prev),
        "--out",
        str(tmp_path / "cli"),
        "--work",
        str(tmp_path / "work"),
        "--sources",
        str(w.reg_path),
        "--takedowns",
        str(w.takedowns),
        "--baseline",
        str(tmp_path / "none.json"),
        "--offline",
        "--dry-run",
        "--max-count-requests",
        "10",
    ]
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "update 9.9.0 -> 9.9.1: ready (dry run" in out and "factly: updated" in out
    assert "factly count check: 3 years recorded (baseline)" in out
    assert "note: count check: 9.9.0 has no post counts" in out
    summary = json.loads((tmp_path / "work" / "summary.json").read_text())
    assert summary["dry_run"] is True and summary["ready_to_deliver"] is False
    assert (tmp_path / "work" / "summary.md").read_text().startswith("**CommonsWire 9.9.1**")
    assert SECRET_TEXT not in out
    stop = argv[:]
    stop[stop.index("--out") + 1] = str(tmp_path / "cli2")
    assert main([*stop, "--open-takedowns", "1"]) == 3
    assert "stop: 1 takedown request(s) are open" in capsys.readouterr().out
    bad = argv[:]
    bad[bad.index("--out") + 1] = str(w.prev / "inside")
    assert main(bad) == 2
    bad[bad.index("--from") + 1] = str(tmp_path / "nowhere")
    assert main(bad) == 2
    gone = argv[:]
    gone[gone.index("--work") + 1] = str(tmp_path / "no-work")
    gone[gone.index("--out") + 1] = str(tmp_path / "cli3")
    assert main(gone) == 2
    assert "nothing to replay" in capsys.readouterr().err


def test_small_helpers():
    assert next_version("0.2.0") == "0.2.1" and next_version("1.9.9") == "1.9.10"
    msg = "https://example.org/2026/11/05/a-story/?x=1 answered HTTP 403"
    assert redact(msg) == "example.org/... answered HTTP 403"
    assert timedelta(days=30) == NOW - datetime(2026, 10, 21, 12, tzinfo=timezone.utc)


def test_a_held_story_not_edited_since_keeps_its_reason_without_the_listing(tmp_path):
    w = World(tmp_path)
    g9 = post(GV, 209, "2026-10-25")  # held in the previous version, never edited since
    m = json.loads((w.prev / "manifest.json").read_text())
    m["held_rows"].append(
        {
            "id": article_id(g9["link"]),
            "source_id": "globalvoices",
            "published_on": "2026-10-25",
            "reason": "credited to an account, not a person",
        }
    )
    (w.prev / "manifest.json").write_text(json.dumps(m))
    w.site.recent["globalvoices"].append(g9)
    res = w.run()
    gv = res.sources["globalvoices"]
    assert gv.listing["held_kept_unedited"] == 1 and gv.listing["wanted"] == 4
    assert gv.listing["pages"] == 3  # the walk does not go back to 2026-10-25
    held = {
        h["id"]: h
        for h in json.loads((tmp_path / "next" / "manifest.json").read_text())["held_rows"]
    }
    assert held[article_id(g9["link"])]["reason"] == "credited to an account, not a person"
