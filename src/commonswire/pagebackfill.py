"""Backfills from article pages, for sources whose API does not give their articles.

SciDev.Net's articles are a custom post type that its WordPress API does not expose, and
Africa Is a Country has no API, feed or sitemap. Their archives are read from article pages,
in two steps, both resumable, every answer written once under
``data/raw/backfill/<source>/<run>/``:

1. **The list of articles** (:func:`collect_urls`): from a sitemap index (the article
   sitemaps it lists, each read once) or from listing pages (page 1, 2, ... until a page
   brings no new article or answers 404). Each sitemap or listing page is saved under
   ``lists/``, and the article addresses found go into ``urls.json``, in order, once.
2. **The pages** (:func:`fetch_pages`): each article page is fetched once through the polite
   client and saved unchanged as ``pages/<id>.html``, with ``pages/<id>.json`` holding its
   address, final address, status and time. The request log names the page by the article's
   id (``log_as``), never by its address. A 404 or 410 is recorded (no page), a robots.txt
   that disallows the page is recorded, and a 5xx or timeout after the client's own retries
   is left unrecorded so a rerun tries it again. A refusal (401, 403, 451 or a bot check)
   stops the run: it is never worked around. ``progress.json`` holds the counts.

:func:`check_pages` checks a saved run with no request: every address in ``urls.json`` has
an answer recorded, and every saved page is on disk at its recorded size. A gap is named,
never left silent.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin, urlsplit

from commonswire.backfill import BuildResult, _short, save_once
from commonswire.fetchers.pages import PageFetcher
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient
from commonswire.schema import article_id, canonical_url

URLS_FILE = "urls.json"
PROGRESS_FILE = "progress.json"
#: Answers recorded with no page: gone, or not to be fetched.
RECORDED_WITHOUT_PAGE = ("404", "410", "disallowed")


@dataclass(frozen=True)
class PageRoute:
    """How a source's article pages are found.

    ``kind`` is ``sitemap`` (``start`` is the sitemap index, and ``sitemap_pattern`` picks the
    article sitemaps in it) or ``listing`` (``start`` is the listing's first page and
    ``next_page`` the address of page N, with ``{n}``). ``article_pattern`` is what an
    article's address must match; anything else on a sitemap or listing is ignored."""

    source_id: str
    kind: Literal["sitemap", "listing"]
    start: str
    article_pattern: str
    sitemap_pattern: str = ""
    next_page: str = ""
    max_listing_pages: int = 3000


PAGE_ROUTES: dict[str, PageRoute] = {
    "scidevnet": PageRoute(
        source_id="scidevnet",
        kind="sitemap",
        start="https://www.scidev.net/global/sitemap_index.xml",
        sitemap_pattern=r"^https://www\.scidev\.net/global/article-sitemap\d*\.xml$",
        article_pattern=r"^https://www\.scidev\.net/global/[^?#]+$",
    ),
    # No API, feed or sitemap: the front-page category, 20 stories a page, newest first.
    "africasacountry": PageRoute(
        source_id="africasacountry",
        kind="listing",
        start="https://africasacountry.com/category/front-page",
        next_page="https://africasacountry.com/category/front-page?page={n}",
        article_pattern=r"^https://africasacountry\.com/\d{4}/\d{2}/[a-z0-9-]+$",
    ),
}


@dataclass
class PageProgress:
    source_id: str
    run: str
    urls: int = 0
    list_pages: int = 0
    recorded: int = 0
    pages_saved: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    bytes_this_run: int = 0
    requests_this_run: int = 0
    retry_later: int = 0
    finished: bool = False
    stopped: str = ""
    updated_at: str = ""

    def save(self, folder: Path) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / (PROGRESS_FILE + ".part")
        tmp.write_text(json.dumps(self.__dict__, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, folder / PROGRESS_FILE)


_LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*([^<\]\s]+)\s*(?:\]\]>)?\s*</loc>", re.I)
_HREF = re.compile(r"""href\s*=\s*["']([^"'#]+)["']""", re.I)


def sitemap_locs(xml: str) -> list[str]:
    """The ``<loc>`` addresses of a sitemap or sitemap index, in order."""
    return [unescape(m.group(1)) for m in _LOC.finditer(xml)]


def listing_links(html: str, base: str, pattern: str) -> list[str]:
    """The article addresses a listing page links to, in order, each once."""
    rx = re.compile(pattern)
    out: list[str] = []
    for m in _HREF.finditer(html):
        url = urljoin(base, unescape(m.group(1)).strip())
        url = url.split("?", 1)[0]
        if rx.match(url) and url not in out:
            out.append(url)
    return out


