"""The interface every fetcher follows, and the sample runner.

A fetcher lists a source's newest items through the source's own API or feed (``items``), says
whether an item is third-party material (``third_party_reason``), and turns an item into an
:class:`~commonswire.schema.Article` (``build``). The runner saves every API answer once,
unchanged, as raw data, keeps the source's own articles, and drops and counts the rest.
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from commonswire.html import article_text
from commonswire.http import PoliteClient, Response
from commonswire.schema import Article, make_article
from commonswire.sources import Source, render_credit

#: The most articles a sample may hold from one source in one session.
SAMPLE_CAP = 200


@dataclass(frozen=True)
class Item:
    """One article as a source's API gives it, before cleaning."""

    url: str
    title: str
    body_html: str
    published_at: datetime
    language: str
    updated_at: datetime | None = None
    authors: tuple[str, ...] = ()
    #: Translators named apart from the writers (Global Voices' listing), never in authors.
    translators: tuple[str, ...] = ()
    section: str = ""
    license: str | None = None
    #: Source-specific facts used to spot third-party material (categories, credits, flags).
    hints: dict[str, object] = field(default_factory=dict)
    #: Body text that is already plain (for APIs that give text, not HTML).
    body_text: str | None = None


@dataclass
class RawStore:
    """Saves every API answer once, unchanged, under ``data/raw/sample/<source>/<date>/``."""

    folder: Path
    count: int = 0
    files: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Continue the numbering of an earlier run, so no file is ever overwritten.
        if self.folder.exists():
            self.count = max(self.count, len(list(self.folder.glob("*.json"))))

    def save(self, resp: Response, label: str) -> None:
        self.count += 1
        self.folder.mkdir(parents=True, exist_ok=True)
        name = f"{self.count:03d}-{label}.json"
        with (self.folder / name).open("xb") as fh:  # write once, never overwrite
            fh.write(resp.body)
        self.files.append(name)


class ReplayStore(RawStore):
    """Stands in for :class:`RawStore` when a sample is rebuilt from saved raw answers: it
    writes nothing and keeps the names of the files it replays."""

    def __post_init__(self) -> None:
        self.count = 0

    def save(self, resp: Response, label: str) -> None:
        self.count += 1
        self.files.append(f"{self.count:03d}-{label}.json")


class ReplayTransport:
    """Answers a fetcher's requests from saved raw files, in the order they were saved.
    robots.txt answers 404 (the live run already honored it). No request leaves the machine."""

    def __init__(self, files: list[Path]) -> None:
        self.files = list(files)
        self.served = 0

    def __call__(self, url: str, headers: object, timeout: float, max_bytes: int) -> object:
        from commonswire.http import RawResponse

        if url.endswith("/robots.txt"):
            return RawResponse(url=url, status=404, headers={}, body=b"")
        if self.served >= len(self.files):
            raise RuntimeError(f"no saved answer left to replay for {url}")
        body = self.files[self.served].read_bytes()
        self.served += 1
        return RawResponse(url=url, status=200, headers={}, body=body)


@dataclass
class SampleResult:
    source_id: str
    kept: list[Article] = field(default_factory=list)
    dropped: Counter[str] = field(default_factory=Counter)
    seen: int = 0
    raw_files: list[str] = field(default_factory=list)
    raw_bytes: int = 0
    api_totals: dict[str, object] = field(default_factory=dict)


