from __future__ import annotations

import csv
from datetime import date

import pytest

from commonswire.sources import (
    SOURCE_FIELDS,
    Source,
    check_quotes,
    load_sources,
    normalize_for_match,
    parse_row,
    read_rows,
    rule_problems,
    validate_sources,
)

TODAY = date(2026, 11, 13)


def row(**over):
    base = {
        "source_id": "example_news",
        "name": "Example News",
        "kind": "news",
        "homepage": "https://news.example.org/",
        "country": "US",
        "languages": "en",
        "license": "CC-BY-4.0",
        "license_url": "https://news.example.org/license/",
        "terms_url": "https://news.example.org/terms/",
        "checked_on": "2026-11-13",
        "quote_license": "All our stories are published under CC BY 4.0.",
        "quote_bulk": "",
        "quote_attribution": "Credit Example News and link to the story.",
        "quote_terms": "",
        "bulk_clause": "silent",
        "robots": "allows",
        "terms_automation": "silent",
        "tracking_required": "no",
        "third_party_rule": "wire stories carry an AP byline",
        "access": "api;feed",
        "est_articles_per_day": "12.5",
        "archive_from": "2005-09",
        "credit_line": "Example News, CC BY 4.0",
        "status": "include",
        "reason": "",
        "notes": "",
    }
    base.update(over)
    return base


def problems(**over):
    return rule_problems(parse_row(row(**over)), TODAY)


def write_csv(tmp_path, rows, fields=SOURCE_FIELDS):
    path = tmp_path / "sources.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_a_clean_cc_by_source_silent_on_bulk_is_a_valid_include():
    src = parse_row(row())
    assert src.languages == ("en",) and src.access == ("api", "feed")
    assert src.est_articles_per_day == 12.5
    assert src.license_family == "open"
    assert rule_problems(src, TODAY) == []


# ---- field checks ----


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_id", "Example News", "lowercase letters"),
        ("homepage", "news.example.org", "starting with https://"),
        ("license_url", "not a url", "or leave it blank"),
        ("country", "USA", "two-letter country code"),
        ("languages", "", "at least one language"),
        ("languages", "English", "not a language tag"),
        ("access", "scrape", "unknown access"),
        ("license", "CC BY 4.0", "unknown license"),
        ("est_articles_per_day", "-1", "can't be negative"),
        ("archive_from", "Sept 2005", "use a year or a date"),
        ("quote_license", "x" * 301, "keep quotes short"),
        ("quote_bulk", "two\nlines", "on one line"),
        ("kind", "blog", "Input should be"),
        ("bulk_clause", "maybe", "Input should be"),
        ("robots", "yes", "Input should be"),
        ("status", "maybe", "Input should be"),
    ],
)
def test_field_checks(field, value, message):
    with pytest.raises(ValueError, match=message):
        parse_row(row(**{field: value}))


def test_unknown_columns_are_refused():
    with pytest.raises(ValueError, match="Extra inputs"):
        Source.model_validate(row(extra_column="x"))


def test_license_ref_and_blank_numbers_are_accepted():
    src = parse_row(row(license="LicenseRef-republish-guidelines", est_articles_per_day=""))
    assert src.est_articles_per_day is None
    assert src.license_family == "none"
    assert parse_row(row(license="LicenseRef-other-terms")).license_family == "closed"


# ---- the rules that link fields ----


def test_checked_on_in_the_future():
    assert "in the future" in problems(checked_on="2026-12-01")[0]


@pytest.mark.parametrize("clause", ["allows", "forbids"])
def test_a_clause_that_allows_or_forbids_needs_its_quote(clause):
    out = problems(
        bulk_clause=clause, status="exclude" if clause == "forbids" else "include", reason="x"
    )
    assert any("give the exact words in quote_bulk" in p for p in out)


def test_terms_that_forbid_automation_need_a_quote():
    out = problems(terms_automation="forbids", status="exclude", reason="terms")
    assert any("quote_terms" in p for p in out)


def test_a_license_needs_its_url():
    assert any("license_url" in p for p in problems(license_url=""))


def test_tracking_required_needs_a_quote():
    out = problems(tracking_required="yes", status="exclude", reason="pixel", quote_attribution="")
    assert any("quote the words that require it" in p for p in out)


@pytest.mark.parametrize(
    ("over", "point"),
    [
        ({"license": "LicenseRef-all-rights-reserved"}, "1: no license allows"),
        ({"bulk_clause": "forbids", "quote_bulk": "Do not republish automatically."}, "2: forbids"),
        ({"tracking_required": "yes"}, "2: requires a tracking pixel"),
        ({"robots": "forbids"}, "3: robots.txt forbids"),
        ({"terms_automation": "forbids", "quote_terms": "No scraping."}, "3: the terms forbid"),
    ],
)
def test_include_is_refused_for_every_failed_point(over, point):
    out = problems(**over)
    assert any(f"fails point {point}" in p for p in out)


