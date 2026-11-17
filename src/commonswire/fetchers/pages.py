"""Sources read from their article pages (saved once by ``commonswire backfill-pages``).

Each fetcher turns one saved page into an :class:`~commonswire.fetchers.base.Item` with no
request: the title, the dates, the byline as the page states it, the body and the hints that
spot third-party material. Rows are then built by the base class, so the credit line and the
held-byline rule are the same as for every other source.

- **SciDev.Net** (CC BY 2.0). The byline is the page's "By:" heading and the names linked in
  it; its JSON-LD ``author`` names the account that posted, never read. Its republishing box
  says "You have to credit our authors", so a page with no byline is held. The body is the
  post-content module; the closing "© SciDev.Net" line is the source's own. Pages that say
  they were first published elsewhere, or carry another holder's copyright line, are dropped.
  A page of any section is kept only when it carries the site's license line and names no
  other holder (no Creative Commons link in the body outside an image's caption); its
  "Supported content" pages (the breadcrumb's label; most name a funder) also need
  SciDev.Net's own byline (every name linked to one of its author pages). Any other page is
  left out as third-party or sponsored material. Two legacy forms in its older bodies are
  cleaned first: angle brackets printed around a link's label, and escaped markup shown as
  text (a player's embed code).
- **Africa Is a Country** (CC BY 4.0). The byline is the header's author list; the date is
  the header's ``MM.DD.YYYY`` (no time is given: rows take 00:00 UTC). Its license names no
  author requirement, so a page with no byline is credited to the source. Pieces that say
  they first appeared elsewhere are dropped.
"""

from __future__ import annotations

import json
import re
from abc import abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlsplit

from commonswire.fetchers.base import Fetcher, Item
from commonswire.html import article_text, element_html
from commonswire.pagebylines import is_person

_TAGS = re.compile(r"<[^>]+>")
_LD = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)
#: Words that say a piece was published somewhere else first.
ELSEWHERE = re.compile(
    r"\b(?:originally|first) (?:published|appeared|ran)\b|\brepublished (?:from|with)\b"
    r"|\breprinted (?:from|with)\b|\breproduced (?:from|with|here|by kind)\b"
    r"|\bexcerpted from\b|\bco-published (?:with|by)\b",
    re.I,
)


#: How a republication note opens ("This essay first appeared in ...", "A version of this ...").
NOTE_OPENING = re.compile(
    r"^(?:this|it|an? (?:earlier |shorter |longer |edited |abridged |different )?version)\b", re.I
)


