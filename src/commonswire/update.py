"""The weekly update: the next version, built from the published one, with no state of its own.

``commonswire update --from PREV --out NEXT`` reads a published version (its Parquet files,
``manifest.json`` and ``sources.csv``, downloaded or local) and builds the next one:

1. **Checks before any request.** The previous version passes its own manifest check; the
   registry (``data/sources.csv``) is byte for byte the one the previous version carries, and
   the next version has the same sources (a new source or a registry change always needs the
   maintainer); no takedown request is open and no earlier update waits as a pull request on
   the dataset (both counted by the caller). Any of these stops the run before it sends
   anything.
2. **Each source that still publishes**, one at a time, through the polite client: its
   category names (to drop partner stories), its users endpoint where the bylines came from
   it (Alt News), the posts published in the last ``window`` days, and the older posts edited
   in that window. These are ``daily``'s rules (:func:`commonswire.daily._take`): a post not
   in the previous version is new; a post whose text hash differs is changed (status
   ``changed``); a row of the window that the listing no longer has and whose page answers 404
   or 410 is removed. Rows already released keep their bylines from the previous version; a
   new row takes its byline from the API, from its own page (360info, The Public Record,
   Balkan Diskurs) or, for Global Voices, from the listing's first pages (writers and
   translators apart).
3. **The build:** the previous rows, plus the new ones, with the changed ones replaced, minus
   the removed ones and the takedown list, through ``release build``'s own checks (every row
   validated and its credit line checked), the near-duplicate flags over every row, the card
   and the manifest, then ``release check`` on the written files.
4. **Stops after the build:** a source that refused, failed or ran over its byte budget (it is
   skipped, its rows carried over, and it is named; never worked around), a failed check, or
   a version that would shrink by more than ``max_shrink`` in all or for one source.

Held rows are not published, so the manifest carries their ids to the next version (with the
source, the day and the reason, never an address or a name), and the count of third-party
posts dropped; version 0.2.0's come from ``data/update-baseline.json``. A run commits nothing,
so its requests are summed per host and day into the manifest (``update.requests``).

Every answer is saved once in the run's answer folder (:class:`commonswire.http.AnswerCache`):
a stopped run resumes without asking again, and ``--offline`` replays a finished run with no
request at all. What the command prints, and the summary it writes, hold counts, ids and
hosts only: never article text, titles, names or article addresses.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from commonswire.daily import DailyResult, _removed, _take
from commonswire.fetchers import WORDPRESS
from commonswire.fetchers.base import ReplayStore
from commonswire.fetchers.wordpress import WordPressFetcher
from commonswire.http import (
    AnswerCache,
    Blocked,
    BudgetExceeded,
    Disallowed,
    FetchError,
    PoliteClient,
    Transport,
    UsageLog,
    make_client,
)
from commonswire.release import (
    CONFIGURATIONS,
    ReleaseError,
    collect,
    series_sources,
    sha256,
    verify,
    write_release,
)
from commonswire.schema import canonical_url
from commonswire.sources import Source, load_sources

WINDOW_DAYS = 30
#: Listing pages of 100 posts read per listing at most; a fuller listing is a site change.
MAX_PAGES = 20
#: Rows of the window missing from the listing whose pages are checked at most; more means
#: the listing itself is wrong, and the source stops.
MAX_REMOVAL_CHECKS = 25
#: Global Voices listing pages read at most for new stories' writers.
MAX_LISTING_PAGES = 20
#: The share of rows a version may lose (in all, or for one source) before the run stops,
#: and the number of rows a source may always lose.
MAX_SHRINK = 0.01
SHRINK_FLOOR = 10
#: Sources whose rows took their bylines from the WordPress users endpoint.
USERS_ENDPOINT = frozenset({"altnews"})
#: Sources that no longer publish: their rows are carried over with no request.
CLOSED = {"wikinews_en": "closed since 2026-05-04; its archive comes from the dump"}
BASELINE = "update-baseline.json"
#: The run's fixed clock, saved with its answers so that an offline replay builds the same.
RUN_FILE = "run.json"

_URL = re.compile(r"https?://([^/\s\"'<>]+)[^\s\"'<>]*")


def redact(text: str) -> str:
    """A message with every web address cut to its host, for logs that are public."""
    return _URL.sub(lambda m: f"{m.group(1)}/...", text)


def next_version(version: str) -> str:
    """0.2.0 -> 0.2.1."""
    major, minor, patch = (int(x) for x in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _from_release(r: dict) -> dict:
    """A released row as a stored row again (the columns the release adds are dropped)."""
    return {
        "id": r["id"],
        "source_id": r["source_id"],
        "url": r["url"],
        "title": r["title"],
        "authors": list(r.get("authors") or []),
        "translators": list(r.get("translators") or []),
        "published_at": _iso(r["published_at"]),
        "updated_at": _iso(r.get("updated_at")),
        "retrieved_at": _iso(r["retrieved_at"]),
        "language": r["language"],
        "section": r.get("section") or "",
        "text": r["text"],
        "license": r["license"],
        "credit_line": r["credit_line"],
        "third_party": False,
        "content_hash": r["content_hash"],
        "status": r.get("status") or "live",
        "releasable": True,
        "hold_reason": "",
        "codings": [],
    }


def read_version(folder: Path) -> tuple[dict, dict[str, dict[str, dict]]]:
    """A published version's manifest and its rows (source -> id -> stored row)."""
    import pyarrow.parquet as pq

    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows: dict[str, dict[str, dict]] = {s: {} for s in manifest["sources"]}
    for config in CONFIGURATIONS:
        for name in manifest["configurations"].get(config, []):
            for r in pq.read_table(folder / name).to_pylist():
                rows.setdefault(r["source_id"], {})[r["id"]] = _from_release(r)
    return manifest, rows


