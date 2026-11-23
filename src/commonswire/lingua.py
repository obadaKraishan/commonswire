"""Global Voices' language editions (Lingua): each post's link to its English version, its
other-language versions, and the rule that releases a Lingua row.

**The rule** (the maintainer's, 2026-11-23). The Lingua sites' footers and the publisher's
policy, which names "our sites", settle the license. Third-party material is settled
mechanically: a Lingua row is released only when its English version is a released row of the
corpus, because the English pages are where republished partner pieces are detected. Every
other Lingua row is held and counted, by edition. The registry marks such editions with the
reason code :data:`RULE_CODE`; :func:`commonswire.release.collect` applies it.

**The link.** A Lingua article page names the post's other-language versions (a list of
``post-translation-<lang>`` links), but neither the site's API nor its listings carry them, so
reading them would take one page per post. A translation keeps the link targets and the images
of the post it translates, so the link is found from the bodies the API already gives: each
body's fingerprint (:func:`fingerprint`: its links to other sites, its links to English Global
Voices articles, and its image file names) is matched against the fingerprints of the saved
English bodies (:class:`EnglishIndex`). A match must share at least :data:`MIN_SHARED`
fingerprint parts, cover at least :data:`MIN_JACCARD` of the two bodies' parts together, and
be clearly ahead of the next candidate (:data:`MIN_LEAD`); anything less is no match, and the
row is held. The route's agreement with the pages' own links was measured on samples read both
ways (``docs/method.md``).

**Versions** (answer 5a). The English version is not assumed to be the original. Each row
records the addresses of its other-language versions (``other_versions``: the posts linked
through the same English post), and ``original_url`` only where exactly one version in the
group credits no translator: that version's address, on the other versions' rows.

No function here sends a request.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from commonswire.schema import canonical_url

#: The registry's reason code for an edition released under the rule.
RULE_CODE = "released_with_english"
#: The English site, whose rows the rule checks against.
ENGLISH_SOURCE = "globalvoices"
ENGLISH_HOST = "globalvoices.org"
#: The hold reasons the rule gives (their first words are what the manifest counts).
NO_ENGLISH = "no English version found (the Lingua rule)"
ENGLISH_NOT_RELEASED = "its English version is not a released row (the Lingua rule)"

#: A match needs this many shared fingerprint parts ...
MIN_SHARED = 3
#: ... this share of the two fingerprints together (Jaccard) ...
MIN_JACCARD = 0.25
#: ... and at least this many times the parts the next candidate shares.
MIN_LEAD = 2.0
#: A fingerprint part found in more English bodies than this says nothing about one post
#: (a donation link, a site-wide image) and is not used.
MAX_POSTS_PER_PART = 40

_HREF = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']([^"']+)["']""", re.I)
_SRC = re.compile(r"""<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']""", re.I)
_GV = re.compile(r"(^|\.)globalvoices\.org$")
_SIZE = re.compile(r"-\d{2,4}x\d{2,4}(?=\.[a-z0-9]{3,4}$)", re.I)
_ARTICLE = re.compile(r"^/\d{4}/\d{2}/\d{2}/[^/?#]+")
_TRANSLATION = re.compile(
    r"""class=['"]translation-language post-translation-([A-Za-z\-]+)['"]>\s*"""
    r"""<a\b[^>]*?href=['"]([^'"]+)['"]"""
)


def _short(url: str) -> str:
    """A link target as host and path (lower-case host, no ``www.`` or ``m.``, no trailing
    slash, percent-escapes decoded); "" for a target with no host."""
    url = url.strip().replace("&amp;", "&")
    if url.startswith("//"):
        url = "https:" + url
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return ""
    for prefix in ("www.", "m."):
        host = host.removeprefix(prefix)
    if not host:
        return ""
    return host + unquote(parts.path).rstrip("/")


