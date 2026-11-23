"""Backfills: a source's whole archive through its API, resumable, raw answers written once.

``backfill_wordpress`` asks a WordPress site for its posts oldest first (so posts published
during the run do not shift the pages), 100 at a time, with only the fields rows need. Every
answer is saved once under ``data/raw/backfill/<source>/<run>/`` (written to a temporary name,
flushed to the disk, then renamed), and ``progress.json`` records the totals. A run can be
stopped at any time: a rerun skips the pages already saved.

A page counted as fetched is always either on disk or reported. After each save the file is
looked up again (a write that never reached the disk, as when an external drive drops off the
bus, stops the run and names the page), and at the end every page from 1 to the last is
checked: a gap is named in ``stopped`` and ``missing_pages``, never left silent.
``check_backfill`` runs the same check on a saved run with no request.

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
from urllib.parse import urlencode

from commonswire.fetchers.wordpress import WordPressFetcher
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient

PAGE_NAME = "posts-p{:05d}.json"
CATEGORY_NAME = "categories-p{:03d}.json"
TAG_NAME = "tags-p{:04d}.json"


def _header(headers: object, name: str) -> str:
    for key, value in getattr(headers, "items", lambda: [])():
        if key.lower() == name.lower():
            return value
    return ""


def save_once(path: Path, body: bytes) -> bool:
    """Write a raw answer once: to a temporary name, flushed to the disk, renamed, and the
    folder flushed, so the answer is on disk when this returns, or an OSError is raised (for
    example when the drive has gone away). False if the file already exists."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with tmp.open("wb") as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    _fsync_folder(path.parent)
    return True


def _fsync_folder(folder: Path) -> None:
    """Flush a folder's entries (the rename) to the disk."""
    fd = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _on_disk(path: Path, size: int) -> bool:
    try:
        return path.stat().st_size == size
    except OSError:
        return False


def _page_number(path: Path) -> int | None:
    m = re.match(r"^posts-p(\d+)\.json$", path.name)
    return int(m.group(1)) if m else None


def missing_pages(folder: Path, total_pages: int | None) -> list[int]:
    """The page numbers from 1 to the last (``total_pages``, or the highest saved) that have
    no file."""
    have = {n for p in folder.glob("posts-p*.json") if (n := _page_number(p)) is not None}
    last = total_pages if total_pages is not None else max(have, default=0)
    return [n for n in range(1, last + 1) if n not in have]


def check_backfill(folder: Path) -> dict[str, object]:
    """A saved run, checked with no request: every page file from 1 to the last is there and
    holds a non-empty list of posts. The last page is ``total_pages`` in ``progress.json``, or
    the highest page saved when there is no progress file."""
    progress = {}
    if (folder / "progress.json").exists():
        progress = json.loads((folder / "progress.json").read_text())
    total_pages = progress.get("total_pages")
    pages = sorted(
        (n, p) for p in folder.glob("posts-p*.json") if (n := _page_number(p)) is not None
    )
    missing = missing_pages(folder, total_pages) if folder.exists() else []
    bad: list[int] = []
    posts = 0
    for n, path in pages:
        try:
            data = json.loads(path.read_bytes())
        except ValueError:
            bad.append(n)
            continue
        if not isinstance(data, list) or not data:
            bad.append(n)
            continue
        posts += len(data)
    expected = total_pages if total_pages is not None else (pages[-1][0] if pages else 0)
    return {
        "pages_expected": expected,
        "pages_present": len(pages),
        "missing_pages": missing,
        "empty_or_invalid": bad,
        "posts": posts,
        "total_posts": progress.get("total_posts"),
        "complete": bool(expected) and not missing and not bad,
    }


