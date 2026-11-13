"""Wikinews (English), through the MediaWiki API.

Wikinews closed on 2026-05-04: its pages stay visible but are no longer edited, so it is a
back-catalogue, not a living source. Articles are listed from ``Category:Published`` (newest
first, with the time each article was published), and their plain text comes from the
TextExtracts API, 20 articles per request. The text stops at the first closing section
(Sources, Related news, External links, Sister links).

Wikinews text is CC BY 2.5 from 2005-09-25; earlier articles are in the public domain.
Articles have no bylines: the credit names "Wikinews contributors".
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from urllib.parse import quote, urlencode

from commonswire.fetchers.base import Fetcher, Item
from commonswire.sources import PUBLIC_DOMAIN

API = "https://en.wikinews.org/w/api.php"
ARTICLE_URL = "https://en.wikinews.org/wiki/"
LICENSE_FROM = date(2005, 9, 25)
EXTRACTS_PER_REQUEST = 20
LIST_LIMIT = 500

#: Section headings where the article body ends.
CLOSING_SECTIONS = re.compile(
    r"^==+\s*(Sources?|Related (news|articles|stories)|External links|Sister links|"
    r"See also|References|Interviews?\s*$)\s*==+\s*$",
    re.I | re.M,
)
_HEADING = re.compile(r"^==+\s*(.*?)\s*==+\s*$", re.M)


def body_from_extract(extract: str) -> str:
    """The article body from a plain-text extract: up to the first closing section, with the
    remaining section headings kept as their own paragraphs."""
    match = CLOSING_SECTIONS.search(extract)
    body = extract[: match.start()] if match else extract
    body = _HEADING.sub(lambda m: m.group(1), body)
    paragraphs = [re.sub(r"[ \t]+", " ", p).strip() for p in body.split("\n")]
    return "\n\n".join(p for p in paragraphs if p)


class WikinewsFetcher(Fetcher):
    source_id = "wikinews_en"

    def _api(self, **params: str) -> str:
        params = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
        return f"{API}?{urlencode(params)}"

    def license_for(self, item: Item) -> str:
        if item.published_at.date() < LICENSE_FROM:
            return PUBLIC_DOMAIN
        return self.source.license

    def items(self, limit: int) -> Iterator[Item]:
        listing = self.get_json(
            self._api(
                action="query",
                list="categorymembers",
                cmtitle="Category:Published",
                cmtype="page",
                cmsort="timestamp",
                cmdir="desc",
                cmprop="ids|title|timestamp",
                cmlimit=str(min(limit, LIST_LIMIT)),
            ),
            "published-list",
        )
        members = (listing.get("query") or {}).get("categorymembers", [])  # type: ignore[union-attr]
        members = [m for m in members if m.get("ns") == 0][:limit]
        for start in range(0, len(members), EXTRACTS_PER_REQUEST):
            batch = members[start : start + EXTRACTS_PER_REQUEST]
            data = self.get_json(
                self._api(
                    action="query",
                    prop="extracts|info|revisions",
                    rvprop="timestamp",
                    pageids="|".join(str(m["pageid"]) for m in batch),
                    explaintext="1",
                    exsectionformat="wiki",
                    exlimit=str(EXTRACTS_PER_REQUEST),
                    inprop="url",
                ),
                f"extracts-{start // EXTRACTS_PER_REQUEST + 1:02d}",
            )
            pages = {p["pageid"]: p for p in (data.get("query") or {}).get("pages", [])}  # type: ignore[union-attr]
            for member in batch:
                page = pages.get(member["pageid"])
                if page is None or "extract" not in page:
                    continue
                title = page.get("title", member["title"])
                yield Item(
                    url=ARTICLE_URL + quote(title.replace(" ", "_"), safe="_(),'!:"),
                    title=title,
                    body_html="",
                    body_text=body_from_extract(page.get("extract", "")),
                    published_at=datetime.fromisoformat(member["timestamp"].replace("Z", "+00:00")),
                    updated_at=_last_edit(page),
                    language="en",
                    hints={"length": page.get("length")},
                )

    def third_party_reason(self, item: Item) -> str | None:
        # Wikinews articles are written by contributors under the site license; there is no
        # wire copy or partner content. Images and media are never collected.
        return None


def _last_edit(page: dict) -> datetime | None:
    """The time of the page's latest revision (its last edit)."""
    revs = page.get("revisions") or []
    value = revs[0].get("timestamp") if revs else None
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