def _unique(urls: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for u in urls:
        key = canonical_url(u)
        if key not in seen:
            seen.add(key)
            out.append(u)
    return out


def _fetch_list_page(
    client: PoliteClient, url: str, path: Path, note: str, progress: PageProgress
) -> str | None:
    """A sitemap or listing page, read from its saved copy or fetched once and saved; None
    when it answers 404 or 410."""
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    resp = client.get(url, note=note)
    progress.requests_this_run += 1
    progress.bytes_this_run += len(resp.body)
    if resp.status in (404, 410):
        return None
    if resp.status != 200:
        raise FetchError(f"{url} answered HTTP {resp.status}")
    save_once(path, resp.body)
    progress.list_pages += 1
    return resp.body.decode("utf-8", errors="replace")


def collect_urls(
    client: PoliteClient,
    route: PageRoute,
    folder: Path,
    progress: PageProgress,
    *,
    say: Callable[[str], None] = lambda _m: None,
) -> list[str]:
    """The article addresses of the source, from ``urls.json`` when a run already has it."""
    urls_file = folder / URLS_FILE
    if urls_file.exists():
        return json.loads(urls_file.read_text(encoding="utf-8"))
    note = f"backfill:{route.source_id}:list"
    lists = folder / "lists"
    found: list[str] = []
    if route.kind == "sitemap":
        index = _fetch_list_page(client, route.start, lists / "index.xml", note, progress)
        if index is None:
            raise FetchError(f"the sitemap index {route.start} is gone")
        maps = [u for u in sitemap_locs(index) if re.match(route.sitemap_pattern, u)]
        say(f"{route.source_id}: {len(maps)} article sitemaps")
        for i, url in enumerate(maps, start=1):
            xml = _fetch_list_page(client, url, lists / f"sitemap-{i:03d}.xml", note, progress)
            if xml is None:
                raise FetchError(f"the sitemap {url} is gone")
            found += [u for u in sitemap_locs(xml) if re.match(route.article_pattern, u)]
    else:
        for n in range(1, route.max_listing_pages + 1):
            url = route.start if n == 1 else route.next_page.format(n=n)
            html = _fetch_list_page(client, url, lists / f"listing-p{n:05d}.html", note, progress)
            if html is None:
                say(f"{route.source_id}: listing page {n} answered 404; the listing ends")
                break
            new = [u for u in listing_links(html, url, route.article_pattern) if u not in found]
            if not new:
                say(f"{route.source_id}: listing page {n} brought no new article; it ends")
                break
            found += new
            if n % 50 == 0:
                say(f"{route.source_id}: {n} listing pages, {len(found)} articles")
                progress.save(folder)
    urls = _unique(found)
    save_once(urls_file, (json.dumps(urls, indent=0) + "\n").encode("utf-8"))
    progress.urls = len(urls)
    progress.save(folder)
    return urls


def page_paths(folder: Path, url: str) -> tuple[Path, Path]:
    """The saved page and its record: ``pages/<id>.html`` and ``pages/<id>.json``."""
    aid = article_id(canonical_url(url))
    return folder / "pages" / f"{aid}.html", folder / "pages" / f"{aid}.json"


def _record(path: Path, data: dict[str, object]) -> None:
    save_once(path, (json.dumps(data, sort_keys=True) + "\n").encode("utf-8"))


def fetch_pages(
    client: PoliteClient,
    route: PageRoute,
    urls: list[str],
    folder: Path,
    progress: PageProgress,
    *,
    max_requests: int | None = None,
    say: Callable[[str], None] = lambda _m: None,
) -> PageProgress:
    """Fetch every article page not yet recorded; see the module docstring."""
    note = f"backfill:{route.source_id}"
    progress.urls = len(urls)
    statuses = Counter(progress.by_status)
    try:
        for i, url in enumerate(urls, start=1):
            html_path, meta_path = page_paths(folder, url)
            if meta_path.exists():
                continue
            if max_requests is not None and progress.requests_this_run >= max_requests:
                progress.stopped = f"the request limit of {max_requests} for this run is reached"
                break
            aid = meta_path.stem
            when = datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                resp = client.get(url, note=note, log_as=aid)
            except Disallowed:
                _record(meta_path, {"url": url, "status": "disallowed", "retrieved_at": when})
                statuses["disallowed"] += 1
                progress.recorded += 1
                continue
            except Blocked as exc:
                progress.stopped = (
                    f"the site refused page {i} (HTTP {exc.status}, {exc.reason}); the run "
                    "stops here and is never worked around"
                )
                break
            except BudgetExceeded:
                raise  # the run's own limit, handled below
            except FetchError:
                progress.retry_later += 1
                continue
            progress.requests_this_run += 1
            progress.bytes_this_run += len(resp.body)
            status = str(resp.status)
            if resp.status == 200:
                save_once(html_path, resp.body)
                if html_path.stat().st_size != len(resp.body):
                    raise OSError(f"{html_path} is not on the disk at its size")
            elif status not in RECORDED_WITHOUT_PAGE:
                # A 5xx after the client's retries, or another answer: try again next run.
                progress.retry_later += 1
                statuses[status] += 1
                continue
            _record(
                meta_path,
                {
                    "url": url,
                    "final_url": resp.url,
                    "status": status,
                    "bytes": len(resp.body),
                    "retrieved_at": when,
                },
            )
            statuses[status] += 1
            progress.recorded += 1
            progress.pages_saved += resp.status == 200
            if progress.recorded % 100 == 0:
                progress.by_status = dict(sorted(statuses.items()))
                progress.save(folder)
                say(
                    f"{route.source_id}: {progress.recorded:,} recorded this run "
                    f"({i:,} of {len(urls):,}), {progress.bytes_this_run / 1e6:,.1f} MB"
                )
    except BudgetExceeded:
        progress.stopped = "the byte budget is used up; ask before fetching more"
    progress.by_status = dict(sorted(statuses.items()))
    done = sum(1 for u in urls if page_paths(folder, u)[1].exists())
    progress.finished = not progress.stopped and done == len(urls)
    progress.save(folder)
    return progress


def check_pages(folder: Path) -> dict[str, object]:
    """A saved run, checked with no request (see the module docstring)."""
    urls_file = folder / URLS_FILE
    if not urls_file.exists():
        return {"urls": 0, "complete": False, "problem": f"{urls_file} is missing"}
    urls = json.loads(urls_file.read_text(encoding="utf-8"))
    statuses: Counter[str] = Counter()
    missing: list[str] = []
    bad: list[str] = []
    for url in urls:
        html_path, meta_path = page_paths(folder, url)
        if not meta_path.exists():
            missing.append(meta_path.stem)
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        statuses[meta["status"]] += 1
        if meta["status"] == "200":
            try:
                ok = html_path.stat().st_size == meta["bytes"]
            except OSError:
                ok = False
            if not ok:
                bad.append(meta_path.stem)
    return {
        "urls": len(urls),
        "recorded": sum(statuses.values()),
        "by_status": dict(sorted(statuses.items())),
        "not_yet_recorded": len(missing),
        "first_not_recorded": missing[:20],
        "pages_not_on_disk_at_their_size": bad[:20],
        "complete": not missing and not bad,
    }


def host_of(route: PageRoute) -> str:
    return (urlsplit(route.start).hostname or "").lower()


def build_page_rows(fetcher: PageFetcher, folder: Path, out: Path) -> BuildResult:
    """Rows from the saved pages of a run (no requests), in the order of ``urls.json``,
    written to ``out``. A page that is not an article, a repeated address and third-party
    material are dropped and counted; every row is checked by the schema."""
    result = BuildResult(source_id=fetcher.source_id)
    urls = json.loads((folder / URLS_FILE).read_text(encoding="utf-8"))
    seen: set[str] = set()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    with tmp.open("w", encoding="utf-8") as fh:
        for url in urls:
            html_path, meta_path = page_paths(folder, url)
            if not meta_path.exists():
                result.dropped["not_fetched"] += 1
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta["status"] != "200":
                result.dropped[f"answer:{meta['status']}"] += 1
                continue
            result.seen += 1
            result.raw_files += 1
            body = html_path.read_bytes()
            result.raw_bytes += len(body)
            try:
                item = fetcher.item_from_page(url, body.decode("utf-8", errors="replace"))
            except ValueError as exc:
                result.dropped[f"not_an_article:{str(exc)[:60]}"] += 1
                continue
            key = canonical_url(item.url)
            if key in seen:
                result.dropped["duplicate_url"] += 1
                continue
            seen.add(key)
            reason = fetcher.third_party_reason(item)
            if reason:
                result.dropped[f"third_party:{reason}"] += 1
                continue
            retrieved = datetime.fromisoformat(meta["retrieved_at"])
            try:
                article = fetcher.build(item, retrieved)
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
