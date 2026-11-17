"""The variables that need no model, on invented articles (no network)."""

from __future__ import annotations

import pytest

from commonswire.variables import (
    host_of,
    html_link_hosts,
    link_stats,
    row_language,
    wiki_categories,
    wiki_link_hosts,
)

BASE = "https://www.invented-news.example/2026/11/a-story/"


@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("https://WWW.Example.org/a", "example.org"),
        ("http://sub.example.org:8080/x", "sub.example.org"),
        ("ftp://example.org/file", None),
        ("https://", None),
        ("https://exa mple.org/", None),
        ("https://localhost/", None),
        ("https://[::1/", None),
    ],
)
def test_host_of(url, host):
    assert host_of(url) == host


def test_html_links_count_web_pages_only():
    html = (
        '<p>An <a href="/about/">invented</a> link, <a href="https://other.example/x">one</a>, '
        "<a href='http://www.other.example/y'>two</a>, <a href=#top>an anchor</a>, "
        '<a href="mailto:x@example.org">mail</a>, <a href="tel:+100">phone</a>, '
        '<a href="javascript:void(0)">script</a>, <a href="https://">broken</a>, '
        '<a href="sub/page">relative</a>, <a name="x">no href</a>, '
        '<a href="https://news.invented-news.example/z">own subdomain</a>.</p>'
    )
    hosts = html_link_hosts(html, BASE)
    assert hosts == [
        "invented-news.example",
        "other.example",
        "other.example",
        "invented-news.example",
        "news.invented-news.example",
    ]
    n, external, unique = link_stats(hosts, "www.invented-news.example")
    assert (n, external) == (5, 2)
    assert unique == ("invented-news.example", "news.invented-news.example", "other.example")
    assert html_link_hosts("", BASE) == []
    assert html_link_hosts('<a href="https://[bad/x">x</a><a href="http://[::1">y</a>', BASE) == []


def test_wikitext_links_and_categories():
    text = (
        "An invented [[Story|story]] and [[w:Invented place|a place]], [[wikt:word]], "
        "[[commons:File:x.jpg]], [[Category:Invented things]], [[Category:Invented_things|x]], "
        "[[File:x.jpg|thumb]], [[fr:Une histoire]], [[:Category:Other]], "
        "[https://www.source.example/a An invented source] and https://bare.example/b "
        "{{source|url=https://cited.example/c|title=An invented title}}"
    )
    hosts = wiki_link_hosts(text, "en.wikinews.org")
    assert hosts.count("en.wikinews.org") == 1
    assert "en.wikipedia.org" in hosts and "en.wiktionary.org" in hosts
    assert "commons.wikimedia.org" in hosts
    assert {"source.example", "bare.example", "cited.example"} <= set(hosts)
    n, external, _hosts = link_stats(hosts, "en.wikinews.org")
    assert n == len(hosts) and external == n - 1
    assert wiki_categories(text) == ["Invented things"]


def test_row_language_follows_the_publishers_own_language_label():
    assert row_language("factly", ("Telugu", "Fact Check"), "en") == "te"
    assert row_language("factly", ("English",), "en") == "en"
    assert row_language("factly", ("English", "Telugu"), "en") == "te"
    assert row_language("factly", ("Politics",), "en") == "en"
    # Elsewhere a category named after a language is a topic, not the post's language.
    assert row_language("globalvoices", ("Telugu",), "en") == "en"
