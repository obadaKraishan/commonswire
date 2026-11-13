"""Metadata-only volume probes: how many articles a source publishes a day, and since when.

No article text is requested. Two methods, at most three requests per source:

- ``wordpress``: the WordPress REST API asked for post dates only (``_fields=date_gmt``): the
  newest 100 dates give the rate, the ``X-WP-Total`` header the archive size, and one more
  request the date of the oldest post.
- ``sitemap``: a news or post sitemap, of which only the ``<loc>`` count and the dates
  (``<news:publication_date>`` or ``<lastmod>``) are read.

Results go to ``data/evidence/volume.csv`` (counts and dates only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

from commonswire.http import PoliteClient

VOLUME_FIELDS = [
    "checked_on",
    "source_id",
    "method",
    "requests",
    "dates_seen",
    "window_days",
    "est_articles_per_day",
    "total_articles",
    "archive_from",
    "newest",
    "note",
]
MAX_REQUESTS = 3

_DATE = re.compile(
    r"<(?:news:publication_date|lastmod)>\s*([0-9]{4}-[0-9]{2}-[0-9]{2}[^<]*)\s*</", re.I
)


@dataclass
class Volume:
    source_id: str
    method: str
    requests: int = 0
    dates_seen: int = 0
    window_days: float | None = None
    per_day: float | None = None
    total: int | None = None
    archive_from: str = ""
    newest: str = ""
    note: str = ""

    def row(self, checked_on: str) -> dict[str, object]:
        return {
            "checked_on": checked_on,
            "source_id": self.source_id,
            "method": self.method,
            "requests": self.requests,
            "dates_seen": self.dates_seen,
            "window_days": "" if self.window_days is None else round(self.window_days, 2),
            "est_articles_per_day": "" if self.per_day is None else round(self.per_day, 1),
            "total_articles": "" if self.total is None else self.total,
            "archive_from": self.archive_from,
            "newest": self.newest,
            "note": self.note,
        }


def parse_date(value: str) -> datetime | None:
    value = value.strip()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def rate(dates: list[datetime], now: datetime) -> tuple[float | None, float | None]:
    """Articles per day over the span from the oldest date seen to now."""
    if not dates:
        return None, None
    span = (now - min(dates)).total_seconds() / 86400
    if span <= 0:
        return None, None
    return len(dates) / span, span


def probe_wordpress(
    client: PoliteClient, source_id: str, base: str, now: datetime | None = None
) -> Volume:
    now = now or datetime.now(timezone.utc)
    vol = Volume(source_id=source_id, method="wordpress")
    api = base.rstrip("/") + "/wp-json/wp/v2/posts?"
    newest = client.get(
        api + urlencode({"per_page": "100", "_fields": "date_gmt", "orderby": "date"}),
        accept="application/json",
        note=f"volume:{source_id}",
    )
    vol.requests += 1
    if newest.status != 200:
        vol.note = f"posts API answered HTTP {newest.status}"
        return vol
    total = _header(newest.headers, "X-WP-Total")
    vol.total = int(total) if total.isdigit() else None
    data = newest.json()
    dates = [d for d in (parse_date(p.get("date_gmt", "")) for p in data or []) if d]
    vol.dates_seen = len(dates)
    vol.per_day, vol.window_days = rate(dates, now)
    if dates:
        vol.newest = max(dates).date().isoformat()
    oldest = client.get(
        api
        + urlencode({"per_page": "1", "order": "asc", "orderby": "date", "_fields": "date_gmt"}),
        accept="application/json",
        note=f"volume:{source_id}",
    )
    vol.requests += 1
    if oldest.status == 200 and oldest.json():
        first = parse_date(oldest.json()[0].get("date_gmt", ""))
        if first:
            vol.archive_from = first.date().isoformat()
    return vol


def probe_sitemap(
    client: PoliteClient, source_id: str, url: str, now: datetime | None = None
) -> Volume:
    now = now or datetime.now(timezone.utc)
    vol = Volume(source_id=source_id, method="sitemap")
    resp = client.get(url, accept="application/xml,text/xml", note=f"volume:{source_id}")
    vol.requests += 1
    if resp.status != 200:
        vol.note = f"sitemap answered HTTP {resp.status}"
        return vol
    text = resp.text
    if "<sitemapindex" in text:
        vol.note = "a sitemap index, not a list of articles"
        return vol
    dates = [d for d in (parse_date(m) for m in _DATE.findall(text)) if d]
    vol.dates_seen = len(dates)
    vol.per_day, vol.window_days = rate(dates, now)
    if dates:
        vol.newest = max(dates).date().isoformat()
    vol.note = "news sitemap" if "news:publication_date" in text else "sitemap lastmod dates"
    return vol


def _header(headers: object, name: str) -> str:
    for key, value in getattr(headers, "items", lambda: [])():
        if key.lower() == name.lower():
            return value
    return ""
