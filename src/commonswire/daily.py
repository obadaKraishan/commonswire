"""The daily fetch, as a local command: new, changed and removed articles per source.

For each collected WordPress source:

- **new:** posts published after the newest one already stored (``after=``);
- **changed:** posts modified since the last run (``modified_after=``) whose text hash differs
  from the stored row: the row gets the new text and status ``changed``;
- **removed:** stored rows of the last ``window`` days that are gone from the source's listing
  of those days, and whose URL then answers 404 or 410: the row keeps its metadata, loses its
  text and gets status ``removed``.

Every API answer is saved once under ``data/raw/daily/<source>/<date>/``, numbered in the
order it came, and so is a small record of every removal found (``NNN-removed.json``: the URL
and its status). The state (the last run per source) is in ``data/interim/daily/state.json``.
Wikinews is closed and is skipped.

:func:`replay_daily` applies the saved answers again, day by day and in their order, to rows
rebuilt from a backfill, with no request: ``commonswire build`` runs it, so a rebuild keeps
the rows that ``daily`` added, changed or removed (maintainer's decision, 2026-11-13).
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from commonswire.backfill import save_once
from commonswire.fetchers.wordpress import WordPressFetcher
from commonswire.http import Blocked, Disallowed, FetchError, PoliteClient
from commonswire.schema import Article, text_hash

if TYPE_CHECKING:
    from commonswire.pagebylines import PageBylineReader

WINDOW_DAYS = 30
MAX_PAGES = 20


@dataclass
class DailyResult:
    source_id: str
    new: int = 0
    changed: int = 0
    removed: int = 0
    unchanged_modified: int = 0
    held: int = 0
    page_bylines: int = 0
    dropped: Counter[str] = field(default_factory=Counter)
    requests: int = 0
    note: str = ""

    def line(self) -> str:
        extra = f"; {self.note}" if self.note else ""
        drops = sum(self.dropped.values())
        pages = f", {self.page_bylines} bylines from article pages" if self.page_bylines else ""
        return (
            f"{self.source_id}: {self.new} new, {self.changed} changed, {self.removed} removed, "
            f"{drops} dropped as third-party or invalid; {self.held} new rows held{pages}; "
            f"{self.requests} requests{extra}"
        )


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def load_rows(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                rows[d["id"]] = d
    return rows


def write_rows(path: Path, rows: dict[str, dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".part")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as fh:
        for d in sorted(rows.values(), key=lambda r: (r["published_at"], r["id"])):
            fh.write(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, path)


class _Pager:
    def __init__(
        self, fetcher: WordPressFetcher, client: PoliteClient, raw: Path, res: DailyResult
    ):
        self.fetcher, self.client, self.raw, self.res = fetcher, client, raw, res
        self.n = len(list(raw.glob("*.json"))) if raw.exists() else 0

    def pages(self, label: str, params: dict[str, str]):  # type: ignore[no-untyped-def]
        for page in range(1, MAX_PAGES + 1):
            q = {"per_page": "100", "page": str(page), **params}
            url = f"{self.fetcher.api_base}/wp-json/wp/v2/posts?{urlencode(q)}"
            resp = self.client.get(
                url, accept="application/json", note=f"daily:{self.res.source_id}"
            )
            self.res.requests += 1
            if resp.status == 400 and page > 1:
                return
            if resp.status != 200:
                raise FetchError(f"{url} answered HTTP {resp.status}")
            self.n += 1
            save_once(self.raw / f"{self.n:03d}-{label}-p{page}.json", resp.body)
            posts = resp.json()
            if not isinstance(posts, list) or not posts:
                return
            yield from posts
            if len(posts) < 100:
                return


def daily_wordpress(
    fetcher: WordPressFetcher,
    client: PoliteClient,
    rows_path: Path,
    raw: Path,
    state: dict[str, str],
    now: datetime,
    window: int = WINDOW_DAYS,
    page_bylines: PageBylineReader | None = None,
) -> DailyResult:
    """One daily pass over a source. With ``page_bylines``, a new post with no byline gets
    the name from its article page (fetched once), as ``commonswire page-bylines`` does."""
    res = DailyResult(source_id=fetcher.source_id)
    rows = load_rows(rows_path)
    if not rows:
        res.note = "no stored rows: run the backfill first"
        return res
    by_url = {d["url"]: i for i, d in rows.items()}
    newest = max(d["published_at"] for d in rows.values())
    last_run = state.get("last_run") or newest
    pager = _Pager(fetcher, client, raw, res)
    fields = fetcher.backfill_fields
    try:
        for post in pager.pages(
            "new", {"after": newest[:19], "orderby": "date", "order": "asc", "_fields": fields}
        ):
            _take(fetcher, post, rows, by_url, res, now, new=True, pages=page_bylines)
        for post in pager.pages("modified", {"modified_after": last_run[:19], "_fields": fields}):
            _take(fetcher, post, rows, by_url, res, now, new=False)
        since = now - timedelta(days=window)
        listed = {
            p.get("link")
            for p in pager.pages("listing", {"after": _iso(since), "_fields": "id,link"})
        }
        for rid, d in list(rows.items()):
            if d["status"] == "removed" or d["published_at"] < _iso(since):
                continue
            if d["url"] in listed:
                continue
            # One article's page: the request log records its id, not its address.
            resp = client.get(
                d["url"], accept="text/html", note=f"daily:{res.source_id}", log_as=rid
            )
            res.requests += 1
            if resp.status in (404, 410):
                pager.n += 1
                record = {"url": d["url"], "status": resp.status, "checked_at": _iso(now)}
                save_once(raw / f"{pager.n:03d}-removed.json", json.dumps(record).encode())
                rows[rid] = _removed(d)
                res.removed += 1
    except (Blocked, Disallowed) as exc:
        res.note = f"refused: {exc}"
    except FetchError as exc:
        res.note = f"stopped: {exc}"
    write_rows(rows_path, rows)
    state["last_run"] = _iso(now)
    return res


def _removed(row: dict) -> dict:
    out = {**row, "text": "", "content_hash": text_hash(""), "status": "removed"}
    Article.model_validate(out)
    return out


#: The saved daily answers: ``001-new-p1.json``, ``002-modified-p1.json``,
#: ``003-listing-p1.json``, ``004-removed.json``.
DAILY_FILE = re.compile(r"^(\d+)-(new|modified|listing|removed)(?:-p\d+)?\.json$")


@dataclass
class ReplayResult(DailyResult):
    days: int = 0
    files: int = 0


def replay_daily(fetcher: WordPressFetcher, rows_path: Path, daily: Path) -> ReplayResult:
    """Apply the saved daily answers under ``daily`` (one folder a day) to the rows in
    ``rows_path``, oldest day first and in the order they were saved, with no request.

    New and modified posts go through the same rules as in ``daily`` (third-party material
    dropped, bylines from the saved names, a changed text marked ``changed``); a saved removal
    marks its row ``removed``. A row's ``retrieved_at`` is the time its answer was saved.
    Listing answers are not replayed: what they said is in the removal records.
    """
    res = ReplayResult(source_id=fetcher.source_id)
    if not daily.is_dir():
        return res
    rows = load_rows(rows_path)
    by_url = {d["url"]: i for i, d in rows.items()}
    for day in sorted(p for p in daily.iterdir() if p.is_dir()):
        files = []
        for f in day.glob("*.json"):
            m = DAILY_FILE.match(f.name)
            if m:
                files.append((int(m.group(1)), f.name, m.group(2), f))
        if not files:
            continue
        res.days += 1
        for _, _, label, f in sorted(files):
            res.files += 1
            saved = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).replace(microsecond=0)
            data = json.loads(f.read_bytes())
            if label in ("new", "modified"):
                for post in data if isinstance(data, list) else []:
                    _take(fetcher, post, rows, by_url, res, saved, new=label == "new")
            elif label == "removed" and isinstance(data, dict):
                rid = by_url.get(str(data.get("url", "")))
                if rid and rows[rid]["status"] != "removed":
                    rows[rid] = _removed(rows[rid])
                    res.removed += 1
    write_rows(rows_path, rows)
    return res


def _take(
    fetcher: WordPressFetcher,
    post: dict,
    rows: dict[str, dict],
    by_url: dict[str, str],
    res: DailyResult,
    now: datetime,
    *,
    new: bool,
    pages: PageBylineReader | None = None,
) -> None:
    try:
        item = fetcher.item_from_post(post)
    except (ValueError, KeyError, TypeError):
        res.dropped["invalid"] += 1
        return
    reason = fetcher.third_party_reason(item)
    if reason:
        res.dropped[f"third_party:{reason}"] += 1
        return
    if pages is not None and new and not item.authors and item.url not in by_url:
        before = pages.stats.pages_fetched
        names = pages.read(item.url)
        res.requests += pages.stats.pages_fetched - before
        if names:
            item = dataclasses.replace(item, authors=names)
            res.page_bylines += 1
        elif pages.credits_source(item.url):
            item = dataclasses.replace(item, hints={**item.hints, "byline_is_source": True})
    try:
        art = fetcher.build(item, now.replace(microsecond=0))
    except ValueError:
        res.dropped["invalid"] += 1
        return
    old_id = by_url.get(item.url)
    if old_id is None:
        rows[art.id] = json.loads(art.model_dump_json())
        by_url[item.url] = art.id
        res.new += 1
        res.held += int(not art.releasable)
        return
    old = rows[old_id]
    if old["content_hash"] == art.content_hash:
        if not new:
            res.unchanged_modified += 1
        return
    changed = json.loads(art.model_dump_json())
    changed["status"] = "changed"
    changed["codings"] = []
    rows[old_id] = changed
    res.changed += 1


def load_state(path: Path) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text()) if path.exists() else {}


def save_state(path: Path, state: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