def carried_state(manifest: dict, folder: Path, baseline: Path) -> tuple[dict, int] | None:
    """The held rows (id -> source, day, reason) and the third-party count of a version, from
    its manifest, or for a version built before updates from the baseline file (which must
    name that version and its manifest's SHA-256). None if neither has them."""
    if "held_rows" in manifest:
        held = {h["id"]: {k: v for k, v in h.items() if k != "id"} for h in manifest["held_rows"]}
        return held, int(manifest.get("third_party_dropped", 0))
    if not baseline.exists():
        return None
    base = json.loads(baseline.read_text(encoding="utf-8"))
    if base.get("version") != manifest["version"]:
        return None
    if base.get("manifest_sha256") != sha256(folder / "manifest.json"):
        return None
    held = {h["id"]: {k: v for k, v in h.items() if k != "id"} for h in base["held_rows"]}
    return held, int(base["third_party_dropped"])


@dataclass
class SourceUpdate:
    """What one source's update did: counts only."""

    source_id: str
    status: str = "updated"  # updated, closed, refused, failed, over_budget
    note: str = ""
    listed: int = 0
    new: int = 0
    held: int = 0
    changed: int = 0
    removed: int = 0
    removal_checks: int = 0
    third_party_new: int = 0
    page_bylines: int = 0
    listing: dict[str, object] = field(default_factory=dict)
    dropped: Counter[str] = field(default_factory=Counter)
    requests: int = 0
    bytes: int = 0
    #: Ids only: rows this run built (any outcome), and the new, changed and removed ones.
    seen_ids: set[str] = field(default_factory=set)
    new_ids: list[str] = field(default_factory=list)
    changed_ids: list[str] = field(default_factory=list)
    removed_ids: list[str] = field(default_factory=list)

    @property
    def skipped(self) -> bool:
        return self.status in ("refused", "failed", "over_budget")

    def summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "note": self.note,
            "posts_listed": self.listed,
            "new": self.new,
            "held": self.held,
            "changed": self.changed,
            "removed": self.removed,
            "removal_checks": self.removal_checks,
            "third_party_dropped_new": self.third_party_new,
            "bylines_from_pages": self.page_bylines,
            "listing_credits": self.listing,
            "dropped": dict(sorted(self.dropped.items())),
            "requests": self.requests,
            "bytes": self.bytes,
        }

    def line(self) -> str:
        if self.status == "closed":
            return f"{self.source_id}: skipped, {self.note}"
        head = f"{self.source_id}: {self.status}"
        if self.note:
            head += f" ({self.note})"
        return (
            f"{head}; {self.listed} posts listed, {self.new} new, {self.changed} changed, "
            f"{self.removed} removed, {self.held} held; {self.requests} requests, "
            f"{self.bytes:,} bytes"
        )


