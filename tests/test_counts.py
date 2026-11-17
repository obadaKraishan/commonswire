"""The count check of older rows, on the invented sources of test_update. No network."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from commonswire.counts import Allowance, check_counts, count_url, record_until
from commonswire.schema import article_id
from test_update import (
    FACTLY,
    NAMES,
    SECRET_TEXT,
    Site,
    World,
    _log,
    make_clients,
    released,
)
from test_update import series as series  # the invented sources' version series (autouse)


def full(posts, *, current="2026-11-12"):
    """Counts of 2024 and 2025 (whole years) and of 2026 up to ``current``."""
    return {
        "2024": {"posts": posts.get(2024, 5), "before": "2025-01-01"},
        "2025": {"posts": posts.get(2025, 5), "before": "2026-01-01"},
        "2026": {"posts": posts.get(2026, 5), "before": current},
    }


def with_counts(w, factly=None, globalvoices=None, thepublicrecord=None):
    """The previous version's manifest with post counts (5 a year unless given)."""
    m = json.loads((w.prev / "manifest.json").read_text())
    m["post_counts"] = {
        "factly": full(factly or {}),
        "globalvoices": full(globalvoices or {}),
        "thepublicrecord": {
            "2026": {"posts": (thepublicrecord or {}).get(2026, 5), "before": "2026-11-12"}
        },
    }
    (w.prev / "manifest.json").write_text(json.dumps(m))
    return m["post_counts"]


def count_calls(site, host):
    return [
        parse_qs(urlsplit(u).query)
        for u in site.calls
        if host in u and "per_page=1&" in u and "_fields=id" in u
    ]


def shown(res):
    return json.dumps(res.summary()) + res.markdown()


def test_a_baseline_run_records_the_counts_and_compares_nothing(tmp_path):
    w = World(tmp_path)
    res = w.run()
    assert res.status == "ready" and res.count_baseline
    fa = res.sources["factly"].count
    assert fa.baseline and fa.years_checked == 0 and fa.count_requests == 3
    assert fa.counts == {
        "2024": {"posts": 5, "before": "2025-01-01"},
        "2025": {"posts": 5, "before": "2026-01-01"},
        "2026": {"posts": 5, "before": "2026-11-19"},  # up to the day before the run
    }
    assert res.sources["thepublicrecord"].count.counts == {
        "2026": {"posts": 5, "before": "2026-11-19"}
    }
    m, _ = released(tmp_path / "next")
    assert set(m["post_counts"]) == {"factly", "globalvoices", "thepublicrecord"}
    assert m["update"]["count_check"]["baseline"] is True
    md = res.markdown()
    assert "a baseline run: 9.9.0 has no post counts" in md
    assert "| factly | 0 of 3 recorded | none | none | 0 | 0 |" in md
    assert any("a baseline run" in n for n in res.notes)
    readme = (tmp_path / "next" / "README.md").read_text()
    assert "first to record each source's post count per year" in readme
    assert "compares every source's post count per year" in readme  # Removals and corrections
    assert "not checked yet" not in readme


def test_counts_that_hold_cost_a_request_a_year_and_list_nothing(tmp_path):
    w = World(tmp_path)
    with_counts(w)
    res = w.run()
    assert res.status == "ready" and not res.count_baseline
    fa = res.sources["factly"].count
    assert (fa.years_checked, fa.drops, fa.rises, fa.listing_pages) == (3, {}, {}, 0)
    # 2024 and 2025 once each; 2026 twice: the days compared, and the longer range recorded.
    befores = [q["before"][0] for q in count_calls(w.site, "factly.in")]
    assert befores == [
        "2025-01-01T00:00:00",
        "2026-01-01T00:00:00",
        "2026-11-12T00:00:00",
        "2026-11-19T00:00:00",
    ]
    assert fa.count_requests == 4 and res.count_used == 0
    m, _ = released(tmp_path / "next")
    assert m["post_counts"]["factly"]["2026"] == {"posts": 5, "before": "2026-11-19"}
    md = res.markdown()
    assert "(0 of 200 requests used for drops)" in md
    assert "| factly | 3 | none | none | 0 | 0 |" in md
    readme = (tmp_path / "next" / "README.md").read_text()
    assert "compared with 9.9.0's (7 years): 0 fell" in readme


