"""Bylines from a source's paged story listing, for sources whose API gives no author names.

Global Voices closes its WordPress users endpoint and refuses author lookups by id, so its API
answers carry an author number but no name. Its paged story listing (``/page/N/``) shows every
story with a credit block: "Written by" with the writers' names (all of them, where the feed
names only one), and "Translated by" for translations. One listing page names the writers of
about 21 stories, so the whole archive takes about a twenty-first of the requests that one
article page per story would.

Each listing page is fetched once through the polite client, newest first, and saved unchanged
under ``data/raw/pages/<source>/listing/<run>/``. A rerun skips the pages already saved, so a
run can be stopped and resumed. New stories published during a run push older ones to later
pages, so a story may be seen twice but is not skipped. A story keeps its first sighting that has
a credit block: the home page (listing page 1) also shows featured teasers with no credit block,
and such a story takes its writers from a later sighting. The walk stops at the first page that
answers 404 or lists no story, and on any refusal.

The names go to ``data/interim/bylines/<source>.listing.json`` (canonical URL -> names, in the
format :func:`commonswire.pagebylines.names_by_url` reads); only counts go into the tracked
evidence. Translators are kept apart from the writers (``translators``), never in ``authors``;
an account such as "Guest Contributor" is no person, as a writer or as a translator. A story
whose credit block names only such accounts says so (``why_none``: ``not_a_person``).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import TYPE_CHECKING

from commonswire.backfill import save_once
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient
from commonswire.pagebylines import is_person, is_source_itself
from commonswire.schema import canonical_url

if TYPE_CHECKING:
    from commonswire.lingua import ListingPlan

PAGE_NAME = "p{:05d}.html"
#: A whole walk's longer waits before asking again for a page whose answer was still a
#: server error after the client's own retries (seconds).
LONG_PAUSES = (300.0, 900.0)
_SPACE = re.compile(r"\s+")
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


@dataclass(frozen=True)
class ListingMarkup:
    """Where a source's listing puts each story and its credits.

    ``story`` is the class of the element holding the story's title link, ``credit`` the class
    of each credit block after it, ``label`` the class of the block's label ("Written by"), and
    the names are the links inside the block.
    """

    url: str  # the listing page, with {page}
    story: str
    credit: str
    label: str
    writer_labels: tuple[str, ...] = ("written by",)
    translator_labels: tuple[str, ...] = ("translated by",)


def learn_labels(stories: list[Story], markup: ListingMarkup) -> ListingMarkup:
    """A listing whose labels are not known (a Global Voices language site prints them in its
    own language) takes them from its stories: the label most stories with two credit blocks
    put first is the writers', the one they put second the translators'. Unchanged when the
    labels are known or the stories show no such pair."""
    if markup.writer_labels:
        return markup
    first: Counter[str] = Counter()
    second: Counter[str] = Counter()
    for story in stories:
        labels = list(story.credits)
        if len(labels) >= 2:
            first[labels[0]] += 1
            second[labels[1]] += 1
    if not first:
        return markup
    writer, translator = first.most_common(1)[0][0], second.most_common(1)[0][0]
    if writer == translator:
        return markup
    return replace(markup, writer_labels=(writer,), translator_labels=(translator,))


def listing_markup(source_id: str) -> ListingMarkup:
    """The listing markup of a source: :data:`LISTING_MARKUP`, or for a Global Voices language
    site (``globalvoices_<site>``) the English site's markup at its own address, with its labels
    learned from its first listing page (:func:`learn_labels`)."""
    if source_id in LISTING_MARKUP:
        return LISTING_MARKUP[source_id]
    from commonswire.fetchers.wordpress import LINGUA_FETCHERS

    if source_id in LINGUA_FETCHERS:
        site = LINGUA_FETCHERS[source_id].site
        return replace(
            LISTING_MARKUP["globalvoices"],
            url=f"https://{site}.globalvoices.org/page/{{page}}/",
            writer_labels=(),
            translator_labels=(),
        )
    raise KeyError(source_id)


def has_listing(source_id: str) -> bool:
    try:
        listing_markup(source_id)
    except KeyError:
        return False
    return True


LISTING_MARKUP: dict[str, ListingMarkup] = {
    # <div class="post-title"><a href="https://globalvoices.org/2026/11/05/...">TITLE</a></div>
    # ... <div class="text-credits-container"><div class="text-credits-section">
    # <span class="credit-label">Written by</span> <a class="user-link" ...>NAME</a></div>
    "globalvoices": ListingMarkup(
        url="https://globalvoices.org/page/{page}/",
        story="post-title",
        credit="text-credits-section",
        label="credit-label",
    ),
}


@dataclass
class Story:
    url: str
    credits: dict[str, list[str]] = field(default_factory=dict)


class _ListingParser(HTMLParser):
    """Collects each story's link and the names in the credit blocks that follow it."""

    def __init__(self, markup: ListingMarkup) -> None:
        super().__init__(convert_charrefs=True)
        self.m = markup
        self.stories: list[Story] = []
        self._stack: list[tuple[str, frozenset[str]]] = []
        self._story: int | None = None  # stack depth of the open title block
        self._story_taken = False
        self._credit: int | None = None  # stack depth of the open credit block
        self._label: str | None = None
        self._in_label: int | None = None
        self._in_name: int | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID:
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        classes = frozenset(a.get("class", "").split())
        self._stack.append((tag, classes))
        if self.m.story in classes and self._story is None:
            self._story, self._story_taken = len(self._stack), False
        if tag == "a" and self._story is not None and not self._story_taken and a.get("href"):
            self.stories.append(Story(url=a["href"]))
            self._story_taken = True
            return
        if self.m.credit in classes and self._credit is None:
            self._credit, self._label = len(self._stack), None
        elif self._credit is not None and self.m.label in classes:
            self._in_label, self._buf = len(self._stack), []
        elif self._credit is not None and tag == "a" and self._label is not None:
            self._in_name, self._buf = len(self._stack), []

    def handle_data(self, data: str) -> None:
        if self._in_label is not None or self._in_name is not None:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID or not any(t == tag for t, _ in self._stack):
            return  # a stray end tag
        while self._stack:
            top, _ = self._stack.pop()
            depth = len(self._stack) + 1
            text = _SPACE.sub(" ", unescape("".join(self._buf))).strip()
            if self._in_label is not None and depth <= self._in_label:
                self._label, self._in_label = text.lower().rstrip(":"), None
            if self._in_name is not None and depth <= self._in_name:
                if text and self.stories and self._label is not None:
                    self.stories[-1].credits.setdefault(self._label, []).append(text)
                self._in_name = None
            if self._credit is not None and depth <= self._credit:
                self._credit = None
            if self._story is not None and depth <= self._story:
                self._story = None
            if top == tag:
                break


