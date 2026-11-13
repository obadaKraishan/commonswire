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
_MONTH = (
    r"(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)\.?"
)
#: A note that only dates the source's own earlier publication ("This was first published on
#: June 8, 2022", "Originally published: March 19, 2020", "first appeared in our ...
#: package"): not third-party material.
SELF_DATED = re.compile(
    r"(originally|first) (published|appeared)\s*(:|on|in)?\s*(on\s+)?"
    rf"({_MONTH}|\d{{1,2}}\s+{_MONTH}|\d{{4}}\b|our\b)",
    re.I,
)


#: A note that the source re-runs its own story in a series or package of its own.
SELF_SERIES = re.compile(
    r"republished (here )?as part of (a|an|our|the) [^.]{0,40}?"
    r"(series|package|special report|collection|edition)",
    re.I,
)


def republication_note(segment: str) -> bool:
    """True if a stretch of text holds a republication note that is not only a date or the
    source's own series."""
    for m in REPUBLISHED.finditer(segment):
        if not (SELF_DATED.match(segment, m.start()) or SELF_SERIES.match(segment, m.start())):
            return True
    return False


#: A note that the text is under someone else's rights.
RIGHTS_NOTE = re.compile(
    r"all rights reserved|\u00a9\s*(the )?(associated press|reuters|afp)", re.I
)
#: Wire agencies, looked for in bylines and in a dateline at the very start of the body.
WIRE = re.compile(r"\b(Associated Press|Reuters|Agence France-Presse|AFP)\b|\(AP\)", re.I)


def _gmt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", ""))
    return dt.replace(tzinfo=timezone.utc)


def byline_from_yoast(meta: object) -> tuple[str, ...]:
    """The byline a Yoast SEO block gives (``author``, or ``twitter_misc["Written by"]``),
    for sites whose WordPress user endpoint is closed. Names are split on commas and "and"."""
    if not isinstance(meta, dict):
        return ()
    misc = meta.get("twitter_misc") if isinstance(meta.get("twitter_misc"), dict) else {}
    name = meta.get("author") or misc.get("Written by") or ""
    if not isinstance(name, str):
        return ()
    parts = re.split(r",\s*|\s+and\s+|\s*&\s*", strip_tags(name))
    return tuple(p.strip() for p in parts if p.strip())


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
    #: Fields asked for in a backfill (``_fields``), so answers carry only what rows need.
    backfill_fields = (
        "id,date_gmt,modified_gmt,link,title,content,author,categories,type,"
        "yoast_head_json.author,yoast_head_json.twitter_misc"
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        #: category id -> name, for answers without embedded terms (backfills).
        self.category_names: dict[int, str] = {}
        #: author id -> byline, for sites whose API gives no author names.
        self.byline_map: dict[int, tuple[str, ...]] = {}

    def backfill_url(self, page: int, per_page: int = PER_PAGE) -> str:
        """Oldest first, so posts published during a backfill do not shift the pages."""
        params = {
            "per_page": str(per_page),
            "page": str(page),
            "orderby": "date",
            "order": "asc",
            "_fields": self.backfill_fields,
        }
        return f"{self.api_base}/wp-json/wp/v2/posts?{urlencode(params)}"

    def categories_url(self, page: int) -> str:
        params = {"per_page": "100", "page": str(page), "_fields": "id,name"}
        return f"{self.api_base}/wp-json/wp/v2/categories?{urlencode(params)}"

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
        if not authors:
            authors = byline_from_yoast(post.get("yoast_head_json"))
        if not authors and isinstance(post.get("author"), int):
            authors = self.byline_map.get(post["author"], ())
        terms = [t for group in embedded.get("wp:term", []) for t in group if isinstance(t, dict)]
        categories = [
            strip_tags(t.get("name", "")) for t in terms if t.get("taxonomy") == "category"
        ]
        if not categories and self.category_names:
            categories = [
                strip_tags(self.category_names[c])
                for c in post.get("categories", [])
                if c in self.category_names
            ]
        tags = [strip_tags(t.get("name", "")) for t in terms if t.get("taxonomy") == "post_tag"]
        published = _gmt(post.get("date_gmt"))
        if published is None:
            raise ValueError("a post has no date_gmt")
        updated = _gmt(post.get("modified_gmt"))
        if updated is not None and updated < published:
            # A scheduled post was last edited before it went live; it has no later update.
            updated = None
        return Item(
            url=post.get("link", ""),
            title=strip_tags((post.get("title") or {}).get("rendered", "")),
            body_html=(post.get("content") or {}).get("rendered", ""),
            published_at=published,
            updated_at=updated,
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
        if self.own_notes:
            text = self.strip_own_notes(text)
        if republication_note(text[:400]) or republication_note(text[-600:]):
            return "republication_note"
        if RIGHTS_NOTE.search(text[:400]) or RIGHTS_NOTE.search(text[-600:]):
            return "rights_reserved_note"
        if any(WIRE.search(a) for a in item.authors) or WIRE.search(text[:80]):
            return "wire_byline"
        return None


class GlobalVoicesFetcher(WordPressFetcher):
    """Global Voices (English site). Its own stories, including its translations, are CC BY;
    partner stories republished under content-sharing agreements are dropped."""

    source_id = "globalvoices"
    api_base = "https://globalvoices.org"
    language = "en"
    requires_byline = True
    drop_classes = (
        "sharedaddy",
        "jp-relatedposts",
        "gv-share",
        "share-box",
        "newsletter",
        "wp-caption",
        "credit",
    )


class ThreeSixtyInfoFetcher(WordPressFetcher):
    """360info: commissioned articles by named researchers, CC BY 4.0 except where noted.
    Third-party material is noted with the content; such posts are dropped."""

    source_id = "360info"
    api_base = "https://360info.org"
    language = "en"
    own_notes = (
        r"Originally published under (?:a )?Creative Commons[^\n]{0,60}? "
        r"by 360info(?:\u2122|TM)?\.?",
    )
    drop_classes = (
        "sharedaddy",
        "jp-relatedposts",
        "republish",
        "share",
        "newsletter",
        "wp-caption",
        "related",
    )


class BalkanDiskursFetcher(WordPressFetcher):
    """Balkan Diskurs, English edition only (its own WordPress site under ``/en/``): CC BY 3.0."""

    source_id = "balkandiskurs"
    api_base = "https://balkandiskurs.com/en"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")


class FactlyFetcher(WordPressFetcher):
    """Factly (English): CC BY 4.0 except videos; embedded social posts are removed."""

    source_id = "factly"
    api_base = "https://factly.in"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")


class AltNewsFetcher(WordPressFetcher):
    """Alt News (English; the Hindi edition is a separate site): CC BY 3.0; embedded social
    posts are removed."""

    source_id = "altnews"
    api_base = "https://www.altnews.in"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")


class PublicRecordFetcher(WordPressFetcher):
    """The Public Record (Hamilton, Ontario): original content CC BY-SA 4.0 unless otherwise
    stated; work used from other sites keeps its own license and is dropped."""

    source_id = "thepublicrecord"
    api_base = "https://thepublicrecord.ca"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")
