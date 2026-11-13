"""Backfill tests with invented API answers. Nothing here touches the network."""

from __future__ import annotations

import json

from commonswire.backfill import backfill_wordpress, build_rows, load_category_names, save_once
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import (
    AltNewsFetcher,
    BalkanDiskursFetcher,
    FactlyFetcher,
    GlobalVoicesFetcher,
    PublicRecordFetcher,
)
from commonswire.sources import parse_row
from commonswire.validate import validate_file
from fakes import FakeTransport, make_test_client
from test_fetchers import gv_source, wp_post
from test_sources import row

GV = "https://globalvoices.org"


def backfill_post(n, **kw):
    post = wp_post(n, **kw)
    post.pop("_embedded")
    post["author"] = 7
    post["categories"] = [1] if n != 3 else [2]
    return post


def gv_backfill_site(pages):
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "User-agent: *\nCrawl-delay: 10\n"))
    t.add(
        f"{GV}/wp-json/wp/v2/categories?per_page=100&page=1&_fields=id%2Cname",
        (200, json.dumps([{"id": 1, "name": "World"}, {"id": 2, "name": "Partner content"}])),
    )
    fetcher_fields = GlobalVoicesFetcher.backfill_fields.replace(",", "%2C")
    for i, posts in enumerate(pages, start=1):
        url = (
            f"{GV}/wp-json/wp/v2/posts?per_page=100&page={i}&orderby=date&order=asc"
            f"&_fields={fetcher_fields}"
        )
        headers = {
            "X-WP-Total": str(sum(len(p) for p in pages)),
            "X-WP-TotalPages": str(len(pages)),
        }
        t.add(url, (200, json.dumps(posts), headers))
    return t


def make(tmp_path, transport, cls=GlobalVoicesFetcher, source=None):
    client, clock = make_test_client(tmp_path, transport)
    fetcher = cls(client, source or gv_source(), ReplayStore(tmp_path / "raw"))
    return fetcher, client, clock


def test_backfill_saves_every_page_once_and_resumes(tmp_path):
    pages = [[backfill_post(1), backfill_post(2)], [backfill_post(3), backfill_post(4)]]
    t = gv_backfill_site(pages)
    fetcher, client, clock = make(tmp_path, t)
    folder = tmp_path / "bf"
    p = backfill_wordpress(fetcher, client, folder, run="r1", max_pages=1)
    assert p.stopped == "stopped after 1 pages, as asked" and p.pages_saved == 1
    assert p.total_posts == 4 and p.total_pages == 2 and not p.finished
    assert 10.0 in clock.sleeps  # the crawl-delay is honored
    before = len(t.calls)
    p = backfill_wordpress(fetcher, client, folder, run="r1")
    assert p.finished and p.pages_saved == 2
    assert len(t.calls) - before == 1  # only the missing page was asked for
    assert json.loads((folder / "progress.json").read_text())["finished"] is True
    assert load_category_names(folder) == {1: "World", 2: "Partner content"}
    p = backfill_wordpress(fetcher, client, folder, run="r1")
    assert p.requests_this_run == 0 and p.finished


def test_build_rows_drops_third_party_and_marks_missing_bylines(tmp_path):
    pages = [[backfill_post(1), backfill_post(2), backfill_post(3)], [backfill_post(1)]]
    fetcher, client, _ = make(tmp_path, gv_backfill_site(pages))
    folder = tmp_path / "bf"
    backfill_wordpress(fetcher, client, folder, run="r1")
    out = tmp_path / "rows.jsonl"
    result = build_rows(fetcher, folder, out)
    assert result.seen == 4 and result.kept == 2 and result.releasable == 0
    assert result.dropped == {"third_party:partner_category": 1, "duplicate_url": 1}
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert all(r["hold_reason"].startswith("no byline") for r in rows)
    fetcher.byline_map = {7: ("A. Writer",)}
    result = build_rows(fetcher, folder, out)
    assert result.releasable == 2
    assert validate_file(out, {"globalvoices": gv_source()}).ok
    assert result.summary()["first"] <= result.summary()["last"]