def read_listing(html: str, markup: ListingMarkup) -> list[Story]:
    """The stories on one listing page, with the names in each credit block."""
    parser = _ListingParser(markup)
    parser.feed(html)
    parser.close()
    return parser.stories


@dataclass
class ListingStats:
    """Counts only: what a run fetched and found."""

    source_id: str
    pages_fetched: int = 0
    pages_already_saved: int = 0
    last_page: int = 0
    stories_seen: int = 0
    stories: int = 0
    with_writer: int = 0
    without_writer: int = 0
    translated: int = 0
    #: Stories seen again on a later page, and how often a later sighting gave the credits
    #: that the first one (a teaser with no credit block) lacked.
    seen_again: int = 0
    credits_from_later_sighting: int = 0
    translators_not_a_person: int = 0
    why_none: Counter[str] = field(default_factory=Counter)
    writers_per_story: Counter[str] = field(default_factory=Counter)
    http_status: Counter[str] = field(default_factory=Counter)
    bytes_fetched: int = 0
    pages_skipped: int = 0
    long_waits: int = 0
    labels_known: bool = True
    end: str = ""
    stopped: str = ""

    def summary(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "pages_fetched": self.pages_fetched,
            "pages_skipped": self.pages_skipped,
            "long_waits": self.long_waits,
            "labels_known": self.labels_known,
            "pages_already_saved": self.pages_already_saved,
            "last_page": self.last_page,
            "stories_seen": self.stories_seen,
            "stories": self.stories,
            "with_writer": self.with_writer,
            "without_writer": self.without_writer,
            "translated": self.translated,
            "seen_again": self.seen_again,
            "credits_from_later_sighting": self.credits_from_later_sighting,
            "translators_not_a_person": self.translators_not_a_person,
            "why_none": dict(sorted(self.why_none.items())),
            "writers_per_story": dict(sorted(self.writers_per_story.items())),
            "http_status": dict(sorted(self.http_status.items())),
            "bytes_fetched": self.bytes_fetched,
            "end": self.end,
            "stopped": self.stopped,
        }


