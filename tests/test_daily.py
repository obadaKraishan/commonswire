"""Daily-fetch tests with invented posts. Nothing here touches the network."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

from commonswire.daily import (
    DailyResult,
    daily_wordpress,
    load_rows,
    load_state,
    replay_daily,
    save_state,
)
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import GlobalVoicesFetcher
from commonswire.schema import article_id
from fakes import FakeTransport, make_test_client
from test_backfill import backfill_post
from test_fetchers import gv_source

GV = "https://globalvoices.org"
NOW = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)


def url(**params):
    return f"{GV}/wp-json/wp/v2/posts?{urlencode({'per_page': '100', 'page': '1', **params})}"


def setup(tmp_path):
    client, _ = make_test_client(tmp_path, FakeTransport())
    fetcher = GlobalVoicesFetcher(client, gv_source(), ReplayStore(tmp_path / "raw"))
    fetcher.byline_map = {7: ("A. Writer",)}
    rows_path = tmp_path / "rows.jsonl"
    stored = []
    for n in (1, 2):
        item = fetcher.item_from_post(backfill_post(n))
        stored.append(fetcher.build(item, NOW).model_dump_json())
    rows_path.write_text("\n".join(stored) + "\n")
    return fetcher, rows_path


def test_daily_adds_new_marks_changed_and_removed(tmp_path):
    fetcher, rows_path = setup(tmp_path)
    rows = load_rows(rows_path)
    newest = max(r["published_at"] for r in rows.values())[:19]
    fields = fetcher.backfill_fields
    t = FakeTransport().add(f"{GV}/robots.txt", (404, ""))
    t.add(
        url(after=newest, orderby="date", order="asc", _fields=fields),
        (200, json.dumps([backfill_post(5)])),
    )
    changed = backfill_post(1, body="<p>An invented corrected paragraph.</p>")
    t.add(
        url(modified_after="2026-11-12T00:00:00", _fields=fields),
        (200, json.dumps([changed, backfill_post(2)])),
    )
    t.add(
        url(after="2026-10-14T12:00:00", _fields="id,link"),
        (
            200,
            json.dumps(
                [{"id": 1, "link": changed["link"]}, {"id": 5, "link": backfill_post(5)["link"]}]
            ),
        ),
    )
    gone = backfill_post(2)["link"]
    t.add(gone, (404, "gone"))
    client, _ = make_test_client(tmp_path / "c", t)
    fetcher.client = client
    state = {"last_run": "2026-11-12T00:00:00"}
    res = daily_wordpress(fetcher, client, rows_path, tmp_path / "raw-daily", state, NOW)
    assert (res.new, res.changed, res.removed, res.unchanged_modified) == (1, 1, 1, 1)
    rows = load_rows(rows_path)
    by_status = sorted(r["status"] for r in rows.values())
    assert by_status == ["changed", "live", "removed"]
    removed = next(r for r in rows.values() if r["status"] == "removed")
    assert removed["text"] == "" and removed["title"]
    assert state["last_run"] == "2026-11-13T12:00:00"
    assert "1 new, 1 changed, 1 removed" in res.line()
    saved = sorted(f.name for f in (tmp_path / "raw-daily").glob("*.json"))
    assert saved == [
        "001-new-p1.json",
        "002-modified-p1.json",
        "003-listing-p1.json",
        "004-removed.json",
    ]
    record = json.loads((tmp_path / "raw-daily" / "004-removed.json").read_text())
    assert record == {"url": gone, "status": 404, "checked_at": "2026-11-13T12:00:00"}
    # The removal check asks for one article's page: the log names its id, not its address.
    with (tmp_path / "c" / "usage_log.csv").open(encoding="utf-8") as fh:
        logged = [r["path"] for r in csv.DictReader(fh)]
    assert logged[-1] == article_id(gone) and urlsplit(gone).path not in logged

    # A rebuild from the backfill alone, then the saved daily answers replayed with no request,
    # gives the same rows as the daily run (only retrieved_at may differ).
    after_daily = load_rows(rows_path)
    (tmp_path / "again").mkdir()
    _, rebuilt = setup(tmp_path / "again")
    daily = tmp_path / "daily-root"
    (daily / "2026-11-13").mkdir(parents=True)
    for f in (tmp_path / "raw-daily").glob("*.json"):
        (daily / "2026-11-13" / f.name).write_bytes(f.read_bytes())
    (daily / "2026-11-13" / "notes.txt").write_text("not an answer")
    (daily / "empty-day").mkdir()
    fetcher.client = None  # no request can leave
    rep = replay_daily(fetcher, rebuilt, daily)
    assert (rep.days, rep.files, rep.new, rep.changed, rep.removed) == (1, 4, 1, 1, 1)
    assert rep.unchanged_modified == 1
    replayed = load_rows(rebuilt)

    def strip(rows):
        return {k: {f: v for f, v in r.items() if f != "retrieved_at"} for k, r in rows.items()}

    assert strip(replayed) == strip(after_daily)
    # Replaying twice ends in the same rows (build always replays onto fresh backfill rows);
    # a missing folder is no replay at all.
    replay_daily(fetcher, rebuilt, daily)
    assert strip(load_rows(rebuilt)) == strip(after_daily)
    assert replay_daily(fetcher, rebuilt, tmp_path / "none").files == 0


def test_daily_without_rows_or_when_refused(tmp_path):
    fetcher, rows_path = setup(tmp_path)
    empty = tmp_path / "none.jsonl"
    res = daily_wordpress(fetcher, fetcher.client, empty, tmp_path / "r", {}, NOW)
    assert res.note.startswith("no stored rows")
    t = FakeTransport().add(f"{GV}/robots.txt", (403, "no"))
    client, _ = make_test_client(tmp_path / "b", t)
    res = daily_wordpress(fetcher, client, rows_path, tmp_path / "r2", {}, NOW)
    assert res.note.startswith("refused")
    assert DailyResult("x", note="n").line().endswith("; n")


def test_state_round_trip(tmp_path):
    path = tmp_path / "d" / "state.json"
    assert load_state(path) == {}
    save_state(path, {"a": {"last_run": "x"}})
    assert load_state(path) == {"a": {"last_run": "x"}}