class _Pages:
    """Pages of a WordPress listing, 100 posts each, until a short page (or a 400 past the
    last page). A listing longer than ``MAX_PAGES`` pages is an error, never a crawl."""

    def __init__(self, fetcher: WordPressFetcher, client: PoliteClient, note: str) -> None:
        self.fetcher, self.client, self.note = fetcher, client, note

    def posts(self, path: str, params: dict[str, str]) -> Iterator[dict]:
        for page in range(1, MAX_PAGES + 1):
            q = {"per_page": "100", "page": str(page), **params}
            url = f"{self.fetcher.api_base}/wp-json/wp/v2/{path}?{urlencode(q)}"
            resp = self.client.get(url, accept="application/json", note=self.note)
            if resp.status == 400 and page > 1:
                return
            if resp.status != 200 or resp.truncated:
                raise FetchError(f"{url} answered HTTP {resp.status}")
            data = resp.json()
            if not isinstance(data, list):
                raise FetchError(f"{url} did not answer with a list")
            yield from data
            if len(data) < 100:
                return
        raise FetchError(f"{self.fetcher.api_base}: more than {MAX_PAGES} pages of {path}")


def _seed_bylines(fetcher: WordPressFetcher, prev: dict[str, dict]) -> None:
    """The bylines of rows already released, as the fetcher's byline maps: a changed row keeps
    its writers and translators without a new request for its page or listing."""
    for d in prev.values():
        try:
            key = canonical_url(d["url"])
        except ValueError:
            continue
        if d["authors"]:
            fetcher.page_bylines[key] = tuple(d["authors"])
        elif fetcher.requires_byline:
            fetcher.source_credited.add(key)  # released with no person: credited to the source
        if d.get("translators"):
            fetcher.page_translators[key] = tuple(d["translators"])


def _listing_credits(
    fetcher: WordPressFetcher,
    client: PoliteClient,
    posts: list[dict],
    known: dict[str, str],
    res: SourceUpdate,
    *,
    held: dict[str, dict] | None = None,
    prev_as_of: str = "",
) -> None:
    """For Global Voices: the writers and translators of new stories with no byline, from
    the listing's first pages, put into the fetcher's byline maps.

    A story the previous version already held, and that has not been edited since that
    version, keeps its recorded reason with no new look at the listing: otherwise every week
    would walk back to the oldest held story of the 30 days."""
    from commonswire.listingbylines import LISTING_MARKUP, listing_credits
    from commonswire.schema import article_id

    if fetcher.source_id not in LISTING_MARKUP:
        return
    held = held or {}
    wanted: dict[str, str] = {}
    kept = 0
    for post in posts:
        try:
            item = fetcher.item_from_post(post)
            key = canonical_url(item.url)
        except (ValueError, KeyError, TypeError):
            continue
        if item.url in known or item.authors or fetcher.third_party_reason(item):
            continue
        before = held.get(article_id(item.url))
        if before and (_iso(item.updated_at) or "") <= prev_as_of:
            if str(before.get("reason", "")).startswith("credited to an account"):
                fetcher.byline_why_none[key] = "not_a_person"
            kept += 1
            continue
        wanted[key] = item.published_at.date().isoformat()
    got, st = listing_credits(
        client,
        fetcher.source_id,
        wanted,
        source_name=fetcher.source.name,
        max_pages=MAX_LISTING_PAGES,
    )
    for key, v in got.items():
        if v["names"]:
            fetcher.page_bylines[key] = tuple(v["names"])
        if v["translators"]:
            fetcher.page_translators[key] = tuple(v["translators"])
        if v["why_none"] == "source_itself":
            fetcher.source_credited.add(key)
        if v["why_none"]:
            fetcher.byline_why_none[key] = v["why_none"]
    res.listing = {
        "held_kept_unedited": kept,
        "wanted": len(wanted),
        "found": st.stories,
        "with_writer": st.with_writer,
        "with_translators": st.translated,
        "why_none": dict(sorted(st.why_none.items())),
        "not_found": len(wanted) - st.stories,
        "pages": st.pages_fetched,
        "end": st.end,
    }
    if st.stopped:
        raise _ListingStopped(st.stopped)


class _ListingStopped(Exception):
    """The listing refused or failed: the source stops."""


