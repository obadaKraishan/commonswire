"""HTML to plain text, with the standard library only.

Two uses:

- :func:`page_text` keeps every visible block of a page, including navigation and footers,
  because license and terms statements often sit in a footer. It is used to read evidence
  pages.
- :func:`article_text` turns an article body (already cut out of its page by a source's API)
  into paragraphs, dropping photos, captions, video, audio, embeds, scripts and any element
  whose class or id matches a source's boilerplate list. The words are never changed: only
  whitespace inside a paragraph is collapsed.

:func:`links` lists the links of a page with their text, for finding policy pages.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from html import unescape
from html.parser import HTMLParser

#: Elements whose content is never text.
NEVER_TEXT = frozenset(
    {"script", "style", "noscript", "template", "svg", "math", "head", "title", "iframe"}
)
#: Media and embeds, dropped from article bodies along with everything inside them.
MEDIA = frozenset(
    {
        "figure",
        "figcaption",
        "img",
        "picture",
        "video",
        "audio",
        "source",
        "track",
        "object",
        "embed",
        "canvas",
        "map",
        "form",
        "button",
        "input",
        "select",
        "textarea",
    }
)
#: Page furniture, dropped from article bodies.
FURNITURE = frozenset({"nav", "aside", "footer", "header"})
BLOCK = frozenset(
    {
        "p",
        "div",
        "section",
        "article",
        "main",
        "br",
        "li",
        "ul",
        "ol",
        "dl",
        "dt",
        "dd",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "table",
        "tr",
        "td",
        "th",
        "hr",
        "address",
        "center",
        "footer",
        "header",
        "nav",
        "aside",
        "figure",
        "figcaption",
        "summary",
        "details",
    }
)
VOID = frozenset(
    {"br", "img", "hr", "input", "meta", "link", "source", "track", "embed", "area", "col", "wbr"}
)

_SPACE = re.compile("[ \\t\\r\\f\\v\u00a0\u200b]+")


class _TextParser(HTMLParser):
    def __init__(self, drop: frozenset[str], drop_classes: tuple[str, ...]) -> None:
        super().__init__(convert_charrefs=True)
        self.drop = drop
        self.drop_classes = tuple(c.lower() for c in drop_classes)
        self.blocks: list[str] = []
        self.current: list[str] = []
        self.skip_stack: list[str] = []

    def _flush(self) -> None:
        text = _SPACE.sub(" ", "".join(self.current)).strip()
        if text:
            self.blocks.append(text)
        self.current = []

    def _drops(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        if tag in self.drop:
            return True
        if not self.drop_classes:
            return False
        names = " ".join(
            (value or "") for key, value in attrs if key in ("class", "id", "role")
        ).lower()
        return any(c in names.split() or c in names for c in self.drop_classes)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_stack:
            if tag not in VOID:
                self.skip_stack.append(tag)
            return
        if self._drops(tag, attrs):
            if tag in BLOCK:
                self._flush()
            if tag not in VOID:
                self.skip_stack.append(tag)
            return
        if tag in BLOCK:
            self._flush()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.skip_stack and tag in BLOCK:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack:
            # Close up to the matching open tag, so sloppy HTML cannot leave us skipping forever.
            if tag in self.skip_stack:
                while self.skip_stack:
                    if self.skip_stack.pop() == tag:
                        break
            return
        if tag in BLOCK:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self.skip_stack:
            self.current.append(data.replace("\n", " "))

    def close(self) -> None:
        super().close()
        self._flush()


def _blocks(html: str, drop: frozenset[str], drop_classes: Iterable[str] = ()) -> list[str]:
    parser = _TextParser(drop, tuple(drop_classes))
    parser.feed(html)
    parser.close()
    return parser.blocks


def page_text(html: str) -> str:
    """Every visible block of a page, one per line."""
    return "\n".join(_blocks(html, NEVER_TEXT))


def article_text(html: str, drop_classes: Iterable[str] = ()) -> str:
    """An article body as paragraphs separated by a blank line, without media or furniture."""
    return "\n\n".join(_blocks(html, NEVER_TEXT | MEDIA | FURNITURE, drop_classes))


def strip_tags(html: str) -> str:
    """Inline HTML (a title or an excerpt) as one line of text."""
    return _SPACE.sub(" ", " ".join(_blocks(html, NEVER_TEXT))).strip()


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []
        elif tag == "link" and self._href is None:
            a = dict(attrs)
            if (a.get("rel") or "").lower() == "license" and a.get("href"):
                self.links.append((a["href"] or "", "rel=license"))

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = _SPACE.sub(" ", " ".join(self._text)).strip()
            self.links.append((unescape(self._href), text))
            self._href = None


def links(html: str) -> list[tuple[str, str]]:
    """The page's links as (href, link text) pairs, in page order."""
    parser = _LinkParser()
    parser.feed(html)
    parser.close()
    return parser.links


_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][a-zA-Z0-9-]*(\s[^<>]*)?/?\s*>")


def has_markup(text: str) -> bool:
    """True if the text still holds an HTML tag."""
    return bool(_TAG.search(text))


def element_html(html: str, cls: str, tag: str | None = None) -> str | None:
    """The outer HTML of the first element whose class list holds ``cls`` (and whose tag is
    ``tag``, when given), nested elements of the same tag included; None when there is none.
    Used to cut an article's body or byline block out of a whole page."""
    start = re.compile(
        rf"""<({tag or r"[a-zA-Z][a-zA-Z0-9]*"})\b[^>]*\bclass\s*=\s*["']([^"']*)["'][^>]*>"""
    )
    for m in start.finditer(html):
        if cls not in m.group(2).split():
            continue
        name = m.group(1).lower()
        depth = 0
        for t in re.finditer(rf"<(/?){name}\b[^>]*?(/?)>", html[m.start() :], re.I):
            if t.group(2):  # <div/>: opens and closes
                continue
            depth += -1 if t.group(1) else 1
            if depth == 0:
                return html[m.start() : m.start() + t.end()]
        return html[m.start() :]
    return None
