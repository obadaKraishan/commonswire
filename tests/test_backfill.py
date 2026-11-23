"""Backfill tests with invented API answers. Nothing here touches the network."""

from __future__ import annotations

import json

from commonswire.backfill import (
    backfill_wordpress,
    build_rows,
    check_backfill,
    load_category_names,
    save_once,
)
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import (
    AltNewsFetcher,
    BalkanDiskursFetcher,
    FactlyFetcher,
    GlobalVoicesFetcher,
    PublicRecordFetcher,
)
from commonswire.schema import canonical_url
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


def test_cli_build_replays_the_saved_daily_answers(tmp_path, capsys):
    from commonswire.cli import main

    run = tmp_path / "data" / "raw" / "backfill" / "globalvoices" / "r1"
    run.mkdir(parents=True)
    (run / "categories-p001.json").write_text(json.dumps([{"id": 1, "name": "World"}]))
    (run / "posts-p00001.json").write_text(json.dumps([backfill_post(1), backfill_post(2)]))
    names = {canonical_url(backfill_post(n)["link"]): {"names": ["A. Writer"]} for n in (1, 2, 5)}
    bylines = tmp_path / "data" / "interim" / "bylines"
    bylines.mkdir(parents=True)
    (bylines / "globalvoices.listing.json").write_text(json.dumps(names))
    day = tmp_path / "data" / "raw" / "daily" / "globalvoices" / "2026-11-13"
    day.mkdir(parents=True)
    (day / "001-new-p1.json").write_text(json.dumps([backfill_post(5)]))
    gone = {"url": backfill_post(2)["link"], "status": 404, "checked_at": "2026-11-13T12:00:00"}
    (day / "002-removed.json").write_text(json.dumps(gone))
    assert main(["--root", str(tmp_path), "build", "globalvoices", "--run", "r1"]) == 0
    out = capsys.readouterr().out
    assert "kept 2 (2 releasable, 0 credited to the source itself)" in out
    assert "2 files over 1 days, 1 new, 0 changed, 1 removed; 3 rows now" in out
    ev = json.loads(
        (tmp_path / "data" / "evidence" / "backfill" / "globalvoices.build.json").read_text()
    )
    assert ev["daily_replayed"]["new"] == 1 and ev["rows_after_daily"] == 3
    assert ev["releasable_after_daily"] == 3 and ev["validate_errors"] == 0


def _three_pages(tmp_path):
    pages = [[backfill_post(1)], [backfill_post(2)], [backfill_post(4)]]
    return make(tmp_path, gv_backfill_site(pages))


def test_a_page_whose_write_is_lost_stops_the_run_and_is_named(tmp_path, monkeypatch):
    """The way a run lost a page when its drive dropped off the bus: the write went to the
    cache and returned, and the file was never on disk. The run must say so and stop."""
    import commonswire.backfill as bf

    real = bf.save_once

    def lose_page_2(path, body):
        if path.name == bf.PAGE_NAME.format(2):
            return True  # reported as written, but nothing reached the disk
        return real(path, body)

    monkeypatch.setattr(bf, "save_once", lose_page_2)
    fetcher, client, _ = _three_pages(tmp_path)
    folder = tmp_path / "bf"
    p = backfill_wordpress(fetcher, client, folder, run="r1")
    assert not p.finished
    assert p.stopped.startswith("page 2 was fetched (") and "but is not on disk" in p.stopped
    assert p.missing_pages == [2, 3] and p.pages_saved == 1
    saved = json.loads((folder / "progress.json").read_text())
    assert saved["missing_pages"] == [2, 3] and saved["stopped"] == p.stopped
    # A rerun with a sound disk fetches only the missing pages and finishes.
    monkeypatch.setattr(bf, "save_once", real)
    p = backfill_wordpress(fetcher, client, folder, run="r1")
    assert p.finished and p.missing_pages == [] and p.pages_saved == 3