@pytest.mark.parametrize(
    ("status", "removed"), [(404, True), (410, True), (200, False), (500, False)]
)
def test_a_drop_lists_the_year_and_checks_the_pages_of_missing_rows(tmp_path, status, removed):
    w = World(tmp_path)
    with_counts(w, factly={2024: 6})  # the site now counts 5 in 2024
    f0 = article_id(w.f[0]["link"])
    w.site.pages[w.f[0]["link"]] = (status, "an answer")
    res = w.run()
    fa = res.sources["factly"]
    c = fa.count
    assert c.drops == {"2024": 1} and c.years_listed == ["2024"] and c.listing_pages == 1
    assert (c.rows_checked, c.rows_removed, c.rows_kept) == (1, int(removed), int(not removed))
    assert res.count_used == 2  # one listing page, one page check
    assert fa.removed == 1 + int(removed)  # f3 (the window) and maybe f0 (the count check)
    m, rows = released(tmp_path / "next")
    assert (f0 not in rows) is removed
    assert m["removed_rows_not_released"] == {"factly": 1 + int(removed)}
    assert f"| factly | 3 | 2024 (1) | none | 1 | {int(removed)} |" in res.markdown()
    # The page check is logged by the row's id; nothing public names an address or a text.
    with (tmp_path / "work" / "usage_log.csv").open(encoding="utf-8") as fh:
        assert f0 in {r["path"] for r in csv.DictReader(fh)}
    out = shown(res)
    assert "/2024/" not in out and SECRET_TEXT not in out
    assert not any(n in out for n in NAMES)


def test_a_drop_with_every_released_row_still_listed_checks_no_page(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2024: 6})
    w.site.year_links["factly"][2024] = [w.f[0]["link"], f"{FACTLY}/2024/01/02/other/"]
    res = w.run()
    c = res.sources["factly"].count
    assert c.drops == {"2024": 1} and c.listing_pages == 1 and c.rows_checked == 0


def test_rows_already_read_this_run_are_not_checked_again(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2025: 6}, globalvoices={2024: 6})  # f5 and g7 were edited: listed
    res = w.run()
    assert res.sources["factly"].count.rows_checked == 0
    assert res.sources["globalvoices"].count.rows_checked == 0


def test_a_rise_is_reported_and_nothing_more_is_done(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2025: 4})  # a back-dated post: the site now counts 5
    res = w.run()
    c = res.sources["factly"].count
    assert c.rises == {"2025": 1} and c.drops == {} and c.listing_pages == 0
    assert "| factly | 3 | none | 2025 (1) | 0 | 0 |" in res.markdown()


def test_a_drop_the_window_explains_is_not_listed(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2026: 6})  # f3 (2026-11-08) was removed, and the window saw it
    res = w.run()
    c = res.sources["factly"].count
    assert c.drops == {"2026": 1} and c.explained == {"2026": 1} and c.listing_pages == 0


def test_past_the_ceiling_the_source_stops_named_with_the_year(tmp_path):
    w = World(tmp_path)
    prev = with_counts(w, factly={2024: 6})
    res = w.run(max_count_requests=1)
    fa = res.sources["factly"]
    assert fa.status == "over_ceiling" and fa.count is None
    assert "post count of 2024 fell by 1" in fa.note
    assert res.status == "stopped"
    assert any(
        r.startswith("factly was over ceiling: the post count of 2024") for r in res.stop_reasons
    )
    assert not [u for u in w.site.calls if "_fields=link" in u]  # nothing was listed
    m, rows = released(tmp_path / "next")
    assert article_id(w.f[3]["link"]) in rows  # its rows carried over unchanged
    assert m["post_counts"]["factly"] == prev["factly"]  # so the drop is still seen next week
    assert "| factly | not run (over ceiling) |" in res.markdown()
    again = World(tmp_path / "b")
    with_counts(again, factly={2024: 6})
    ok = again.run(max_count_requests=1, allow_skipped=frozenset({"factly"}))
    assert ok.status == "ready"


