"""Bylines from article pages, for sources whose API gives no author names.

Some sources ask for the author's name in the credit line but give no names through their API
(a closed users endpoint, or one shared account for every post). For their rows that have no
byline, the article page is fetched once through the polite client and saved unchanged under
``data/raw/pages/<source>/``, and the author's name is read from the page's own byline markup
or metadata only, in this order:

1. **the source's byline block** (:data:`SITE_MARKUP`): the first element of the article's
   meta block that holds the byline, and the names in it (links or bold names), so bylines of
   related posts elsewhere on the page are never taken;
2. **structured data:** ``author`` entries of type ``Person`` in JSON-LD blocks;
3. **meta tags:** ``<meta name="author">`` and Yoast's "Written by" pair
   (``twitter:label1`` and ``twitter:data1``).

The first of these that names a person wins, with two limits. When the page has the source's
byline block, only that block counts: a page whose visible byline credits the source itself is
not given a name from its metadata. And a source whose metadata names the account that posted
the article rather than its writer (``metadata_fallback=False``) is read from its byline block
only. A name that is the source's own name or an account such as "admin" or "editorial team"
names no person, and the reason is counted. When the visible byline block names the source
itself and nothing else (``why_none`` is ``source_itself``), that is the page's own word: the
row is released with no personal author, and its credit line names the source (maintainer's
decision, 2026-11-13). Any other page with no person stays held. Names are never inferred
from the body text.

The names found are kept in ``data/interim/bylines/<source>.pages.json`` (canonical URL ->
names); only counts go into the tracked evidence. ``commonswire build`` and ``commonswire
daily`` read the names into the rows.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from commonswire.backfill import save_once
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient
from commonswire.schema import canonical_url


@dataclass(frozen=True)
class BylineMarkup:
    """Where a source's theme puts the article's byline.

    ``container`` is the set of class names the byline element carries, ``within`` a class name
    one of its ancestors carries (the article's meta block), and ``name_tag`` the tag of each
    name inside it. Only the first matching element on the page is read. With
    ``metadata_fallback`` False, a page without the block gets no name from JSON-LD or meta tags.
    """

    container: frozenset[str]
    within: str = ""
    name_tag: str = "a"
    metadata_fallback: bool = True


#: The byline block of each source whose article pages are read for bylines.
SITE_MARKUP: dict[str, BylineMarkup] = {
    # <div class="entry-meta"><span class="byline"><span>by</span> <span class="author vcard">
    # <a class="url fn n" href=".../author/...">NAME</a></span></span>
    "thepublicrecord": BylineMarkup(frozenset({"byline"}), within="entry-meta", name_tag="a"),
    # <div class="single-meta ..."><p class="byline author vcard ..."><a href="/en/profile/...">
    # NAME</a> | <a ...>NAME</a></p>; related posts use the same class in "card-footer".
    # Its JSON-LD author is the account that posted the article: on pages with a byline it
    # differs from that byline almost every time, so it is never used.
    "balkandiskurs": BylineMarkup(
        frozenset({"byline", "vcard"}), within="single-meta", name_tag="a", metadata_fallback=False
    ),
    # <div class="post-meta-authors"><div class="post-authors"><span>Authors</span>
    # <strong>NAME</strong><br>AFFILIATION ...; the editors are in "post-meta-editors".
    "360info": BylineMarkup(frozenset({"post-meta-authors"}), name_tag="strong"),
}

#: Account names that stand for an organization or a role, not a person.
NOT_A_PERSON = re.compile(
    r"^(admin(istrator)?|editor(s|ial)?( (team|board|desk|staff))?|editorial|staff"
    r"( (writer|reporter)s?)?|team|newsroom|news ?desk|desk|redakcija|redakcia|redazione|"
    r"r[eé]daction|guest( (author|writer|contributor))?|contributors?|web ?master|"
    r"web ?team|authors?|unknown|anonymous|n/?a|none)$",
    re.I,
)
_SPACE = re.compile(r"\s+")
_SPLIT = re.compile(r"\s*,\s*|\s+and\s+|\s*&\s*|\s*\|\s*")
_BY = re.compile(r"^\s*(by|written by)\s*:?\s+", re.I)
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


def page_file(folder: Path, url: str) -> Path:
    """Where the page of a URL is saved: the first 20 hex digits of the SHA-256 of its
    canonical form, so a page is saved once whatever form of its URL a row carries."""
    digest = hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()
    return folder / f"{digest[:20]}.html"


def _clean(name: str) -> str:
    return _SPACE.sub(" ", unescape(name)).strip(" \t\n|\u00b7\u2013\u2014,-")


def split_names(value: str) -> tuple[str, ...]:
    """A byline string as names: "By A, B and C" -> ("A", "B", "C")."""
    value = _BY.sub("", _clean(value))
    return tuple(p for p in (_clean(x) for x in _SPLIT.split(value)) if p)


class _PageParser(HTMLParser):
    """Collects the JSON-LD blocks, the meta tags and the names in the site's byline block."""

    def __init__(self, markup: BylineMarkup | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.markup = markup
        self.jsonld: list[str] = []
        self.meta: dict[str, str] = {}
        self.site_names: list[str] = []
        self.site_block_found = False
        self._script: list[str] | None = None
        self._stack: list[tuple[str, frozenset[str]]] = []
        self._block_depth: int | None = None  # stack depth of the byline block while inside
        self._name: list[str] | None = None
        self._name_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            if a.get("type", "").lower() == "application/ld+json":
                self._script = []
            return
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key and key not in self.meta:
                self.meta[key] = a.get("content", "")
            return
        if tag in _VOID:
            return
        classes = frozenset(a.get("class", "").split())
        self._stack.append((tag, classes))
        m = self.markup
        if m is None:
            return
        if self._block_depth is None and not self.site_block_found:
            if m.container <= classes and (
                not m.within or any(m.within in c for _, c in self._stack[:-1])
            ):
                self._block_depth = len(self._stack)
                self.site_block_found = True
        elif self._block_depth is not None and tag == m.name_tag and self._name is None:
            self._name = []
            self._name_depth = len(self._stack)

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script.append(data)
        elif self._name is not None:
            self._name.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self._script is not None:
                self.jsonld.append("".join(self._script))
            self._script = None
            return
        if tag in _VOID or not any(t == tag for t, _ in self._stack):
            return  # a stray end tag
        while self._stack:
            top, _ = self._stack.pop()
            depth = len(self._stack) + 1
            if self._name is not None and depth <= self._name_depth:
                value = _clean(" ".join(self._name))
                if value:
                    self.site_names.append(value)
                self._name = None
            if self._block_depth is not None and depth <= self._block_depth:
                self._block_depth = None
            if top == tag:
                break


def _jsonld_authors(blocks: Iterable[str]) -> tuple[list[str], list[str]]:
    """The author names in JSON-LD: (people, other authors such as organizations)."""
    people: list[str] = []
    others: list[str] = []
    by_id: dict[str, dict] = {}
    with_author: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            if isinstance(node.get("@id"), str):
                by_id.setdefault(node["@id"], node)
            if "author" in node:
                with_author.append(node)
            if "@graph" in node:
                walk(node["@graph"])

    for block in blocks:
        try:
            walk(json.loads(block))
        except ValueError:
            continue
    for node in with_author:
        authors = node["author"] if isinstance(node["author"], list) else [node["author"]]
        for author in authors:
            if isinstance(author, dict) and set(author) <= {"@id"} and author.get("@id"):
                author = by_id.get(author["@id"], author)
            if isinstance(author, str):
                others.append(_clean(author))
                continue
            if not isinstance(author, dict) or not isinstance(author.get("name"), str):
                continue
            kind = author.get("@type", "Person")
            kinds = kind if isinstance(kind, list) else [kind]
            (people if "Person" in kinds else others).append(_clean(author["name"]))
    return people, others


@dataclass(frozen=True)
class PageByline:
    """The byline read from one page: the names, where they came from, or why none."""

    names: tuple[str, ...]
    route: str  # site, jsonld, meta, twitter, or "" when none
    why_none: str = ""  # no_byline, not_a_person, source_itself, or ""
    #: Whether the JSON-LD people agree with the site's byline block (None: nothing to compare).
    jsonld_agrees: bool | None = None


def is_person(name: str, source_name: str = "") -> bool:
    """False for a name that is the source's own, an account such as "admin", or no name."""
    low = name.lower().strip()
    if not low or NOT_A_PERSON.match(low):
        return False
    if source_name and low == source_name.lower().strip():
        return False
    return any(ch.isalpha() for ch in name) and len(name) <= 80


def byline_from_page(
    html: str, markup: BylineMarkup | None = None, source_name: str = ""
) -> PageByline:
    """The author's name from a page's own byline markup or metadata (see the module)."""
    parser = _PageParser(markup)
    parser.feed(html)
    parser.close()
    people, others = _jsonld_authors(parser.jsonld)
    meta_author = parser.meta.get("author", "")
    twitter = ""
    for i in ("1", "2"):
        if parser.meta.get(f"twitter:label{i}", "").lower().strip() == "written by":
            twitter = parser.meta.get(f"twitter:data{i}", "")
    routes: list[tuple[str, list[str]]] = [
        ("site", [n for v in parser.site_names for n in split_names(v)]),
        ("jsonld", people),
        ("meta", list(split_names(meta_author))),
        ("twitter", list(split_names(twitter))),
    ]
    if markup is not None and (parser.site_block_found or not markup.metadata_fallback):
        routes = routes[:1]  # the visible byline block is the page's own word
        others = []
    jsonld_people = tuple(dict.fromkeys(n for n in people if is_person(n, source_name)))
    seen_any = bool(others)
    own = False
    for route, names in routes:
        if not names:
            continue
        seen_any = True
        kept = tuple(dict.fromkeys(n for n in names if is_person(n, source_name)))
        if kept:
            agrees = None
            if route == "site" and jsonld_people:
                agrees = set(kept) == set(jsonld_people)
            return PageByline(names=kept, route=route, jsonld_agrees=agrees)
        if route == "site" and markup is not None and parser.site_block_found:
            own = is_source_itself(names, source_name)
    if own:
        return PageByline(names=(), route="", why_none="source_itself")
    return PageByline(names=(), route="", why_none="not_a_person" if seen_any else "no_byline")


def is_source_itself(names: Iterable[str], source_name: str) -> bool:
    """True when every name in a byline is the source's own name (and there is one)."""
    own = source_name.lower().strip()
    names = [n.lower().strip() for n in names]
    return bool(own) and bool(names) and all(n == own for n in names)


@dataclass
class PageBylineStats:
    """Counts only: what a run fetched and found."""

    source_id: str
    rows: int = 0
    rows_without_byline: int = 0
    pages_fetched: int = 0
    pages_already_saved: int = 0
    with_person: int = 0
    no_person: Counter[str] = field(default_factory=Counter)
    routes: Counter[str] = field(default_factory=Counter)
    authors_per_page: Counter[str] = field(default_factory=Counter)
    jsonld_check: Counter[str] = field(default_factory=Counter)
    http_status: Counter[str] = field(default_factory=Counter)
    bytes_fetched: int = 0
    stopped: str = ""

    def summary(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "rows": self.rows,
            "rows_without_byline": self.rows_without_byline,
            "pages_fetched": self.pages_fetched,
            "pages_already_saved": self.pages_already_saved,
            "with_person": self.with_person,
            "no_person": dict(sorted(self.no_person.items())),
            "routes": dict(sorted(self.routes.items())),
            "authors_per_page": dict(sorted(self.authors_per_page.items())),
            "jsonld_check": dict(sorted(self.jsonld_check.items())),
            "http_status": dict(sorted(self.http_status.items())),
            "bytes_fetched": self.bytes_fetched,
            "stopped": self.stopped,
        }


def load_page_bylines(path: Path) -> dict[str, dict]:
    """The saved map of canonical URL -> {"names", "route", "why_none", "http_status"}."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def names_by_url(path: Path) -> dict[str, tuple[str, ...]]:
    """Canonical URL -> names, for the URLs whose page names a person."""
    return {u: tuple(v["names"]) for u, v in load_page_bylines(path).items() if v.get("names")}


def source_credited(path: Path) -> set[str]:
    """The canonical URLs whose page byline names the source itself and no person."""
    return {u for u, v in load_page_bylines(path).items() if v.get("why_none") == "source_itself"}


class PageBylineReader:
    """Reads the byline of one article page at a time, fetching each page at most once.

    With ``client`` None nothing is fetched, and only pages already saved are read.
    """

    def __init__(
        self,
        client: PoliteClient | None,
        source_id: str,
        pages: Path,
        map_path: Path,
        *,
        source_name: str = "",
        say: Callable[[str], None] = lambda _m: None,
    ) -> None:
        self.client = client
        self.source_id = source_id
        self.pages = pages
        self.map_path = map_path
        self.source_name = source_name
        self.markup = SITE_MARKUP.get(source_id)
        self.say = say
        self.found = load_page_bylines(map_path)
        self.stats = PageBylineStats(source_id=source_id)

    def read(self, url: str, *, fetch: bool = True) -> tuple[str, ...]:
        """The names on the page of ``url`` (fetched once if not saved), or ()."""
        st = self.stats
        key = canonical_url(url)
        path = page_file(self.pages, url)
        if not path.exists():
            prior = self.found.get(key, {})
            if prior.get("http_status") not in (None, 200):
                st.http_status[str(prior["http_status"])] += 1
                st.no_person[f"http_{prior['http_status']}"] += 1
                return ()
            if self.client is None or not fetch:
                st.no_person["not_fetched"] += 1
                return ()
            try:
                resp = self.client.get(
                    url, accept="text/html", note=f"page-byline:{self.source_id}"
                )
            except (Blocked, Disallowed, BudgetExceeded) as exc:
                st.stopped = f"{type(exc).__name__}: {exc}"
                st.no_person["not_fetched"] += 1
                self.client = None  # send nothing more in this run
                return ()
            except FetchError as exc:
                st.http_status["error"] += 1
                st.no_person["fetch_error"] += 1
                self.say(f"{self.source_id}: {exc}")
                return ()
            st.pages_fetched += 1
            st.bytes_fetched += len(resp.body)
            st.http_status[str(resp.status)] += 1
            if resp.status != 200 or resp.truncated:
                status = resp.status if resp.status != 200 else "truncated"
                self.found[key] = {
                    "names": [],
                    "route": "",
                    "why_none": "",
                    "http_status": status,
                }
                st.no_person[f"http_{status}"] += 1
                return ()
            save_once(path, resp.body)
        else:
            st.pages_already_saved += 1
            st.http_status["200"] += 1
        html = path.read_bytes().decode("utf-8", errors="replace")
        result = byline_from_page(html, self.markup, self.source_name)
        self.found[key] = {
            "names": list(result.names),
            "route": result.route,
            "why_none": result.why_none,
            "http_status": 200,
        }
        if result.names:
            st.with_person += 1
            st.routes[result.route] += 1
            st.authors_per_page[str(min(len(result.names), 4))] += 1
            if result.jsonld_agrees is not None:
                st.jsonld_check["agrees" if result.jsonld_agrees else "differs"] += 1
        else:
            st.no_person[result.why_none] += 1
        return result.names

    def credits_source(self, url: str) -> bool:
        """True when the page of ``url``, already read, credits the source itself."""
        return self.found.get(canonical_url(url), {}).get("why_none") == "source_itself"

    def save(self) -> None:
        self.map_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.map_path.with_suffix(self.map_path.suffix + ".part")
        tmp.write_text(
            json.dumps(self.found, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.map_path)


def collect_page_bylines(
    reader: PageBylineReader,
    rows_path: Path,
    *,
    limit: int | None = None,
) -> PageBylineStats:
    """Read (fetching once) the page of every row in ``rows_path`` that has no byline."""
    st = reader.stats
    urls: list[str] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            st.rows += 1
            if row.get("authors") or row.get("status") == "removed":
                continue
            st.rows_without_byline += 1
            urls.append(row["url"])
    for n, url in enumerate(urls, 1):
        reader.read(url, fetch=limit is None or st.pages_fetched < limit)
        if n % 100 == 0:
            reader.save()
            reader.say(
                f"{reader.source_id}: {n} of {len(urls)} pages read, "
                f"{st.with_person} name a person, {st.pages_fetched} fetched"
            )
    reader.save()
    return st
