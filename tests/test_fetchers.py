"""Fetcher tests with invented API answers. Nothing here touches the network."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from commonswire.fetchers import FETCHERS
from commonswire.fetchers.base import RawStore, dumps, run_sample, summary, write_sample
from commonswire.fetchers.wikinews import WikinewsFetcher, body_from_extract
from commonswire.fetchers.wordpress import GlobalVoicesFetcher
from commonswire.sources import parse_row
from commonswire.validate import validate_file
from fakes import FakeTransport, make_test_client
from test_sources import row

GV_TEMPLATE = "{title}, by {authors} for {source} ({url}), {license}"


def gv_source(**over):
    base = dict(
        source_id="globalvoices",
        name="Global Voices",
        homepage="https://globalvoices.org/",
        license="CC-BY-3.0",
        credit_line=GV_TEMPLATE,
    )
    base.update(over)
    return parse_row(row(**base))


def wp_post(n, *, body=None, categories=("World",), authors=("A. Writer",), title=None):
    return {
        "link": f"https://globalvoices.org/2026/11/0{n % 9 + 1}/invented-story-{n}/",
        "title": {"rendered": title or f"Invented story {n} &amp; more"},
        "content": {
            "rendered": body
            or f"<p>Invented paragraph one of story {n}.</p>"
            "<figure><img src='x.jpg'><figcaption>A caption</figcaption></figure>"
            f"<p>Invented paragraph two of story {n}.</p>"
        },
        "date_gmt": f"2026-11-0{n % 9 + 1}T08:00:00",
        "modified_gmt": f"2026-11-0{n % 9 + 1}T09:00:00",
        "type": "post",
        "_embedded": {
            "author": [{"name": a} for a in authors],
            "wp:term": [
                [{"taxonomy": "category", "name": c} for c in categories],
                [{"taxonomy": "post_tag", "name": "invented"}],
            ],
        },
    }


def gv_site(posts_p1, posts_p2=(), total=None, per_page=3):
    t = FakeTransport().add(
        "https://globalvoices.org/robots.txt", (200, "User-agent: *\nAllow: /\n")
    )
    base = "https://globalvoices.org/wp-json/wp/v2/posts?"
    t.add(
        base + f"per_page={per_page}&page=1&orderby=date&order=desc&_embed=author%2Cwp%3Aterm",
        (200, json.dumps(list(posts_p1)), {"X-WP-Total": str(total or len(posts_p1))}),
    )
    t.add(
        base + "per_page=100&page=2&orderby=date&order=desc&_embed=author%2Cwp%3Aterm",
        (200, json.dumps(list(posts_p2))),
    )
    t.add(
        base + "per_page=1&order=asc&orderby=date&_fields=date_gmt",
        (200, json.dumps([{"date_gmt": "2005-03-01T00:00:00"}])),
    )
    return t


def test_registry_of_fetchers():
    assert set(FETCHERS) == {"globalvoices", "wikinews_en"}


def test_fetcher_refuses_a_source_that_is_not_include(tmp_path):
    client, _ = make_test_client(tmp_path, FakeTransport())
    raw = RawStore(tmp_path / "raw")
    with pytest.raises(ValueError, match="only include sources"):
        GlobalVoicesFetcher(client, gv_source(status="pending", reason="?"), raw)
    with pytest.raises(ValueError, match="this fetcher is for globalvoices"):
        GlobalVoicesFetcher(client, parse_row(row()), raw)


def test_global_voices_sample_keeps_own_stories_and_drops_partners(tmp_path):
    posts = [
        wp_post(1),
        wp_post(2, categories=("Partner",)),
        wp_post(
            3,
            body="<p>Invented text.</p><p>This story was originally published by an invented "
            "outlet and is republished as part of a content-sharing agreement.</p>",
        ),
    ]
    t = gv_site(posts, total=9000)
    client, _ = make_test_client(tmp_path, t)
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "raw"))
    result = run_sample(fetcher, limit=3)
    assert fetcher.archive_start() == "2005-03-01"
    assert result.seen == 3 and len(result.kept) == 1
    assert dict(result.dropped) == {
        "third_party:partner_category": 1,
        "third_party:republication_note": 1,
    }
    art = result.kept[0]
    assert art.title == "Invented story 1 & more"
    assert art.text == "Invented paragraph one of story 1.\n\nInvented paragraph two of story 1."
    assert art.authors == ("A. Writer",) and art.section == "World"
    assert art.license == "CC-BY-3.0"
    assert art.credit_line.endswith("by A. Writer for Global Voices (" + art.url + "), CC BY 3.0")
    assert result.api_totals == {"total_posts": 9000}
    assert result.raw_files == ["001-posts-p1.json"]
    # Raw answers are saved once and never overwritten.
    with pytest.raises(FileExistsError):
        RawStore(tmp_path / "raw").save(type("R", (), {"body": b"x"})(), "posts-p1")
    s = summary(result)
    assert s["kept"] == 1 and s["raw_bytes"] > 0 and "text" not in dumps(s)


def test_wire_bylines_and_bad_posts_are_dropped_and_counted(tmp_path):
    posts = [
        wp_post(1, authors=("The Associated Press",)),
        wp_post(2, body="<p>(AP) — Invented wire text.</p>"),
        dict(wp_post(3), date_gmt=None),
    ]
    client, _ = make_test_client(tmp_path, gv_site(posts))
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "raw"))
    with pytest.raises(ValueError, match="no date_gmt"):
        run_sample(fetcher, limit=3)
    posts = [
        wp_post(1, authors=("The Associated Press",)),
        wp_post(2, body="<p>(AP) — Invented wire text.</p>"),
        wp_post(4, body="<figure>only a photo</figure>"),
    ]
    client, _ = make_test_client(tmp_path / "b", gv_site(posts))
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "b" / "raw"))
    result = run_sample(fetcher, limit=3)
    assert result.dropped["third_party:wire_byline"] == 2
    assert sum(v for k, v in result.dropped.items() if k.startswith("invalid:")) == 1


def test_wordpress_paging_and_duplicates(tmp_path):
    p1 = [wp_post(1), wp_post(2), wp_post(3)]
    site = gv_site(p1, posts_p2=[wp_post(3), wp_post(5)], per_page=5)
    client, _ = make_test_client(tmp_path, site)
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "raw"))
    items = list(fetcher.items(5))
    assert len(items) == 5
    site = gv_site(p1, posts_p2=[wp_post(3), wp_post(5)], per_page=5)
    client, _ = make_test_client(tmp_path / "c", site)
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "c" / "raw"))
    # run_sample caps at 200 and drops repeated URLs
    with pytest.raises(ValueError, match="at most 200"):
        run_sample(fetcher, limit=201)
    result = run_sample(fetcher, limit=5)
    assert result.dropped["duplicate"] == 1 and len(result.kept) == 4
    out = write_sample(result, tmp_path / "s.jsonl")
    assert len(out) == 64
    reg = {"globalvoices": gv_source()}
    assert validate_file(tmp_path / "s.jsonl", reg).ok


def test_wordpress_errors(tmp_path):
    t = FakeTransport().add("https://globalvoices.org/robots.txt", (404, ""))
    client, _ = make_test_client(tmp_path, t)
    fetcher = GlobalVoicesFetcher(client, gv_source(), RawStore(tmp_path / "raw"))
    with pytest.raises(RuntimeError, match="answered HTTP 404"):
        list(fetcher.items(3))
    with pytest.raises(RuntimeError, match="answered HTTP 404"):
        fetcher.archive_start()
    t2 = gv_site([])
    client2, _ = make_test_client(tmp_path / "e", t2)
    fetcher2 = GlobalVoicesFetcher(client2, gv_source(), RawStore(tmp_path / "e" / "raw"))
    assert list(fetcher2.items(3)) == []


# ---- Wikinews ----

WN_TEMPLATE = "{title}, by Wikinews contributors ({url}), {license}"


def wn_source():
    return parse_row(
        row(
            source_id="wikinews_en",
            name="Wikinews",
            homepage="https://en.wikinews.org/",
            license="CC-BY-2.5",
            credit_line=WN_TEMPLATE,
        )
    )


EXTRACT = """Friday, May 1, 2026

