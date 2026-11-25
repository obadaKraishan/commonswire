"""Wikinews' language editions (series 0.3 on): their dumps, their articles' creation dates and
licenses by date, read with no request once the dumps are saved.

Every edition closed on 2026-05-04 and is read from Wikimedia's dump server, like the English
edition (``commonswire.wikidump``). Two files are saved for each edition:

- ``<wiki>-latest-pages-articles.xml.bz2``: each page's latest wikitext;
- ``<wiki>-latest-stub-meta-history.xml.gz``: every revision's metadata (no text), for each
  page's **creation date**, its first revision. The maintainer's rule (2026-11-23) takes an
  article's license from its edition's license-by-date table (``commonswire.licensing``) by
  that date; a date the table does not place is held and counted.

Editions mark a published article in their own words, so each edition's markers
(:data:`EDITION_MARKERS`) are set from that edition's own dump: :func:`template_census` counts
the templates of its article pages (names and counts only). An edition with no markers set is
not read. No function here sends a request.
"""

from __future__ import annotations

import gzip
import re
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO
from urllib.parse import quote

from commonswire.wikidump import _REF, DumpArticle, _local, _remove_balanced, wiki_to_text

DUMPS = "https://dumps.wikimedia.org"
_TEMPLATE = re.compile(r"\{\{\s*([^{}|\n]{1,60}?)\s*[|}]")


def wiki_name(source_id: str) -> str:
    """``wikinews_fr`` -> ``frwikinews`` (the dump server's name of the edition)."""
    return f"{source_id.split('_', 1)[1]}wikinews"


def file_names(source_id: str) -> dict[str, str]:
    wiki = wiki_name(source_id)
    return {
        "articles": f"{wiki}-latest-pages-articles.xml.bz2",
        "stubs": f"{wiki}-latest-stub-meta-history.xml.gz",
        "md5sums": f"{wiki}-latest-md5sums.txt",
    }


def file_url(source_id: str, name: str) -> str:
    return f"{DUMPS}/{wiki_name(source_id)}/latest/{name}"


def site_url(source_id: str) -> str:
    return f"https://{source_id.split('_', 1)[1]}.wikinews.org/wiki/"


@dataclass(frozen=True)
class EditionMarkers:
    """How an edition marks its articles, read from its own dump: ``published`` is a template
    every published article carries; ``not_published`` the templates of drafts and pages under
    review; ``closing`` the headings of the closing sections (sources, related news), where
    the article's text ends."""

    published: re.Pattern[str]
    not_published: re.Pattern[str] | None = None
    closing: re.Pattern[str] | None = None


def _markers(published: str, closing: str, not_published: str = "") -> EditionMarkers:
    return EditionMarkers(
        published=re.compile(rf"\{{\{{\s*(?:{published})\s*[|}}]", re.I),
        not_published=re.compile(rf"\{{\{{\s*(?:{not_published})\s*[|}}]", re.I)
        if not_published
        else None,
        closing=re.compile(rf"^\s*==\s*(?:{closing})\s*==\s*$", re.I | re.M),
    )


#: Set edition by edition from its template census (dumps of 2026-11-25; counts are article
#: pages carrying the template); an edition not listed is not read. Swedish has no template
#: on most of its pages ("publicerad" on 186 of 3,317), so it is not read yet.
EDITION_MARKERS: dict[str, EditionMarkers] = {
    # "publication" 19,586 and "archive" 10,356 of 24,220 article pages
    "wikinews_fr": _markers("publication|archive", "sources?|voir aussi"),
    # "publish" 18,602 of 18,708; "develop" 284 (drafts)
    "wikinews_zh": _markers(
        "publish",
        "消息來源|消息来源|資料來源|资料来源|相關新聞|相关新闻|伸延閱讀|延伸閱讀|延伸阅读|参见|參見",
        "develop",
    ),
    # "نشر" (publish) 6,941 of 7,831
    "wikinews_ar": _markers(
        "نشر", "مصادر|المصادر|مصدر|انظر أيضاً|انظر أيضا|أخبار ذات الصلة|اقرأ أيضا"
    ),
    # "δημοσίευση" (publication) 2,982 and "αρχειοθετημένα" (archived) 3,013 of 3,103
    "wikinews_el": _markers(
        "δημοσίευση|αρχειοθετημένα",
        "πηγές|πηγή|παραπομπές|σχετικά νέα|δείτε επίσης|εξωτερικοί σύνδεσμοι",
    ),
    # "publicare" 1,175 and "arhivare" 704 of 1,710
    "wikinews_ro": _markers("publicare|arhivare", "referințe|sursă|surse|vezi și"),
    # "발행" (publication) 819 and "보존" (preservation) 483 of 851
    "wikinews_ko": _markers("발행|보존", "출처|관련 기사|같이 보기|같이보기"),
}


