"""The daily fetch, as a local command: new, changed and removed articles per source.

For each collected WordPress source:

- **new:** posts published after the newest one already stored (``after=``);
- **changed:** posts modified since the last run (``modified_after=``) whose text hash differs
  from the stored row: the row gets the new text and status ``changed``;
- **removed:** stored rows of the last ``window`` days that are gone from the source's listing
  of those days, and whose URL then answers 404 or 410: the row keeps its metadata, loses its
  text and gets status ``removed``.

Every API answer is saved once under ``data/raw/daily/<source>/<date>/``. The state (the last
run per source) is in ``data/interim/daily/state.json``. Wikinews is closed and is skipped.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from commonswire.backfill import save_once
from commonswire.fetchers.wordpress import WordPressFetcher
from commonswire.http import Blocked, Disallowed, FetchError, PoliteClient
from commonswire.schema import Article, text_hash

WINDOW_DAYS = 30
MAX_PAGES = 20


@dataclass
class DailyResult:
    source_id: str
    new: int = 0
    changed: int = 0
    removed: int = 0
    unchanged_modified: int = 0
    dropped: Counter[str] = field(default_factory=Counter)
    requests: int = 0
    note: str = ""

    def line(self) -> str:
        extra = f"; {self.note}" if self.note else ""
        drops = sum(self.dropped.values())
        return (
            f"{self.source_id}: {self.new} new, {self.changed} changed, {self.removed} removed, "
            f"{drops} dropped as third-party or invalid; {self.requests} requests{extra}"
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
) -> DailyResult:
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
            _take(fetcher, post, rows, by_url, res, now, new=True)
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
            resp = client.get(d["url"], accept="text/html", note=f"daily:{res.source_id}")
            res.requests += 1
            if resp.status in (404, 410):
                rows[rid] = {**d, "text": "", "content_hash": text_hash(""), "status": "removed"}
                Article.model_validate(rows[rid])
                res.removed += 1
    except (Blocked, Disallowed) as exc:
        res.note = f"refused: {exc}"
    except FetchError as exc:
        res.note = f"stopped: {exc}"
    write_rows(rows_path, rows)
    state["last_run"] = _iso(now)
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
