from __future__ import annotations

import csv

import pytest

from commonswire.http import (
    USER_AGENT,
    Blocked,
    BudgetExceeded,
    Disallowed,
    FetchError,
    Pacer,
    RawResponse,
    Response,
    UsageLog,
    make_client,
    parse_robots,
    requests_transport,
)
from fakes import CONNECTION_ERROR, FakeClock, FakeTransport, make_test_client

SITE = "https://news.example.org"


def log_rows(tmp_path):
    with (tmp_path / "usage_log.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_user_agent_names_the_project_and_a_contact_url_but_no_email():
    assert USER_AGENT.startswith("CommonsWire/")
    assert "https://github.com/obadaKraishan" in USER_AGENT
    assert "@" not in USER_AGENT


def test_get_reads_robots_once_then_fetches_and_logs_every_attempt(tmp_path):
    t = FakeTransport()
    t.add(f"{SITE}/robots.txt", (200, "User-agent: *\nAllow: /\n"))
    t.add(f"{SITE}/a?page=2&secret=x", (200, "<p>one</p>", {"Content-Type": "text/html"}))
    t.add(f"{SITE}/b", (200, "<p>two</p>"))
    client, _clock = make_test_client(tmp_path, t)
    resp = client.get(f"{SITE}/a?page=2&secret=x")
    client.get(f"{SITE}/b")
    assert resp.status == 200 and resp.text == "<p>one</p>"
    assert [c[0] for c in t.calls] == [
        f"{SITE}/robots.txt",
        f"{SITE}/a?page=2&secret=x",
        f"{SITE}/b",
    ]
    assert all(c[1]["User-Agent"] == USER_AGENT for c in t.calls)
    rows = log_rows(tmp_path)
    assert [r["path"] for r in rows] == ["/robots.txt", "/a", "/b"]
    assert rows[0]["note"] == "robots"
    assert rows[1]["query_keys"] == "page;secret"
    assert "x" not in rows[1]["query_keys"].split(";")
    assert rows[1]["bytes"] == "10" and rows[1]["host"] == "news.example.org"


def test_requests_start_at_least_two_seconds_apart(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    client, clock = make_test_client(tmp_path, t)
    client.get(f"{SITE}/a")
    client.get(f"{SITE}/b")
    # robots, a, b: the second and third each waited the full 2 s gap (the fake clock does
    # not move during a request).
    assert clock.sleeps == [2.0, 2.0]


def test_crawl_delay_longer_than_the_minimum_is_honored(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (200, "User-agent: *\nCrawl-delay: 7\n"))
    client, clock = make_test_client(tmp_path, t)
    client.get(f"{SITE}/a")
    client.get(f"{SITE}/b")
    assert clock.sleeps == [7.0, 7.0]


def test_robots_disallow_stops_the_request_before_it_is_sent(tmp_path):
    t = FakeTransport().add(
        f"{SITE}/robots.txt", (200, "User-agent: CommonsWire\nDisallow: /private/\n")
    )
    client, _ = make_test_client(tmp_path, t)
    with pytest.raises(Disallowed, match="does not allow CommonsWire"):
        client.get(f"{SITE}/private/x")
    assert [c[0] for c in t.calls] == [f"{SITE}/robots.txt"]
    assert client.get(f"{SITE}/public").status == 404


@pytest.mark.parametrize("status", [401, 403, 451])
def test_a_refusal_raises_blocked_without_any_retry(tmp_path, status):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/a", (status, "no"))
    client, _clock = make_test_client(tmp_path, t)
    with pytest.raises(Blocked) as exc:
        client.get(f"{SITE}/a")
    assert exc.value.status == status
    assert [c[0] for c in t.calls].count(f"{SITE}/a") == 1


def test_a_bot_check_page_with_status_200_counts_as_a_block(tmp_path):
    wall = "<html><head><title>Just a moment...</title></head></html>"
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/a", (200, wall))
    client, _ = make_test_client(tmp_path, t)
    with pytest.raises(Blocked, match="bot check page"):
        client.get(f"{SITE}/a")


def test_robots_that_refuses_us_blocks_the_whole_host(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (403, "forbidden"))
    client, _ = make_test_client(tmp_path, t)
    with pytest.raises(Disallowed):
        client.get(f"{SITE}/a")
    assert client.robots(f"{SITE}/a").state == "blocked"


def test_robots_with_a_server_error_means_do_not_crawl_now(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (503, "down"))
    client, _clock = make_test_client(tmp_path, t)
    with pytest.raises(Disallowed):
        client.get(f"{SITE}/a")
    assert client.robots(SITE).state == "unreachable"
    assert len(t.calls) == 4  # the first try and three retries


def test_robots_network_error_is_unreachable(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", CONNECTION_ERROR)
    client, _ = make_test_client(tmp_path, t)
    assert client.robots(SITE).state == "unreachable"


def test_429_and_5xx_back_off_honoring_retry_after(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(f"{SITE}/a", (429, "slow down", {"Retry-After": "30"}), (502, "bad"), (200, "ok"))
    client, clock = make_test_client(tmp_path, t)
    assert client.get(f"{SITE}/a").status == 200
    backoffs = [s for s in clock.sleeps if s not in (2.0,)]
    assert backoffs[0] == 30.0  # Retry-After beats the 4 s base
    assert 8.0 in backoffs  # the second retry doubles the base
    assert [r["status"] for r in log_rows(tmp_path)][1:] == ["429", "502", "200"]


def test_retry_after_is_capped(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(f"{SITE}/a", (429, "", {"retry-after": "9999"}), (200, "ok"))
    client, clock = make_test_client(tmp_path, t)
    client.get(f"{SITE}/a")
    assert 120.0 in clock.sleeps


def test_persistent_server_errors_return_the_last_answer(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/a", (500, "err"))
    client, _ = make_test_client(tmp_path, t)
    assert client.get(f"{SITE}/a").status == 500
    assert [c[0] for c in t.calls].count(f"{SITE}/a") == 4


def test_persistent_network_errors_raise_fetch_error(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/a", CONNECTION_ERROR)
    client, _ = make_test_client(tmp_path, t)
    with pytest.raises(FetchError, match="failed after 4 tries"):
        client.get(f"{SITE}/a")
    assert log_rows(tmp_path)[-1]["status"] == "error"
    assert log_rows(tmp_path)[-1]["note"] == "ConnectionError"


def test_redirects_are_followed_by_hand_with_robots_and_a_log_row_per_hop(tmp_path):
    other = "https://www.example.org"
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(f"{SITE}/old", (301, "", {"Location": f"{other}/new"}))
    t.add(f"{other}/robots.txt", (200, "User-agent: *\nAllow: /\n"))
    t.add(f"{other}/new", (302, "", {"location": "/final"}))
    t.add(f"{other}/final", (200, "done"))
    client, _ = make_test_client(tmp_path, t)
    resp = client.get(f"{SITE}/old")
    assert resp.url == f"{other}/final"
    assert resp.redirects == (f"{SITE}/old", f"{other}/new")
    assert [r["path"] for r in log_rows(tmp_path)] == [
        "/robots.txt",
        "/old",
        "/robots.txt",
        "/new",
        "/final",
    ]


def test_too_many_redirects_fail(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(f"{SITE}/loop", (302, "", {"Location": f"{SITE}/loop"}))
    client, _ = make_test_client(tmp_path, t)
    with pytest.raises(FetchError, match="redirected more than"):
        client.get(f"{SITE}/loop")


def test_byte_budget_stops_further_requests(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/a", (200, "x" * 50))
    client, _ = make_test_client(tmp_path, t, byte_budget=40)
    client.get(f"{SITE}/a")
    assert client.bytes_used >= 40
    with pytest.raises(BudgetExceeded, match="ask before fetching more"):
        client.get(f"{SITE}/a")


def test_max_bytes_cuts_a_large_answer_and_logs_it(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, "")).add(f"{SITE}/big", (200, "y" * 100))
    client, _ = make_test_client(tmp_path, t)
    resp = client.get(f"{SITE}/big", max_bytes=10)
    assert resp.truncated and len(resp.body) == 10
    assert log_rows(tmp_path)[-1]["note"] == "truncated"


def test_parse_robots_records_ai_crawlers_shut_out_of_the_site():
    rule = parse_robots(
        "x.org", 200, "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
    )
    assert rule.ai_crawlers_shut_out == ("GPTBot",)
    assert rule.allows("https://x.org/story") and rule.state == "present"
    assert rule.crawl_delay() is None
    none = parse_robots("x.org", 404, "")
    assert none.state == "none" and none.allows("https://x.org/a") and none.crawl_delay() is None


def test_response_text_uses_the_declared_charset_and_json_parses():
    resp = Response(
        url="u", status=200, headers={"Content-Type": "text/html; charset=latin-1"}, body=b"caf\xe9"
    )
    assert resp.text == "café"
    assert Response(url="u", status=200, headers={}, body=b'{"a": 1}').json() == {"a": 1}


def test_pacer_waits_only_for_the_rest_of_the_gap_per_host(tmp_path):
    clock = FakeClock()
    pacer = Pacer(tmp_path / "locks", 2.0, clock=clock.time, sleep=clock.sleep)
    with pacer.slot("a.org"):
        pass
    clock.now += 1.5
    with pacer.slot("a.org"):
        pass
    assert clock.sleeps == [pytest.approx(0.5)]
    with pacer.slot("b.org"):
        pass  # another host does not wait for a.org
    assert len(clock.sleeps) == 1
    with pacer.slot("a.org", 10.0):
        pass  # a crawl-delay longer than the minimum is honored
    assert clock.sleeps[-1] == pytest.approx(10.0)
    pacer.paths("a.org")[1].write_text("garbage")
    with pacer.slot("a.org"):
        pass  # an unreadable stamp counts as no earlier request
    assert pacer.paths("Weird Host:443")[0].name == "weird_host_443.lock"
    assert pacer.paths("")[0].name == "_any.lock"


def test_a_new_process_waits_the_crawl_delay_another_process_recorded(tmp_path):
    clock = FakeClock()
    running = Pacer(tmp_path / "locks", 2.0, clock=clock.time, sleep=clock.sleep)
    with running.slot("a.org", 10.0):
        pass  # a process that has read robots.txt: crawl-delay 10
    clock.now += 3.0
    fresh = Pacer(tmp_path / "locks", 2.0, clock=clock.time, sleep=clock.sleep)
    with fresh.slot("a.org"):
        pass  # a new process's robots.txt request waits the full 10 s, not 2
    assert clock.sleeps == [pytest.approx(7.0)]
    with fresh.slot("a.org", 0.0):
        pass  # robots.txt read, no crawl-delay: the minimum, and the record is updated
    assert clock.sleeps[-1] == pytest.approx(2.0)
    assert fresh.gap_path("a.org").read_text() == "0.000"
    assert fresh.paths("a.org")[1].read_text().replace(".", "").isdigit()  # old stamp format


def test_crawl_delay_is_shared_with_a_second_client(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (200, "User-agent: *\nCrawl-delay: 9\n"))
    first, clock = make_test_client(tmp_path, t)
    first.get(f"{SITE}/a")
    second = type(first)(
        usage_log=first.usage_log,
        pacer=first.pacer,
        transport=t,
        sleep=clock.sleep,
        jitter=lambda: 0.0,
    )
    second.get(f"{SITE}/b")  # its own robots.txt request comes 9 s after /a, then /b 9 s later
    assert clock.sleeps == [9.0, 9.0, 9.0]


def test_usage_log_writes_a_header_once(tmp_path):
    log = UsageLog(tmp_path / "sub" / "log.csv")
    log.write("https://a.org/x", 200, 5)
    log.write("https://a.org/y", 404, 0, "note")
    lines = (tmp_path / "sub" / "log.csv").read_text().splitlines()
    assert lines[0].startswith("time,host,path") and len(lines) == 3


def test_make_client_logs_under_data(tmp_path):
    client = make_client(tmp_path, byte_budget=10)
    assert client.usage_log.path == tmp_path / "data" / "usage_log.csv"
    assert client.byte_budget == 10
    fake = FakeTransport()
    assert make_client(tmp_path, transport=fake).transport is fake


class _FakeResp:
    def __init__(self, chunks, status=200):
        self._chunks = chunks
        self.status_code = status
        self.headers = {"Content-Type": "text/plain"}

    def iter_content(self, chunk_size):
        yield from self._chunks

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeSession:
    def __init__(self, resp):
        self.resp = resp
        self.kwargs = None

    def get(self, url, **kwargs):
        self.kwargs = kwargs
        return self.resp


def test_requests_transport_streams_never_follows_redirects_and_caps_size():
    sess = _FakeSession(_FakeResp([b"abc", b"def", b"ghi"]))
    send = requests_transport(sess)  # type: ignore[arg-type]
    raw = send("https://a.org/x", {"User-Agent": USER_AGENT}, 5.0, 4)
    assert isinstance(raw, RawResponse)
    assert raw.body == b"abcd" and raw.truncated
    assert sess.kwargs["allow_redirects"] is False and sess.kwargs["stream"] is True
    whole = requests_transport(_FakeSession(_FakeResp([b"ab"])))("https://a.org", {}, 5.0, 10)  # type: ignore[arg-type]
    assert whole.body == b"ab" and not whole.truncated
