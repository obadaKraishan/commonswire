"""Fetchers for sources that publish through the WordPress REST API (``/wp-json/wp/v2/posts``).

One request returns up to 100 posts with their body HTML, so a sample of 200 articles takes two
requests. The total number of posts comes from the ``X-WP-Total`` header, and the archive start
from one request for the oldest post (dates only).
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import datetime, timezone
from urllib.parse import urlencode

from commonswire.fetchers.base import Fetcher, Item
from commonswire.html import strip_tags

PER_PAGE = 100

#: Words that mark a post as someone else's work republished by the source.
REPUBLISHED = re.compile(
    r"(originally (published|appeared)|first (published|appeared)|"
    r"republished (here )?(as part of|under|with (the )?permission|from)|"
    r"content[- ]sharing (agreement|partnership)|is part of a (content )?partnership|"
    r"reprinted with permission|published (here )?with permission)",
    re.I,
)
#: Wire agencies, looked for in bylines and in a dateline at the very start of the body.
WIRE = re.compile(r"\b(Associated Press|Reuters|Agence France-Presse|AFP)\b|\(AP\)", re.I)


def _gmt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", ""))
    return dt.replace(tzinfo=timezone.utc)


def _header(headers: object, name: str) -> str:
    for key, value in getattr(headers, "items", lambda: [])():
        if key.lower() == name.lower():
            return value
    return ""


class WordPressFetcher(Fetcher):
    """A WordPress source. Subclasses set ``api_base`` and ``language`` and may extend
    ``third_party_reason``."""

    api_base: str = ""
    language: str = "en"

    def _posts_url(self, page: int, per_page: int = PER_PAGE, **extra: str) -> str:
        params = {
            "per_page": str(per_page),
            "page": str(page),
            "orderby": "date",
            "order": "desc",
            "_embed": "author,wp:term",
        }
        params.update(extra)
        return f"{self.api_base}/wp-json/wp/v2/posts?{urlencode(params)}"

    def items(self, limit: int) -> Iterator[Item]:
        page = 1
        given = 0
        while given < limit:
            per_page = min(PER_PAGE, limit - given) if page == 1 else PER_PAGE
            url = self._posts_url(page, per_page)
            resp = self.client.get(url, accept="application/json", note=f"sample:{self.source_id}")
            if resp.status != 200:
                raise RuntimeError(f"{url} answered HTTP {resp.status}")
            self.raw.save(resp, f"posts-p{page}")
            if page == 1:
                total = _header(resp.headers, "X-WP-Total")
                self.api_totals["total_posts"] = int(total) if total.isdigit() else None
            posts = resp.json()
            if not isinstance(posts, list) or not posts:
                return
            for post in posts:
                if given >= limit:
                    return
                yield self.item_from_post(post)
                given += 1
            page += 1

    def archive_start(self) -> str | None:
        """The date of the oldest post (one request for dates only)."""
        url = f"{self.api_base}/wp-json/wp/v2/posts?" + urlencode(
            {"per_page": "1", "order": "asc", "orderby": "date", "_fields": "date_gmt"}
        )
        data = self.get_json(url, "oldest-post")
        if isinstance(data, list) and data:
            first = _gmt(data[0].get("date_gmt"))
            if first:
                self.api_totals["archive_from"] = first.date().isoformat()
                return first.date().isoformat()
        return None

    def item_from_post(self, post: dict) -> Item:
        embedded = post.get("_embedded") or {}
        authors = tuple(
            strip_tags(a.get("name", ""))
            for a in embedded.get("author", [])
            if isinstance(a, dict) and a.get("name")
        )
        terms = [t for group in embedded.get("wp:term", []) for t in group if isinstance(t, dict)]
        categories = [
            strip_tags(t.get("name", "")) for t in terms if t.get("taxonomy") == "category"
        ]
        tags = [strip_tags(t.get("name", "")) for t in terms if t.get("taxonomy") == "post_tag"]
        published = _gmt(post.get("date_gmt"))
        if published is None:
            raise ValueError("a post has no date_gmt")
        return Item(
            url=post.get("link", ""),
            title=strip_tags((post.get("title") or {}).get("rendered", "")),
            body_html=(post.get("content") or {}).get("rendered", ""),
            published_at=published,
            updated_at=_gmt(post.get("modified_gmt")),
            language=self.language,
            authors=authors,
            section=categories[0] if categories else "",
            hints={"categories": categories, "tags": tags, "type": post.get("type", "")},
        )

    def third_party_reason(self, item: Item) -> str | None:
        names = [str(c).lower() for c in item.hints.get("categories", [])]  # type: ignore[union-attr]
        names += [str(t).lower() for t in item.hints.get("tags", [])]  # type: ignore[union-attr]
        if any("partner" in n or "syndicat" in n or "republish" in n for n in names):
            return "partner_category"
        # Look for a republication note at the start or the end of the body only, where
        # sources put them; the middle of a story may quote other outlets.
        text = strip_tags(item.body_html)
        if REPUBLISHED.search(text[:400]) or REPUBLISHED.search(text[-600:]):
            return "republication_note"
        if any(WIRE.search(a) for a in item.authors) or WIRE.search(text[:80]):
            return "wire_byline"
        return None


class GlobalVoicesFetcher(WordPressFetcher):
    """Global Voices (English site). Its own stories, including its translations, are CC BY;
    partner stories republished under content-sharing agreements are dropped."""

    source_id = "globalvoices"
    api_base = "https://globalvoices.org"
    language = "en"
    drop_classes = (
        "sharedaddy",
        "jp-relatedposts",
        "gv-share",
        "share-box",
        "newsletter",
        "wp-caption",
        "credit",
    )
