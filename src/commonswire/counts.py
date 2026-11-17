"""The count check: articles removed at their source after they left the update's window.

A WordPress site lists no deleted posts. So each weekly update, for each source that still
publishes and each year of its archive, reads the site's post count for that year (one request
with ``per_page=1``, read from the ``X-WP-Total`` header) and keeps it in the version's
manifest (``post_counts``). The next update reads the same ranges again and compares:

- **No counts in the previous version** (a baseline run): the counts are recorded and nothing
  is compared.
- **A count that fell:** the year's posts are listed (links only, 100 a page), and the page of
  each released row missing from that listing is read once. A row whose page answers 404 or
  410 is removed, by the same rule as a removal in the window; any other answer leaves the row
  in place, and it is counted. A fall that the window's own removals explain is not listed.
- **A count that rose:** a back-dated or restored post. The edited-since listing already
  takes such a post as a new row (its modified date falls in the window), so nothing more is
  done; the rise is reported.
- **A ceiling** on the requests that falls may cost in one run (listing pages and page checks,
  over every source): past it the source stops, named with the year, for the maintainer.

The current year's count covers the days up to the day before the run (by then every site's
time zone has published them); the next update compares the same days (one more request) and
records the longer range. That range overlaps the window, so a removal is missed only when a
back-dated post offsets it in the same range, or when two runs are more than the window apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from commonswire.daily import _removed
from commonswire.http import FetchError, PoliteClient
from commonswire.schema import canonical_url

#: Requests a run may spend on falls in the counts (listing pages and page checks), shared
#: by every source; past it the source stops for the maintainer to look at.
MAX_COUNT_REQUESTS = 150
PER_PAGE = 100
#: Days added on each side of a range when it is listed, so that a row's day in UTC and the
#: site's own day (its time zone) cannot fall on different sides of the edge.
EDGE_DAYS = 2


class CountCeiling(Exception):
    """A fall in a count needs more requests than the run has left."""


@dataclass
class Allowance:
    """The requests left for falls in the counts, shared by every source of a run."""

    limit: int = MAX_COUNT_REQUESTS
    used: int = 0

    @property
    def left(self) -> int:
        return max(0, self.limit - self.used)


@dataclass
class CountCheck:
    """What one source's count check did and found: counts, years and ids only."""

    baseline: bool = False
    years_checked: int = 0
    drops: dict[str, int] = field(default_factory=dict)
    explained: dict[str, int] = field(default_factory=dict)
    rises: dict[str, int] = field(default_factory=dict)
    years_listed: list[str] = field(default_factory=list)
    listing_pages: int = 0
    rows_checked: int = 0
    rows_removed: int = 0
    rows_kept: int = 0
    count_requests: int = 0
    removed_ids: list[str] = field(default_factory=list)
    #: year -> {"posts": n, "before": "YYYY-MM-DD"}: what the next update compares.
    counts: dict[str, dict[str, object]] = field(default_factory=dict)

    def summary(self) -> dict[str, object]:
        return {
            "baseline": self.baseline,
            "years_recorded": len(self.counts),
            "years_checked": self.years_checked,
            "drops": self.drops,
            "drops_explained_by_the_window": self.explained,
            "rises": self.rises,
            "years_listed": self.years_listed,
            "listing_pages": self.listing_pages,
            "rows_checked": self.rows_checked,
            "rows_removed": self.rows_removed,
            "rows_kept": self.rows_kept,
            "count_requests": self.count_requests,
        }


def count_url(api_base: str, year: int, before: date) -> str:
    """The post count of ``year`` up to the day ``before`` (the site's own dates)."""
    q = {
        "per_page": "1",
        "after": f"{year - 1}-12-31T23:59:59",
        "before": f"{before.isoformat()}T00:00:00",
        "_fields": "id",
    }
    return f"{api_base}/wp-json/wp/v2/posts?{urlencode(q)}"


def record_until(year: int, now: datetime) -> date | None:
    """The end of the range recorded for ``year``: the year's end, or for the current year
    the day before the run. None if that range is still empty (the year's first days)."""
    bound = min(date(year + 1, 1, 1), now.date() - timedelta(days=1))
    return bound if bound > date(year, 1, 1) else None


def _header(headers: object, name: str) -> str:
    for key, value in getattr(headers, "items", lambda: [])():
        if key.lower() == name.lower():
            return str(value)
    return ""


def _count(client: PoliteClient, url: str, note: str) -> int:
    resp = client.get(url, accept="application/json", note=note)
    total = _header(resp.headers, "X-WP-Total")
    if resp.status != 200 or not total.isdigit():
        raise FetchError(f"{url} answered HTTP {resp.status} with no post count")
    return int(total)


def _canon(url: str) -> str:
    try:
        return canonical_url(url)
    except ValueError:
        return url


