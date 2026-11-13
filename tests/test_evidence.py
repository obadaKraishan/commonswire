from __future__ import annotations

import csv

import pytest

from commonswire.evidence import (
    EvidencePaths,
    extract_evidence,
    fetch_evidence,
    license_links,
    normalize_link,
    page_texts,
    policy_links,
    read_candidates,
    read_rows,
    same_site,
    snapshot_files,
)
from fakes import CONNECTION_ERROR, FakeTransport, make_test_client

HOME = "https://news.example.org/"
HOME_HTML = """<html><body><p>Latest news</p>
<footer>
<a href="/terms-of-use/">Terms of Use</a>
<a href="/about/">About</a>
<a href="/republishing-guidelines/">Republish our stories</a>
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
<a href="https://facebook.com/news">Facebook</a>
<a href="https://other.example.com/license">Someone else's license</a>
<a href="/copyright">Copyright</a>
<a href="/republishing-guidelines/#top">Republish (again)</a>
</footer></body></html>"""
REPUBLISH_HTML = "<p>You may republish our stories for free under CC BY 4.0.</p>"
REPUBLISH_HTML += "<p>Please do not republish automatically.</p><p>Unrelated text here.</p>"


def write_candidates(tmp_path, rows):
    path = tmp_path / "candidates.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["source_id", "name", "homepage", "kind", "seed_urls", "notes"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def candidate_rows():
    return [
        {
            "source_id": "examplenews",
            "name": "Example News",
            "homepage": HOME,
            "kind": "news",
            "seed_urls": "https://news.example.org/missing-page",
            "notes": "",
        }
    ]


def site():
    t = FakeTransport()
    t.add(
        "https://news.example.org/robots.txt",
        (
            200,
            "User-agent: *\nDisallow: /copyright\nCrawl-delay: 3\n\n"
            "User-agent: CCBot\nDisallow: /\n",
        ),
    )
    t.add(HOME, (200, HOME_HTML))
    t.add("https://news.example.org/republishing-guidelines/", (200, REPUBLISH_HTML))
    t.add("https://news.example.org/terms-of-use/", (403, "no"))
    return t


def test_read_candidates_checks_required_fields_and_duplicates(tmp_path):
    rows = candidate_rows()
    cands = read_candidates(write_candidates(tmp_path, rows))
    assert cands[0].seed_urls == ("https://news.example.org/missing-page",)
    with pytest.raises(ValueError, match="source_id used twice"):
        read_candidates(write_candidates(tmp_path, rows + rows))
    bad = [dict(rows[0], homepage="")]
    with pytest.raises(ValueError, match="line 2: fill in homepage"):
        read_candidates(write_candidates(tmp_path, bad))


def test_policy_links_rank_republish_first_and_stay_on_site():
    found = policy_links(HOME_HTML, HOME, HOME)
    assert found == [
        "https://news.example.org/republishing-guidelines/",
        "https://news.example.org/copyright",
        "https://news.example.org/terms-of-use/",
    ]


def test_policy_words_match_whole_words_only():
    html = '<a href="/wiki/Court_rules_eviction_illegally_done">Eviction illegally done</a>'
    html += '<a href="/legal">Legal</a>'
    assert policy_links(html, HOME, HOME) == ["https://news.example.org/legal"]


def test_link_helpers():
    assert normalize_link("mailto:a@b.org", HOME) is None
    assert normalize_link("", HOME) is None
    assert normalize_link("ftp://x.org/a", HOME) is None
    assert normalize_link("/a#frag", HOME) == "https://news.example.org/a"
    assert same_site("https://www.example.org/a", "https://example.org/")
    assert same_site("https://fr.globalvoices.org/", "https://globalvoices.org/")
    assert not same_site("https://other.org/", "https://example.org/")
    assert license_links(HOME_HTML, HOME) == [
        ("https://creativecommons.org/licenses/by/4.0/", "CC BY 4.0")
    ]


