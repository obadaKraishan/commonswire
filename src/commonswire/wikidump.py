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
from html import unescape as html_unescape
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
#: Tags whose content is not article text: galleries, formulas, scores, and the JSON of maps
#: and charts (Kartographer's ``<mapframe>`` and ``<maplink>``, ``<graph>``).
_DROP_TAGS = re.compile(
    r"<(gallery|math|score|timeline|imagemap|syntaxhighlight|source|mapframe|maplink|graph|"
    r"chart|templatedata)\b[^>]*?(/>|>.*?</\1\s*>)",
    re.I | re.S,
)
_BR = re.compile(r"<br\s*/?\s*>", re.I)
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
#: Character references with their semicolon (``&mdash;``, ``&#8212;``, ``&#x2014;``).
_ENTITY = re.compile(r"&(#\d{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
_APOSTROPHES = re.compile(r"'{2,}")
#: A template or a link with no other template or link inside: expanded innermost first.
_INNER_TEMPLATE = re.compile(r"\{\{([^{}]*)\}\}")
_INNER_LINK = re.compile(r"\[\[((?:[^\[\]]|\[(?!\[)|\](?!\]))*)\]\]")
#: Common slips in the wikitext: a template on one line with its last brace missing
#: (``{{name|...}``); ``{[w|...}}``, ``{w|...}}`` or ``{w|...}`` for ``{{w|...}}`` (and the same
#: for ``{{wikt}}``); a link with one bracket missing at its end (``[[a|b]``) or at its start
#: (``[a|b]]``).
_SLIP_CLOSE = re.compile(r"(\{\{[^{}\n]{1,300}?)\}(?!\})")
_SLIP_OPEN = re.compile(r"(?<!\{)\{\[?(?=\s*(?:w|wikt)\s*\|[^{}\n]{1,200}?\}\})", re.I)
_SLIP_BOTH = re.compile(r"(?<!\{)\{\s*((?:w|wikt)\s*\|[^{}\n]{1,200}?)\}(?!\})", re.I)
#: ``{{w|...]]`` or ``[[w|...}}``: a {{w}} call closed or opened like a link.
_SLIP_W_AS_LINK_END = re.compile(r"\{\{\s*((?:w|wikt)\s*\|[^{}\[\]\n]{1,200}?)\]\]", re.I)
_SLIP_W_AS_LINK_START = re.compile(r"\[\[\s*((?:w|wikt)\s*\|[^{}\[\]\n]{1,200}?)\}\}", re.I)
_LINK_SHORT_END = re.compile(r"\[\[([^\[\]\n]{1,200})\](?!\])")
_LINK_SHORT_START = re.compile(r"(?<!\[)\[(?![\[/]|https?:)([^\[\]\n]{1,200})\]\]")
#: Lines left by a template or table that was never closed: ``| name = value``, ``|-``, ``|}``.
_PARAM_LINE = re.compile(r"^[ \t]*(\|[ \t]*[\w .-]{1,40}=.*|\|[-+}].*|\{\|.*|!.*\|.*)$", re.M)
_NAMED = re.compile(r"^\s*[A-Za-z][\w ]{0,30}=")
#: The name after a template opener that is never closed, up to a bar or the end of a line.
_UNCLOSED_TAIL = re.compile(r"[^|{}\[\]\n]{0,40}(?=\||\n|$)")


def _shown_link(pos: list[str]) -> str:
    """``{{w|target}}`` shows the target and ``{{w|target|label}}`` the label."""
    if len(pos) > 1 and pos[1].strip():
        return pos[1]
    return pos[0] if pos else ""


def _shown_translation(pos: list[str]) -> str:
    """``{{translated quote|code|language|original|translation}}`` shows the translation."""
    return f'"{pos[3].strip()}"' if len(pos) > 3 else ""


#: Templates that show words in the sentence, and how they render their positional params.
SHOWN_TEMPLATES = {
    "w": _shown_link,
    "wikt": _shown_link,
    "nowrap": lambda pos: pos[0] if pos else "",
    "translated quote": _shown_translation,
}


def _params(inner: str) -> tuple[str, list[str]]:
    """A template's name and its positional parameters (named ones such as ``nocat=`` are
    left out), split on bars that are not inside a link."""
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    i = 0
    while i < len(inner):
        if inner.startswith("[[", i):
            depth += 1
            cur.append("[[")
            i += 2
        elif depth and inner.startswith("]]", i):
            depth -= 1
            cur.append("]]")
            i += 2
        elif inner[i] == "|" and not depth:
            parts.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(inner[i])
            i += 1
    parts.append("".join(cur))
    name = parts[0].strip().lower().replace("_", " ")
    return name, [p for p in parts[1:] if not _NAMED.match(p)]


def _render_template(match: re.Match[str]) -> str:
    name, positional = _params(match.group(1))
    render = SHOWN_TEMPLATES.get(name)
    return render(positional) if render else ""


def _repair_slips(text: str) -> str:
    """Mend a missing brace in a template call (see the ``_SLIP_`` patterns)."""
    text = _SLIP_CLOSE.sub(r"\1}}", text)
    text = _SLIP_OPEN.sub("{{", text)
    text = _SLIP_BOTH.sub(r"{{\1}}", text)
    text = _SLIP_W_AS_LINK_END.sub(r"{{\1}}", text)
    return _SLIP_W_AS_LINK_START.sub(r"{{\1}}", text)


def _expand_templates(text: str) -> str:
    """Replace templates innermost first: the few that show words keep them, the rest go."""
    while True:
        new = _INNER_TEMPLATE.sub(_render_template, text)
        if new == text:
            return text
        text = new


def _remove_balanced(text: str, opener: str, closer: str) -> str:
    """Remove every balanced ``opener ... closer`` block, nested blocks included. An opener
    that is never closed is removed with its template name (or, for a table, the rest of its
    line), so it does not take the rest of the text with it."""
    spans: list[tuple[int, int]] = []
    stack: list[int] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(opener, i):
            stack.append(i)
            i += len(opener)
        elif stack and text.startswith(closer, i):
            start = stack.pop()
            i += len(closer)
            if not stack:
                spans.append((start, i))
        else:
            i += 1
    for s in stack:  # never closed: the opener goes with its name (or a table's attributes)
        m = _UNCLOSED_TAIL.match(text, s + len(opener)) if opener == "{{" else None
        end = m.end() if m else text.find("\n", s) if opener == "{|" else s + len(opener)
        spans.append((s, end if end > s else n))
    out: list[str] = []
    last = 0
    for s, e in sorted(spans):
        if s < last:
            continue
        out.append(text[last:s])
        last = e
    out.append(text[last:])
    return "".join(out)


def _render_link(match: re.Match[str]) -> str:
    target, _, label = match.group(1).partition("|")
    t = target.strip()
    if _FILE_LINK.match(t) and not _LINK_PREFIX.match(t):
        return ""  # a file, a category, or an interlanguage link: dropped
    # A label with more bars ("[[w:X|Label|]]") is a slip: its last non-empty part is shown.
    parts = [x for x in label.split("|") if x.strip()]
    return parts[-1] if parts else _LINK_PREFIX.sub("", t).split("#")[0]


def _replace_links(text: str) -> str:
    """``[[target|label]]`` -> label and ``[[target]]`` -> target, innermost first, so a
    file whose caption holds links is dropped whole; files, categories and interlanguage links
    are removed. A link with one bracket missing is still read as a link, and stray double
    brackets left over are removed."""
    while True:
        new = _INNER_LINK.sub(_render_link, text)
        if new == text:
            break
        text = new
    text = _LINK_SHORT_END.sub(_render_link, text)
    text = _LINK_SHORT_START.sub(_render_link, text)
    return text.replace("[[", "").replace("]]", "")


def _apostrophes(match: re.Match[str]) -> str:
    """Runs of apostrophes: two (italic), three (bold) and five (both) are markup; in a run
    of four, or of more than five, the extra apostrophes are real ones."""
    n = len(match.group())
    if n == 4:
        return "'"
    return "'" * (n - 5) if n > 5 else ""


def _entity(match: re.Match[str]) -> str:
    out = html_unescape(match.group())
    return " " if out == "\u00a0" else out


def wiki_to_text(wikitext: str) -> str:
    """Plain paragraphs from an article's wikitext, up to its closing sections."""
    text = _COMMENT.sub("", wikitext)
    match = CLOSING.search(text)
    if match:
        text = text[: match.start()]
    text = _REF.sub("", text)
    text = _DROP_TAGS.sub("", text)
    text = _repair_slips(text)
    text = _expand_templates(text)
    text = _remove_balanced(text, "{|", "|}")
    text = _expand_templates(text)
    text = _remove_balanced(text, "{{", "}}")
    text = text.replace("{{", "").replace("}}", "")
    text = _EXT_LINK.sub(lambda m: m.group(1) or "", text)
    text = _replace_links(text)
    text = _APOSTROPHES.sub(_apostrophes, text)
    text = _HEADING.sub(lambda m: m.group(2), text)
    text = _PARAM_LINE.sub("", text)
    text = _LIST.sub("", text)
    text = _MAGIC.sub("", text)
    text = _BR.sub("\n", text)
    text = _TAG.sub("", text)
    text = _ENTITY.sub(_entity, text)
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
    #: The page's wikitext, for the variables that need no model (categories, links).
    wikitext: str = ""


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
            wikitext=wikitext,
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