class Fetcher(ABC):
    """Base class: subclasses set ``source_id`` and implement ``items`` and
    ``third_party_reason``."""

    source_id: str = ""
    #: Classes and ids of boilerplate blocks inside the body (share boxes, newsletter forms).
    drop_classes: tuple[str, ...] = ()
    #: The source's own sign-off lines (for example "Originally published under Creative
    #: Commons by ..."): removed from the text as boilerplate, and never taken as a sign of
    #: third-party material.
    own_notes: tuple[str, ...] = ()
    #: True when the source's attribution policy asks for the author's name: a row without a
    #: byline is stored but marked not releasable.
    requires_byline: bool = False
    #: Classes of embedded third-party posts and players, always removed from the text.
    embed_classes: tuple[str, ...] = (
        "twitter-tweet",
        "twitter-video",
        "instagram-media",
        "tiktok-embed",
        "fb-post",
        "fb-video",
        "wp-block-embed",
        "wp-embedded-content",
        "embed-youtube",
        "jetpack-video-wrapper",
    )

    def strip_own_notes(self, text: str) -> str:
        """The text without the source's own sign-off lines, and without paragraphs they emptied."""
        for pattern in self.own_notes:
            text = re.sub(pattern, "", text, flags=re.I)
        paragraphs = [re.sub(r"[ \t]{2,}", " ", p).strip() for p in text.split("\n\n")]
        return "\n\n".join(p for p in paragraphs if p)

    def __init__(self, client: PoliteClient, source: Source, raw: RawStore) -> None:
        if source.source_id != self.source_id:
            raise ValueError(f"this fetcher is for {self.source_id}, not {source.source_id}")
        if source.status != "include":
            raise ValueError(
                f"{source.source_id} is {source.status} in the registry; only include sources "
                "are fetched"
            )
        self.client = client
        self.source = source
        self.raw = raw
        self.api_totals: dict[str, object] = {}

    def get_json(self, url: str, label: str) -> object:
        """GET an API answer politely, save it as raw data, and parse it."""
        resp = self.client.get(url, accept="application/json", note=f"sample:{self.source_id}")
        if resp.status != 200:
            raise RuntimeError(f"{url} answered HTTP {resp.status}")
        self.raw.save(resp, label)
        return resp.json()

    @abstractmethod
    def items(self, limit: int) -> Iterator[Item]:
        """The newest items, newest first, at most ``limit`` of them."""

    @abstractmethod
    def third_party_reason(self, item: Item) -> str | None:
        """Why an item is third-party material, or None if it is the source's own."""

    def license_for(self, item: Item) -> str:
        return item.license or self.source.license

    def build(self, item: Item, retrieved_at: datetime) -> Article:
        text = (
            item.body_text
            if item.body_text is not None
            else article_text(item.body_html, self.drop_classes + self.embed_classes)
        )
        if self.own_notes:
            text = self.strip_own_notes(text)
        lic = self.license_for(item)
        credit = render_credit(
            self.source.credit_line,
            title=item.title,
            authors=item.authors,
            source=self.source.name,
            url=item.url,
            license=lic,
            translators=item.translators,
        )
        hold = ""
        # A page whose own byline names the source itself is released with no personal
        # author; the credit line then names the source (maintainer's decision, 2026-11-13).
        if self.requires_byline and not item.authors and not item.hints.get("byline_is_source"):
            if item.hints.get("byline_why_none") == "not_a_person":
                hold = (
                    f"credited to an account, not a person: {self.source.name} asks for the "
                    "author's name"
                )
            else:
                hold = f"no byline: {self.source.name} asks for the author's name"
        return make_article(
            releasable=not hold,
            hold_reason=hold,
            source_id=self.source_id,
            url=item.url,
            title=item.title,
            text=text,
            published_at=item.published_at,
            updated_at=item.updated_at,
            retrieved_at=retrieved_at,
            language=item.language,
            license=lic,
            credit_line=credit,
            authors=item.authors,
            translators=item.translators,
            section=item.section,
            **self.variables(item),
        )

    def variables(self, item: Item) -> dict[str, object]:
        """The variables that need no model (``commonswire.variables``), from the item."""
        from commonswire.variables import html_link_hosts, link_stats, wiki_link_hosts

        own = urlsplit(self.source.homepage).hostname or ""
        hosts: list[str] | None = None
        if item.hints.get("wikitext") is not None:
            hosts = wiki_link_hosts(str(item.hints["wikitext"]), own)
        elif item.body_text is None:
            hosts = html_link_hosts(item.body_html, item.url)
        out: dict[str, object] = {
            "publisher_section": str(item.hints.get("publisher_section", item.section) or ""),
            "publisher_categories": tuple(item.hints.get("categories") or ()),  # type: ignore[call-overload]
            "publisher_tags": tuple(item.hints.get("tags") or ()),  # type: ignore[call-overload]
            "original_url": str(item.hints.get("original_url") or ""),
        }
        if hosts is not None:
            n, ext, uniq = link_stats(hosts, own)
            out.update(n_links=n, n_links_external=ext, link_hosts=uniq)
        return out


def run_sample(fetcher: Fetcher, limit: int = SAMPLE_CAP) -> SampleResult:
    """Fetch up to ``limit`` items; keep the source's own articles, drop and count the rest."""
    if limit > SAMPLE_CAP:
        raise ValueError(f"a sample holds at most {SAMPLE_CAP} articles per source; ask first")
    result = SampleResult(source_id=fetcher.source_id)
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0)
    seen_urls: set[str] = set()
    for item in fetcher.items(limit):
        result.seen += 1
        if item.url in seen_urls:
            result.dropped["duplicate"] += 1
            continue
        seen_urls.add(item.url)
        reason = fetcher.third_party_reason(item)
        if reason:
            result.dropped[f"third_party:{reason}"] += 1
            continue
        try:
            article = fetcher.build(item, retrieved_at)
        except ValueError as exc:
            result.dropped[f"invalid:{_short(exc)}"] += 1
            continue
        result.kept.append(article)
    result.raw_files = list(fetcher.raw.files)
    result.raw_bytes = sum((fetcher.raw.folder / f).stat().st_size for f in fetcher.raw.files)
    result.api_totals = dict(fetcher.api_totals)
    return result


def _short(exc: Exception) -> str:
    text = str(exc).splitlines()
    for line in text:
        if line.strip() and not line.startswith(("1 validation error", "  ")):
            return line.strip()[:60]
    return type(exc).__name__


def write_sample(result: SampleResult, path: Path) -> str:
    """Write the kept articles as JSON Lines; return the file's SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "".join(a.model_dump_json() + "\n" for a in result.kept).encode("utf-8")
    # Built rows are working data (data/interim), rebuilt from the raw answers when the code
    # changes; the raw answers themselves are never overwritten.
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def summary(result: SampleResult) -> dict[str, object]:
    """Counts only, no text: what was seen, kept and dropped, and why."""
    return {
        "source_id": result.source_id,
        "seen": result.seen,
        "kept": len(result.kept),
        "dropped": dict(sorted(result.dropped.items())),
        "raw_files": len(result.raw_files),
        "raw_bytes": result.raw_bytes,
        "api_totals": result.api_totals,
    }


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n"
