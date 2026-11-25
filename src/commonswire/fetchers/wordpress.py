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
from commonswire.schema import canonical_url

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


#: WordPress writes a post's zero date ("0000-00-00 00:00:00") as a time near the Unix epoch;
#: no news site published before this, so an earlier date is no date at all.
EARLIEST_DATE = datetime(1991, 1, 1, tzinfo=timezone.utc)


def _gmt(value: str | None) -> datetime | None:
    """A WordPress ``*_gmt`` value as UTC, or None when there is none (or only a zero date)."""
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "")).replace(tzinfo=timezone.utc)
    return dt if dt >= EARLIEST_DATE else None


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
        #: tag id -> name, and post id -> tag ids (a tags backfill), for answers without
        #: embedded terms.
        self.tag_names: dict[int, str] = {}
        self.post_tags: dict[int, tuple[int, ...]] = {}
        #: author id -> byline, for sites whose API gives no author names.
        self.byline_map: dict[int, tuple[str, ...]] = {}
        #: canonical URL -> byline read from the article page (``commonswire page-bylines``).
        self.page_bylines: dict[str, tuple[str, ...]] = {}
        #: canonical URLs whose page byline names the source itself and no person.
        self.source_credited: set[str] = set()
        #: canonical URL -> translators named apart from the writers (a story listing).
        self.page_translators: dict[str, tuple[str, ...]] = {}
        #: canonical URL -> why the page or listing names no person (``not_a_person``, ...).
        self.byline_why_none: dict[str, str] = {}
        #: canonical URL -> its other-language versions and original (series 0.3 on;
        #: ``commonswire versions``).
        self.versions: dict[str, dict] = {}

    def fields(self, *, with_tags: bool = False) -> str:
        """The fields a backfill or an update asks for. Series 0.3 on also asks for each
        post's tag ids (``with_tags``); the fields of series 0.1 and 0.2 are unchanged."""
        return f"{self.backfill_fields},tags" if with_tags else self.backfill_fields

    def backfill_url(self, page: int, per_page: int = PER_PAGE, *, with_tags: bool = False) -> str:
        """Oldest first, so posts published during a backfill do not shift the pages."""
        params = {
            "per_page": str(per_page),
            "page": str(page),
            "orderby": "date",
            "order": "asc",
            "_fields": self.fields(with_tags=with_tags),
        }
        return f"{self.api_base}/wp-json/wp/v2/posts?{urlencode(params)}"

    def tags_only_url(self, page: int, per_page: int = PER_PAGE) -> str:
        """A page of posts with their ids and tag ids only (the tags backfill of an archive
        saved without them), oldest first."""
        params = {
            "per_page": str(per_page),
            "page": str(page),
            "orderby": "date",
            "order": "asc",
            "_fields": "id,tags",
        }
        return f"{self.api_base}/wp-json/wp/v2/posts?{urlencode(params)}"

    def categories_url(self, page: int) -> str:
        params = {"per_page": "100", "page": str(page), "_fields": "id,name"}
        return f"{self.api_base}/wp-json/wp/v2/categories?{urlencode(params)}"

    def tags_url(self, page: int) -> str:
        params = {"per_page": "100", "page": str(page), "_fields": "id,name"}
        return f"{self.api_base}/wp-json/wp/v2/tags?{urlencode(params)}"

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
        key = ""
        if post.get("link"):
            try:
                key = canonical_url(post["link"])
            except ValueError:
                key = ""
        if not authors and key:
            authors = self.page_bylines.get(key, ())
        byline_is_source = not authors and key in self.source_credited
        translators = self.page_translators.get(key, ()) if key else ()
        why_none = "" if authors or not key else self.byline_why_none.get(key, "")
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
        if not tags and self.tag_names:
            ids = post.get("tags")
            if not isinstance(ids, list):
                ids = self.post_tags.get(post.get("id"), ())  # type: ignore[arg-type]
            tags = [strip_tags(self.tag_names[t]) for t in ids if t in self.tag_names]
        versions = self.versions.get(key, {}) if key else {}
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
            translators=translators,
            section=categories[0] if categories else "",
            hints={
                "categories": categories,
                "tags": tags,
                "type": post.get("type", ""),
                "byline_is_source": byline_is_source,
                "byline_why_none": why_none,
                "other_versions": tuple(versions.get("other_versions") or ()),
                "original_url": versions.get("original_url", ""),
            },
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


