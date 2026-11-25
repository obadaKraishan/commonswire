"""The weekly route of a Global Voices language site (series 0.3 on), with an invented English
site, an invented French site, their listings and pages. No network."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlsplit

import pytest

from commonswire import release as rel
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import LINGUA_FETCHERS, GlobalVoicesFetcher
from commonswire.http import RawResponse
from commonswire.lingua import NO_ENGLISH
from commonswire.release import collect, write_release
from commonswire.release_text import card, licenses_md
from commonswire.schema import article_id
from commonswire.sources import load_sources
from commonswire.update import run_update
from test_sources import row, write_csv
from test_update import BUILT, NOW, _log, built_row, listing_page, make_clients, post, released

GV = "https://globalvoices.org"
FR = "https://fr.globalvoices.org"
CREDIT = "{title}, by {authors} for {source} ({url}), {license}"


@pytest.fixture(autouse=True)
def series(monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 8), ("globalvoices", "globalvoices_fr"))


def links(tag, n=5, words="Invented words"):
    return f"<p>{words}.</p>" + "".join(
        f'<p>Invented words <a href="https://ex{i}.{tag}.org/p">x</a>.</p>' for i in range(n)
    )


def story(link, labels, names):
    blocks = "".join(
        f'<div class="text-credits-section"><span class="credit-label">{lab}</span> '
        f'<a class="user-link" href="{GV}/author/x/">{name}</a></div>'
        for lab, name in zip(labels, names, strict=True)
    )
    return (
        f'<div class="post-summary"><div class="post-title"><a href="{link}">An invented '
        f'title</a></div><div class="text-credits-container">{blocks}</div></div>'
    )


def by_url_check(tmp_path):
    _, rows = released(tmp_path / "next")
    fr_rows = [x for x in rows.values() if x["source_id"] == "globalvoices_fr"]
    return all(x["publisher_categories"] == ["Term 1"] for x in fr_rows)


class Site:
    def __init__(self):
        self.recent: dict[str, list[dict]] = {"en": [], "fr": []}
        self.listing: dict[tuple[str, int], str] = {}
        self.pages: dict[str, tuple[int, str]] = {}
        self.calls: list[str] = []
        self.term_lookups: list[tuple[str, str]] = []

    def __call__(self, url, headers, timeout, max_bytes):
        self.calls.append(url)
        parts = urlsplit(url)
        q = dict(parse_qsl(parts.query))
        site = "fr" if parts.hostname == "fr.globalvoices.org" else "en"

        def answer(status, body, hdrs=None):
            return RawResponse(url=url, status=status, headers=hdrs or {}, body=body.encode())

        if parts.path == "/robots.txt":
            return answer(200, "User-agent: *\nCrawl-delay: 10\n")
        if "/wp-json/wp/v2/" in parts.path:
            if q.get("per_page") == "1" and q.get("_fields") == "id":
                return answer(200, '[{"id": 1}]', {"X-WP-Total": "5"})
            if "include" in q:  # terms by id
                ids = [int(x) for x in q["include"].split(",")]
                self.term_lookups.append((parts.path.rsplit("/", 1)[-1], site))
                return answer(200, json.dumps([{"id": i, "name": f"Term {i}"} for i in ids]))
            if q.get("page") != "1":
                return answer(400, "{}")
            if parts.path.endswith("/categories"):
                return answer(200, json.dumps([{"id": 1, "name": "World"}]))
            if "after" in q:
                return answer(200, json.dumps(self.recent[site]))
            return answer(200, "[]")
        if parts.path.startswith("/page/"):
            n = int(parts.path.split("/")[2])
            return (
                answer(200, self.listing[(site, n)])
                if (site, n) in self.listing
                else answer(404, "")
            )
        if url in self.pages:
            return answer(*self.pages[url])
        return answer(404, "not found")


def test_a_language_site_week_links_new_posts_and_applies_the_rule(tmp_path):
    reg_path = write_csv(
        tmp_path,
        [
            row(
                source_id="globalvoices",
                name="Global Voices",
                homepage=f"{GV}/",
                license="CC-BY-3.0",
                credit_line=CREDIT,
            ),
            row(
                source_id="globalvoices_fr",
                name="Global Voices (fr)",
                homepage=f"{FR}/",
                languages="fr",
                edition_of="globalvoices",
                license="CC-BY-3.0",
                credit_line=CREDIT,
                reason_code="released_with_english",
                third_party_rule="released only with its released English version",
            ),
        ],
    )
    registry = load_sources(reg_path)
    site = Site()
    client = make_clients(site)(10**9, _log(tmp_path / "unused"), None)
    gv = GlobalVoicesFetcher(client, registry["globalvoices"], ReplayStore(tmp_path / "x"))
    a = post(GV, 401, "2026-11-12", body=links("a"))  # in the window
    c = post(
        GV, 403, "2025-01-01", body=links("c", words="Invented words, c")
    )  # old: not in the week's answers
    prev_rows = {
        "globalvoices": [
            built_row(gv, a, authors=("Ana Invented",)),
            built_row(gv, c, authors=("Bo Invented",)),
        ],
        "globalvoices_fr": [],
    }
    takedowns = tmp_path / "takedowns.csv"
    takedowns.write_text("id,requested_on,basis\n")
    r = collect(tmp_path, "9.8.0", registry, rows=prev_rows, takedowns_path=takedowns)
    prev = tmp_path / "prev"
    write_release(
        r,
        prev,
        reg_path,
        registry,
        card=card(r, registry, 0),
        licenses_md=licenses_md(r, registry),
        extra={"third_party_dropped": 0, "held_rows": []},
    )

    # A week later: three new French posts and one new English one.
    b = post(GV, 402, "2026-11-18", body=links("b", words="Invented words, b"))
    fr1 = post(
        FR, 501, "2026-11-16", body=links("a", words="Mots inventés, un")
    )  # A's translation: same links
    fr2 = post(FR, 502, "2026-11-17", body="<p>Mots inventés, deux.</p>")  # its page names C
    fr3 = post(FR, 503, "2026-11-19", body="<p>Mots inventés, trois.</p>")  # names nothing
    site.recent["en"] = [a, b]
    site.recent["fr"] = [fr1, fr2, fr3]
    site.listing[("en", 1)] = listing_page(
        story(a["link"], ["Written by"], ["Ana Invented"]),
        story(b["link"], ["Written by"], ["Ed Invented"]),
    )
    labels = ["Écrit par", "Traduit par"]
    site.listing[("fr", 1)] = listing_page(
        story(fr1["link"], labels, ["Ana Invented", "Cy Translator"]),
        story(fr2["link"], labels, ["Bo Invented", "Cy Translator"]),
        story(fr3["link"], labels, ["Di Invented", "Cy Translator"]),
    )
    old_c = (
        c["link"]
        .replace("globalvoices.org", "globalvoicesonline.org")
        .replace("/01/01/", "/01/02/")
    )
    site.pages[fr2["link"]] = (
        200,
        f"<span class='translation-language post-translation-en'><a href=\"{old_c}\">x</a></span>",
    )
    site.pages[fr3["link"]] = (200, "<html><body>no list</body></html>")

    res = run_update(
        tmp_path,
        prev,
        tmp_path / "next",
        tmp_path / "work",
        registry_path=reg_path,
        takedowns_path=takedowns,
        baseline_path=tmp_path / "baseline.json",
        clients=make_clients(site),
        now=NOW,
        dry_run=False,
    )
    assert res.status == "ready", res.stop_reasons
    fr = res.sources["globalvoices_fr"]
    assert fr.lingua == {
        "by_fingerprint": 1,
        "by_page": 1,
        "new_posts": 3,
        "no_english_version": 1,
        "page_names_no_english_row": 1,
        "pages_read": 2,
    }
    # A language site's count check: its first series 0.3 run records its total (baseline).
    assert fr.count is not None and fr.count.baseline and fr.count.count_requests == 1
    assert fr.count.counts == {"total": {"posts": 5, "before": "2026-11-19"}}
    m = json.loads((tmp_path / "next" / "manifest.json").read_text())
    assert m["post_counts"]["globalvoices_fr"] == fr.count.counts
    # the language site asks only for the categories its posts use, not its whole list
    assert ("categories", "fr") in site.term_lookups
    assert not any("fr.globalvoices.org/wp-json/wp/v2/categories?per_page" in u for u in site.calls)
    assert by_url_check(tmp_path)
    _, rows = released(tmp_path / "next")
    by_url = {x["url"]: x for x in rows.values()}
    assert {fr1["link"], fr2["link"]} <= set(by_url) and fr3["link"] not in by_url
    assert by_url[fr1["link"]]["other_versions"] == [a["link"]]
    assert by_url[fr1["link"]]["original_url"] == a["link"]
    assert by_url[fr1["link"]]["translators"] == ["Cy Translator"]
    assert by_url[fr1["link"]]["language"] == "fr"
    assert by_url[fr2["link"]]["other_versions"] == [c["link"]]
    assert by_url[a["link"]]["other_versions"] == [fr1["link"]]
    assert by_url[c["link"]]["other_versions"] == [fr2["link"]]
    m = json.loads((tmp_path / "next" / "manifest.json").read_text())
    held = {h["id"]: h for h in m["held_rows"]}
    assert held[article_id(fr3["link"])]["reason"] == NO_ENGLISH
    assert m["update"]["versions_added"] >= 2
    # page reads are logged by the article's id, never its address
    log = (tmp_path / "work" / "usage_log.csv").read_text()
    assert "/2026/11/17/invented-502" not in log and article_id(fr2["link"]) in log
    assert BUILT < NOW and datetime(2026, 1, 1, tzinfo=timezone.utc) < NOW
    assert "globalvoices_fr" in LINGUA_FETCHERS