@pytest.mark.parametrize(
    ("over", "point"),
    [
        ({"license": "NOASSERTION", "license_url": ""}, "1: no license is named"),
        ({"license": "CC-BY-NC-ND-4.0"}, "2: a NonCommercial or NoDerivatives license"),
        ({"license": "CC-BY-ND-4.0"}, "2: a NonCommercial or NoDerivatives license"),
        ({"robots": "blocked"}, "3: the site refused scripted requests"),
        ({"third_party_rule": ""}, "4: no way to tell"),
        ({"quote_license": ""}, "1: no quote for the license"),
    ],
)
def test_include_is_refused_when_a_point_is_silent_or_unclear(over, point):
    out = problems(**over)
    assert any(f"point {point}" in p for p in out)


def test_bespoke_terms_silent_on_bulk_are_pending_and_name_both_points():
    src = parse_row(
        row(
            license="LicenseRef-republish-guidelines",
            status="pending",
            reason="Does the outlet allow automatic republishing?",
        )
    )
    assert [p.split(":")[0] for p in src.open_points()] == ["1", "2"]
    assert rule_problems(src, TODAY) == []


def test_restricted_license_that_allows_bulk_can_be_included():
    out = problems(
        license="CC-BY-ND-4.0",
        bulk_clause="allows",
        quote_bulk="You may republish all our stories automatically.",
    )
    assert out == []


def test_include_needs_credit_line_and_access_but_a_site_may_have_no_terms_page():
    out = problems(credit_line="", access="", terms_url="")
    assert any("credit_line" in p for p in out)
    assert any("access" in p for p in out)
    assert not any("terms_url" in p for p in out)
    assert any("unknown placeholder" in p for p in problems(credit_line="{byline}"))


def test_exclude_needs_a_reason_and_a_failed_point():
    out = problems(status="exclude")
    assert any("say why in reason" in p for p in out)
    assert any("no point fails outright" in p for p in out)
    ok = problems(
        status="exclude",
        reason="forbids automatic republishing",
        bulk_clause="forbids",
        quote_bulk="not automatically",
    )
    assert ok == []


def test_pending_needs_a_question_and_no_failed_point():
    assert any("exact question" in p for p in problems(status="pending", reason="unclear"))
    out = problems(status="pending", reason="Is it ok?", robots="forbids")
    assert any("exclude it" in p for p in out)


# ---- the file ----


def test_validate_sources_reports_lines_duplicates_and_field_errors(tmp_path):
    rows = [row(), row(), row(source_id="other", country="usa")]
    sources, out = validate_sources(write_csv(tmp_path, rows), TODAY)
    assert len(sources) == 2
    assert any("line 3 (example_news): source_id is also on line 2" in p for p in out)
    assert any("homepage is also on line 2" in p for p in out)
    assert any("line 4 (other): country:" in p for p in out)


def test_header_must_match(tmp_path):
    path = write_csv(tmp_path, [], fields=["source_id", "name", "surprise"])
    with pytest.raises(ValueError, match=r"missing kind.*unexpected surprise"):
        read_rows(path)


def test_load_sources_raises_on_any_problem(tmp_path):
    good = write_csv(tmp_path, [row()])
    assert list(load_sources(good)) == ["example_news"]
    bad = write_csv(tmp_path, [row(credit_line="")])
    with pytest.raises(ValueError, match="1 problem"):
        load_sources(bad)


# ---- quotes ----


def test_quotes_must_be_word_for_word_on_a_saved_page():
    src = parse_row(row(quote_attribution="Credit \u201cExample News\u201d \u2014 and link."))
    page = "Intro.\nAll our stories are published under   CC BY 4.0.\n"
    page += 'Credit "Example News" - and link.'
    assert check_quotes([src], lambda _id: {"p1": page}) == []
    out = check_quotes([src], lambda _id: {"p1": "All our stories are published under CC BY."})
    assert any("quote_license is not on any saved page" in p for p in out)
    assert check_quotes([src], lambda _id: {}) == [
        "example_news: no saved pages to check its quotes against"
    ]
    quiet = parse_row(row(quote_license="", quote_attribution="", status="pending", reason="?"))
    assert check_quotes([quiet], lambda _id: {}) == []


def test_normalize_for_match():
    assert normalize_for_match("a\u00a0b \u2018c\u2019\n\nd") == "a b 'c' d"


def test_the_credit_line_names_translators_set_off_by_commas():
    from commonswire.sources import render_credit

    gv = "This story by {authors} originally appeared on {source}: {title} ({url}), {license}"
    comma = "{title}, by {authors}, {source} ({url}), {license}"
    kw = dict(title="T", source="S", url="https://s.example/t", license="CC-BY-3.0")
    assert render_credit(gv, authors=("A",), translators=("B", "C"), **kw) == (
        "This story by A, translated by B, C, originally appeared on S: T "
        "(https://s.example/t), CC BY 3.0"
    )
    assert render_credit(comma, authors=("A",), translators=("B",), **kw) == (
        "T, by A, translated by B, S (https://s.example/t), CC BY 3.0"
    )
    assert render_credit("{title} by {authors}", authors=("A",), translators=("B",), **kw) == (
        "T by A, translated by B"
    )
    assert render_credit(gv, authors=("A",), translators=(" ",), **kw) == render_credit(
        gv, authors=("A",), **kw
    )
    assert "by S, translated by B," in render_credit(gv, authors=(), translators=("B",), **kw)
    assert render_credit("{title}, {source}", authors=("A",), translators=("B",), **kw) == "T, S"