def test_a_ceiling_reached_while_checking_pages_stops_the_source(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2024: 6})
    w.site.year_links["factly"][2024] = [f"{FACTLY}/2024/01/01/other-{n}/" for n in range(150)]
    res = w.run(max_count_requests=2)  # the listing fits (2 pages), the page check does not
    fa = res.sources["factly"]
    assert fa.status == "over_ceiling" and "1 released rows are missing" in fa.note


def test_a_source_that_refuses_the_counts_is_skipped_like_any_other(tmp_path):
    w = World(tmp_path)
    prev = with_counts(w)
    w.site.refuse_counts.add("factly.in")
    res = w.run()
    assert res.sources["factly"].status == "refused"
    assert any("factly was refused" in r for r in res.stop_reasons)
    m, _ = released(tmp_path / "next")
    assert m["post_counts"]["factly"] == prev["factly"]


def test_a_count_check_removal_counts_toward_the_shrink_stop(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2024: 6})
    s = w.site
    s.recent = {"factly": [w.f[1], w.f[2], w.f[4]], "globalvoices": [w.g[1]], "tpr": [w.t[1]]}
    s.edited = {"factly": [], "globalvoices": [], "tpr": []}
    s.pages[w.f[0]["link"]] = (404, "gone")
    res = w.run()  # 12 rows, minus f3 (the window) and f0 (the count check): more than 1%
    assert res.rows_after == res.rows_before - 2
    assert res.status == "stopped" and any("would shrink" in r for r in res.stop_reasons)
    assert w.run(out="loose", work=tmp_path / "w2", max_shrink=0.5).status == "ready"


def test_an_offline_replay_of_a_drop_sends_nothing(tmp_path):
    w = World(tmp_path)
    with_counts(w, factly={2024: 6})
    w.site.pages[w.f[0]["link"]] = (404, "gone")
    first = w.run(out="a")
    sent = len(w.site.calls)
    again = w.run(out="b", offline=True, now=None)
    assert len(w.site.calls) == sent
    assert (
        again.sources["factly"].count.rows_removed
        == first.sources["factly"].count.rows_removed
        == 1
    )
    assert (tmp_path / "a" / "manifest.json").exists() and (
        tmp_path / "b" / "manifest.json"
    ).exists()


def test_the_new_year_compares_the_old_range_and_records_the_whole_year(tmp_path):
    site = Site()
    client = make_clients(site)(10**9, _log(tmp_path), None)
    url = f"{FACTLY}/2026/03/01/invented-1/"
    prev_rows = {"cw_x": {"published_at": "2026-03-01T08:00:00Z", "url": url}}
    chk = check_counts(
        FACTLY,
        client,
        prev_rows,
        {"2026": {"posts": 5, "before": "2026-12-28"}},
        now=datetime(2027, 1, 4, 6, tzinfo=timezone.utc),
        rows=dict(prev_rows),
        skip=set(),
        removed_in_window={},
        allowance=Allowance(),
        note="test",
    )
    assert chk.counts == {
        "2026": {"posts": 5, "before": "2027-01-01"},
        "2027": {"posts": 5, "before": "2027-01-03"},
    }
    assert [q["before"][0] for q in count_calls(site, "factly.in")] == [
        "2026-12-28T00:00:00",
        "2027-01-01T00:00:00",
        "2027-01-03T00:00:00",
    ]
    assert chk.years_checked == 1 and not chk.baseline


def test_record_until_and_count_url():
    at = lambda d: datetime.fromisoformat(d).replace(tzinfo=timezone.utc)  # noqa: E731
    assert record_until(2026, at("2026-11-20T12:00")) == date(2026, 11, 19)
    assert record_until(2025, at("2026-11-20T12:00")) == date(2026, 1, 1)
    assert record_until(2027, at("2027-01-01T06:00")) is None  # nothing of 2027 yet
    assert record_until(2027, at("2027-01-02T06:00")) is None
    assert record_until(2027, at("2027-01-03T06:00")) == date(2027, 1, 2)
    assert record_until(2026, at("2027-01-01T06:00")) == date(2026, 12, 31)
    q = parse_qs(urlsplit(count_url(FACTLY, 2024, date(2025, 1, 1))).query)
    assert q == {
        "per_page": ["1"],
        "after": ["2023-12-31T23:59:59"],
        "before": ["2025-01-01T00:00:00"],
        "_fields": ["id"],
    }