def test_a_page_missing_at_the_end_is_named_never_silent(tmp_path):
    fetcher, client, _ = _three_pages(tmp_path)
    folder = tmp_path / "bf"
    assert backfill_wordpress(fetcher, client, folder, run="r1").finished
    (folder / "posts-p00002.json").unlink()  # lost after the run, for example on remount
    report = check_backfill(folder)
    assert report["missing_pages"] == [2] and report["pages_expected"] == 3
    assert report["pages_present"] == 2 and report["posts"] == 2 and not report["complete"]
    # The next run names the gap if it cannot close it (max_pages=0 sends nothing).
    p = backfill_wordpress(fetcher, client, folder, run="r1", max_pages=0)
    assert not p.finished and p.missing_pages == [2]
    p = backfill_wordpress(fetcher, client, folder, run="r1")
    assert p.finished and check_backfill(folder)["complete"]


def test_check_backfill_reports_bad_files_and_unknown_totals(tmp_path):
    folder = tmp_path / "bf"
    folder.mkdir()
    (folder / "posts-p00001.json").write_text(json.dumps([backfill_post(1)]))
    (folder / "posts-p00003.json").write_text("[]")
    (folder / "posts-p00004.json").write_text("{not json")
    report = check_backfill(folder)  # no progress.json: the last page seen is the end
    assert report["pages_expected"] == 4 and report["missing_pages"] == [2]
    assert report["empty_or_invalid"] == [3, 4] and not report["complete"]
    assert report["total_posts"] is None and report["posts"] == 1
    assert check_backfill(tmp_path / "none")["pages_expected"] == 0


def test_save_once_flushes_to_disk_and_reports_a_failed_flush(tmp_path, monkeypatch):
    import os

    import commonswire.backfill as bf

    synced = []
    real_fsync = os.fsync
    monkeypatch.setattr(bf.os, "fsync", lambda fd: synced.append(fd) or real_fsync(fd))
    assert save_once(tmp_path / "a" / "x.json", b"[1]")
    assert (tmp_path / "a" / "x.json").read_bytes() == b"[1]" and len(synced) == 2
    assert not (tmp_path / "a" / "x.json.part").exists()

    def gone(fd):
        raise OSError(6, "Device not configured")

    monkeypatch.setattr(bf.os, "fsync", gone)
    import pytest

    with pytest.raises(OSError):
        save_once(tmp_path / "a" / "y.json", b"[2]")
    assert not (tmp_path / "a" / "y.json").exists()  # never renamed into place


def test_cli_backfill_check_sends_nothing_and_names_gaps(tmp_path, capsys):
    from commonswire.cli import main

    args = ["--root", str(tmp_path), "backfill", "globalvoices", "--run", "r1", "--check"]
    assert main(args) == 2 and "data/raw is missing" in capsys.readouterr().err
    folder = tmp_path / "data" / "raw" / "backfill" / "globalvoices" / "r1"
    folder.parent.mkdir(parents=True)
    assert main(args) == 2 and "no saved run" in capsys.readouterr().err
    folder.mkdir()
    for n in (1, 2, 3):
        (folder / f"posts-p{n:05d}.json").write_text(json.dumps([backfill_post(n)]))
    (folder / "progress.json").write_text(json.dumps({"total_pages": 3, "total_posts": 3}))
    assert main(args) == 0
    assert (
        "3 of 3 pages, 3 posts (the site counted 3); missing pages: none" in capsys.readouterr().out
    )
    (folder / "posts-p00002.json").unlink()
    assert main(args) == 1
    out = capsys.readouterr().out
    assert "2 of 3 pages" in out and "missing pages: 2;" in out and "NOT complete" in out