def published_elsewhere(text: str) -> bool:
    """Whether the article says it was published somewhere else first. Only a note counts:
    in the first paragraph or the last three, short or opening like a note, so a sentence
    such as "the novel first appeared in 1958" in the middle of an essay does not."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    edges = paras[:1] + paras[1:][-3:]
    for para in edges:
        for m in ELSEWHERE.finditer(para):
            sentence = re.split(r"(?<=[.!?])\s+", para[: m.start()])[-1].lstrip("*_([ ")
            if len(para) < 400 or NOTE_OPENING.match(sentence):
                return True
    return False


#: Words that mark a line as an image's credit.
IMAGE_CREDIT = re.compile(r"\b(?:image|photo|picture|credit|illustration)s?\b", re.I)
#: Words (or photo sites) that mark the block around a license link as an image's credit.
IMAGE_BLOCK = re.compile(
    r"image|photo|picture|credit|illustration|flickr|wikimedia|pexels|unsplash", re.I
)
_CC_LINK = re.compile(r"creativecommons\.org/licenses/", re.I)
_BLOCK_OPEN = re.compile(r"<(?:p|div|figcaption|li|td|blockquote|h[1-6])\b[^>]*>", re.I)


#: Angle brackets printed around a link, escaped or literal (``&lt;<a ...>label</a>&gt;`` or
#: ``<<a ...>label</a>>``).
_BRACKETED_LINK = re.compile(r"(?:&lt;|<)\s*(<a\b[^>]*>.*?</a>)\s*(?:&gt;|>)", re.S | re.I)
#: Two or more escaped tags in a row: markup shown as text (a player's embed code).
_ESCAPED_MARKUP = re.compile(r"(?:&lt;/?[a-z][^<>]*?&gt;\s*){2,}", re.S | re.I)


def clean_legacy_body(body: str) -> str:
    """SciDev.Net's older bodies: the brackets printed around a link's label are dropped (the
    link stays), and markup shown as text (two or more escaped tags in a row, such as an embed
    code) is removed."""
    return _ESCAPED_MARKUP.sub("", _BRACKETED_LINK.sub(r"\1", body))


def licenses_outside_captions(body: str) -> int:
    """Creative Commons license links in an article body that are not an image's credit: the
    block that holds the link is no caption (``figcaption``, a ``wp-caption`` class, inside a
    ``<figure>``) and names no image or photo site before the link."""
    n = 0
    for m in _CC_LINK.finditer(body):
        before = body[max(0, m.start() - 600) : m.start()]
        opens = list(_BLOCK_OPEN.finditer(before))
        block = before[opens[-1].start() :] if opens else before
        in_figure = before.rfind("<figure") > before.rfind("</figure")
        if in_figure or re.search(r"caption", block, re.I):
            continue
        if IMAGE_BLOCK.search(_TAGS.sub(" ", block)):
            continue
        n += 1
    return n


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(_TAGS.sub(" ", fragment))).strip()


def _meta(html: str, prop: str) -> str:
    m = re.search(
        rf"""<meta\s+(?:property|name)=["']{re.escape(prop)}["']\s+content=["']([^"']*)["']""",
        html,
        re.I,
    )
    return unescape(m.group(1)).strip() if m else ""


def jsonld_nodes(html: str) -> list[dict]:
    """Every JSON-LD node of the page (``@graph`` members included)."""
    out: list[dict] = []
    for block in _LD.findall(html):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for node in data.get("@graph", [data]) if isinstance(data, dict) else data:
            if isinstance(node, dict):
                out.append(node)
    return out


def _aware(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None


class PageFetcher(Fetcher):
    """A source whose rows come from saved article pages (no API)."""

    def items(self, limit: int) -> Iterator[Item]:
        raise NotImplementedError(
            f"{self.source_id} is read from saved pages: run commonswire backfill-pages, then "
            "commonswire build"
        )

    @abstractmethod
    def item_from_page(self, url: str, html: str) -> Item:
        """One saved page as an item; raises ValueError when the page has no article."""

    def names(self, raw: list[str]) -> tuple[tuple[str, ...], bool]:
        """The persons among a byline's names, and whether the byline names only the source."""
        names = [n for n in (_text(x) for x in raw) if n]
        people = tuple(n for n in names if is_person(n, self.source.name))
        itself = (
            bool(names)
            and not people
            and all(n.casefold() == self.source.name.casefold() for n in names)
        )
        return people, itself


class SciDevNetFetcher(PageFetcher):
    source_id = "scidevnet"
    requires_byline = True
    own_notes = (r"(?m)^©\s*SciDev\.Net\b[^\n]*$",)
    #: The line every page of the site carries (its footer), linked to the media page.
    LICENSE_LINE = (
        "All site content, except where otherwise noted, is licensed under a Creative Commons "
        "Attribution License"
    )
    #: A byline link to one of the site's own author pages (three address forms).
    OWN_AUTHOR_PAGE = re.compile(
        r"^(?:https://www\.scidev\.net)?/global/(?:author|\?post_type=author)", re.I
    )
    SUPPORTED = "supported-content"

    def item_from_page(self, url: str, html: str) -> Item:
        nodes = jsonld_nodes(html)
        article = next((n for n in nodes if n.get("@type") == "Article"), {})
        title = unescape(str(article.get("headline") or _meta(html, "og:title"))).strip()
        published = next((d for n in nodes if (d := _aware(str(n.get("datePublished", ""))))), None)
        updated = next((d for n in nodes if (d := _aware(str(n.get("dateModified", ""))))), None)
        if not title or published is None:
            raise ValueError("no title or no dated JSON-LD: not an article page")
        body = element_html(html, "fl-module-fl-post-content")
        if not body:
            raise ValueError("no post-content module: not an article page")
        body = clean_legacy_body(body)
        raw_names: list[str] = []
        targets: list[str] = []
        for h4 in re.findall(r"<h4\b[^>]*>(.*?)</h4>", html, re.S | re.I):
            label = _text(re.sub(r"<a\b.*?</a>", "", h4, flags=re.S | re.I))
            links = re.findall(r"<a\b([^>]*)>(.*?)</a>", h4, re.S | re.I)
            if links and label.lower().rstrip(": ").startswith("by"):
                raw_names = [inner for _attrs, inner in links]
                for attrs, _inner in links:
                    href = re.search(r"""href\s*=\s*["']([^"']*)["']""", attrs, re.I)
                    targets.append(unescape(href.group(1)).strip() if href else "")
                break
        authors, itself = self.names(raw_names)
        text = article_text(body, self.drop_classes + self.embed_classes)
        # A paragraph that is a copyright line naming someone else, unless it credits an image
        # (photos are never collected, and their credits are not the article's).
        holders = [
            para
            for para in (x.strip() for x in text.split("\n\n"))
            if para.startswith("©")
            and "scidev" not in para.lower()
            and not IMAGE_CREDIT.search(para)
        ]
        parts = urlsplit(url).path.strip("/").split("/")
        crumb = re.search(r'<span class="breadcrumb_last"[^>]*>(.*?)</span>', html, re.S | re.I)
        return Item(
            url=url,
            title=title,
            body_html=body,
            published_at=published,
            updated_at=updated if updated and updated >= published else None,
            language="en",
            authors=authors,
            section=parts[1] if len(parts) > 2 else "",
            hints={
                "byline_is_source": itself,
                "other_holders": holders,
                "elsewhere": published_elsewhere(text),
                "byline_own": bool(targets) and all(self.OWN_AUTHOR_PAGE.match(t) for t in targets),
                "license_line": self.LICENSE_LINE in _text(html),
                "other_licenses": licenses_outside_captions(body),
                # The section's label as the site prints it (its breadcrumb).
                "publisher_section": _text(crumb.group(1)) if crumb else "",
            },
        )

    def third_party_reason(self, item: Item) -> str | None:
        if item.hints.get("other_holders"):
            return "another holder's copyright line"
        if item.hints.get("elsewhere"):
            return "says it was published elsewhere first"
        if item.section == self.SUPPORTED and (
            not item.authors or not item.hints.get("byline_own")
        ):
            return "supported content without a byline of its own"
        if not item.hints.get("license_line"):
            return "no site license line on the page"
        if item.hints.get("other_licenses"):
            return "another license named outside an image's caption"
        return None


class AfricaIsACountryFetcher(PageFetcher):
    source_id = "africasacountry"

    def item_from_page(self, url: str, html: str) -> Item:
        head = element_html(html, "po-hr") or ""
        title_el = element_html(head, "po-hr-cn__title")
        title = _text(title_el) if title_el else _meta(html, "og:title")
        date_el = element_html(head, "po-hr-fl__date")
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", _text(date_el) if date_el else "")
        body = element_html(html, "po-bo__content")
        if not title or not m or not body:
            raise ValueError("no title, date or body: not an article page")
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        path = re.match(r"^/(\d{4})/(\d{2})/", urlsplit(url).path)
        if path and (int(path.group(1)), int(path.group(2))) != (year, month):
            raise ValueError("the page's date does not match the year and month in its address")
        published = datetime(year, month, day, tzinfo=timezone.utc)
        block = element_html(head, "po-hr-cn__authors") or ""
        raw = re.findall(
            r"""<a\b[^>]*class=["'][^"']*po-hr-cn__author-link[^"']*["'][^>]*>(.*?)</a>""",
            block,
            re.S | re.I,
        )
        authors, itself = self.names(raw)
        # The article's categories, as its header links them.
        categories = list(
            dict.fromkeys(
                c
                for c in (
                    _text(x)
                    for x in re.findall(
                        r"""<a\b[^>]*href=["'][^"']*/category/[^"']*["'][^>]*>(.*?)</a>""",
                        head,
                        re.S | re.I,
                    )
                )
                if c
            )
        )
        return Item(
            url=url,
            title=title,
            body_html=body,
            published_at=published,
            language="en",
            authors=authors,
            hints={
                "categories": categories,
                "byline_is_source": itself,
                "elsewhere": published_elsewhere(article_text(body, self.embed_classes)),
            },
        )

    def third_party_reason(self, item: Item) -> str | None:
        if item.hints.get("elsewhere"):
            return "says it was published elsewhere first"
        return None


PAGE_FETCHERS: dict[str, type[PageFetcher]] = {
    cls.source_id: cls for cls in (SciDevNetFetcher, AfricaIsACountryFetcher)
}
