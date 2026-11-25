"""The polite HTTP client that every CommonsWire request goes through.

The rules it enforces:

- **One request at a time per host**, across processes: a lock file per host is held for the
  whole request, and requests to a host start at least ``min_interval`` seconds (2 by default)
  after the previous one to that host ended. Different hosts may be fetched in parallel.
- **robots.txt** is read once per host and honored for the CommonsWire user agent, including any
  crawl-delay longer than ``min_interval``. A robots.txt that answers 401 or 403 is treated as a
  block; 404 or 410 means there is none; a 5xx answer means the site may not be crawled now.
- **Backoff** on 429 and 5xx answers and on network errors, honoring ``Retry-After`` up to a cap.
- **Blocks are never worked around.** A 401, 403 or 451 answer, or a bot-check page, raises
  :class:`Blocked` at once; there is no retry with other headers, no cache or mirror, and no
  other user agent.
- **Redirects** are followed by hand, so each hop is checked against robots.txt, paced and
  logged like any other request.
- **Every attempt is logged** to the usage log (time, host, path, status, bytes). Query values
  are never logged, only the names of the query parameters. A request for one article's page
  is logged with the article's id (``log_as``) in place of its path, so the tracked log never
  lists article addresses; listing, API, feed, robots.txt and policy-page paths are logged as
  they are.
"""

from __future__ import annotations

import contextlib
import csv
import fcntl
import random
import re
import time
import urllib.robotparser
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

from commonswire import __version__

CONTACT_URL = "https://github.com/obadaKraishan"
ROBOTS_TOKEN = "CommonsWire"
USER_AGENT = f"{ROBOTS_TOKEN}/{__version__} (+{CONTACT_URL})"

MIN_INTERVAL = 2.0
MAX_RETRIES = 3
BACKOFF_BASE = 4.0
RETRY_AFTER_CAP = 120.0
MAX_REDIRECTS = 5
DEFAULT_MAX_BYTES = 8 * 1024 * 1024
TIMEOUT = 30.0

#: Crawlers that collect text for AI training or large corpora. A robots.txt that shuts them
#: out of the whole site is recorded as a signal for the source review; it does not bind the
#: CommonsWire user agent, which is checked on its own.
AI_CRAWLERS = ("CCBot", "GPTBot", "ClaudeBot", "anthropic-ai", "Google-Extended", "Bytespider")

USAGE_FIELDS = ["time", "host", "path", "query_keys", "status", "bytes", "note"]

_BOT_WALL_MARKERS = (
    b"<title>Just a moment...</title>",
    b"cf-browser-verification",
    b"challenges.cloudflare.com/turnstile",
    b"<title>Attention Required! | Cloudflare</title>",
    b"_Incapsula_Resource",
    b"Please enable JS and disable any ad blocker",
    b"px-captcha",
)


class FetchError(Exception):
    """A request could not be completed."""


class Blocked(FetchError):
    """The site refused scripted access. Record it and list the page for a person to read."""

    def __init__(self, url: str, status: int, reason: str) -> None:
        super().__init__(f"{url} refused scripted access ({reason}, HTTP {status})")
        self.url = url
        self.status = status
        self.reason = reason


class Disallowed(FetchError):
    """robots.txt does not allow the CommonsWire user agent to fetch this URL."""

    def __init__(self, url: str) -> None:
        super().__init__(f"robots.txt does not allow {ROBOTS_TOKEN} to fetch {url}")
        self.url = url


class BudgetExceeded(FetchError):
    """The session's byte budget is used up."""


@dataclass(frozen=True)
class RawResponse:
    """What a transport returns: the status, the headers and the body (possibly cut short)."""

    url: str
    status: int
    headers: Mapping[str, str]
    body: bytes
    truncated: bool = False


@dataclass(frozen=True)
class Response:
    """A finished request, after redirects."""

    url: str
    status: int
    headers: Mapping[str, str]
    body: bytes
    truncated: bool = False
    redirects: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return self.body.decode(_charset(self.headers), errors="replace")

    def json(self) -> object:
        import json

        return json.loads(self.body.decode("utf-8", errors="replace"))


Transport = Callable[[str, Mapping[str, str], float, int], RawResponse]


def requests_transport(session: requests.Session | None = None) -> Transport:
    """A transport that sends one GET with requests, never following redirects itself."""
    sess = session or requests.Session()

    def send(url: str, headers: Mapping[str, str], timeout: float, max_bytes: int) -> RawResponse:
        with sess.get(
            url, headers=dict(headers), timeout=timeout, allow_redirects=False, stream=True
        ) as resp:
            chunks: list[bytes] = []
            size = 0
            truncated = False
            for chunk in resp.iter_content(chunk_size=65536):
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    truncated = True
                    break
            body = b"".join(chunks)[:max_bytes]
            return RawResponse(
                url=url,
                status=resp.status_code,
                headers=dict(resp.headers),
                body=body,
                truncated=truncated,
            )

    return send