def test_backfill_with_tags_asks_for_tag_ids_and_saves_tag_names(tmp_path):
    from commonswire.backfill import build_rows

    post = backfill_post(1)
    post["tags"] = [5, 6]
    t = FakeTransport().add(f"{GV}/robots.txt", (200, "User-agent: *\nCrawl-delay: 10\n"))
    t.add(
        f"{GV}/wp-json/wp/v2/categories?per_page=100&page=1&_fields=id%2Cname",
        (200, json.dumps([{"id": 1, "name": "World"}])),
    )
    t.add(
        f"{GV}/wp-json/wp/v2/tags?per_page=100&page=1&_fields=id%2Cname",
        (200, json.dumps([{"id": 5, "name": "Invented tag"}, {"id": 6, "name": "Another"}])),
    )
    fields = (GlobalVoicesFetcher.backfill_fields + ",tags").replace(",", "%2C")
    t.add(
        f"{GV}/wp-json/wp/v2/posts?per_page=100&page=1&orderby=date&order=asc&_fields={fields}",
        (200, json.dumps([post]), {"X-WP-Total": "1", "X-WP-TotalPages": "1"}),
    )
    fetcher, client, _ = make(tmp_path, t)
    folder = tmp_path / "bf"
    p = backfill_wordpress(fetcher, client, folder, run="r1", with_tags=True)
    assert p.finished and p.tag_pages == 1 and (folder / "tags-p0001.json").exists()
    fetcher.byline_map = {7: ("A. Writer",)}
    build_rows(fetcher, folder, tmp_path / "rows.jsonl")
    row = json.loads((tmp_path / "rows.jsonl").read_text().splitlines()[0])
    assert row["publisher_tags"] == ["Invented tag", "Another"]
    # series 0.1 and 0.2 ask for the same fields as before
    assert "tags" not in fetcher.backfill_url(1) and "tags" in fetcher.backfill_url(
        1, with_tags=True
    )
    assert fetcher.tags_only_url(2).endswith("_fields=id%2Ctags")


def test_the_bosnian_edition_drops_bosnian_republication_notes(tmp_path):
    from commonswire.fetchers.wordpress import BalkanDiskursBosnianFetcher

    src = parse_row(
        row(
            source_id="balkandiskurs_bs",
            name="Balkan Diskurs (Bosnian)",
            homepage="https://balkandiskurs.com/",
            languages="bs",
            edition_of="balkandiskurs",
        )
    )
    f, _, _ = make(tmp_path, FakeTransport(), cls=BalkanDiskursBosnianFetcher, source=src)
    assert f.language == "bs" and f.api_base == "https://balkandiskurs.com"
    own = f.item_from_post(wp_post(1, body="<p>Izmišljen tekst o izmišljenom mostu.</p>"))
    assert f.third_party_reason(own) is None
    note = "<p>Izmišljen tekst.</p><p>Tekst je preuzet sa izmišljenog portala.</p>"
    assert f.third_party_reason(f.item_from_post(wp_post(2, body=note))) == "republication_note"
    first = "<p>Ovaj članak je originalno objavljen na drugom portalu.</p><p>Tekst.</p>"
    assert f.third_party_reason(f.item_from_post(wp_post(3, body=first))) == "republication_note"


def test_a_lingua_fetcher_takes_its_language_and_versions(tmp_path):
    from commonswire.fetchers.wordpress import LINGUA_FETCHERS

    src = parse_row(
        row(
            source_id="globalvoices_zht",
            name="Global Voices (zht)",
            homepage="https://zht.globalvoices.org/",
            languages="zh-Hant",
            edition_of="globalvoices",
        )
    )
    cls = LINGUA_FETCHERS["globalvoices_zht"]
    f, _, _ = make(tmp_path, FakeTransport(), cls=cls, source=src)
    post = wp_post(1)
    post["link"] = "https://zht.globalvoices.org/2026/11/02/12345/"
    f.versions = {
        canonical_url(post["link"]): {
            "other_versions": [f"{GV}/2026/11/01/invented-story-1/"],
            "original_url": f"{GV}/2026/11/01/invented-story-1/",
        }
    }
    item = f.item_from_post(post)
    assert item.language == "zh-Hant"
    a = f.build(item, item.published_at)
    assert a.other_versions == (f"{GV}/2026/11/01/invented-story-1/",)
    assert a.original_url == f"{GV}/2026/11/01/invented-story-1/"