def fingerprint(html: str) -> frozenset[str]:
    """The parts of a body that a translation keeps: links to other sites (``a:``), links to
    English Global Voices articles (``gv:``, by date and slug), and image file names (``i:``,
    without WordPress's size suffix). Links to the Lingua sites are left out, since a
    translation points its links at its own language's versions."""
    out: set[str] = set()
    for href in _HREF.findall(html):
        short = _short(href)
        if not short:
            continue
        host, _, path = short.partition("/")
        path = "/" + path
        if _GV.search(host):
            if host == ENGLISH_HOST and _ARTICLE.match(path):
                out.add("gv:" + _ARTICLE.match(path).group(0))  # type: ignore[union-attr]
            continue
        out.add("a:" + short)
    for src in _SRC.findall(html):
        short = _short(src)
        if not short:
            continue
        name = _SIZE.sub("", short.rsplit("/", 1)[-1].lower())
        if len(name) > 6:
            out.add("i:" + name)
    return frozenset(out)


@dataclass(frozen=True)
class Match:
    """The English post a body is matched to, with the evidence (counts only)."""

    url: str  # the English post's address, as the publisher gives it
    shared: int
    jaccard: float
    runner_up: int  # the parts the next candidate shares


class EnglishIndex:
    """The fingerprints of the English bodies, and the posts each rare part occurs in, keyed
    by canonical URL (``links`` keeps each post's address as the publisher gives it)."""

    def __init__(self, entries: Iterable[tuple[str, str, frozenset[str]]]) -> None:
        self.prints: dict[str, frozenset[str]] = {}
        self.links: dict[str, str] = {}
        for key, link, parts in entries:
            self.prints[key] = parts  # a later answer (an edit) replaces an earlier one
            self.links[key] = link
        posts: dict[str, list[str]] = defaultdict(list)
        for url, parts in self.prints.items():
            for part in parts:
                posts[part].append(url)
        self.posts = {p: u for p, u in posts.items() if len(u) <= MAX_POSTS_PER_PART}

    def __len__(self) -> int:
        return len(self.prints)

    def candidates(self, parts: frozenset[str], top: int = 2) -> list[tuple[str, int, float]]:
        """The English posts sharing the most rare parts: (url, shared, Jaccard), best first;
        ties go to the earlier address in sort order, so the result never depends on order."""
        score: Counter[str] = Counter()
        for part in parts:
            for url in self.posts.get(part, ()):
                score[url] += 1
        ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        return [(u, s, s / (len(parts | self.prints[u]) or 1)) for u, s in ranked]

    def match(self, parts: frozenset[str]) -> Match | None:
        """The English post a body translates or is translated from, or None (see the module's
        thresholds)."""
        found = self.candidates(parts)
        if not found:
            return None
        url, shared, jaccard = found[0]
        runner_up = found[1][1] if len(found) > 1 else 0
        if shared < MIN_SHARED or jaccard < MIN_JACCARD or shared < MIN_LEAD * runner_up:
            return None
        return Match(
            url=self.links[url], shared=shared, jaccard=round(jaccard, 4), runner_up=runner_up
        )


def _posts_in(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_bytes())
    except ValueError:
        return []
    return [p for p in data if isinstance(p, dict)] if isinstance(data, list) else []


def english_posts(root: Path) -> Iterator[dict]:
    """Every English post saved on the drive: the backfill runs, then the update runs' answer
    caches (oldest first, so an edited post's later answer comes last)."""
    base = root / "data" / "raw"
    for folder in sorted((base / "backfill" / ENGLISH_SOURCE).glob("*")):
        for path in sorted(folder.glob("posts-p*.json")):
            yield from _posts_in(path)
    for meta in sorted((base / "update").glob("*/cache/*.json")):
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
        except ValueError:
            continue
        parts = urlsplit(str(info.get("url", "")))
        if parts.hostname != ENGLISH_HOST or not parts.path.startswith("/wp-json/wp/v2/posts"):
            continue
        if int(info.get("status", 0)) == 200:
            yield from _posts_in(meta.with_suffix(".body"))