def update_wordpress(
    fetcher: WordPressFetcher,
    client: PoliteClient,
    prev: dict[str, dict],
    *,
    now: datetime,
    since: datetime,
    prev_as_of: str,
    pages_dir: Path,
    held: dict[str, dict] | None = None,
) -> tuple[dict[str, dict], SourceUpdate]:
    """One source's update over the window. Returns the source's rows after the update (the
    previous rows unchanged if the source refused, failed or ran over its budget) and what
    happened, as counts and ids. ``held`` is the previous version's held rows (id -> source,
    day, reason)."""
    from commonswire.pagebylines import SITE_MARKUP, PageBylineReader

    sid = fetcher.source_id
    res = SourceUpdate(source_id=sid)
    note = f"update:{sid}"
    pager = _Pages(fetcher, client, note)
    since_s = since.strftime("%Y-%m-%dT%H:%M:%S")
    since_iso = _iso(since) or ""
    fields = fetcher.backfill_fields
    rows = dict(prev)
    try:
        fetcher.category_names = {
            int(c["id"]): str(c.get("name", ""))
            for c in pager.posts("categories", {"_fields": "id,name"})
            if isinstance(c, dict) and "id" in c
        }
        if sid in USERS_ENDPOINT:
            fetcher.byline_map = {
                int(u["id"]): (str(u["name"]),)
                for u in pager.posts("users", {"_fields": "id,name"})
                if isinstance(u, dict) and u.get("name")
            }
        _seed_bylines(fetcher, prev)
        recent = list(
            pager.posts(
                "posts", {"after": since_s, "orderby": "date", "order": "asc", "_fields": fields}
            )
        )
        edited = list(
            pager.posts(
                "posts",
                {
                    "modified_after": since_s,
                    "before": since_s,
                    "orderby": "date",
                    "order": "asc",
                    "_fields": fields,
                },
            )
        )
        posts: list[dict] = []
        links: set[str] = set()
        for post in recent + edited:
            link = post.get("link") if isinstance(post, dict) else None
            if not link or link in links:
                continue
            links.add(link)
            posts.append(post)
        res.listed = len(posts)
        known = {d["url"]: rid for rid, d in prev.items()}
        _listing_credits(fetcher, client, posts, known, res, held=held, prev_as_of=prev_as_of)
        reader = None
        if sid in SITE_MARKUP and fetcher.requires_byline:
            reader = PageBylineReader(
                client,
                sid,
                pages_dir / sid,
                pages_dir / f"{sid}.pages.json",
                source_name=fetcher.source.name,
            )
        daily = DailyResult(source_id=sid)
        by_url = dict(known)
        for post in posts:
            try:
                item = fetcher.item_from_post(post)
            except (ValueError, KeyError, TypeError):
                item = None
            if (
                item is not None
                and fetcher.third_party_reason(item)
                and (_iso(item.published_at) or "") > prev_as_of
            ):
                res.third_party_new += 1
            _take(fetcher, post, rows, by_url, daily, now, new=True, pages=reader)
            if item is not None and item.url in by_url:
                res.seen_ids.add(by_url[item.url])
        if reader is not None:
            res.page_bylines = daily.page_bylines
            if reader.stats.stopped:
                raise _ListingStopped(reader.stats.stopped)
        res.dropped = daily.dropped
        listed = {p.get("link") for p in recent}
        missing = [
            (rid, d)
            for rid, d in sorted(prev.items())
            if d["published_at"] >= since_iso and d["url"] not in listed
        ]
        if len(missing) > MAX_REMOVAL_CHECKS:
            raise FetchError(
                f"{len(missing)} rows of the last days are missing from the listing (more than "
                f"{MAX_REMOVAL_CHECKS}): the listing looks wrong"
            )
        for rid, d in missing:
            # One article's page: the request log records its id, not its address.
            resp = client.get(d["url"], accept="text/html", note=note, log_as=rid)
            res.removal_checks += 1
            if resp.status in (404, 410):
                rows[rid] = _removed(d)
                res.seen_ids.add(rid)
    except (Blocked, Disallowed) as exc:
        return dict(prev), _skipped(res, client, "refused", exc)
    except BudgetExceeded as exc:
        return dict(prev), _skipped(res, client, "over_budget", exc)
    except _ListingStopped as exc:
        why = str(exc)
        status = (
            "refused"
            if why.startswith(("Blocked", "Disallowed"))
            else "over_budget"
            if why.startswith("BudgetExceeded")
            else "failed"
        )
        return dict(prev), _skipped(res, client, status, exc)
    except FetchError as exc:
        return dict(prev), _skipped(res, client, "failed", exc)
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
    return rows, res


