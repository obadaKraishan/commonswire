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
  are never logged, only the names of the query parameters.
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
    """Appends one row per request attempt to a CSV file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def write(self, url: str, status: int | str, nbytes: int, note: str = "") -> None:
        parts = urlsplit(url)
        keys = sorted({kv.split("=", 1)[0] for kv in parts.query.split("&") if kv})
        row = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "host": parts.hostname or "",
            "path": parts.path or "/",
            "query_keys": ";".join(keys),
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
    ) -> Response:
        """GET a URL politely. Raises :class:`Disallowed`, :class:`Blocked` or
        :class:`FetchError`."""
        return self._send_following(url, accept=accept, max_bytes=max_bytes, note=note)

    def _send_following(
        self,
        url: str,
        *,
        check_robots: bool = True,
        accept: str = "*/*",
        max_bytes: int = DEFAULT_MAX_BYTES,
        note: str = "",
    ) -> Response:
        hops: list[str] = []
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            if check_robots and not self.robots(current).allows(current):
                raise Disallowed(current)
            raw = self._send_once(current, accept=accept, max_bytes=max_bytes, note=note)
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

    def _send_once(self, url: str, *, accept: str, max_bytes: int, note: str) -> RawResponse:
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
            with self.pacer.slot(host, delay):
                try:
                    raw = self.transport(url, headers, TIMEOUT, max_bytes)
                except requests.RequestException as exc:
                    self.usage_log.write(url, "error", 0, _join(note, type(exc).__name__))
                    raw = None
                    error = exc
                else:
                    self.bytes_used += len(raw.body)
                    self.usage_log.write(
                        url, raw.status, len(raw.body), _join(note, "truncated" * raw.truncated)
                    )
            if raw is not None:
                if raw.status in (401, 403, 451):
                    raise Blocked(url, raw.status, "refused")
                if raw.status == 200 and looks_like_bot_wall(raw.body):
                    raise Blocked(url, raw.status, "bot check page")
                if raw.status != 429 and raw.status < 500:
                    return raw
            if attempt >= self.max_retries:
                if raw is not None:
                    return raw
                raise FetchError(f"{url} failed after {attempt + 1} tries: {error}")
            wait = BACKOFF_BASE * (2**attempt) + self.jitter()
            if raw is not None:
                wait = max(wait, _retry_after(raw.headers))
            self.sleep(min(wait, RETRY_AFTER_CAP))
            attempt += 1


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
) -> PoliteClient:
    """A client that logs to ``data/usage_log.csv`` and paces through ``data/interim/``."""
    log = UsageLog(root / "data" / "usage_log.csv")
    pacer = Pacer(root / "data" / "interim" / "locks")
    if transport is None:
        return PoliteClient(usage_log=log, pacer=pacer, byte_budget=byte_budget)
    return PoliteClient(usage_log=log, pacer=pacer, transport=transport, byte_budget=byte_budget)