class UsageLog:
    """Appends one row per request attempt to a CSV file, and keeps this process's rows in
    ``recent`` (for a run's own summary by host and day)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.recent: list[dict[str, object]] = []

    def write(
        self, url: str, status: int | str, nbytes: int, note: str = "", log_as: str = ""
    ) -> None:
        """One row. With ``log_as`` (an article's id), the row names that instead of the
        URL's path and query keys."""
        parts = urlsplit(url)
        keys = sorted({kv.split("=", 1)[0] for kv in parts.query.split("&") if kv})
        row = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "host": parts.hostname or "",
            "path": log_as or parts.path or "/",
            "query_keys": "" if log_as else ";".join(keys),
            "status": status,
            "bytes": nbytes,
            "note": note,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=USAGE_FIELDS)
            if new:
                writer.writeheader()
            writer.writerow(row)
        self.recent.append(row)


#: The response headers an answer cache keeps (enough to replay paging and redirects).
CACHED_HEADERS = ("content-type", "location", "retry-after", "x-wp-total", "x-wp-totalpages")


class AnswerCache:
    """Every final answer of a run saved once under ``folder``, keyed by the SHA-256 of its URL
    (``<key>.body`` and ``<key>.json`` with the status and a few headers).

    A request whose answer is saved is served from the folder: no request is sent, nothing is
    logged and the pacer does not wait, so a run that stops can be resumed and a finished run
    replayed without fetching anything twice. With ``offline`` a missing answer is an error and
    nothing is ever sent.
    """

    def __init__(self, folder: Path, *, offline: bool = False) -> None:
        self.folder = Path(folder)
        self.offline = offline
        self.hits = 0

    def _paths(self, url: str) -> tuple[Path, Path]:
        import hashlib

        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.folder / f"{key}.body", self.folder / f"{key}.json"

    def get(self, url: str) -> RawResponse | None:
        import json

        body_path, meta_path = self._paths(url)
        if not meta_path.exists() or not body_path.exists():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.hits += 1
        return RawResponse(
            url=url,
            status=int(meta["status"]),
            headers=dict(meta.get("headers") or {}),
            body=body_path.read_bytes(),
            truncated=bool(meta.get("truncated")),
        )

    def put(self, url: str, raw: RawResponse) -> None:
        import json

        body_path, meta_path = self._paths(url)
        if meta_path.exists():
            return  # written once, never overwritten
        headers = {k: v for k, v in raw.headers.items() if k.lower() in CACHED_HEADERS}
        meta = {"url": url, "status": raw.status, "headers": headers, "truncated": raw.truncated}
        _write_once(body_path, raw.body)
        # The record last, so a half-written answer is never served.
        _write_once(meta_path, json.dumps(meta, sort_keys=True).encode("utf-8"))