def test_fetch_evidence_saves_pages_once_and_records_every_outcome(tmp_path):
    t = site()
    client, clock = make_test_client(tmp_path, t)
    paths = EvidencePaths(tmp_path, "2026-11-13")
    cands = read_candidates(write_candidates(tmp_path, candidate_rows()))
    counts = fetch_evidence(client, cands, paths, max_policy_pages=3)
    assert counts == {"ok": 2, "not_found": 1, "disallowed": 1, "blocked": 1}
    pages = read_rows(tmp_path / "data" / "evidence" / "pages.csv")
    by_url = {r["url"]: r for r in pages}
    assert by_url[HOME]["role"] == "home" and by_url[HOME]["outcome"] == "ok"
    assert by_url["https://news.example.org/terms-of-use/"]["status"] == "403"
    assert by_url["https://news.example.org/copyright"]["outcome"] == "disallowed"
    assert len(by_url[HOME]["sha256"]) == 64
    robots = read_rows(tmp_path / "data" / "evidence" / "robots.csv")[0]
    assert robots["state"] == "present" and robots["crawl_delay"] == "3.0"
    assert robots["ai_crawlers_shut_out"] == "CCBot" and robots["feed_allowed"] == "yes"
    lic = read_rows(tmp_path / "data" / "evidence" / "license_links.csv")
    assert [r["license_url"] for r in lic] == ["https://creativecommons.org/licenses/by/4.0/"]
    assert 3.0 in clock.sleeps  # the crawl-delay is honored
    files = snapshot_files(tmp_path, "examplenews")
    assert [f.name for f in files] == ["01-home.html", "03-republishing-guidelines.html"]
    # A second run on the same date sends nothing new.
    before = len(t.calls)
    assert fetch_evidence(client, cands, paths) == {}
    assert len(t.calls) == before


def test_extra_urls_and_extract(tmp_path):
    t = site().add(
        "https://news.example.org/about/", (200, "<p>About us. All rights reserved.</p>")
    )
    client, _ = make_test_client(tmp_path, t)
    paths = EvidencePaths(tmp_path, "2026-11-13")
    cands = read_candidates(write_candidates(tmp_path, candidate_rows()))
    fetch_evidence(
        client,
        cands,
        paths,
        max_policy_pages=1,
        extra_urls={"examplenews": ["https://news.example.org/about/"]},
    )
    assert extract_evidence(tmp_path, "2026-11-13") == 3
    hits = (paths.interim / "examplenews" / "hits.md").read_text()
    assert "- You may republish our stories for free under CC BY 4.0." in hits
    assert "- Please do not republish automatically." in hits
    assert "Unrelated text here." not in hits
    assert "All rights reserved" in hits
    texts = page_texts(tmp_path, "examplenews")
    assert any("Please do not republish automatically." in v for v in texts.values())
    assert extract_evidence(tmp_path, "2026-11-13", ["nobody"]) == 0


def test_network_error_and_budget_outcomes(tmp_path):
    t = FakeTransport().add("https://news.example.org/robots.txt", (404, ""))
    t.add(HOME, CONNECTION_ERROR)
    client, _ = make_test_client(tmp_path, t)
    paths = EvidencePaths(tmp_path, "2026-11-13")
    cands = read_candidates(write_candidates(tmp_path, [dict(candidate_rows()[0], seed_urls="")]))
    assert fetch_evidence(client, cands, paths) == {"error": 1}
    t2 = FakeTransport().add("https://news.example.org/robots.txt", (200, "x" * 10))
    client2, _ = make_test_client(tmp_path / "b", t2, byte_budget=5)
    assert fetch_evidence(client2, cands, EvidencePaths(tmp_path / "b", "2026-11-13")) == {
        "budget": 1
    }


def test_snapshot_helpers_without_a_drive(tmp_path):
    assert snapshot_files(tmp_path, "x") == []
    assert page_texts(tmp_path, "x") == {}
    assert read_rows(tmp_path / "none.csv") == []