def _usage(client: PoliteClient) -> tuple[int, int]:
    rows = client.usage_log.recent
    return len(rows), sum(int(r["bytes"]) for r in rows)  # type: ignore[call-overload]


def _skipped(res: SourceUpdate, client: PoliteClient, status: str, exc: Exception) -> SourceUpdate:
    fresh = SourceUpdate(source_id=res.source_id, status=status, note=redact(str(exc))[:300])
    fresh.listed, fresh.listing = res.listed, res.listing
    fresh.requests, fresh.bytes = _usage(client)
    return fresh


def requests_by_host_and_day(rows: list[dict[str, object]]) -> dict[str, dict[str, dict]]:
    """The request log of a run, summed: host -> day -> requests, bytes and statuses."""
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        host, day = str(r["host"]), str(r["time"])[:10]
        cell = out[host].setdefault(day, {"requests": 0, "bytes": 0, "statuses": Counter()})
        cell["requests"] += 1
        cell["bytes"] += int(r["bytes"])  # type: ignore[call-overload]
        cell["statuses"][str(r["status"])] += 1
    return {
        h: {d: {**c, "statuses": dict(sorted(c["statuses"].items()))} for d, c in sorted(v.items())}
        for h, v in sorted(out.items())
    }


#: Makes a source's polite client from its byte budget, the request log and the answer cache.
ClientFactory = Callable[[int, UsageLog, AnswerCache], PoliteClient]


def default_clients(
    root: Path, lock_dir: Path, transport: Transport | None = None
) -> ClientFactory:
    """Real polite clients, paced through ``lock_dir`` (one request at a time per host)."""

    def make(budget: int, log: UsageLog, cache: AnswerCache) -> PoliteClient:
        return make_client(
            root,
            byte_budget=budget,
            transport=transport,
            usage_log=log,
            lock_dir=lock_dir,
            cache=cache,
        )

    return make