@dataclass
class Progress:
    source_id: str
    run: str
    total_posts: int | None = None
    total_pages: int | None = None
    pages_saved: int = 0
    category_pages: int = 0
    tag_pages: int = 0
    bytes_this_run: int = 0
    requests_this_run: int = 0
    finished: bool = False
    stopped: str = ""
    #: Page numbers from 1 to the last with no file at the end of the run (the first 50).
    missing_pages: list[int] = field(default_factory=list)
    updated_at: str = ""

    def save(self, folder: Path) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / "progress.json.part"
        tmp.write_text(json.dumps(self.__dict__, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, folder / "progress.json")


def _save_terms(
    client: PoliteClient,
    url_of: Callable[[int], str],
    folder: Path,
    name: str,
    note: str,
    progress: Progress,
) -> int:
    """Save a site's term names (categories or tags), 100 a page, once; return the pages."""
    page = 1
    while True:
        path = folder / name.format(page)
        if not path.exists():
            resp = _get(client, url_of(page), note, progress)
            if resp.status != 200:
                return page - 1
            data = resp.json()
            if not isinstance(data, list) or not data:
                return page - 1
            save_once(path, resp.body)
        data = json.loads(path.read_bytes())
        if len(data) < 100:
            return page
        page += 1


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
    with_tags: bool = False,
    say: Callable[[str], None] = lambda _m: None,
) -> Progress:
    """Save every page of a WordPress site's posts (and its category names) under ``folder``.
    With ``with_tags`` (series 0.3 on), each post's tag ids are asked for too, and the site's
    tag names are saved like its category names."""
    note = f"backfill:{fetcher.source_id}"
    progress = Progress(source_id=fetcher.source_id, run=run)
    old = folder / "progress.json"
    if old.exists():
        saved = json.loads(old.read_text())
        progress.total_posts = saved.get("total_posts")
        progress.total_pages = saved.get("total_pages")
    try:
        progress.category_pages = _save_terms(
            client, fetcher.categories_url, folder, CATEGORY_NAME, note, progress
        )
        if with_tags:
            progress.tag_pages = _save_terms(
                client, fetcher.tags_url, folder, TAG_NAME, note, progress
            )
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
            resp = _get(client, fetcher.backfill_url(page, with_tags=with_tags), note, progress)
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
            try:
                posts = resp.json()
            except ValueError:
                # Kept once, so the answer can be looked at; the run stops at this page.
                save_once(path.with_suffix(".notjson"), resp.body)
                progress.stopped = (
                    f"page {page} answered 200 with {len(resp.body):,} bytes that are not JSON "
                    f"(kept as {path.with_suffix('.notjson').name})"
                )
                break
            if not isinstance(posts, list) or not posts:
                break
            save_once(path, resp.body)
            if not _on_disk(path, len(resp.body)):
                progress.stopped = (
                    f"page {page} was fetched ({len(resp.body):,} bytes) but is not on disk; "
                    "check the data drive, then run the backfill again"
                )
                break
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
    except OSError as exc:
        progress.stopped = f"could not write to {folder}: {exc}"
    progress.pages_saved = len(list(folder.glob("posts-p*.json")))
    missing = missing_pages(folder, progress.total_pages)
    progress.missing_pages = missing[:50]
    if missing and not progress.stopped:
        shown = ", ".join(str(n) for n in missing[:10])
        progress.stopped = f"{len(missing)} pages missing: {shown}" + (
            ", ..." if len(missing) > 10 else ""
        )
    progress.finished = not progress.stopped and not missing
    progress.save(folder)
    return progress


def load_category_names(folder: Path, pattern: str = "categories-p*.json") -> dict[int, str]:
    names: dict[int, str] = {}
    for path in sorted(folder.glob(pattern)):
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
    tag_names = load_category_names(folder, "tags-p*.json")
    if tag_names:
        fetcher.tag_names = {**fetcher.tag_names, **tag_names}
    load_tags_run(fetcher, folder.parent)
    pages = sorted(folder.glob("posts-p*.json"))
    result.raw_files = (
        len(pages)
        + len(list(folder.glob("categories-p*.json")))
        + len(list(folder.glob("tags-p*.json")))
    )
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


POSTTAGS_NAME = "posttags-p{:05d}.json"
TAGNAMES_NAME = "tagnames-p{:04d}.json"


