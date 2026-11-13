"""Schema tests. Every article here is invented."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from commonswire.schema import Article, Coding, article_id, canonical_url, make_article, text_hash
from commonswire.sources import license_label, render_credit

UTC = timezone.utc
TEXT = "An invented first paragraph about a town council vote.\n\nA second invented paragraph."


def art(**over):
    base = dict(
        source_id="example_news",
        url="https://news.example.org/2026/11/13/invented-story/",
        title="An invented story",
        text=TEXT,
        published_at=datetime(2026, 11, 13, 9, 0, tzinfo=UTC),
        retrieved_at=datetime(2026, 11, 13, 12, 0, tzinfo=UTC),
        language="en",
        license="CC-BY-4.0",
        credit_line="An invented story, by Example News, CC BY 4.0",
    )
    base.update(over)
    return make_article(**base)


def as_dict(a: Article, **over):
    data = json.loads(a.model_dump_json())
    data.update(over)
    return data


def test_canonical_url_rules():
    assert (
        canonical_url("HTTP://www.News.Example.org:80/a//b/?utm_source=x&b=2&a=1#frag")
        == "https://news.example.org/a/b?a=1&b=2"
    )
    assert canonical_url("https://en.m.wikinews.org/wiki/X") == "https://en.wikinews.org/wiki/X"
    assert canonical_url("https://m.example.org/") == "https://example.org/"
    assert canonical_url("https://example.org:8443/x") == "https://example.org:8443/x"
    with pytest.raises(ValueError, match="not a web address"):
        canonical_url("mailto:someone")


def test_article_id_is_stable_and_golden():
    url = "https://news.example.org/2026/11/13/invented-story/"
    assert article_id(url) == article_id("http://www.news.example.org/2026/11/13/invented-story")
    assert (
        article_id(url)
        == "cw_"
        + __import__("hashlib")
        .sha256(b"https://news.example.org/2026/11/13/invented-story")
        .hexdigest()[:16]
    )
    assert article_id(url) == "cw_588a8165f3de2ca6"


def test_make_article_computes_id_and_hash():
    a = art()
    assert a.id == article_id(a.url)
    assert a.content_hash == text_hash(TEXT)
    assert a.status == "live" and not a.third_party


@pytest.mark.parametrize(
    ("over", "message"),
    [
        ({"id": "cw_0000000000000000"}, "does not match the URL"),
        ({"content_hash": "0" * 64}, "content_hash does not match"),
        ({"content_hash": "abc"}, "64-digit SHA-256"),
        ({"published_at": "2026-11-13T09:00:00"}, "needs a time zone"),
        ({"language": "English"}, "language tag"),
        ({"license": "NOASSERTION"}, "not a license that allows"),
        ({"license": "LicenseRef-republish-guidelines"}, "not a license that allows"),
        ({"authors": ["  "]}, "author name is empty"),
        ({"title": ""}, "at least 1 character"),
        ({"credit_line": ""}, "at least 1 character"),
        ({"surprise": 1}, "Extra inputs"),
        ({"updated_at": "2026-11-12T00:00:00Z"}, "updated_at is earlier"),
        ({"retrieved_at": "2026-11-10T00:00:00Z"}, "retrieved_at is earlier"),
        ({"status": "deleted"}, "Input should be"),
    ],
)
def test_article_rules(over, message):
    with pytest.raises(ValueError, match=message):
        Article.model_validate(as_dict(art(), **over))


def test_text_rules():
    with pytest.raises(ValueError, match="text is empty"):
        art(text="   ")
    with pytest.raises(ValueError, match="HTML tags"):
        art(text="An invented <p>paragraph</p>.")
    removed = as_dict(art(), status="removed", text="", content_hash=text_hash(""))
    assert Article.model_validate(removed).status == "removed"
    with pytest.raises(ValueError, match="removed article keeps its row but not its text"):
        Article.model_validate(as_dict(art(), status="removed"))


def coding(**over):
    base = dict(
        variable="topic",
        value="Health",
        codebook_version="v0",
        model="example-model-7b",
        model_license="Apache-2.0",
        prompt_version="p1",
        coded_at="2026-11-13T12:00:00Z",
        provenance="llm_coded",
    )
    base.update(over)
    return base


def test_codings_need_full_provenance():
    a = Article.model_validate(
        as_dict(art(), codings=[coding(), coding(variable="tone", value="neutral")])
    )
    assert [c.variable for c in a.codings] == ["topic", "tone"]
    with pytest.raises(ValueError, match="needs model_license"):
        Coding.model_validate(coding(model_license=""))
    with pytest.raises(ValueError, match="needs a time zone"):
        Coding.model_validate(coding(coded_at="2026-11-13T12:00:00"))
    with pytest.raises(ValueError, match="value is empty"):
        Coding.model_validate(coding(value=""))
    human = Coding.model_validate(
        coding(model="", model_license="", prompt_version="", provenance="human_written")
    )
    assert human.provenance == "human_written"
    with pytest.raises(ValueError, match="coded twice"):
        Article.model_validate(as_dict(art(), codings=[coding(), coding(value="Other")]))
    with pytest.raises(ValueError, match="Input should be"):
        Coding.model_validate(coding(variable="gender"))


def test_license_label_and_credit_rendering():
    assert license_label("CC-BY-4.0") == "CC BY 4.0"
    assert license_label("CC-BY-NC-ND-3.0-US") == "CC BY-NC-ND 3.0 US"
    assert license_label("CC-BY-SA-3.0-IGO") == "CC BY-SA 3.0 IGO"
    assert license_label("public-domain") == "Public domain"
    assert license_label("CC0-1.0") == "CC0 1.0"
    assert license_label("MIT") == "MIT"
    kw = dict(title="T", source="Example News", url="https://x.org/a", license="CC-BY-4.0")
    assert render_credit(
        "{title}, by {authors} for {source} ({url}), {license}",
        authors=["A. Writer", "B. Writer"],
        **kw,
    ) == ("T, by A. Writer, B. Writer for Example News (https://x.org/a), CC BY 4.0")
    assert render_credit("{authors}", authors=[], **kw) == "Example News"
    with pytest.raises(ValueError, match="unknown placeholder"):
        render_credit("{byline}", authors=[], **kw)
