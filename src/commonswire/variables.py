"""The variables that need no model, read from each article as its publisher gave it.

Series 0.3 adds these columns to every row (earlier series keep their columns):

- ``publisher_section``, ``publisher_categories``, ``publisher_tags``: the publisher's own
  labels, as it wrote them. A WordPress site's categories (its first one is the section) and
  tags; SciDev.Net's section label (its breadcrumb); Africa Is a Country's categories (its
  article header); Wikinews' categories (its wikitext). A label the saved answer does not
  carry is left empty, never guessed.
- ``n_links``, ``n_links_external`` and ``link_hosts``: the links in the article's body. A
  link counts when it leads to a web address: relative links are resolved against the
  article's own address; anchors on the same page (``#...``), ``mailto:``, ``tel:``,
  ``javascript:``, ``data:`` and ``sms:`` links, and addresses with no valid host, are not
  counted. A host is lower case, without ``www.``; it is external when it is neither the
  source's own host nor one of its subdomains. ``link_hosts`` lists every host once, sorted.
  For Wikinews the links come from its wikitext: internal links lead to its own host, the
  ``w:``, ``wikt:`` and ``commons:`` prefixes to Wikipedia, Wiktionary and Commons, external
  and bare links and ``url=`` parameters to their own hosts; category, file and
  interlanguage links are not counted. Counts are null when the body is not known.
- ``original_url``: for a translation, the address of the article it translates, when the
  page gives it (empty otherwise).
- ``language``: the source's language, except where the publisher labels each article's
  language itself (Factly's "Telugu" and "English" categories): then the label's.
"""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin, urlsplit

#: Link schemes that do not lead to a web page.
NOT_WEB = ("mailto:", "tel:", "javascript:", "data:", "sms:")
_HREF = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)
_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")

#: Sources whose own categories name each article's language (label, lower case -> code).
LANGUAGE_CATEGORIES: dict[str, dict[str, str]] = {"factly": {"telugu": "te", "english": "en"}}


def host_of(url: str) -> str | None:
    """The host of a web address, lower case and without ``www.``; None when there is none."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https"):
        return None
    host = (parts.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host if _HOST.match(host) else None


def html_link_hosts(html: str, base: str) -> list[str]:
    """The host of each counted link of an HTML body, in order (one per link)."""
    out = []
    for m in _HREF.finditer(html or ""):
        href = unescape(next(g for g in m.groups() if g is not None)).strip()
        if not href or href.startswith("#") or href.lower().startswith(NOT_WEB):
            continue
        try:
            given = urlsplit(href)
        except ValueError:
            continue
        if given.scheme and not given.netloc:
            continue  # a scheme with no host ("https://", "http:/x"): malformed
        try:
            host = host_of(urljoin(base, href))
        except ValueError:
            continue  # a malformed address (an unclosed "[", say) is not counted

        if host:
            out.append(host)
    return out


_WIKILINK = re.compile(r"\[\[([^\[\]|#]*)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
_EXTERNAL = re.compile(r"\[(https?://[^\s\]]+)[^\]]*\]")
_BARE = re.compile(r"(?<![\[=|\w/])(https?://[^\s\]\[<>|}{\"']+)")
_URL_PARAM = re.compile(r"\|\s*url\s*=\s*(https?://[^\s|}]+)", re.I)
_CATEGORY = re.compile(r"\[\[\s*Category\s*:\s*([^\]|]+)(?:\|[^\]]*)?\]\]", re.I)
#: Wikitext link prefixes that lead to another project.
WIKI_PREFIXES = {
    "w": "en.wikipedia.org",
    "wikipedia": "en.wikipedia.org",
    "wikt": "en.wiktionary.org",
    "wiktionary": "en.wiktionary.org",
    "commons": "commons.wikimedia.org",
}
#: Namespaces whose links are not links in the text.
WIKI_SKIP = {"category", "file", "image", "media", "template"}


def wiki_link_hosts(wikitext: str, own_host: str) -> list[str]:
    """The host of each counted link of a wikitext, in order."""
    out = []
    for m in _WIKILINK.finditer(wikitext or ""):
        target = m.group(1).strip().lstrip(":")
        prefix, _, _rest = target.partition(":")
        key = prefix.strip().lower()
        if ":" in target and key in WIKI_PREFIXES:
            out.append(WIKI_PREFIXES[key])
        elif ":" in target and (key in WIKI_SKIP or re.fullmatch(r"[a-z]{2,3}(-[a-z]+)?", key)):
            continue  # a category, a file or an interlanguage link
        elif target:
            out.append(own_host)
    for rx in (_EXTERNAL, _URL_PARAM, _BARE):
        for m in rx.finditer(wikitext or ""):
            host = host_of(m.group(1))
            if host:
                out.append(host)
    return out


def wiki_categories(wikitext: str) -> list[str]:
    """The categories a wikitext names, as written, each once, in order."""
    seen: list[str] = []
    for m in _CATEGORY.finditer(wikitext or ""):
        name = re.sub(r"\s+", " ", m.group(1).replace("_", " ")).strip()
        if name and name not in seen:
            seen.append(name)
    return seen


def link_stats(hosts: list[str], own_host: str) -> tuple[int, int, tuple[str, ...]]:
    """The links counted, the external ones among them, and every host once, sorted."""
    own = (host_of(f"https://{own_host}") or own_host).lower()
    external = sum(1 for h in hosts if h != own and not h.endswith("." + own))
    return len(hosts), external, tuple(sorted(set(hosts)))


def row_language(source_id: str, categories: tuple[str, ...] | list[str], default: str) -> str:
    """The language of a row: the publisher's own language label where it gives one."""
    labels = LANGUAGE_CATEGORIES.get(source_id, {})
    found = {labels[c.strip().lower()] for c in categories if c.strip().lower() in labels}
    if len(found) == 1:
        return found.pop()
    if len(found) > 1 and "en" in found:
        found.discard("en")  # an article filed under English and another language
        if len(found) == 1:
            return found.pop()
    return default