def _template_name(raw: str) -> str:
    name = raw.strip().replace("_", " ")
    return (name[:1].lower() + name[1:]) if name else name


def template_census(stream: BinaryIO) -> tuple[int, Counter[str]]:
    """The article pages (main namespace, not redirects) of a ``pages-articles`` stream, and on
    how many of them each template name occurs (each page counted once per name)."""
    pages = 0
    counts: Counter[str] = Counter()
    for _event, elem in ET.iterparse(stream, events=("end",)):
        if _local(elem.tag) != "page":
            continue
        ns = text = ""
        redirect = False
        for child in elem.iter():
            name = _local(child.tag)
            if name == "ns" and not ns:
                ns = child.text or ""
            elif name == "text" and not text:
                text = child.text or ""
            elif name == "redirect":
                redirect = True
        elem.clear()
        if ns != "0" or redirect:
            continue
        pages += 1
        counts.update({_template_name(m) for m in _TEMPLATE.findall(text)})
    return pages, counts


def first_revisions(stream: BinaryIO) -> dict[str, datetime]:
    """Each page's creation date (its earliest revision's time), by page id, from a
    ``stub-meta-history`` stream."""
    out: dict[str, datetime] = {}
    page_id = ""
    in_revision = False
    for event, elem in ET.iterparse(stream, events=("start", "end")):
        name = _local(elem.tag)
        if event == "start":
            if name == "revision":
                in_revision = True
            continue
        if name == "id" and not in_revision and not page_id:
            page_id = elem.text or ""
        elif name == "timestamp" and in_revision and page_id:
            stamp = datetime.fromisoformat((elem.text or "").replace("Z", "+00:00"))
            if page_id not in out or stamp < out[page_id]:
                out[page_id] = stamp
        elif name == "revision":
            in_revision = False
            elem.clear()
        elif name == "page":
            page_id = ""
            elem.clear()
    return out


def read_edition(
    source_id: str,
    stream: BinaryIO,
    created: dict[str, datetime],
    skipped: Counter[str],
    markers: EditionMarkers | None = None,
) -> Iterator[DumpArticle]:
    """An edition's published articles, each dated by its creation (its first revision)."""
    markers = markers or EDITION_MARKERS[source_id]
    base = site_url(source_id)
    for _event, elem in ET.iterparse(stream, events=("end",)):
        if _local(elem.tag) != "page":
            continue
        fields: dict[str, str] = {}
        redirect = False
        for child in elem.iter():
            name = _local(child.tag)
            if name in ("title", "ns", "id", "text", "timestamp") and name not in fields:
                fields[name] = child.text or ""
            elif name == "redirect":
                redirect = True
        elem.clear()
        if fields.get("ns") != "0":
            skipped["not_an_article_namespace"] += 1
            continue
        if redirect:
            skipped["redirect"] += 1
            continue
        wikitext = fields.get("text", "")
        if not markers.published.search(wikitext):
            skipped["not_marked_published"] += 1
            continue
        if markers.not_published is not None and markers.not_published.search(wikitext):
            skipped["marked_draft_or_under_review"] += 1
            continue
        born = created.get(fields.get("id", ""))
        if born is None:
            skipped["no_first_revision"] += 1
            continue
        body = wikitext
        if markers.closing is not None:
            m = markers.closing.search(body)
            if m:
                body = body[: m.start()]
        text = wiki_to_text(body)
        if not text.strip():
            skipped["empty_text"] += 1
            continue
        stamp = fields.get("timestamp", "")
        last_edit = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
        if last_edit is not None and last_edit < born:
            last_edit = None
        title = fields.get("title", "")
        yield DumpArticle(
            title=title,
            url=base + quote(title.replace(" ", "_"), safe="_(),'!:"),
            published_at=born,
            last_edit=last_edit,
            text=text,
            wikitext=wikitext,
        )


def open_stubs(path: Path) -> BinaryIO:
    return gzip.open(path, "rb")  # type: ignore[return-value]