def collect_listing_bylines(
    client: PoliteClient | None,
    source_id: str,
    folder: Path,
    map_path: Path,
    *,
    source_name: str = "",
    max_pages: int = 6000,
    plan: ListingPlan | None = None,
    say: Callable[[str], None] = lambda _m: None,
    sleep: Callable[[float], None] | None = None,
) -> ListingStats:
    """Walk the listing from page 1, fetching each page once (none with ``client`` None), and
    write the names of every story's writers to ``map_path``. With a ``plan``
    (:class:`commonswire.lingua.ListingPlan`), a page that is not saved is fetched only when
    it may show a story the Lingua rule could release."""
    markup = listing_markup(source_id)
    st = ListingStats(source_id=source_id)
    found: dict[str, dict] = {}
    uncredited: set[str] = set()  # stories kept from a sighting with no credit block
    for page in range(1, max_pages + 1):
        if plan is not None and not (folder / PAGE_NAME.format(page)).exists():
            if plan.done():
                st.end = f"page {page} would start past the last post (the plan)"
                break
            if not plan.wanted(page):
                st.pages_skipped += 1
                plan.skipped()
                continue
        path = folder / PAGE_NAME.format(page)
        if path.exists():
            st.pages_already_saved += 1
        else:
            if client is None:
                st.end = f"page {page} is not saved (replay)"
                break
            try:
                for pause in (0.0, *LONG_PAUSES):
                    if pause:
                        # The client's own retries ended in a server error: wait longer, then
                        # ask again (a backoff, never another route).
                        st.long_waits += 1
                        (sleep or client.sleep)(pause)
                    resp = client.get(
                        markup.url.format(page=page),
                        accept="text/html",
                        note=f"listing-byline:{source_id}",
                    )
                    if resp.status < 500:
                        break
                    st.http_status[str(resp.status)] += 1
            except (Blocked, Disallowed, BudgetExceeded) as exc:
                st.stopped = f"{type(exc).__name__}: {exc}"
                break
            except FetchError as exc:
                st.stopped = f"error: {exc}"
                break
            st.pages_fetched += 1
            st.bytes_fetched += len(resp.body)
            if resp.status < 500:
                st.http_status[str(resp.status)] += 1
            if resp.status == 404:
                st.end = f"page {page} answered 404: past the last page"
                break
            if resp.status != 200 or resp.truncated:
                st.stopped = f"page {page} answered HTTP {resp.status}" + (
                    " (cut short)" if resp.truncated else ""
                )
                break
            stories = read_listing(resp.text, markup)
            if not stories:
                st.end = f"page {page} lists no story"
                break
            save_once(path, resp.body)
        stories = read_listing(path.read_bytes().decode("utf-8", errors="replace"), markup)
        markup = learn_labels(stories, markup)
        st.labels_known = bool(markup.writer_labels)
        if plan is not None:
            plan.observe(page, [s.url for s in stories])
        st.last_page = page
        for story in stories:
            st.stories_seen += 1
            _take_story(story, markup, source_name, found, uncredited, st)
        if page % 100 == 0:
            say(f"{source_id}: listing page {page}, {len(found)} stories so far")
            _write_map(map_path, found)
    st.stories = len(found)
    st.with_writer = sum(1 for v in found.values() if v["names"])
    st.without_writer = st.stories - st.with_writer
    st.translated = sum(1 for v in found.values() if v["translators"])
    st.translators_not_a_person = sum(v["_dropped_translators"] for v in found.values())
    st.why_none = Counter(v["why_none"] for v in found.values() if v["why_none"])
    st.writers_per_story = Counter(str(min(len(v["names"]), 4)) for v in found.values())
    _write_map(map_path, found)
    return st


def _take_story(
    story: Story,
    markup: ListingMarkup,
    source_name: str,
    found: dict[str, dict],
    uncredited: set[str],
    st: ListingStats,
) -> str | None:
    """Record one sighting of a story; returns its canonical URL (None if it has none). A story
    keeps its first sighting that has a credit block."""
    try:
        key = canonical_url(story.url)
    except ValueError:
        return None
    if key in found:
        st.seen_again += 1
        if key not in uncredited or not story.credits:
            return key  # the first sighting with a credit block stands
        st.credits_from_later_sighting += 1
    if markup.writer_labels:
        named = [n for label in markup.writer_labels for n in story.credits.get(label, [])]
        listed = [n for label in markup.translator_labels for n in story.credits.get(label, [])]
    else:  # labels not learned yet: the first credit block is the writers', the second the
        # translators' (the order every story with two blocks shows)
        blocks = list(story.credits.values())
        named = list(blocks[0]) if blocks else []
        listed = list(blocks[1]) if len(blocks) > 1 else []
    writers = [n for n in named if is_person(n, source_name)]
    own = is_source_itself(named, source_name)
    translators = [n for n in listed if is_person(n, source_name)]
    if writers:
        why = ""
    elif own:
        why = "source_itself"
    else:
        why = "not_a_person" if named else "no_byline"
    found[key] = {
        "names": list(dict.fromkeys(writers)),
        "translators": list(dict.fromkeys(translators)),
        "route": "listing",
        "why_none": why,
        "http_status": 200,
        "_dropped_translators": len(listed) - len(translators),
    }
    if story.credits:
        uncredited.discard(key)
    else:
        uncredited.add(key)
    return key


