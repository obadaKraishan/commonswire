"""The weekly route of the sources read from their article pages (series 0.3 on).

SciDev.Net and Africa Is a Country have no API that gives their articles, so their archives
were read page by page (:mod:`commonswire.pagebackfill`). Their weekly update reads only what
is new or edited, each page once, through the same page fetchers
(:mod:`commonswire.fetchers.pages`) and the polite client:

- **A sitemap** (SciDev.Net): the sitemap index, then the newest article sitemap, and the one
  before it only while a sitemap still starts after the mark (at most :data:`MAX_SITEMAPS`).
  The site lists its articles by the date they were last changed, oldest first, so the newest
  sitemap holds the new and the edited ones. The pages read are the entries changed after
  the mark (``through``: the newest change date seen by the previous version).
- **A listing** (Africa Is a Country): listing pages 1 and 2 (newest first), and one more
  while the last page read shares no story with the previous version (at most
  :data:`MAX_LISTING_PAGES`). The pages read are the stories the previous version does not
  have, does not hold and has not seen (``seen``: the ids on the listing pages read last
  time, so a piece left out as third-party is not read every week). The site gives no date
  of change, so an edit of an older story is not seen.

A page not in the previous version is a new row (held when its byline is missing and the
publisher asks for it); a page whose text hash differs is changed; a released row whose page
now answers 404 or 410 is removed. Rows that left a sitemap or the listing are not looked
for: page sources have no post counts, so the count check of older removals does not cover
them. The route's state (``through`` or ``seen``) goes into the next manifest's
``page_state``, ids and dates only. A source that refuses, fails, or would need more pages
than the limit is skipped and named, its rows and state carried over unchanged.

:func:`page_state_from_backfill` gives the state of a source's first version, from its saved
backfill run (no request).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from commonswire.daily import _removed
from commonswire.fetchers.pages import PAGE_FETCHERS, PageFetcher
from commonswire.http import (
    AnswerCache,
    Blocked,
    BudgetExceeded,
    Disallowed,
    FetchError,
    PoliteClient,
    UsageLog,
)
from commonswire.pagebackfill import (
    PAGE_ROUTES,
    URLS_FILE,
    PageRoute,
    listing_links,
    sitemap_locs,
)
from commonswire.schema import article_id, canonical_url
from commonswire.update import (
    RUN_FILE,
    ClientFactory,
    SourceUpdate,
    _iso,
    _skipped,
    _usage,
    default_clients,
)

#: Article pages one source may need in a week at most; more means the site changed (or the
#: state is wrong), and the source stops before reading them.
MAX_PAGE_REQUESTS = 60
#: Article sitemaps read back from the newest at most.
MAX_SITEMAPS = 3
#: Listing pages always read, and read at most.
LISTING_PAGES = 2
MAX_LISTING_PAGES = 5
#: The days back whose stories a listing source re-reads each week (edits are seen by hash).
REREAD_DAYS = 30
#: The removal check: released rows gone from the sitemaps or the listing whose pages are
#: read in one run at most (more means the site changed: the source stops), how often a
#: listing is walked in full, and the listing pages such a walk reads at most.
MAX_REMOVAL_CONFIRMATIONS = 25
FULL_WALK_DAYS = 28
MAX_WALK_PAGES = 200

_URL_ENTRY = re.compile(r"<url>(.*?)</url>", re.S | re.I)
_LASTMOD = re.compile(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", re.I)


class _RouteStop(Exception):
    """The route cannot go on: the source stops (status, then the reason)."""

    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status


def _when(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else None


def sitemap_entries(xml: str) -> list[tuple[str, datetime | None]]:
    """The ``(address, last change)`` of each ``<url>`` of a sitemap, in order."""
    out = []
    for block in _URL_ENTRY.findall(xml):
        locs = sitemap_locs(block)
        if not locs:
            continue
        m = _LASTMOD.search(block)
        out.append((locs[0], _when(m.group(1)) if m else None))
    return out


def _aid(url: str) -> str:
    return article_id(canonical_url(url))


def _get(client: PoliteClient, url: str, note: str) -> str | None:
    """A sitemap or listing page; None when it answers 404 or 410."""
    resp = client.get(url, note=note)
    if resp.status in (404, 410):
        return None
    if resp.status != 200 or resp.truncated:
        raise FetchError(f"{url} answered HTTP {resp.status}")
    return resp.body.decode("utf-8", errors="replace")


def _sitemap_candidates(
    client: PoliteClient,
    route: PageRoute,
    through: datetime,
    known: set[str],
    note: str,
    *,
    read_all: bool = False,
) -> tuple[list[str], datetime, dict[str, object], set[str] | None]:
    """The pages changed after the mark, the newest change date, what was read, and (with
    ``read_all``: every article sitemap, for the removal check) the ids of every address the
    sitemaps list."""
    index = _get(client, route.start, note)
    if index is None:
        raise FetchError(f"the sitemap index {route.start} is gone")
    maps = [u for u in sitemap_locs(index) if re.match(route.sitemap_pattern, u)]
    if not maps:
        raise FetchError(f"the sitemap index {route.start} lists no article sitemap")
    wanted: list[str] = []
    listed: set[str] = set()
    newest = through
    read = 0
    reached = False
    for url in reversed(maps if read_all else maps[-MAX_SITEMAPS:]):
        xml = _get(client, url, note)
        if xml is None:
            raise FetchError(f"the sitemap {url} is gone")
        read += 1
        entries = [(u, d) for u, d in sitemap_entries(xml) if re.match(route.article_pattern, u)]
        listed.update(_aid(u) for u, _d in entries)
        for u, d in reversed(entries):
            fresh = (d is not None and d > through) or (d is None and _aid(u) not in known)
            if fresh and u not in wanted:
                wanted.append(u)
            if d is not None and d > newest:
                newest = d
        dated = [d for _u, d in entries if d is not None]
        if not dated or min(dated) <= through:
            reached = True
            if not read_all:
                break
    if not reached:
        raise _RouteStop(
            "failed",
            f"{read} article sitemaps were changed after {_iso(through)}: more than the route "
            f"reads ({MAX_SITEMAPS}); the mark looks wrong",
        )
    wanted.reverse()  # oldest change first
    what = {"route": "sitemap", "sitemaps_read": read, "after_mark": len(wanted)}
    return wanted, newest, what, (listed if read_all else None)


def _listing_walk(client: PoliteClient, route: PageRoute, note: str) -> tuple[set[str], int]:
    """Every story of the listing: pages 1, 2, ... until a page answers 404 or brings no new
    story (the same answers as the weekly pages, so pages 1 and 2 are not asked twice)."""
    listed: set[str] = set()
    for n in range(1, MAX_WALK_PAGES + 1):
        url = route.start if n == 1 else route.next_page.format(n=n)
        html = _get(client, url, note)
        if html is None:
            return listed, n
        ids = {_aid(u) for u in listing_links(html, url, route.article_pattern)}
        if not ids - listed:
            return listed, n
        listed |= ids
    raise _RouteStop(
        "failed", f"the listing has more than {MAX_WALK_PAGES} pages: the walk looks wrong"
    )


def _listing_candidates(
    client: PoliteClient, route: PageRoute, known: set[str], note: str
) -> tuple[list[str], list[str], dict[str, object]]:
    wanted: list[str] = []
    on_pages: list[str] = []
    overlap = False
    n = 0
    for n in range(1, MAX_LISTING_PAGES + 1):
        url = route.start if n == 1 else route.next_page.format(n=n)
        html = _get(client, url, note)
        if html is None:
            break
        links = listing_links(html, url, route.article_pattern)
        ids = [_aid(u) for u in links]
        on_pages += [i for i in ids if i not in on_pages]
        wanted += [u for u, i in zip(links, ids, strict=True) if i not in known and u not in wanted]
        overlap = overlap or any(i in known for i in ids)
        if n >= LISTING_PAGES and (overlap or not known):
            break
    if known and not overlap:
        raise _RouteStop(
            "failed",
            f"listing pages 1 to {n} share no story with the previous version: more new "
            "stories than the route reads, or the listing changed",
        )
    return wanted, sorted(on_pages), {"route": "listing", "listing_pages_read": n}


def update_pages(
    fetcher: PageFetcher,
    client: PoliteClient,
    prev: dict[str, dict],
    *,
    now: datetime,
    prev_as_of: str,
    state: dict | None,
    held: dict[str, dict] | None = None,
    max_pages: int = MAX_PAGE_REQUESTS,
    max_requests: int | None = None,
    removals: bool = True,
    only_removals: bool = False,
) -> tuple[dict[str, dict], SourceUpdate, dict]:
    """One page source's weekly route (see the module). Returns the source's rows after the
    update, what happened (counts and ids), and the route's state for the next manifest;
    for a source that stops, the previous rows and state unchanged. ``state`` is the
    previous manifest's ``page_state`` for this source (None: the previous version's
    ``as_of`` is the mark, and no story counts as seen). ``max_pages`` caps the article
    pages read (new, changed, re-read and removal confirmations); ``max_requests``, when
    given (dry runs), caps every request, robots.txt and the lists included. ``removals``
    runs the removal check (each week for a sitemap; every :data:`FULL_WALK_DAYS` days for a
    listing); ``only_removals`` runs that check alone (a dry run of it)."""
    sid = fetcher.source_id
    route = PAGE_ROUTES[sid]
    res = SourceUpdate(source_id=sid)
    note = f"update:{sid}"
    state = dict(state or {})
    held = held or {}
    known = set(prev) | set(held) | set(state.get("seen") or [])
    rows = dict(prev)
    new_state: dict[str, object]
    today = now.date().isoformat()
    try:
        listed: set[str] | None = None
        if route.kind == "sitemap":
            through = _when(str(state.get("through") or prev_as_of))
            if through is None:
                raise _RouteStop(
                    "failed", "no mark: neither the page state nor the version gives a date"
                )
            wanted, newest, res.route, listed = _sitemap_candidates(
                client, route, through, known, note, read_all=removals or only_removals
            )
            new_state = {**state, "through": _iso(newest)}
            if listed is not None:
                new_state["removals_checked"] = today
            lists = int(res.route["sitemaps_read"]) + 1  # type: ignore[call-overload]
        else:
            if only_removals:
                wanted, on_pages, lists = [], list(state.get("seen") or []), 0
                res.route = {"route": "listing", "listing_pages_read": 0}
            else:
                wanted, on_pages, res.route = _listing_candidates(client, route, known, note)
                lists = int(res.route["listing_pages_read"])  # type: ignore[call-overload]
                # The stories of the last days are read again, so their edits are seen.
                since = _iso(now - timedelta(days=REREAD_DAYS)) or ""
                again = [
                    d["url"]
                    for _rid, d in sorted(prev.items())
                    if d["published_at"] >= since
                    and d["status"] != "removed"
                    and d["url"] not in wanted
                ]
                wanted += again
                res.route["reread"] = len(again)
            new_state = {**state, "seen": on_pages}
            last = _when(f"{state.get('full_walk') or ''}T00:00:00+00:00")
            due = last is None or (now - last).days >= FULL_WALK_DAYS
            if (removals and due) or only_removals:
                listed, walked = _listing_walk(client, route, note)
                res.route["walk_pages_read"] = walked
                lists = max(lists, walked)
                new_state["full_walk"] = today
        if only_removals:
            wanted = []
        missing: list[str] = []
        if listed is not None:
            missing = sorted(
                rid for rid, d in prev.items() if rid not in listed and d["status"] != "removed"
            )
            res.route["removal_check"] = {"listed": len(listed), "rows_not_listed": len(missing)}
            if len(missing) > MAX_REMOVAL_CONFIRMATIONS:
                raise _RouteStop(
                    "over_ceiling",
                    f"{len(missing)} released rows are no longer listed, more than the "
                    f"{MAX_REMOVAL_CONFIRMATIONS} pages a run confirms: the site changed; ask "
                    "before reading them",
                )
        res.listed = len(wanted)
        pages = len(wanted) + len(missing)
        if pages > max_pages:
            raise _RouteStop(
                "over_budget",
                f"{pages} pages to read, more than the weekly limit of {max_pages}: ask "
                "before reading more",
            )
        needed = 1 + lists + pages  # robots.txt, the lists, the pages
        if max_requests is not None and needed > max_requests:
            raise _RouteStop(
                "over_budget",
                f"{pages} pages to read ({needed} requests with robots.txt and the "
                f"lists), more than the limit of {max_requests}: ask before reading more",
            )
        unchanged = 0
        for url in wanted:
            aid = _aid(url)
            resp = client.get(url, accept="text/html", note=note, log_as=aid)
            res.seen_ids.add(aid)
            if resp.status in (404, 410):
                if aid in prev:
                    rows[aid] = _removed(prev[aid])
                else:
                    res.dropped[f"answer:{resp.status}"] += 1
                continue
            if resp.status != 200 or resp.truncated:
                raise FetchError(f"article {aid} answered HTTP {resp.status}")
            try:
                item = fetcher.item_from_page(url, resp.body.decode("utf-8", errors="replace"))
            except ValueError:
                res.dropped["not_an_article"] += 1
                continue
            reason = fetcher.third_party_reason(item)
            if reason:
                res.dropped[f"third_party:{reason}"] += 1
                res.third_party_new += int(aid not in prev)
                continue
            try:
                art = fetcher.build(item, now.replace(microsecond=0))
            except ValueError:
                res.dropped["invalid"] += 1
                continue
            old = prev.get(art.id)
            if old is None:
                rows[art.id] = json.loads(art.model_dump_json())
            elif old["content_hash"] == art.content_hash:
                unchanged += 1
            else:
                changed = json.loads(art.model_dump_json())
                changed["status"] = "changed"
                changed["codings"] = []
                rows[art.id] = changed
        res.route["unchanged"] = unchanged
        removed = still = 0
        for rid in missing:
            # The row's own page confirms a removal: only 404 or 410 removes it.
            resp = client.get(prev[rid]["url"], accept="text/html", note=note, log_as=rid)
            res.seen_ids.add(rid)
            if resp.status in (404, 410):
                rows[rid] = _removed(prev[rid])
                removed += 1
            elif resp.status == 200:
                still += 1
            else:
                raise FetchError(f"article {rid} answered HTTP {resp.status}")
        if listed is not None:
            res.route["removal_check"].update(  # type: ignore[union-attr]
                {"confirmed_removed": removed, "still_answer": still}
            )
    except (Blocked, Disallowed) as exc:
        return dict(prev), _page_skipped(res, client, "refused", exc), state
    except BudgetExceeded as exc:
        return dict(prev), _page_skipped(res, client, "over_budget", exc), state
    except _RouteStop as exc:
        return dict(prev), _page_skipped(res, client, exc.status, exc), state
    except FetchError as exc:
        return dict(prev), _page_skipped(res, client, "failed", exc), state
    for rid, d in rows.items():
        old = prev.get(rid)
        if old is None:
            if d.get("releasable", True):
                res.new_ids.append(rid)
            else:
                res.held += 1
        elif d is not old:
            if d["status"] == "removed":
                res.removed_ids.append(rid)
            elif d["status"] == "changed":
                res.changed_ids.append(rid)
    res.new, res.changed, res.removed = (
        len(res.new_ids),
        len(res.changed_ids),
        len(res.removed_ids),
    )
    res.requests, res.bytes = _usage(client)
    return rows, res, new_state


def _page_skipped(
    res: SourceUpdate, client: PoliteClient, status: str, exc: Exception
) -> SourceUpdate:
    fresh = _skipped(res, client, status, exc)
    fresh.route = dict(res.route) or {"route": PAGE_ROUTES[res.source_id].kind}
    return fresh


def page_state_from_backfill(source_id: str, folder: Path) -> dict[str, object]:
    """The route's state after a saved backfill run (no request): for a sitemap, the newest
    change date of its saved article sitemaps; for a listing, the ids of the stories on its
    first :data:`LISTING_PAGES` saved listing pages."""
    route = PAGE_ROUTES[source_id]
    lists = folder / "lists"
    if route.kind == "sitemap":
        dates = [
            d
            for path in sorted(lists.glob("sitemap-*.xml"))
            for u, d in sitemap_entries(path.read_text(encoding="utf-8", errors="replace"))
            if d is not None and re.match(route.article_pattern, u)
        ]
        if not dates:
            raise FetchError(f"{lists} holds no dated article sitemap")
        return {"through": _iso(max(dates))}
    ids: list[str] = []
    for n in range(1, LISTING_PAGES + 1):
        path = lists / f"listing-p{n:05d}.html"
        if not path.exists():
            break
        url = route.start if n == 1 else route.next_page.format(n=n)
        html = path.read_text(encoding="utf-8", errors="replace")
        ids += list(map(_aid, listing_links(html, url, route.article_pattern)))
    if not ids:
        raise FetchError(f"{lists} holds no saved listing page")
    if not (folder / URLS_FILE).exists():
        raise FetchError(f"{folder / URLS_FILE} is missing")
    return {"seen": sorted(set(ids))}


def run_route(
    root: Path,
    prev_dir: Path,
    source_id: str,
    work: Path,
    *,
    answers: Path | None = None,
    usage_log: Path | None = None,
    lock_dir: Path | None = None,
    max_requests: int = MAX_PAGE_REQUESTS,
    max_mb: float = 50,
    offline: bool = False,
    only_removals: bool = False,
    now: datetime | None = None,
    clients: ClientFactory | None = None,
    registry_path: Path | None = None,
    say: Callable[[str], None] = lambda _m: None,
) -> dict[str, object]:
    """One page source's weekly route alone, from a version (a dry run of the route): what
    it would read and build, as a summary of counts and ids in ``work``. No version is
    written. Answers are saved once in ``answers`` and replayed with ``offline``."""
    from commonswire.fetchers.base import ReplayStore
    from commonswire.release import ReleaseError
    from commonswire.sources import load_sources
    from commonswire.update import read_version

    if source_id not in PAGE_FETCHERS:
        raise ReleaseError(f"{source_id} is not read from its pages: no page route")
    manifest = json.loads((prev_dir / "manifest.json").read_text(encoding="utf-8"))
    if source_id not in manifest["sources"]:
        raise ReleaseError(f"version {manifest['version']} has no {source_id}")
    answers = answers or work / "answers"
    run_file = answers / RUN_FILE
    if run_file.exists():
        now = datetime.fromisoformat(json.loads(run_file.read_text())["now"])
    elif offline:
        raise ReleaseError(f"{run_file} is missing: nothing to replay offline")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    if not offline and not run_file.exists():
        answers.mkdir(parents=True, exist_ok=True)
        run_file.write_text(json.dumps({"now": now.isoformat(), "source": source_id}) + "\n")
    registry = load_sources(registry_path or root / "data" / "sources.csv")
    cache = AnswerCache(answers / "cache", offline=offline)
    log = UsageLog(usage_log or root / "data" / "usage_log.csv")
    clients = clients or default_clients(root, lock_dir or root / "data" / "interim" / "locks")
    client = clients(int(max_mb * 1e6), log, cache)
    say(f"reading version {manifest['version']} from {prev_dir}")
    _, prev_rows = read_version(prev_dir)
    held = {h["id"]: h for h in manifest.get("held_rows", []) if h["source_id"] == source_id}
    state = (manifest.get("page_state") or {}).get(source_id)
    fetcher = PAGE_FETCHERS[source_id](client, registry[source_id], ReplayStore(answers / "rs"))
    prev = prev_rows.get(source_id, {})
    rows, upd, new_state = update_pages(
        fetcher,
        client,
        prev,
        now=now,
        prev_as_of=str(manifest.get("as_of", "")),
        state=state,
        held=held,
        max_requests=max_requests,
        only_removals=only_removals,
    )
    say(upd.line())
    summary: dict[str, object] = {
        "source_id": source_id,
        "from_version": manifest["version"],
        "now": _iso(now),
        "offline": offline,
        "only_removals": only_removals,
        "state_before": state,
        "state_after": new_state,
        "rows_before": len(prev),
        "rows_after": sum(1 for d in rows.values() if d["status"] != "removed"),
        "update": upd.summary(),
        "new_ids": sorted(upd.new_ids),
        "changed_ids": sorted(upd.changed_ids),
        "removed_ids": sorted(upd.removed_ids),
        "answers_served_from_disk": cache.hits,
    }
    work.mkdir(parents=True, exist_ok=True)
    (work / "route-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
