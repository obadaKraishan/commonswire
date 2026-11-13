"""The Wikinews dump: one polite download, then a streaming reader of published articles.

Wikinews closed on 2026-05-04; its robots.txt closes the MediaWiki API (``/w/``) to general user
agents, and the archive is read from the dump on dumps.wikimedia.org instead
(``enwikinews-latest-pages-articles.xml.bz2``, about 48 MB).

:func:`read_dump` streams the bz2 XML and yields published articles only: main namespace, not
a redirect, marked published (``{{publish}}`` or ``{{archive}}``) and not also marked as a
draft, under review or abandoned, with a ``{{date|...}}``. Every page that is skipped is
counted by reason. :func:`wiki_to_text` strips wiki markup to plain paragraphs and stops at the
closing sections (Sources, Related news, External links, Sister links).
"""

from __future__ import annotations

import bz2
import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from urllib.parse import quote

DUMP_URL = "https://dumps.wikimedia.org/enwikinews/latest/enwikinews-latest-pages-articles.xml.bz2"
MD5_URL = "https://dumps.wikimedia.org/enwikinews/latest/enwikinews-latest-md5sums.txt"
DUMP_NAME = "enwikinews-latest-pages-articles.xml.bz2"
ARTICLE_URL = "https://en.wikinews.org/wiki/"

PUBLISHED = re.compile(r"\{\{\s*(publish|published|archive|archived)\s*[|}]", re.I)
NOT_PUBLISHED = re.compile(
    r"\{\{\s*(develop|developing|review|under review|abandoned|tasks|delete|"
    r"prepared|minimal)\s*[|}]",
    re.I,
)
DATE = re.compile(r"\{\{\s*date\s*\|\s*([^}|]+?)\s*[|}]", re.I)
CLOSING = re.compile(
    r"^\s*==+\s*(Sources?|Related (news|articles|stories)|External links|Sister links|"
    r"See also|References)\s*==+\s*$",
    re.I | re.M,
)
_REF = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", re.I | re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_DROP_TAGS = re.compile(
    r"<(gallery|math|score|timeline|imagemap|syntaxhighlight|source)[^>]*>.*?</\1>", re.I | re.S
)
_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
_FILE_LINK = re.compile(
    r"^(file|image|media|category|template|wikinews|user|talk|special|portal|help|"
    r"[a-z]{2,3}(-[a-z]+)?):",
    re.I,
)
_LINK_PREFIX = re.compile(r"^:?(w|wikipedia|wikt|wiktionary|commons|n|s|b|q|v|voy):", re.I)
_EXT_LINK = re.compile(r"\[(?:https?:)?//[^\s\]]+(?:\s+([^\]]*))?\]")
_HEADING = re.compile(r"^\s*(=+)\s*(.*?)\s*\1\s*$", re.M)
_LIST = re.compile(r"^[*#:;]+\s*", re.M)
_MAGIC = re.compile(r"__[A-Z]+__")
_SPACES = re.compile(r"[ \t]+")


def _remove_balanced(text: str, opener: str, closer: str) -> str:
    """Remove every balanced ``opener ... closer`` block, nested blocks included."""
    out: list[str] = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(opener, i):
            depth += 1
            i += len(opener)
        elif depth and text.startswith(closer, i):
            depth -= 1
            i += len(closer)
        else:
            if not depth:
                out.append(text[i])
            i += 1
    return "".join(out)


