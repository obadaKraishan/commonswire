"""Probe, report and sample-command tests with invented data. No network."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone

import pytest

from commonswire import cli
from commonswire.probe import parse_date, probe_sitemap, probe_wordpress, rate
from commonswire.report import quantiles, sample_report
from commonswire.schema import make_article
from commonswire.sources import SOURCE_FIELDS
from fakes import FakeTransport, make_test_client
from test_fetchers import gv_site, wp_post
from test_sources import row

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
SITE = "https://news.example.org"


def test_parse_date_and_rate():
    assert parse_date("2026-11-12T10:00:00") == datetime(2026, 11, 12, 10, tzinfo=timezone.utc)
    assert parse_date("2026-11-12T10:00:00+02:00").utcoffset() == timedelta(hours=2)
    assert parse_date("2026-11-12 junk") == datetime(2026, 11, 12, tzinfo=timezone.utc)
    assert parse_date("not a date") is None
    assert rate([], NOW) == (None, None)
    assert rate([NOW + timedelta(days=1)], NOW) == (None, None)
    per_day, span = rate([NOW - timedelta(days=2), NOW - timedelta(days=1)], NOW)
    assert per_day == 1.0 and span == 2.0


def wp_dates(n, step_hours=6):
    return [
        {"date_gmt": (NOW - timedelta(hours=step_hours * (i + 1))).strftime("%Y-%m-%dT%H:%M:%S")}
        for i in range(n)
    ]


def test_probe_wordpress_reads_dates_and_totals_only(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(
        f"{SITE}/wp-json/wp/v2/posts?per_page=100&_fields=date_gmt&orderby=date",
        (200, json.dumps(wp_dates(100)), {"X-WP-Total": "5000"}),
    )
    t.add(
        f"{SITE}/wp-json/wp/v2/posts?per_page=1&order=asc&orderby=date&_fields=date_gmt",
        (200, json.dumps([{"date_gmt": "2009-01-05T00:00:00"}])),
    )
    client, _ = make_test_client(tmp_path, t)
    vol = probe_wordpress(client, "example_news", SITE + "/", now=NOW)
    assert vol.requests == 2 and vol.total == 5000 and vol.archive_from == "2009-01-05"
    assert vol.per_day == pytest.approx(4.0) and vol.dates_seen == 100
    r = vol.row("2026-11-13")
    assert r["est_articles_per_day"] == 4.0 and r["window_days"] == 25.0


def test_probe_wordpress_api_missing(tmp_path):
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    client, _ = make_test_client(tmp_path, t)
    vol = probe_wordpress(client, "example_news", SITE, now=NOW)
    assert vol.note == "posts API answered HTTP 404" and vol.requests == 1
    assert vol.row("d")["total_articles"] == ""


def test_probe_sitemap(tmp_path):
    news = (
        "<urlset>"
        + "".join(
            f"<url><loc>{SITE}/a{i}</loc><news:publication_date>"
            f"{(NOW - timedelta(hours=4 * (i + 1))).isoformat()}</news:publication_date></url>"
            for i in range(12)
        )
        + "</urlset>"
    )
    t = FakeTransport().add(f"{SITE}/robots.txt", (404, ""))
    t.add(f"{SITE}/news.xml", (200, news)).add(
        f"{SITE}/index.xml", (200, "<sitemapindex></sitemapindex>")
    )
    client, _ = make_test_client(tmp_path, t)
    vol = probe_sitemap(client, "example_news", f"{SITE}/news.xml", now=NOW)
    assert vol.dates_seen == 12 and vol.per_day == pytest.approx(6.0) and vol.note == "news sitemap"
    assert probe_sitemap(client, "x", f"{SITE}/index.xml", now=NOW).note.startswith(
        "a sitemap index"
    )
    assert (
        probe_sitemap(client, "x", f"{SITE}/gone.xml", now=NOW).note == "sitemap answered HTTP 404"
    )


def invented_articles():
    out = []
    for i in range(5):
        out.append(
            make_article(
                source_id="example_news",
                url=f"{SITE}/story-{i}",
                title=f"Invented story {i}",
                text="word " * (50 * (i + 1)),
                published_at=NOW - timedelta(days=i),
                retrieved_at=NOW,
                language="en",
                license="CC-BY-4.0",
                credit_line="c",
                authors=("A. Writer",) if i % 2 == 0 else (),
            )
        )
    return out


def test_quantiles_and_sample_report():
    assert quantiles([]) == {}
    q = quantiles([1, 2, 3, 4, 5])
    assert q["min"] == 1 and q["p50"] == 3 and q["max"] == 5 and q["mean"] == 3.0
    summary = {
        "source_id": "example_news",
        "seen": 10,
        "dropped": {"third_party:partner_category": 2, "duplicate": 3},
        "api_totals": {"archive_from": "2005-01-01"},
    }
    rep = sample_report(invented_articles(), summary, total_articles=1000)
    assert rep["kept"] == 5 and rep["third_party_share"] == 0.2
    assert rep["articles_per_day_in_sample"] == 1.0
    assert rep["share_with_byline"] == 0.6 and rep["missing"]["authors"] == 2
    assert rep["archive_from"] == "2005-01-01" and rep["languages"] == {"en": 5}
    assert rep["backfill"]["est_rows_after_third_party_drop"] == 800
    assert rep["backfill"]["est_jsonl_gb"] > 0
    assert "text" not in json.dumps(rep).replace("est_jsonl", "")
    empty = sample_report([], {"seen": 0})
    assert empty["kept"] == 0 and empty["share_with_byline"] is None and empty["backfill"] == {}


def write_registry(tmp_path, rows):
    path = tmp_path / "sources.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def test_cli_sample_probe_and_report(tmp_path, monkeypatch, capsys):
    reg = write_registry(
        tmp_path,
        [
            row(
                source_id="globalvoices",
                name="Global Voices",
                homepage="https://globalvoices.org/",
                license="CC-BY-3.0",
                credit_line="{title}, by {authors}, {source} ({url}), {license}",
            )
        ],
    )
    site = gv_site([wp_post(1), wp_post(2), wp_post(3, categories=("Partner",))], total=40)
    site.add(f"{SITE}/robots.txt", (404, ""))
    site.add(
        f"{SITE}/wp-json/wp/v2/posts?per_page=100&_fields=date_gmt&orderby=date",
        (200, json.dumps(wp_dates(10)), {"X-WP-Total": "77"}),
    )
    site.add(
        f"{SITE}/wp-json/wp/v2/posts?per_page=1&order=asc&orderby=date&_fields=date_gmt",
        (200, "[]"),
    )

    def fake_make_client(root, *, byte_budget=None, transport=None):
        client, _ = make_test_client(root / "data", site, byte_budget=byte_budget)
        return client

    monkeypatch.setattr("commonswire.http.make_client", fake_make_client)
    root = ["--root", str(tmp_path)]
    assert (
        cli.main(
            [
                *root,
                "sample",
                "globalvoices",
                "--max",
                "3",
                "--date",
                "2026-11-13",
                "--sources",
                str(reg),
            ]
        )
        == 2
    )
    assert "Mount the data drive" in capsys.readouterr().err
    (tmp_path / "data" / "raw").mkdir(parents=True)
    assert cli.main([*root, "sample", "nobody", "--sources", str(reg)]) == 2
    assert cli.main([*root, "sample", "wikinews_en", "--sources", str(reg)]) == 2
    assert (
        cli.main(
            [
                *root,
                "sample",
                "globalvoices",
                "--max",
                "3",
                "--date",
                "2026-11-13",
                "--sources",
                str(reg),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "saw 3, kept 2" in out and "validate: 0 errors" in out
    summary = json.loads(
        (
            tmp_path / "data" / "evidence" / "sample" / "globalvoices-2026-11-13.summary.json"
        ).read_text()
    )
    assert summary["kept"] == 2 and summary["api_totals"]["archive_from"] == "2005-03-01"
    assert (
        cli.main([*root, "probe", "globalvoices", "--wordpress", SITE, "--date", "2026-11-13"]) == 0
    )
    assert "10 dates; total 77" in capsys.readouterr().out
    assert cli.main([*root, "sample-report", "globalvoices", "--date", "2026-11-13"]) == 0
    rep = json.loads(
        (
            tmp_path / "data" / "evidence" / "sample" / "globalvoices-2026-11-13.report.json"
        ).read_text()
    )
    assert rep["kept"] == 2 and rep["backfill"]["archive_articles"] == 40