#: A story's date in its address (``/2026/11/05/slug/``), when the source puts it there.
_URL_DATE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")


def _url_day(url: str) -> str | None:
    m = _URL_DATE.search(url)
    return "-".join(m.groups()) if m else None


def listing_credits(
    client: PoliteClient,
    source_id: str,
    wanted: dict[str, str],
    *,
    source_name: str = "",
    max_pages: int = 20,
) -> tuple[dict[str, dict], ListingStats]:
    """The credits of a few new stories, read from the listing's first pages.

    ``wanted`` maps each story's canonical URL to its publication day (``YYYY-MM-DD``). The
    pages are read from page 1, once each, until every wanted story has been seen with a credit
    block, or a page lists only stories dated two days or more before the oldest wanted one
    (from the dates in their addresses), or ``max_pages`` pages are read. The walk also stops
    at a 404, a page that lists no story, and any refusal (``stats.stopped``). Returns the
    entries of the wanted stories found (as in the listing map: ``names``, ``translators``,
    ``why_none``) and counts only."""
    from datetime import date, timedelta

    markup = listing_markup(source_id)
    st = ListingStats(source_id=source_id)
    found: dict[str, dict] = {}
    uncredited: set[str] = set()
    if not wanted:
        return {}, st
    floor = (date.fromisoformat(min(wanted.values())) - timedelta(days=2)).isoformat()
    for page in range(1, max_pages + 1):
        try:
            resp = client.get(
                markup.url.format(page=page),
                accept="text/html",
                note=f"listing-byline:{source_id}",
            )
        except (Blocked, Disallowed, BudgetExceeded) as exc:
            st.stopped = f"{type(exc).__name__}: {exc}"
            break
        except FetchError as exc:
            st.stopped = f"error: {exc}"
            break
        st.pages_fetched += 1
        st.bytes_fetched += len(resp.body)
        st.http_status[str(resp.status)] += 1
        if resp.status == 404:
            st.end = f"page {page} answered 404: past the last page"
            break
        if resp.status != 200 or resp.truncated:
            st.stopped = f"page {page} answered HTTP {resp.status}" + (
                " (cut short)" if resp.truncated else ""
            )
            break
        stories = read_listing(resp.text, markup)
        if not stories:
            st.end = f"page {page} lists no story"
            break
        markup = learn_labels(stories, markup)
        st.labels_known = bool(markup.writer_labels)
        st.last_page = page
        for story in stories:
            st.stories_seen += 1
            _take_story(story, markup, source_name, found, uncredited, st)
        if all(k in found and k not in uncredited for k in wanted):
            st.end = f"every wanted story found by page {page}"
            break
        days = [d for s in stories if (d := _url_day(s.url))]
        if days and max(days) < floor:
            st.end = f"page {page} lists only stories older than the wanted ones"
            break
    else:
        st.end = f"stopped after {max_pages} pages"
    entries = {k: {f: x for f, x in v.items() if not f.startswith("_")} for k, v in found.items()}
    got = {k: entries[k] for k in wanted if k in entries}
    st.stories = len(got)
    st.with_writer = sum(1 for v in got.values() if v["names"])
    st.without_writer = st.stories - st.with_writer
    st.translated = sum(1 for v in got.values() if v["translators"])
    st.why_none = Counter(v["why_none"] for v in got.values() if v["why_none"])
    return got, st


def _write_map(path: Path, found: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    public = {k: {f: x for f, x in v.items() if not f.startswith("_")} for k, v in found.items()}
    tmp.write_text(
        json.dumps(public, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def translators_by_url(path: Path) -> dict[str, tuple[str, ...]]:
    """Canonical URL -> translators, for the stories whose listing names one."""
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {u: tuple(v["translators"]) for u, v in data.items() if v.get("translators")}
