"""Backfills: a source's whole archive through its API, resumable, raw answers written once.

``backfill_wordpress`` asks a WordPress site for its posts oldest first (so posts published
during the run do not shift the pages), 100 at a time, with only the fields rows need. Every
answer is saved once under ``data/raw/backfill/<source>/<run>/`` (written to a temporary name,
then renamed), and ``progress.json`` records the totals. A run can be stopped at any time: a
rerun skips the pages already saved.

``build_rows`` turns the saved answers into rows with no request at all: third-party material
is dropped and counted, repeated URLs are dropped and counted, and every row is checked by the
schema. The output is JSON Lines plus a counts-only summary.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from commonswire.fetchers.wordpress import WordPressFetcher
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient

PAGE_NAME = "posts-p{:05d}.json"
CATEGORY_NAME = "categories-p{:03d}.json"


def _header(headers: object, name: str) -> str:
    for key, value in getattr(headers, "items", lambda: [])():
        if key.lower() == name.lower():
            return value
    return ""


def save_once(path: Path, body: bytes) -> bool:
    """Write a raw answer once (temporary name, then rename). False if it already exists."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(body)
    os.replace(tmp, path)
    return True


@dataclass
class Progress:
    source_id: str
    run: str
    total_posts: int | None = None
    total_pages: int | None = None
    pages_saved: int = 0
    category_pages: int = 0
    bytes_this_run: int = 0
    requests_this_run: int = 0
    finished: bool = False
    stopped: str = ""
    updated_at: str = ""

    def save(self, folder: Path) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / "progress.json.part"
        tmp.write_text(json.dumps(self.__dict__, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, folder / "progress.json")


def _get(client: PoliteClient, url: str, note: str, progress: Progress) -> object:
    resp = client.get(url, accept="application/json", note=note)
    progress.requests_this_run += 1
    progress.bytes_this_run += len(resp.body)
    return resp


def backfill_wordpress(
    fetcher: WordPressFetcher,
    client: PoliteClient,
    folder: Path,
    *,
    run: str,
    max_pages: int | None = None,
    say: Callable[[str], None] = lambda _m: None,
) -> Progress:
    """Save every page of a WordPress site's posts (and its category names) under ``folder``."""
    note = f"backfill:{fetcher.source_id}"
    progress = Progress(source_id=fetcher.source_id, run=run)
    old = folder / "progress.json"
    if old.exists():
        saved = json.loads(old.read_text())
        progress.total_posts = saved.get("total_posts")
        progress.total_pages = saved.get("total_pages")
    try:
        page = 1
        while True:
            path = folder / CATEGORY_NAME.format(page)
            if not path.exists():
                resp = _get(client, fetcher.categories_url(page), note, progress)
                if resp.status != 200:
                    break
                data = resp.json()
                if not isinstance(data, list) or not data:
                    break
                save_once(path, resp.body)
            progress.category_pages = page
            page += 1
            data = json.loads(path.read_bytes())
            if len(data) < 100:
                break
        page = 1
        done_this_run = 0
        while True:
            if progress.total_pages is not None and page > progress.total_pages:
                break
            path = folder / PAGE_NAME.format(page)
            if path.exists():
                page += 1
                continue
            if max_pages is not None and done_this_run >= max_pages:
                progress.stopped = f"stopped after {max_pages} pages, as asked"
                break
            resp = _get(client, fetcher.backfill_url(page), note, progress)
            if resp.status == 400 and page > 1:
                break  # past the last page
            if resp.status != 200:
                progress.stopped = f"page {page} answered HTTP {resp.status}"
                break
            if progress.total_posts is None:
                total = _header(resp.headers, "X-WP-Total")
                pages = _header(resp.headers, "X-WP-TotalPages")
                progress.total_posts = int(total) if total.isdigit() else None
                progress.total_pages = int(pages) if pages.isdigit() else None
            posts = resp.json()
            if not isinstance(posts, list) or not posts:
                break
            save_once(path, resp.body)
            done_this_run += 1
            progress.save(folder)
            if page % 25 == 0:
                say(f"{fetcher.source_id}: page {page} of {progress.total_pages or '?'}")
            page += 1
        else:  # pragma: no cover - the loop always breaks
            pass
    except (Blocked, Disallowed) as exc:
        progress.stopped = f"refused: {exc}"
    except BudgetExceeded as exc:
        progress.stopped = f"budget: {exc}"
    except FetchError as exc:
        progress.stopped = f"error: {exc}"
    progress.pages_saved = len(list(folder.glob("posts-p*.json")))
    progress.finished = not progress.stopped and (
        progress.total_pages is None or progress.pages_saved >= progress.total_pages
    )
    progress.save(folder)
    return progress


def load_category_names(folder: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    for path in sorted(folder.glob("categories-p*.json")):
        for row in json.loads(path.read_bytes()):
            if isinstance(row, dict) and "id" in row:
                names[int(row["id"])] = str(row.get("name", ""))
    return names


@dataclass
class BuildResult:
    source_id: str
    seen: int = 0
    kept: int = 0
    releasable: int = 0
    #: Releasable rows with no personal author, whose page byline names the source itself.
    credited_to_source: int = 0
    dropped: Counter[str] = field(default_factory=Counter)
    raw_files: int = 0
    raw_bytes: int = 0
    rows_bytes: int = 0
    first: str = ""
    last: str = ""

    def summary(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "seen": self.seen,
            "kept": self.kept,
            "releasable": self.releasable,
            "credited_to_source": self.credited_to_source,
            "dropped": dict(sorted(self.dropped.items())),
            "raw_files": self.raw_files,
            "raw_bytes": self.raw_bytes,
            "rows_bytes": self.rows_bytes,
            "first": self.first,
            "last": self.last,
        }


def _short(exc: Exception) -> str:
    for line in str(exc).splitlines():
        line = line.strip()
        if line and not line.startswith(("1 validation error", "For further")):
            return re.sub(r"\s*\[type=.*$", "", line)[:70]
    return type(exc).__name__


def build_rows(fetcher: WordPressFetcher, folder: Path, out: Path) -> BuildResult:
    """Rows from the saved answers of a backfill (no requests), written to ``out``."""
    result = BuildResult(source_id=fetcher.source_id)
    fetcher.category_names = load_category_names(folder)
    pages = sorted(folder.glob("posts-p*.json"))
    result.raw_files = len(pages) + len(list(folder.glob("categories-p*.json")))
    result.raw_bytes = sum(p.stat().st_size for p in folder.glob("*.json"))
    retrieved = datetime.fromtimestamp(pages[0].stat().st_mtime, timezone.utc) if pages else None
    seen_urls: set[str] = set()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    with tmp.open("w", encoding="utf-8") as fh:
        for path in pages:
            fetched = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(
                microsecond=0
            )
            for post in json.loads(path.read_bytes()):
                result.seen += 1
                try:
                    item = fetcher.item_from_post(post)
                except (ValueError, KeyError, TypeError) as exc:
                    result.dropped[f"invalid:{_short(exc)}"] += 1
                    continue
                if item.url in seen_urls:
                    result.dropped["duplicate_url"] += 1
                    continue
                seen_urls.add(item.url)
                reason = fetcher.third_party_reason(item)
                if reason:
                    result.dropped[f"third_party:{reason}"] += 1
                    continue
                try:
                    article = fetcher.build(item, max(fetched, retrieved or fetched))
                except ValueError as exc:
                    result.dropped[f"invalid:{_short(exc)}"] += 1
                    continue
                line = article.model_dump_json() + "\n"
                fh.write(line)
                result.rows_bytes += len(line.encode("utf-8"))
                result.kept += 1
                result.releasable += int(article.releasable)
                result.credited_to_source += int(
                    article.releasable and not article.authors and fetcher.requires_byline
                )
                day = article.published_at.date().isoformat()
                result.first = min(result.first or day, day)
                result.last = max(result.last or day, day)
    os.replace(tmp, out)
    return result