#: Global Voices' language sites (Lingua), by subdomain, as listed on
#: https://globalvoices.org/lingua/ (2026-11-17).
LINGUA_SITES = (
    "am", "ar", "aym", "bg", "bn", "ca", "cs", "da", "de", "el", "eo", "es", "fa", "fil", "fr",
    "he", "hi", "hr", "hu", "id", "ig", "it", "jp", "kk", "km", "ko", "ku", "mg", "mk", "my",
    "ne", "nl", "or", "pa", "pl", "pt", "ro", "ru", "sat", "sq", "sr", "sv", "sw", "tet", "tr",
    "uk", "ur", "uz", "yo", "zhs", "zht",
)  # fmt: skip


class GlobalVoicesLinguaFetcher(GlobalVoicesFetcher):
    """A Global Voices language site (Lingua). Its rows take their language from the registry
    row, their writers and translators from the site's own listing, and their other-language
    versions from ``commonswire versions``; the release applies the Lingua rule
    (``commonswire.lingua``)."""

    site = ""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.language = self.source.languages[0]


def _lingua_class(site: str) -> type[GlobalVoicesLinguaFetcher]:
    return type(
        f"GlobalVoicesLingua_{site}",
        (GlobalVoicesLinguaFetcher,),
        {
            "source_id": f"globalvoices_{site}",
            "site": site,
            "api_base": f"https://{site}.globalvoices.org",
            "__doc__": f"Global Voices' {site} site (Lingua).",
        },
    )


#: One fetcher class per Lingua site.
LINGUA_FETCHERS: dict[str, type[GlobalVoicesLinguaFetcher]] = {
    f"globalvoices_{site}": _lingua_class(site) for site in LINGUA_SITES
}


class ThreeSixtyInfoFetcher(WordPressFetcher):
    """360info: commissioned articles by named researchers, CC BY 4.0 except where noted.
    Third-party material is noted with the content; such posts are dropped."""

    source_id = "360info"
    requires_byline = True
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
    requires_byline = True
    api_base = "https://balkandiskurs.com/en"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")


#: Republication notes in Bosnian ("originally published", "taken from"), for the Bosnian
#: edition, whose notes the English words would miss.
REPUBLISHED_BS = re.compile(
    r"\b((originalno|prvobitno|izvorno) (je )?(objavljen|objavljena|objavljeno)|"
    r"(tekst|članak|clanak) (je )?(preuzet|prenesen)|preuzeto (sa|s|iz|od)|"
    r"preneseno (sa|s|iz|od)|objavljeno uz dozvolu)",
    re.I,
)


class BalkanDiskursBosnianFetcher(BalkanDiskursFetcher):
    """Balkan Diskurs, Bosnian edition (the root WordPress site, its default language): CC BY
    under its own Bosnian attribution policy. Republication notes are looked for in Bosnian
    as well as in English."""

    source_id = "balkandiskurs_bs"
    api_base = "https://balkandiskurs.com"
    language = "bs"

    def third_party_reason(self, item: Item) -> str | None:
        reason = super().third_party_reason(item)
        if reason:
            return reason
        text = strip_tags(item.body_html)
        if REPUBLISHED_BS.search(text[:400]) or REPUBLISHED_BS.search(text[-600:]):
            return "republication_note"
        return None


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
    requires_byline = True
    api_base = "https://thepublicrecord.ca"
    language = "en"
    drop_classes = ("sharedaddy", "jp-relatedposts", "share", "newsletter", "wp-caption")