def english_index(posts: Iterable[Mapping]) -> EnglishIndex:
    """The index of English bodies, from WordPress posts (``link`` and ``content``)."""

    def entries() -> Iterator[tuple[str, str, frozenset[str]]]:
        for post in posts:
            link = post.get("link") or ""
            body = (post.get("content") or {}).get("rendered", "")
            try:
                key = canonical_url(link)
            except ValueError:
                continue
            yield key, link, fingerprint(body)

    return EnglishIndex(entries())


def page_versions(html: str) -> dict[str, str]:
    """The other-language versions an article page lists itself (language code -> canonical
    URL), for the weekly route and for checking the match."""
    out: dict[str, str] = {}
    for lang, url in _TRANSLATION.findall(html):
        try:
            out.setdefault(lang, canonical_url(url))
        except ValueError:
            continue
    return out


def same_post(a: str, b: str) -> bool:
    """True when two addresses of Global Voices posts name the same post: equal, or the same
    host and slug under another date (an old address that redirects)."""
    if a == b:
        return True
    pa, pb = urlsplit(a), urlsplit(b)
    sa = pa.path.rstrip("/").rsplit("/", 1)[-1]
    sb = pb.path.rstrip("/").rsplit("/", 1)[-1]
    return pa.hostname == pb.hostname and bool(sa) and sa == sb and not sa.isdigit()


@dataclass
class LinkStats:
    """Counts only: an edition's posts and how many were matched."""

    source_id: str
    posts: int = 0
    matched: int = 0
    no_parts: int = 0  # bodies with fewer fingerprint parts than a match needs
    no_match: int = 0
    english_posts: int = 0

    def summary(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "posts": self.posts,
            "matched": self.matched,
            "no_parts": self.no_parts,
            "no_match": self.no_match,
            "english_posts_indexed": self.english_posts,
        }


def link_posts(
    source_id: str, posts: Iterable[Mapping], index: EnglishIndex
) -> tuple[dict[str, dict], LinkStats]:
    """Each Lingua post's English version (canonical URL -> match), and counts."""
    st = LinkStats(source_id=source_id, english_posts=len(index))
    links: dict[str, dict] = {}
    for post in posts:
        link = post.get("link") or ""
        try:
            url = canonical_url(link)
        except ValueError:
            continue
        st.posts += 1
        parts = fingerprint((post.get("content") or {}).get("rendered", ""))
        if len(parts) < MIN_SHARED:
            st.no_parts += 1
            continue
        m = index.match(parts)
        if m is None:
            st.no_match += 1
            continue
        st.matched += 1
        links[url] = {
            "url": link,
            "en": m.url,
            "shared": m.shared,
            "jaccard": m.jaccard,
            "runner_up": m.runner_up,
        }
    return links, st