# ---- notices of a page's own (the maintainer's rule of 2026-11-23) ----

#: A file or image link, and a gallery: the image's own notice, not the page's.
_FILE_LINK = re.compile(
    r"\[\[[^\[\]|:\n]{1,24}:[^\[\]|\n]+\.(?:jpe?g|png|gif|svg|tiff?|webp|ogg|ogv|webm|pdf)"
    r"\s*(?:\|(?:[^\[\]]|\[\[[^\[\]]*\]\])*)?\]\]",
    re.I,
)
_GALLERY = re.compile(r"<gallery\b.*?</gallery\s*>", re.I | re.S)
#: Templates that state a license or a copyright.
_LICENSE_TEMPLATE = re.compile(
    r"^(cc[- ]?by(?:[- ]?(?:sa|nc|nd))*(?:[- ]?\d(?:\.\d)?)?|cc[- ]?zero|cc0|gfdl|gnu[- ]?fdl|"
    r"copyright(?:ed)?|copyvio|pd|pd-[\w-]+|public[- ]domain|domaine[- ]public|"
    r"dominio[- ]p[uú]blico|gemeinfrei|pubblico[- ]dominio|dom[ií]nio[- ]p[uú]blico|"
    r"all rights reserved|license|licence|licencia|lizenz|licenza|licença|licentie|"
    r"лицензия|版权|著作権|저작권)",
    re.I,
)
_CC_VERSIONED = re.compile(
    r"(?:\bCC|Creative\s+Commons)[\s-]*(?:Attribution\s*|BY)"
    r"((?:[\s-]*(?:SA|ShareAlike|NC|NonCommercial|ND|NoDerivs|NoDerivatives))*)"
    r"[\s-]*(\d\.\d)",
    re.I,
)
_RESERVED = re.compile(
    r"©|\(c\)\s*\d{4}|\bcopyright\s*(?:©|\(c\)|\d{4})|all rights reserved|tous droits réservés|"
    r"todos los derechos reservados|alle rechte vorbehalten|tutti i diritti riservati|"
    r"все права защищены|版权所有|著作權所有|저작권 소유|toate drepturile rezervate|"
    r"alla rättigheter förbehållna|جميع الحقوق محفوظة|πνευματικά δικαιώματα κατοχυρωμένα",
    re.I,
)
_PD_TEMPLATE = re.compile(
    r"^(pd|pd-[\w-]+|public[- ]domain|domaine[- ]public|dominio[- ]p[uú]blico|gemeinfrei|"
    r"pubblico[- ]dominio|dom[ií]nio[- ]p[uú]blico)$",
    re.I,
)


def _cc_spdx(terms: str, version: str) -> str:
    t = terms.upper()
    parts = ["BY"]
    for short, long_ in (("NC", "NONCOMMERCIAL"), ("ND", "NODERIV"), ("SA", "SHAREALIKE")):
        if re.search(rf"\b{short}\b|{long_}", t):
            parts.append(short)
    return f"CC-{'-'.join(parts)}-{version}"


def page_notices(wikitext: str) -> list[str]:
    """The licenses a page's own notices name (an SPDX id, ``public-domain``, or
    ``rights-reserved`` for a copyright notice, or ``unknown`` for a license template that
    names none). Image captions and galleries are left out: they are the image's notice."""
    text = _GALLERY.sub(" ", _FILE_LINK.sub(" ", wikitext))
    found: list[str] = []
    for raw in _TEMPLATE.findall(text):
        name = raw.strip()
        if not _LICENSE_TEMPLATE.match(name):
            continue
        if _PD_TEMPLATE.match(name):
            found.append("public-domain")
            continue
        m = _CC_VERSIONED.search(name.replace("_", " "))
        found.append(_cc_spdx(m.group(1), m.group(2)) if m else "unknown")
    # Statements count only in the page's own text: outside any template (an image or source
    # template names a photo's or a source's license) and outside references.
    plain = _remove_balanced(_REF.sub(" ", text), "{{", "}}")
    for m in _CC_VERSIONED.finditer(plain):
        found.append(_cc_spdx(m.group(1), m.group(2)))
    if _RESERVED.search(plain):
        found.append("rights-reserved")
    return found


def notice_differs(wikitext: str, table_license: str) -> bool:
    """True when the page carries a notice of its own that differs from the license its
    edition's table gives for its date (the page is then held and counted)."""
    return any(n != table_license for n in page_notices(wikitext))