def _replace_links(text: str) -> str:
    """``[[target|label]]`` -> label, ``[[target]]`` -> target; files, categories and
    interlanguage links are removed."""
    out: list[str] = []
    i = 0
    while True:
        start = text.find("[[", i)
        if start < 0:
            out.append(text[i:])
            break
        out.append(text[i:start])
        depth = 0
        j = start
        while j < len(text):
            if text.startswith("[[", j):
                depth += 1
                j += 2
            elif text.startswith("]]", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        inner = text[start + 2 : j - 2]
        target, _, label = inner.partition("|")
        if _FILE_LINK.match(target.strip()) and not _LINK_PREFIX.match(target.strip()):
            pass  # a file, a category, or an interlanguage link: dropped
        else:
            shown = label if label else _LINK_PREFIX.sub("", target).split("#")[0]
            out.append(shown)
        i = j
    return "".join(out)


def wiki_to_text(wikitext: str) -> str:
    """Plain paragraphs from an article's wikitext, up to its closing sections."""
    text = _COMMENT.sub("", wikitext)
    match = CLOSING.search(text)
    if match:
        text = text[: match.start()]
    text = _REF.sub("", text)
    text = _DROP_TAGS.sub("", text)
    text = _remove_balanced(text, "{|", "|}")
    text = _remove_balanced(text, "{{", "}}")
    text = _replace_links(text)
    text = _EXT_LINK.sub(lambda m: m.group(1) or "", text)
    text = text.replace("'''", "").replace("''", "")
    text = _HEADING.sub(lambda m: m.group(2), text)
    text = _LIST.sub("", text)
    text = _MAGIC.sub("", text)
    text = _TAG.sub("", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )
    paragraphs = []
    for block in re.split(r"\n\s*\n|\n", text):
        block = _SPACES.sub(" ", block).strip()
        if block:
            paragraphs.append(block)
    return "\n\n".join(paragraphs)


def parse_date(value: str) -> datetime | None:
    value = re.sub(r"\s+", " ", value.strip())
    for fmt in ("%B %d, %Y", "%d %B %Y", "%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt).replace(hour=12, tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class DumpArticle:
    title: str
    url: str
    published_at: datetime
    last_edit: datetime | None
    text: str


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_dump(stream: BinaryIO, skipped: Counter[str]) -> Iterator[DumpArticle]:
    """Published Wikinews articles from a ``pages-articles`` XML stream (bz2 already opened)."""
    context = ET.iterparse(stream, events=("end",))
    for _event, elem in context:
        if _local(elem.tag) != "page":
            continue
        fields: dict[str, str] = {}
        redirect = False
        for child in elem.iter():
            name = _local(child.tag)
            if name in ("title", "ns", "text", "timestamp") and name not in fields:
                fields[name] = child.text or ""
            elif name == "redirect":
                redirect = True
        elem.clear()
        if fields.get("ns") != "0":
            skipped["not_an_article_namespace"] += 1
            continue
        if redirect:
            skipped["redirect"] += 1
            continue
        wikitext = fields.get("text", "")
        if not PUBLISHED.search(wikitext):
            skipped["not_marked_published"] += 1
            continue
        if NOT_PUBLISHED.search(wikitext):
            skipped["marked_draft_review_or_abandoned"] += 1
            continue
        m = DATE.search(wikitext)
        published = parse_date(m.group(1)) if m else None
        if published is None:
            skipped["no_date"] += 1
            continue
        text = wiki_to_text(wikitext)
        if not text.strip():
            skipped["empty_text"] += 1
            continue
        title = fields.get("title", "")
        stamp = fields.get("timestamp", "")
        last_edit = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
        if last_edit is not None and last_edit < published:
            last_edit = None
        yield DumpArticle(
            title=title,
            url=ARTICLE_URL + quote(title.replace(" ", "_"), safe="_(),'!:"),
            published_at=published,
            last_edit=last_edit,
            text=text,
        )


def open_dump(path: Path) -> BinaryIO:
    return bz2.open(path, "rb")  # type: ignore[return-value]


def md5_of(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_md5(md5sums: str, name: str = DUMP_NAME) -> str | None:
    """The md5 the dump's own md5sums file gives for ``name`` (the ``latest`` alias resolved)."""
    suffix = name.replace("enwikinews-latest-", "")
    for line in md5sums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].endswith(suffix):
            return parts[0]
    return None