def write_links(path: Path, links: Mapping[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(dict(sorted(links.items())), indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_links(path: Path) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@dataclass(frozen=True)
class Versions:
    """A row's other-language versions and, where answer 5a sets one, its original."""

    other_versions: tuple[str, ...]
    original_url: str = ""


def version_groups(
    english_of: Mapping[str, str], translators: Mapping[str, tuple[str, ...]]
) -> dict[str, Versions]:
    """Each version's other versions and original, from the Lingua posts' English versions.

    ``english_of`` maps each Lingua post's address to its English version's address (both as
    the publisher gives them); ``translators`` maps any version's canonical URL to the
    translators its credits name (a missing URL credits none). The result is keyed by
    canonical URL; the addresses in it are the publisher's.
    A group is an English post and the Lingua posts linked to it. A row's ``original_url`` is
    set only where exactly one version in its group credits no translator, and only on the
    other versions' rows."""
    groups: dict[str, list[str]] = defaultdict(list)
    for lingua, english in english_of.items():
        groups[english].append(lingua)
    out: dict[str, Versions] = {}
    for english, linguas in groups.items():
        members = sorted({english, *linguas})
        untranslated = [u for u in members if not translators.get(canonical_url(u))]
        original = untranslated[0] if len(untranslated) == 1 else ""
        for u in members:
            out[canonical_url(u)] = Versions(
                other_versions=tuple(v for v in members if v != u),
                original_url=original if original != u else "",
            )
    return out


def english_version(other_versions: Iterable[str]) -> str:
    """The English Global Voices address among a row's other versions, or "" (none or more
    than one)."""
    found = [u for u in other_versions if urlsplit(u).hostname == ENGLISH_HOST]
    return found[0] if len(found) == 1 else ""


class ListingPlan:
    """Which listing pages of a language site to read: those that may show a story the rule
    could release. The listing shows the posts newest first, as the API orders them, so a
    page's stories are a run of the API's order. After each page read, the plan knows where
    the next page starts; a page whose run (widened by ``margin`` stories each side) holds no
    releasable story is skipped, and the estimate moves on by one page's worth of stories.

    ``order`` is every post's canonical URL, newest first; ``releasable`` the URLs the rule
    could release (their English version is a releasable row)."""

    def __init__(
        self, order: list[str], releasable: set[str], *, per_page: int = 21, margin: int = 3
    ) -> None:
        self.rank = {u: i for i, u in enumerate(order)}
        self.total = len(order)
        self.flags = [u in releasable for u in order]
        self.per_page = per_page
        self.margin = margin
        self.next_start = 0
        self._sizes: list[int] = []

    def wanted(self, page: int) -> bool:
        if page <= 2:
            return True  # page 1 has the featured stories; page 2 shows the page size
        lo = max(0, self.next_start - self.margin)
        hi = min(self.total, self.next_start + self.per_page + self.margin)
        return any(self.flags[lo:hi])

    def done(self) -> bool:
        return self.next_start >= self.total

    def skipped(self) -> None:
        self.next_start += self.per_page

    def observe(self, page: int, urls: Iterable[str]) -> None:
        ranks = []
        n = 0
        for url in urls:
            n += 1
            try:
                r = self.rank.get(canonical_url(url))
            except ValueError:
                r = None
            if r is not None:
                ranks.append(r)
        if page >= 2 and n:
            self._sizes.append(n)
            self.per_page = sorted(self._sizes)[len(self._sizes) // 2]
        if ranks:
            self.next_start = max(self.next_start, max(ranks) + 1)
        elif page >= 2:
            self.next_start += self.per_page


def saved_posts(folder: Path) -> Iterator[dict]:
    """The posts of a saved backfill run, page by page."""
    for path in sorted(folder.glob("posts-p*.json")):
        yield from _posts_in(path)


def plan_for(root: Path, source_id: str, run: str) -> tuple[ListingPlan, dict[str, int]]:
    """The listing plan of a language site: its posts newest first (from the backfill run),
    and those the rule could release: matched to an English post that is a releasable row of
    ``data/interim/rows/globalvoices.jsonl``."""
    folder = root / "data" / "raw" / "backfill" / source_id / run
    links_path = root / "data" / "interim" / "lingua" / f"{source_id}.links.json"
    rows_path = root / "data" / "interim" / "rows" / f"{ENGLISH_SOURCE}.jsonl"
    for p in (folder, links_path, rows_path):
        if not p.exists():
            raise FileNotFoundError(f"{p} is missing (backfill, lingua-link and build first)")
    released: set[str] = set()
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("releasable") and row.get("status") != "removed":
                released.add(canonical_url(row["url"]))
    links = read_links(links_path)
    dated: list[tuple[str, int, str]] = []
    for post in saved_posts(folder):
        try:
            url = canonical_url(post.get("link") or "")
        except ValueError:
            continue
        dated.append((str(post.get("date_gmt") or ""), int(post.get("id") or 0), url))
    order = [u for _, _, u in sorted(dated, reverse=True)]
    releasable = {u for u in order if u in links and canonical_url(links[u]["en"]) in released}
    plan = ListingPlan(order, releasable)
    return plan, {"posts": len(order), "releasable": len(releasable)}
