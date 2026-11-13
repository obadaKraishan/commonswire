"""The article schema: one row per article, with its license, credit line and coded variables.

A row's ``id`` is a stable hash of the article's canonical URL, so the same article keeps its
id across fetches; ``content_hash`` is the SHA-256 of the body text, so a changed article is
easy to spot. ``text`` is the body as published (no boilerplate, no captions), with only the
whitespace inside paragraphs collapsed. Third-party material never enters the corpus: a row
with ``third_party`` true is dropped and counted by the fetcher. A removed article keeps its
row, marked ``removed``, with its text dropped.

The coded variables (topic, frame, types of sources quoted, tone) are stubs until the codebook
is accepted; each one carries its full provenance.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from commonswire.html import has_markup
from commonswire.sources import KNOWN_LICENSES, NO_LICENSE

ID_PREFIX = "cw_"
ID_HEX = 16

#: Query parameters that only track a visit and never change the article.
TRACKING_PARAMS = re.compile(
    r"^(utm_[a-z]+|fbclid|gclid|dclid|mc_cid|mc_eid|cmpid|ref|ref_src|at_[a-z]+|"
    r"_ga|igshid|ocid|smid|sh)$",
    re.I,
)
_LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
#: How far a source's clock may run ahead of ours before a date counts as wrong.
CLOCK_SKEW = timedelta(hours=14)

Variable = Literal["topic", "frame", "source_types", "tone"]
CodingProvenance = Literal[
    "llm_coded",
    "llm_drafted_human_validated",
    "llm_drafted_human_edited",
    "human_written",
]
ArticleStatus = Literal["live", "changed", "removed"]


def canonical_url(url: str) -> str:
    """The form of a URL that the id is computed from.

    https, a lowercase host without ``www.`` or a mobile ``m.`` label, no default port, no
    fragment, no tracking parameters, the other parameters sorted, and no trailing slash.
    """
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not a web address: {url!r}")
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]
    host = host.replace(".m.", ".")
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if len(path) > 1:
        path = path.rstrip("/")
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not TRACKING_PARAMS.match(k)
    )
    return urlunsplit(("https", host, path, urlencode(query), ""))


def article_id(url: str) -> str:
    """``cw_`` and the first 16 hex digits of the SHA-256 of the canonical URL."""
    digest = hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()
    return ID_PREFIX + digest[:ID_HEX]


def text_hash(text: str) -> str:
    """The SHA-256 of the body text (Unicode NFC, UTF-8)."""
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def _aware(value: datetime | None, name: str) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{name} needs a time zone, for example 2026-11-13T09:30:00Z")
    return value


class Coding(BaseModel):
    """One coded variable of one article, with where it came from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    variable: Variable
    value: str | tuple[str, ...]
    codebook_version: str = Field(min_length=1)
    model: str = ""
    model_license: str = ""
    prompt_version: str = ""
    coded_at: datetime
    provenance: CodingProvenance

    @field_validator("coded_at")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        return _aware(v, "coded_at")  # type: ignore[return-value]

    @model_validator(mode="after")
    def _model_named(self) -> Coding:
        if self.provenance != "human_written":
            missing = [
                f for f in ("model", "model_license", "prompt_version") if not getattr(self, f)
            ]
            if missing:
                raise ValueError(
                    f"a {self.provenance} value needs {', '.join(missing)} "
                    "(which model coded it, under which license, with which prompt)"
                )
        if self.value in ("", ()):
            raise ValueError("value is empty")
        return self


class Article(BaseModel):
    """One article row."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_id: str = Field(min_length=1)
    url: str
    title: str = Field(min_length=1)
    authors: tuple[str, ...] = ()
    published_at: datetime
    updated_at: datetime | None = None
    retrieved_at: datetime
    language: str
    section: str = ""
    text: str
    license: str
    credit_line: str = Field(min_length=1)
    third_party: bool = False
    content_hash: str
    status: ArticleStatus = "live"
    codings: tuple[Coding, ...] = ()

    @field_validator("published_at", "updated_at", "retrieved_at")
    @classmethod
    def _tz(cls, v: datetime | None, info) -> datetime | None:  # type: ignore[no-untyped-def]
        return _aware(v, info.field_name)

    @field_validator("language")
    @classmethod
    def _language(cls, v: str) -> str:
        if not _LANG.match(v):
            raise ValueError("use a language tag such as en or pt-BR")
        return v

    @field_validator("license")
    @classmethod
    def _license(cls, v: str) -> str:
        if v not in KNOWN_LICENSES or v == NO_LICENSE or v.startswith("LicenseRef-"):
            raise ValueError(
                f"{v!r} is not a license that allows redistribution; use the license of the "
                "source, such as CC-BY-4.0 or public-domain"
            )
        return v

    @field_validator("content_hash")
    @classmethod
    def _hash_form(cls, v: str) -> str:
        if not _HEX64.match(v):
            raise ValueError("content_hash is the 64-digit SHA-256 of the text")
        return v

    @field_validator("authors")
    @classmethod
    def _authors(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(not a.strip() for a in v):
            raise ValueError("an author name is empty")
        return v

    @model_validator(mode="after")
    def _consistent(self) -> Article:
        expected = article_id(self.url)
        if self.id != expected:
            raise ValueError(f"id {self.id} does not match the URL; it should be {expected}")
        if self.content_hash != text_hash(self.text):
            raise ValueError("content_hash does not match the text; recompute it with text_hash")
        if self.status == "removed":
            if self.text:
                raise ValueError("a removed article keeps its row but not its text: empty text")
        else:
            if not self.text.strip():
                raise ValueError("text is empty; only a removed article may have no text")
            if has_markup(self.text):
                raise ValueError("text still holds HTML tags; give plain text")
        if self.updated_at is not None and self.updated_at < self.published_at:
            raise ValueError("updated_at is earlier than published_at")
        if self.retrieved_at + CLOCK_SKEW < self.published_at:
            raise ValueError("retrieved_at is earlier than published_at")
        seen: set[tuple[str, str, str]] = set()
        for c in self.codings:
            key = (c.variable, c.codebook_version, c.model)
            if key in seen:
                raise ValueError(f"{c.variable} is coded twice by the same model and codebook")
            seen.add(key)
        return self


def make_article(
    *,
    source_id: str,
    url: str,
    title: str,
    text: str,
    published_at: datetime,
    retrieved_at: datetime,
    language: str,
    license: str,
    credit_line: str,
    authors: tuple[str, ...] = (),
    updated_at: datetime | None = None,
    section: str = "",
    third_party: bool = False,
) -> Article:
    """Build an article row, computing its id and content hash."""
    return Article(
        id=article_id(url),
        source_id=source_id,
        url=url,
        title=title,
        authors=authors,
        published_at=published_at,
        updated_at=updated_at,
        retrieved_at=retrieved_at,
        language=language,
        section=section,
        text=text,
        license=license,
        credit_line=credit_line,
        third_party=third_party,
        content_hash=text_hash(text),
        status="live",
    )