def _list_range(
    api_base: str,
    client: PoliteClient,
    year: int,
    before: date,
    allowance: Allowance,
    chk: CountCheck,
    note: str,
) -> set[str]:
    """The links of every post of ``year`` up to ``before``, with ``EDGE_DAYS`` on each side."""
    start = date(year, 1, 1) - timedelta(days=EDGE_DAYS)
    end = before + timedelta(days=EDGE_DAYS)
    links: set[str] = set()
    page = 1
    while True:
        if allowance.left <= 0:
            raise CountCeiling(
                f"listing {year} ran past this run's {allowance.limit} requests for falls in the "
                "counts: a removal on that scale is for the maintainer to look at"
            )
        q = {
            "per_page": str(PER_PAGE),
            "page": str(page),
            "after": f"{start.isoformat()}T00:00:00",
            "before": f"{end.isoformat()}T00:00:00",
            "orderby": "date",
            "order": "asc",
            "_fields": "link",
        }
        url = f"{api_base}/wp-json/wp/v2/posts?{urlencode(q)}"
        resp = client.get(url, accept="application/json", note=note)
        allowance.used += 1
        chk.listing_pages += 1
        if resp.status == 400 and page > 1:
            return links
        if resp.status != 200 or resp.truncated:
            raise FetchError(f"{url} answered HTTP {resp.status}")
        data = resp.json()
        if not isinstance(data, list):
            raise FetchError(f"{url} did not answer with a list")
        for post in data:
            if isinstance(post, dict) and post.get("link"):
                links.add(_canon(str(post["link"])))
        pages = _header(resp.headers, "X-WP-TotalPages")
        if len(data) < PER_PAGE or (pages.isdigit() and page >= int(pages)):
            return links
        page += 1


def check_counts(
    api_base: str,
    client: PoliteClient,
    prev_rows: dict[str, dict],
    prev_counts: dict[str, dict] | None,
    *,
    now: datetime,
    rows: dict[str, dict],
    skip: set[str],
    removed_in_window: dict[str, str],
    allowance: Allowance,
    note: str,
) -> CountCheck:
    """One source's count check. ``prev_rows`` are its released rows in the previous version,
    ``prev_counts`` the counts that version recorded (None: a baseline run). Rows found removed
    are marked removed in ``rows``; ``skip`` holds ids this run already read or
    checked, and ``removed_in_window`` the publication times of rows the window removed."""
    chk = CountCheck(baseline=prev_counts is None)
    old_counts = prev_counts or {}
    known = {int(d["published_at"][:4]) for d in prev_rows.values()} | {int(y) for y in old_counts}
    compared: dict[int, tuple[date, int, int]] = {}
    for year in range(min(known), now.year + 1) if known else ():
        until = record_until(year, now)
        old = old_counts.get(str(year))
        if old is not None:
            before = date.fromisoformat(str(old["before"]))
            got = _count(client, count_url(api_base, year, before), note)
            chk.count_requests += 1
            compared[year] = (before, int(old["posts"]), got)
            chk.years_checked += 1
            if until is None or until == before:
                chk.counts[str(year)] = {"posts": got, "before": before.isoformat()}
                continue
        if until is None:
            continue
        rec = _count(client, count_url(api_base, year, until), note)
        chk.count_requests += 1
        chk.counts[str(year)] = {"posts": rec, "before": until.isoformat()}

    for year, (before, was, got) in sorted(compared.items()):
        key = str(year)
        if got > was:
            chk.rises[key] = got - was
            continue
        if got == was:
            continue
        fall = was - got
        chk.drops[key] = fall
        start, end = f"{year}-01-01T00:00:00Z", f"{before.isoformat()}T00:00:00Z"
        explained = sum(1 for p in removed_in_window.values() if start <= p < end)
        if explained:
            chk.explained[key] = min(explained, fall)
        if fall <= explained:
            continue
        need = got // PER_PAGE + 2
        if need > allowance.left:
            raise CountCeiling(
                f"the post count of {year} fell by {fall} ({was:,} to {got:,}); listing that "
                f"year needs about {need} requests, {allowance.left} left of this run's "
                f"{allowance.limit}: a removal on that scale is for the maintainer to look at"
            )
        chk.years_listed.append(key)
        links = _list_range(api_base, client, year, before, allowance, chk, note)
        missing = [
            (rid, d)
            for rid, d in sorted(prev_rows.items())
            if rid not in skip
            and start <= d["published_at"] < end
            and _canon(d["url"]) not in links
        ]
        if len(missing) > allowance.left:
            raise CountCeiling(
                f"the post count of {year} fell by {fall}, and {len(missing)} released rows are "
                f"missing from its listing; {allowance.left} requests are left of this run's "
                f"{allowance.limit}: a removal on that scale is for the maintainer to look at"
            )
        for rid, d in missing:
            # One article's page: the request log records its id, not its address.
            resp = client.get(d["url"], accept="text/html", note=note, log_as=rid)
            allowance.used += 1
            chk.rows_checked += 1
            skip.add(rid)
            if resp.status in (404, 410):
                rows[rid] = _removed(d)
                chk.rows_removed += 1
                chk.removed_ids.append(rid)
            else:
                chk.rows_kept += 1
    return chk