An invented first paragraph.
An invented second paragraph.

== Reactions ==
An invented reaction paragraph.

== Sources ==
An invented source line that must be cut."""


def test_body_from_extract_stops_at_sources_and_keeps_inner_headings():
    assert body_from_extract(EXTRACT) == (
        "Friday, May 1, 2026\n\nAn invented first paragraph.\n\nAn invented second paragraph."
        "\n\nReactions\n\nAn invented reaction paragraph."
    )
    assert body_from_extract("Only text") == "Only text"


def wn_site():
    t = FakeTransport().add(
        "https://en.wikinews.org/robots.txt", (200, "User-agent: *\nDisallow: /w/index.php\n")
    )
    listing = {
        "query": {
            "categorymembers": [
                {
                    "pageid": 11,
                    "ns": 0,
                    "title": "Invented town elects council",
                    "timestamp": "2026-04-30T10:00:00Z",
                },
                {
                    "pageid": 12,
                    "ns": 14,
                    "title": "Category:Not an article",
                    "timestamp": "2026-04-29T10:00:00Z",
                },
                {
                    "pageid": 13,
                    "ns": 0,
                    "title": "Invented early story",
                    "timestamp": "2005-01-10T10:00:00Z",
                },
                {
                    "pageid": 14,
                    "ns": 0,
                    "title": "Missing page",
                    "timestamp": "2005-01-09T10:00:00Z",
                },
            ]
        }
    }
    api = "https://en.wikinews.org/w/api.php?format=json&formatversion=2&maxlag=5&"
    t.add(
        api
        + "action=query&list=categorymembers&cmtitle=Category%3APublished&cmtype=page"
        + "&cmsort=timestamp&cmdir=desc&cmprop=ids%7Ctitle%7Ctimestamp&cmlimit=3",
        (200, json.dumps(listing)),
    )
    pages = {
        "query": {
            "pages": [
                {
                    "pageid": 11,
                    "title": "Invented town elects council",
                    "extract": EXTRACT,
                    "revisions": [{"timestamp": "2026-05-01T00:00:00Z"}],
                },
                {
                    "pageid": 13,
                    "title": "Invented early story",
                    "extract": "An invented 2005 paragraph.",
                },
            ]
        }
    }
    t.add(
        api
        + "action=query&prop=extracts%7Cinfo%7Crevisions&rvprop=timestamp"
        + "&pageids=11%7C13%7C14&explaintext=1&exsectionformat=wiki&exlimit=20&inprop=url",
        (200, json.dumps(pages)),
    )
    return t


def test_wikinews_sample_licenses_by_date_and_credits_contributors(tmp_path):
    client, _ = make_test_client(tmp_path, wn_site())
    fetcher = WikinewsFetcher(client, wn_source(), RawStore(tmp_path / "raw"))
    result = run_sample(fetcher, limit=3)
    assert [a.title for a in result.kept] == [
        "Invented town elects council",
        "Invented early story",
    ]
    new, old = result.kept
    assert new.license == "CC-BY-2.5" and old.license == "public-domain"
    assert new.url == "https://en.wikinews.org/wiki/Invented_town_elects_council"
    assert new.updated_at == datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert old.updated_at is None
    assert new.credit_line == (
        "Invented town elects council, by Wikinews contributors "
        "(https://en.wikinews.org/wiki/Invented_town_elects_council), CC BY 2.5"
    )
    assert old.credit_line.endswith("Public domain")
    assert "invented source line" not in new.text
    assert new.authors == ()
    assert result.raw_files == ["001-published-list.json", "002-extracts-01.json"]