def test_backfill_stops_on_refusal_and_on_server_errors(tmp_path):
    t = FakeTransport().add(f"{GV}/robots.txt", (403, "no"))
    fetcher, client, _ = make(tmp_path, t)
    p = backfill_wordpress(fetcher, client, tmp_path / "a", run="r")
    assert p.stopped.startswith("refused") and not p.finished
    t2 = gv_backfill_site([[backfill_post(1)]])
    fields = GlobalVoicesFetcher.backfill_fields.replace(",", "%2C")
    t2.routes[
        f"{GV}/wp-json/wp/v2/posts?per_page=100&page=1&orderby=date&order=asc&_fields={fields}"
    ] = [(500, "x")]
    fetcher2, client2, _ = make(tmp_path / "b", t2)
    p2 = backfill_wordpress(fetcher2, client2, tmp_path / "b" / "bf", run="r")
    assert p2.stopped == "page 1 answered HTTP 500"


def test_save_once_never_overwrites(tmp_path):
    path = tmp_path / "x" / "a.json"
    assert save_once(path, b"1") and not save_once(path, b"2")
    assert path.read_bytes() == b"1" and not list(tmp_path.glob("x/*.part"))


def test_source_classes_and_embeds_and_rights_notes(tmp_path):
    for cls, sid, base in [
        (PublicRecordFetcher, "thepublicrecord", "https://thepublicrecord.ca"),
        (BalkanDiskursFetcher, "balkandiskurs", "https://balkandiskurs.com/en"),
        (FactlyFetcher, "factly", "https://factly.in"),
        (AltNewsFetcher, "altnews", "https://www.altnews.in"),
    ]:
        src = parse_row(
            row(
                source_id=sid,
                name=sid,
                homepage=base + "/",
                credit_line="{title}, by {authors}, {source} ({url}), {license}",
            )
        )
        f, _, _ = make(tmp_path / sid, FakeTransport(), cls=cls, source=src)
        assert f.backfill_url(2).startswith(f"{base}/wp-json/wp/v2/posts?per_page=100&page=2")
        body = (
            "<p>Invented claim check.</p><blockquote class='twitter-tweet'><p>An invented "
            "post by someone else.</p></blockquote><p>Invented verdict.</p>"
        )
        item = f.item_from_post(wp_post(1, body=body))
        assert f.third_party_reason(item) is None
        art = f.build(item, item.published_at)
        assert art.text == "Invented claim check.\n\nInvented verdict." and art.releasable
        held = f.item_from_post(wp_post(2, body="<p>Invented text.</p><p>All rights reserved.</p>"))
        assert f.third_party_reason(held) == "rights_reserved_note"


def test_cli_bylines_from_an_open_users_endpoint(tmp_path, monkeypatch, capsys):
    import csv

    from commonswire.cli import main
    from commonswire.sources import SOURCE_FIELDS

    reg = tmp_path / "sources.csv"
    with reg.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerow(
            row(
                source_id="altnews",
                name="Alt News",
                homepage="https://www.altnews.in/",
                credit_line="{title}, by {authors}, {source} ({url}), {license}",
            )
        )
    base = "https://www.altnews.in"
    t = FakeTransport().add(f"{base}/robots.txt", (404, ""))
    t.add(
        f"{base}/wp-json/wp/v2/users?per_page=100&page=1&_fields=id%2Cname",
        (200, json.dumps([{"id": 7, "name": "A. Writer"}, {"id": 8, "name": ""}])),
    )

    def fake_make_client(root, *, byte_budget=None, transport=None):
        client, _ = make_test_client(root / "data", t, byte_budget=byte_budget)
        return client

    monkeypatch.setattr("commonswire.http.make_client", fake_make_client)
    assert (
        main(["--root", str(tmp_path), "bylines", "altnews", "--run", "r", "--sources", str(reg)])
        == 0
    )
    out = json.loads((tmp_path / "data" / "interim" / "bylines" / "altnews.json").read_text())
    assert out == {"7": ["A. Writer"]}
    t.routes[f"{base}/wp-json/wp/v2/users?per_page=100&page=1&_fields=id%2Cname"] = [(403, "no")]
    (
        tmp_path / "data" / "raw" / "backfill" / "altnews" / "r" / "users" / "users-p001.json"
    ).unlink()
    assert (
        main(["--root", str(tmp_path), "bylines", "altnews", "--run", "r", "--sources", str(reg)])
        == 1
    )