def _write_once(path: Path, data: bytes) -> None:
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with tmp.open("wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


class Pacer:
    """Holds a lock file per host for each request and spaces request starts to that host.

    The time the last request to a host ended is kept in a small file next to its lock, so two
    CommonsWire processes on the same machine never send to the same host at the same moment,
    while different hosts can be fetched in parallel (one request at a time per host).
    """

    def __init__(
        self,
        lock_dir: Path,
        min_interval: float = MIN_INTERVAL,
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.lock_dir = Path(lock_dir)
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep

    def paths(self, host: str) -> tuple[Path, Path]:
        """The lock file and the last-request stamp of a host."""
        key = re.sub(r"[^a-z0-9.-]", "_", host.lower()) or "_any"
        return self.lock_dir / f"{key}.lock", self.lock_dir / f"{key}.last"

    def gap_path(self, host: str) -> Path:
        """The host's crawl-delay as last read from its robots.txt by any process."""
        return self.paths(host)[1].with_suffix(".gap")

    @contextlib.contextmanager
    def slot(self, host: str = "", interval: float | None = None) -> Iterator[None]:
        """Wait for the host's turn. ``interval`` is the crawl-delay this process knows; a
        process that does not know it yet (its first request, for robots.txt) waits the
        delay another process last recorded, so a new process never comes in early."""
        lock_path, stamp_path = self.paths(host)
        gap_path = self.gap_path(host)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                known = interval if interval is not None else _read_stamp(gap_path)
                gap = max(self.min_interval, known or 0.0)
                last = _read_stamp(stamp_path)
                wait = last + gap - self._clock()
                if wait > 0:
                    self._sleep(wait)
                try:
                    yield
                finally:
                    stamp_path.write_text(f"{self._clock():.3f}")
                    if interval is not None:
                        gap_path.write_text(f"{interval:.3f}")
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def _read_stamp(path: Path) -> float:
    try:
        return float(path.read_text().strip() or 0)
    except (FileNotFoundError, ValueError):
        return 0.0


@dataclass
class RobotsRule:
    """The robots.txt answer for one host."""

    host: str
    status: int | str
    parser: urllib.robotparser.RobotFileParser | None = None
    blocked: bool = False
    unreachable: bool = False
    ai_crawlers_shut_out: tuple[str, ...] = ()

    @property
    def state(self) -> str:
        """``none`` (no robots.txt), ``present``, ``blocked`` or ``unreachable``."""
        if self.blocked:
            return "blocked"
        if self.unreachable:
            return "unreachable"
        return "present" if self.parser is not None else "none"

    def allows(self, url: str) -> bool:
        if self.blocked or self.unreachable:
            return False
        if self.parser is None:
            return True
        return self.parser.can_fetch(ROBOTS_TOKEN, url)

    def crawl_delay(self) -> float | None:
        if self.parser is None:
            return None
        delay = self.parser.crawl_delay(ROBOTS_TOKEN)
        return float(delay) if delay is not None else None


def parse_robots(host: str, status: int, text: str) -> RobotsRule:
    """Read a robots.txt answer into a :class:`RobotsRule`."""
    if status in (401, 403):
        return RobotsRule(host=host, status=status, blocked=True)
    if status >= 500:
        return RobotsRule(host=host, status=status, unreachable=True)
    if status >= 400:
        return RobotsRule(host=host, status=status)
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(text.splitlines())
    root = f"https://{host}/"
    shut = tuple(bot for bot in AI_CRAWLERS if not parser.can_fetch(bot, root))
    return RobotsRule(host=host, status=status, parser=parser, ai_crawlers_shut_out=shut)


def looks_like_bot_wall(body: bytes) -> bool:
    head = body[:20000]
    return any(marker in head for marker in _BOT_WALL_MARKERS)


@dataclass
class PoliteClient:
    """Sends GET requests under the CommonsWire rules (see the module docstring)."""

    usage_log: UsageLog
    pacer: Pacer
    transport: Transport = field(default_factory=requests_transport)
    sleep: Callable[[float], None] = time.sleep
    byte_budget: int | None = None
    max_retries: int = MAX_RETRIES
    jitter: Callable[[], float] = random.random
    bytes_used: int = 0
    #: Requests this client may send (every attempt counts, a saved answer does not); None
    #: for no limit.
    request_budget: int | None = None
    requests_sent: int = 0
    #: Saved answers to serve instead of sending (``AnswerCache``); None sends every request.
    cache: AnswerCache | None = None
    _robots: dict[str, RobotsRule] = field(default_factory=dict)

    def robots(self, url: str) -> RobotsRule:
        """The robots.txt rule for the URL's host, fetched once and kept for the session."""
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host not in self._robots:
            robots_url = f"{parts.scheme or 'https'}://{parts.netloc}/robots.txt"
            try:
                resp = self._send_following(robots_url, check_robots=False, note="robots")
                rule = parse_robots(host, resp.status, resp.text)
            except Blocked as exc:
                rule = RobotsRule(host=host, status=exc.status, blocked=True)
            except BudgetExceeded:
                raise  # the run's own limit, not the site's answer
            except FetchError:
                rule = RobotsRule(host=host, status="error", unreachable=True)
            self._robots[host] = rule
        return self._robots[host]

    def get(
        self,
        url: str,
        *,
        accept: str = "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        max_bytes: int = DEFAULT_MAX_BYTES,
        note: str = "",
        log_as: str = "",
    ) -> Response:
        """GET a URL politely. Raises :class:`Disallowed`, :class:`Blocked` or
        :class:`FetchError`.

        ``log_as`` is what the usage log records in place of the path, for every hop and
        every retry of this request: the article's id when the URL is one article's page."""
        return self._send_following(
            url, accept=accept, max_bytes=max_bytes, note=note, log_as=log_as
        )

    def _send_following(
        self,
        url: str,
        *,
        check_robots: bool = True,
        accept: str = "*/*",
        max_bytes: int = DEFAULT_MAX_BYTES,
        note: str = "",
        log_as: str = "",
    ) -> Response:
        hops: list[str] = []
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            if check_robots and not self.robots(current).allows(current):
                raise Disallowed(current)
            raw = self._send_once(
                current, accept=accept, max_bytes=max_bytes, note=note, log_as=log_as
            )
            if raw.status in (301, 302, 303, 307, 308) and _header(raw.headers, "Location"):
                hops.append(current)
                current = urljoin(current, _header(raw.headers, "Location"))
                continue
            return Response(
                url=current,
                status=raw.status,
                headers=raw.headers,
                body=raw.body,
                truncated=raw.truncated,
                redirects=tuple(hops),
            )
        raise FetchError(f"{url} redirected more than {MAX_REDIRECTS} times")

    def _send_once(
        self, url: str, *, accept: str, max_bytes: int, note: str, log_as: str = ""
    ) -> RawResponse:
        if self.cache is not None:
            saved = self.cache.get(url)
            if saved is not None:
                return _refuse_or_return(url, saved)
            if self.cache.offline:
                raise FetchError(f"{url} has no saved answer (an offline replay sends nothing)")
        if self.byte_budget is not None and self.bytes_used >= self.byte_budget:
            raise BudgetExceeded(
                f"the byte budget of {self.byte_budget:,} bytes is used up; "
                "ask before fetching more"
            )
        host = (urlsplit(url).hostname or "").lower()
        rule = self._robots.get(host)
        # None until this process has read the host's robots.txt: the pacer then waits the
        # crawl-delay another process last recorded.
        delay = (rule.crawl_delay() or 0.0) if rule else None
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        attempt = 0
        error: Exception | None = None
        while True:
            if self.request_budget is not None and self.requests_sent >= self.request_budget:
                raise BudgetExceeded(
                    f"the request budget of {self.request_budget:,} requests is used up; "
                    "ask before sending more"
                )
            with self.pacer.slot(host, delay):
                self.requests_sent += 1
                try:
                    raw = self.transport(url, headers, TIMEOUT, max_bytes)
                except requests.RequestException as exc:
                    self.usage_log.write(
                        url, "error", 0, _join(note, type(exc).__name__), log_as=log_as
                    )
                    raw = None
                    error = exc
                else:
                    self.bytes_used += len(raw.body)
                    self.usage_log.write(
                        url,
                        raw.status,
                        len(raw.body),
                        _join(note, "truncated" * raw.truncated),
                        log_as=log_as,
                    )
            if raw is not None:
                final = raw.status != 429 and raw.status < 500
                if self.cache is not None and (final or attempt >= self.max_retries):
                    self.cache.put(url, raw)
                if final:
                    return _refuse_or_return(url, raw)
            if attempt >= self.max_retries:
                if raw is not None:
                    return raw
                raise FetchError(f"{url} failed after {attempt + 1} tries: {error}")
            wait = BACKOFF_BASE * (2**attempt) + self.jitter()
            if raw is not None:
                wait = max(wait, _retry_after(raw.headers))
            self.sleep(min(wait, RETRY_AFTER_CAP))
            attempt += 1


def _refuse_or_return(url: str, raw: RawResponse) -> RawResponse:
    """The answer, unless it refuses scripted access (then :class:`Blocked`, never a retry)."""
    if raw.status in (401, 403, 451):
        raise Blocked(url, raw.status, "refused")
    if raw.status == 200 and looks_like_bot_wall(raw.body):
        raise Blocked(url, raw.status, "bot check page")
    return raw


def _retry_after(headers: Mapping[str, str]) -> float:
    value = _header(headers, "Retry-After")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _header(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def _charset(headers: Mapping[str, str]) -> str:
    ctype = _header(headers, "Content-Type")
    for part in ctype.split(";"):
        part = part.strip()
        if part.lower().startswith("charset="):
            return part.split("=", 1)[1].strip("\"' ") or "utf-8"
    return "utf-8"


def _join(*notes: str) -> str:
    return ";".join(n for n in notes if n)


def make_client(
    root: Path,
    *,
    byte_budget: int | None = None,
    transport: Transport | None = None,
    usage_log: UsageLog | Path | None = None,
    lock_dir: Path | None = None,
    cache: AnswerCache | None = None,
) -> PoliteClient:
    """A client that logs to ``data/usage_log.csv`` and paces through ``data/interim/``
    (or the log, lock folder and answer cache given)."""
    if isinstance(usage_log, UsageLog):
        log = usage_log
    else:
        log = UsageLog(usage_log or root / "data" / "usage_log.csv")
    pacer = Pacer(lock_dir or root / "data" / "interim" / "locks")
    kwargs: dict[str, object] = {"byte_budget": byte_budget, "cache": cache}
    if transport is not None:
        kwargs["transport"] = transport
    return PoliteClient(usage_log=log, pacer=pacer, **kwargs)  # type: ignore[arg-type]