@dataclass
class UpdateResult:
    """What a run did and found: counts, ids and hosts only."""

    from_version: str
    version: str
    dry_run: bool
    status: str = "ready"  # ready, unchanged, stopped
    stop_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    sources: dict[str, SourceUpdate] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""
    seconds: float = 0.0
    window_days: int = WINDOW_DAYS
    since: str = ""
    rows_before: int = 0
    rows_after: int = 0
    rows_by_source_before: dict[str, int] = field(default_factory=dict)
    rows_by_source_after: dict[str, int] = field(default_factory=dict)
    rows_by_configuration: dict[str, int] = field(default_factory=dict)
    held: int = 0
    taken_down_ids: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    requests: dict[str, dict[str, dict]] = field(default_factory=dict)
    out: str = ""
    size_bytes: int = 0

    @property
    def ready_to_deliver(self) -> bool:
        return self.status == "ready" and not self.dry_run

    def stop(self, reason: str) -> None:
        self.status = "stopped"
        self.stop_reasons.append(redact(reason))

    def summary(self) -> dict[str, object]:
        def ids(name: str) -> list[str]:
            return sorted(i for s in self.sources.values() for i in getattr(s, name))

        return {
            "status": self.status,
            "dry_run": self.dry_run,
            "ready_to_deliver": self.ready_to_deliver,
            "from_version": self.from_version,
            "version": self.version,
            "stop_reasons": self.stop_reasons,
            "notes": self.notes,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "seconds": round(self.seconds, 1),
            "window_days": self.window_days,
            "since": self.since,
            "rows_before": self.rows_before,
            "rows_after": self.rows_after,
            "rows_by_source_before": self.rows_by_source_before,
            "rows_by_source_after": self.rows_by_source_after,
            "rows_by_configuration": self.rows_by_configuration,
            "held_rows_not_released": self.held,
            "sources": {k: v.summary() for k, v in self.sources.items()},
            "ids": {
                "new": ids("new_ids"),
                "changed": ids("changed_ids"),
                "removed": ids("removed_ids"),
                "taken_down": sorted(self.taken_down_ids),
            },
            "checks": self.checks,
            "requests": self.requests,
            "out": self.out,
            "size_bytes": self.size_bytes,
        }

    def markdown(self, max_ids: int = 40) -> str:
        """The summary for a pull request or an issue: counts, ids and hosts only."""
        s = self.summary()
        lines = [
            f"**CommonsWire {self.version}**, built from {self.from_version} "
            f"({self.window_days} days up to {self.finished_at[:10]}): **{self.status}**"
            + (" (dry run)" if self.dry_run else ""),
            "",
            f"Rows: {self.rows_before:,} before, {self.rows_after:,} after; "
            f"held back: {self.held:,}.",
            "",
        ]
        if self.stop_reasons:
            lines += ["Stopped because:", *[f"- {r}" for r in self.stop_reasons], ""]
        lines += [
            "| Source | Status | New | Changed | Removed | Held | Requests | Bytes |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for sid, u in self.sources.items():
            lines.append(
                f"| {sid} | {u.status} | {u.new} | {u.changed} | {u.removed} | {u.held} | "
                f"{u.requests} | {u.bytes:,} |"
            )
        lines.append("")
        for sid, u in self.sources.items():
            if u.note and u.status != "closed":
                lines.append(f"- {sid}: {u.note}")
            if u.listing:
                lines.append(f"- {sid} listing credits: {json.dumps(u.listing, sort_keys=True)}")
        idmap = s["ids"]  # type: ignore[index]
        for name in ("new", "changed", "removed", "taken_down"):
            got = idmap[name]  # type: ignore[index]
            if got:
                more = f" and {len(got) - max_ids} more" if len(got) > max_ids else ""
                lines.append(f"- {name.replace('_', ' ')} ids: {', '.join(got[:max_ids])}{more}")
        lines += ["", "Checks: " + ("all passed" if not self.checks else "; ".join(self.checks))]
        hosts = ", ".join(
            f"{h} {sum(d['requests'] for d in v.values())} requests "
            f"({sum(d['bytes'] for d in v.values()):,} bytes)"
            for h, v in self.requests.items()
        )
        lines.append(f"Requests: {hosts or 'none'}.")
        lines += [*[f"Note: {n}" for n in self.notes]]
        return "\n".join(lines) + "\n"


def run_update(
    root: Path,
    prev_dir: Path,
    out: Path,
    work: Path,
    *,
    registry_path: Path,
    takedowns_path: Path,
    baseline_path: Path,
    version: str | None = None,
    answers: Path | None = None,
    usage_log: Path | None = None,
    lock_dir: Path | None = None,
    now: datetime | None = None,
    window: int = WINDOW_DAYS,
    max_mb: float = 300,
    max_mb_per_source: float = 100,
    max_shrink: float = MAX_SHRINK,
    open_takedowns: int = 0,
    open_dataset_prs: int = 0,
    allow_skipped: frozenset[str] = frozenset(),
    dry_run: bool = True,
    offline: bool = False,
    clients: ClientFactory | None = None,
    say: Callable[[str], None] = lambda _m: None,
) -> UpdateResult:
    """A whole weekly run, from the version in ``prev_dir`` to the next one in ``out``.
    ``clients`` makes each source's polite client (tests pass one with a fake clock)."""
    import time

    from commonswire.release_text import card, licenses_md

    clock = time.monotonic()
    answers = answers or work / "answers"
    run_file = answers / RUN_FILE
    # A replay, or a run resumed in the same answer folder, keeps the clock of the first run.
    if run_file.exists():
        now = datetime.fromisoformat(json.loads(run_file.read_text())["now"])
    elif offline:
        raise ReleaseError(f"{run_file} is missing: nothing to replay offline")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    manifest = json.loads((prev_dir / "manifest.json").read_text(encoding="utf-8"))
    version = version or next_version(manifest["version"])
    res = UpdateResult(from_version=manifest["version"], version=version, dry_run=dry_run)
    res.window_days = window
    since = now - timedelta(days=window)
    res.started_at, res.since = _iso(now) or "", _iso(since) or ""

    # 1. Checks before any request.
    for problem in verify(prev_dir, ignore_hidden=True):
        res.stop(f"the previous version fails its own check: {problem}")
    if registry_path.read_bytes() != (prev_dir / "sources.csv").read_bytes():
        res.stop(
            "the registry (data/sources.csv) differs from the one in the previous version: a "
            "registry change needs the maintainer"
        )
    try:
        sources = series_sources(version)
    except ReleaseError as exc:
        sources = ()
        res.stop(str(exc))
    if sources and list(sources) != list(manifest["sources"]):
        res.stop(
            f"version {version} has the sources {', '.join(sources)}, the previous version "
            f"{', '.join(manifest['sources'])}: a new source needs the maintainer"
        )
    if open_takedowns:
        res.stop(f"{open_takedowns} takedown request(s) are open: apply them first")
    if open_dataset_prs:
        res.stop(f"{open_dataset_prs} pull request(s) on the dataset are still open")
    state = carried_state(manifest, prev_dir, baseline_path)
    if state is None:
        res.stop(
            f"version {manifest['version']} carries no list of held rows, and {baseline_path.name} "
            "does not match it"
        )
    if out.exists() and any(out.iterdir()):
        res.stop(f"{out} is not empty: a version is never overwritten")
    if res.stop_reasons:
        return _finish(res, clock)
    assert state is not None
    held_prev, third_prev = state

    # 2. Each source, one at a time.
    say(f"reading version {manifest['version']} from {prev_dir}")
    _, prev_rows = read_version(prev_dir)
    res.rows_by_source_before = {s: len(prev_rows.get(s, {})) for s in sources}
    res.rows_before = int(manifest["rows"])
    registry = load_sources(registry_path)
    if not offline and not run_file.exists():
        answers.mkdir(parents=True, exist_ok=True)
        run_file.write_text(json.dumps({"now": now.isoformat(), "version": version}) + "\n")
    cache = AnswerCache(answers / "cache", offline=offline)
    log = UsageLog(usage_log or work / "usage_log.csv")
    clients = clients or default_clients(root, lock_dir or work / "locks")
    budget_left = int(max_mb * 1e6)
    merged: dict[str, dict[str, dict]] = {}
    for sid in sources:
        if sid in CLOSED:
            merged[sid] = prev_rows.get(sid, {})
            res.sources[sid] = SourceUpdate(source_id=sid, status="closed", note=CLOSED[sid])
            say(res.sources[sid].line())
            continue
        if sid not in WORDPRESS:
            merged[sid] = prev_rows.get(sid, {})
            res.sources[sid] = SourceUpdate(sid, status="failed", note="no update route")
            say(res.sources[sid].line())
            continue
        src_log = UsageLog(log.path)
        client = clients(max(0, min(int(max_mb_per_source * 1e6), budget_left)), src_log, cache)
        fetcher = WORDPRESS[sid](client, registry[sid], ReplayStore(answers / sid))
        rows, upd = update_wordpress(
            fetcher,
            client,
            prev_rows.get(sid, {}),
            now=now,
            since=since,
            prev_as_of=str(manifest.get("as_of", "")),
            pages_dir=answers / "pages",
            held={k: v for k, v in held_prev.items() if v["source_id"] == sid},
        )
        budget_left -= client.bytes_used
        log.recent.extend(src_log.recent)
        merged[sid] = rows
        res.sources[sid] = upd
        say(upd.line())
    res.requests = requests_by_host_and_day(log.recent)

    # 3. The build, with the counts carried from the previous version.
    rel = collect(
        root,
        version,
        registry,
        rows={s: list(merged[s].values()) for s in sources},
        takedowns_path=takedowns_path,
    )
    seen = {i for u in res.sources.values() for i in u.seen_ids}
    held = {k: v for k, v in held_prev.items() if k not in seen and k not in rel.checks.held_ids}
    held.update(rel.checks.held_ids)
    rel.checks.held = Counter(v["source_id"] for v in held.values())
    rel.checks.held_reasons = Counter(v["reason"] for v in held.values())
    published = {rid: d["published_at"] for rows in merged.values() for rid, d in rows.items()}
    prev_as_of = str(manifest.get("as_of", ""))
    new_dupes = Counter(
        f"same_text:{merged_source(merged, rid)}"
        for rid in rel.checks.duplicate_ids
        if published.get(rid, "") > prev_as_of
    )
    rel.checks.exact_duplicates = Counter(manifest.get("exact_duplicates_dropped", {})) + new_dupes
    rel.checks.removed = Counter(manifest.get("removed_rows_not_released", {})) + rel.checks.removed
    rel.checks.taken_down = (
        Counter(manifest.get("taken_down_rows_not_released", {})) + rel.checks.taken_down
    )
    res.taken_down_ids = list(rel.checks.taken_down_ids)
    third = third_prev + sum(u.third_party_new for u in res.sources.values())
    res.held = len(held)
    if not rel.checks.ok:
        for problem in rel.checks.problems():
            res.stop(f"check failed: {problem}")
    counts = rel.counts()
    res.rows_after = int(counts["rows"])  # type: ignore[call-overload]
    res.rows_by_configuration = dict(counts["rows_by_configuration"])  # type: ignore[call-overload]
    by_source = counts["rows_by_source"]
    res.rows_by_source_after = {s: sum(by_source[s].values()) for s in sources}  # type: ignore[index]
    changes = {
        "new": sum(u.new for u in res.sources.values()),
        "changed": sum(u.changed for u in res.sources.values()),
        "removed": sum(u.removed for u in res.sources.values()),
        "taken_down": len(res.taken_down_ids),
    }
    for sid, u in res.sources.items():
        if u.skipped:
            why = f"{sid} was {u.status.replace('_', ' ')}: {u.note}"
            if sid in allow_skipped:
                res.notes.append(f"{why} (skipped, as allowed)")
            else:
                res.stop(f"{why}; its rows were carried over unchanged")
    _shrink(res, max_shrink)
    if res.stop_reasons and not rel.checks.ok:
        return _finish(res, clock)

    update_info = {
        "from_version": manifest["version"],
        "window_days": window,
        "as_of": now.date().isoformat(),
        **changes,
    }
    extra = {
        "third_party_dropped": third,
        "held_rows": [{"id": k, **v} for k, v in sorted(held.items())],
        "update": {
            **update_info,
            "since": res.since,
            "sources": {k: v.summary() for k, v in res.sources.items()},
            "requests": res.requests,
        },
    }
    say(f"writing version {version} to {out}")
    manifest_out = write_release(
        rel,
        out,
        registry_path,
        registry,
        card=card(rel, registry, third, update=update_info),
        licenses_md=licenses_md(rel, registry),
        extra=extra,
    )
    for problem in verify(out):
        res.stop(f"release check: {problem}")
    res.checks = [r for r in res.stop_reasons if r.startswith(("check failed", "release check"))]
    res.out = str(out)
    res.size_bytes = sum(int(f["bytes"]) for f in manifest_out["files"])  # type: ignore[union-attr]
    if res.status == "ready" and not any(changes.values()):
        res.status = "unchanged"
    return _finish(res, clock)


def merged_source(merged: dict[str, dict[str, dict]], rid: str) -> str:
    for sid, rows in merged.items():
        if rid in rows:
            return sid
    return "?"


def _shrink(res: UpdateResult, max_shrink: float) -> None:
    if res.rows_after < res.rows_before * (1 - max_shrink):
        res.stop(
            f"the version would shrink from {res.rows_before:,} to {res.rows_after:,} rows "
            f"(more than {max_shrink:.0%})"
        )
    for sid, before in res.rows_by_source_before.items():
        after = res.rows_by_source_after.get(sid, 0)
        if before - after > max(SHRINK_FLOOR, before * max_shrink):
            res.stop(f"{sid} would shrink from {before:,} to {after:,} rows")


def _finish(res: UpdateResult, clock: float) -> UpdateResult:
    import time

    res.seconds = time.monotonic() - clock
    res.finished_at = _iso(datetime.now(timezone.utc)) or ""
    if res.status == "ready" and res.stop_reasons:
        res.status = "stopped"
    return res


def baseline(root: Path, version: str, registry: dict[str, Source]) -> dict[str, object]:
    """The held rows and the third-party count of a version built before updates existed,
    from the stored rows and the build evidence it was built from (no request). The counts
    must match the version's manifest; the caller writes ``data/update-baseline.json``."""
    rel = collect(root, version, registry)
    release_dir = root / "data" / "release" / version
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    if dict(rel.checks.held) != manifest["held_rows_not_released"]:
        raise ReleaseError(
            f"the stored rows hold {dict(rel.checks.held)} back, the manifest of {version} "
            f"{manifest['held_rows_not_released']}: the rows changed since the build"
        )
    third = 0
    for s in rel.sources:
        path = root / "data" / "evidence" / "backfill" / f"{s}.build.json"
        if path.exists():
            info = json.loads(path.read_text())
            drops = info.get("dropped") or info.get("skipped") or {}
            third += sum(v for k, v in drops.items() if k.startswith("third_party"))
    return {
        "version": version,
        "manifest_sha256": sha256(release_dir / "manifest.json"),
        "note": (
            f"What version {version}'s manifest does not carry and an update needs: the ids of "
            "its held rows (with source, day and reason; no address, no name) and the count of "
            "third-party posts dropped. Later versions carry both in their manifest."
        ),
        "third_party_dropped": third,
        "held_rows": [{"id": k, **v} for k, v in sorted(rel.checks.held_ids.items())],
    }