def backfill_tags(
    fetcher: WordPressFetcher,
    client: PoliteClient,
    folder: Path,
    *,
    run: str,
    max_requests: int | None = None,
    only_ids: list[int] | None = None,
    say: Callable[[str], None] = lambda _m: None,
) -> Progress:
    """The tags of an archive saved without them (series 0.3 on): every page of the site's
    posts with their ids and tag ids only, oldest first, then the names of the tags those
    posts use, 100 ids a request (never more requests than paging every tag). Saved once
    under ``folder`` (``posttags-pNNNNN.json``, ``tagnames-pNNNN.json``); a rerun skips
    what is saved. With ``only_ids``, only those posts are asked for, 100 ids a request
    (``posttags-ids-pNNNN.json``): the few pages of a run that were saved without tags."""
    note = f"tags:{fetcher.source_id}"
    progress = Progress(source_id=fetcher.source_id, run=run)
    old = folder / "progress.json"
    if old.exists():
        saved = json.loads(old.read_text())
        progress.total_posts = saved.get("total_posts")
        progress.total_pages = saved.get("total_pages")

    def budget_left() -> bool:
        return max_requests is None or progress.requests_this_run < max_requests

    try:
        if only_ids is not None:
            ids_sorted = sorted(set(only_ids))
            progress.total_pages = -(-len(ids_sorted) // 100)
            progress.total_posts = len(ids_sorted)
        page = 1
        while only_ids is None and (progress.total_pages is None or page <= progress.total_pages):
            path = folder / POSTTAGS_NAME.format(page)
            if path.exists():
                page += 1
                continue
            if not budget_left():
                progress.stopped = f"stopped after {max_requests} requests, as asked"
                break
            resp = _get(client, fetcher.tags_only_url(page), note, progress)
            if resp.status == 400 and page > 1:
                break
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
            progress.save(folder)
            if page % 100 == 0:
                say(f"{fetcher.source_id}: tags page {page} of {progress.total_pages or '?'}")
            page += 1
        if only_ids is not None:
            for n, begin in enumerate(range(0, len(ids_sorted), 100), start=1):
                path = folder / f"posttags-ids-p{n:04d}.json"
                if path.exists():
                    continue
                if not budget_left():
                    progress.stopped = f"stopped after {max_requests} requests, as asked"
                    break
                chunk = ",".join(str(i) for i in ids_sorted[begin : begin + 100])
                url = f"{fetcher.api_base}/wp-json/wp/v2/posts?" + urlencode(
                    {"include": chunk, "per_page": "100", "_fields": "id,tags"}
                )
                resp = _get(client, url, note, progress)
                if resp.status != 200:
                    progress.stopped = f"posts by id {n} answered HTTP {resp.status}"
                    break
                save_once(path, resp.body)
        if not progress.stopped:
            used = sorted({t for ids in load_post_tags(folder).values() for t in ids})
            for n, start in enumerate(range(0, len(used), 100), start=1):
                path = folder / TAGNAMES_NAME.format(n)
                if path.exists():
                    continue
                if not budget_left():
                    progress.stopped = f"stopped after {max_requests} requests, as asked"
                    break
                ids = ",".join(str(t) for t in used[start : start + 100])
                url = f"{fetcher.api_base}/wp-json/wp/v2/tags?" + urlencode(
                    {"include": ids, "per_page": "100", "_fields": "id,name"}
                )
                resp = _get(client, url, note, progress)
                if resp.status != 200:
                    progress.stopped = f"tag names {n} answered HTTP {resp.status}"
                    break
                save_once(path, resp.body)
            progress.tag_pages = len(list(folder.glob("tagnames-p*.json")))
    except (Blocked, Disallowed) as exc:
        progress.stopped = f"refused: {exc}"
    except BudgetExceeded as exc:
        progress.stopped = f"budget: {exc}"
    except FetchError as exc:
        progress.stopped = f"error: {exc}"
    except OSError as exc:
        progress.stopped = f"could not write to {folder}: {exc}"
    if only_ids is not None:
        progress.pages_saved = len(list(folder.glob("posttags-ids-p*.json")))
        missing = [
            n
            for n in range(1, (progress.total_pages or 0) + 1)
            if not (folder / f"posttags-ids-p{n:04d}.json").exists()
        ]
    else:
        progress.pages_saved = len(list(folder.glob("posttags-p*.json")))
        have = {int(p.name[10:15]) for p in folder.glob("posttags-p*.json")}
        missing = [n for n in range(1, (progress.total_pages or 0) + 1) if n not in have]
    progress.missing_pages = missing[:50]
    if missing and not progress.stopped:
        progress.stopped = f"{len(missing)} tag pages missing"
    progress.finished = not progress.stopped
    progress.save(folder)
    return progress


def load_post_tags(folder: Path) -> dict[int, tuple[int, ...]]:
    """Post id -> tag ids, from a tags backfill run (or a backfill asked with tags)."""
    out: dict[int, tuple[int, ...]] = {}
    for path in sorted(folder.glob("posttags-*.json")):
        for post in json.loads(path.read_bytes()):
            if isinstance(post, dict) and isinstance(post.get("id"), int):
                tags = post.get("tags")
                out[post["id"]] = tuple(t for t in tags if isinstance(t, int)) if tags else ()
    return out


def load_tags_run(fetcher: WordPressFetcher, source_folder: Path) -> int:
    """Put the latest tags run of a source (``<run>-tags`` beside its backfill runs) into the
    fetcher: post ids' tags and the tag names. Returns the posts it covers."""
    runs = sorted(p for p in source_folder.glob("*-tags") if p.is_dir())
    if not runs:
        return 0
    folder = runs[-1]
    fetcher.post_tags = {**fetcher.post_tags, **load_post_tags(folder)}
    fetcher.tag_names = {**fetcher.tag_names, **load_category_names(folder, "tagnames-p*.json")}
    return len(fetcher.post_tags)
