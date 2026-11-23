"""Each row's other-language versions (series 0.3 on), from what the publishers link, with no
request.

- **Global Voices:** the English site and its language sites, grouped through each Lingua
  post's English version (``commonswire lingua-link``), with ``original_url`` by answer 5a
  (:func:`commonswire.lingua.version_groups`); translators come from the listings.
- **Balkan Diskurs:** its English and Bosnian pages name each other in ``<link
  rel="alternate" hreflang="…">`` tags, read from the article pages saved for bylines. Neither
  edition credits a translator, so no ``original_url`` is set.

``commonswire versions`` writes ``data/interim/versions/<source>.json`` (canonical URL ->
``other_versions`` and ``original_url``), which ``commonswire build`` reads.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from urllib.parse import urlsplit

from commonswire.lingua import ENGLISH_HOST, ENGLISH_SOURCE, read_links, version_groups
from commonswire.schema import canonical_url

_ALTERNATE = re.compile(r"<link\b[^>]*>", re.I)
_ATTR = re.compile(r"""(\w[\w-]*)\s*=\s*["']([^"']*)["']""")

#: Sources whose saved article pages name their other-language versions with hreflang:
#: source id -> {hreflang -> source id of that language's edition}.
HREFLANG_SOURCES: dict[str, dict[str, str]] = {
    "balkandiskurs": {"en": "balkandiskurs", "bs": "balkandiskurs_bs"},
    "balkandiskurs_bs": {"en": "balkandiskurs", "bs": "balkandiskurs_bs"},
}


def hreflang_links(html: str) -> dict[str, str]:
    """The ``<link rel="alternate" hreflang="…" href="…">`` tags of a page's head (language ->
    the address as given), ``x-default`` left out."""
    head = html.split("</head>", 1)[0]
    out: dict[str, str] = {}
    for tag in _ALTERNATE.findall(head):
        attrs = {k.lower(): v for k, v in _ATTR.findall(tag)}
        if attrs.get("rel", "").lower() != "alternate":
            continue
        lang = attrs.get("hreflang", "").lower()
        href = attrs.get("href", "")
        if not lang or lang == "x-default" or not href:
            continue
        try:
            canonical_url(href)
        except ValueError:
            continue
        out.setdefault(lang, href)
    return out


def hreflang_groups(pages: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Canonical URL -> the other versions' addresses, from pages' hreflang tags (each page
    names itself too)."""
    groups: dict[str, dict[str, str]] = defaultdict(dict)
    for html in pages:
        links = {canonical_url(u): u for u in hreflang_links(html).values()}
        if len(links) < 2:
            continue
        for key in links:
            groups[key].update(links)
    return {k: tuple(sorted(u for c, u in v.items() if c != k)) for k, v in groups.items()}


def lingua_source(url: str) -> str:
    """The source id of a Global Voices address: ``globalvoices`` or ``globalvoices_<site>``."""
    host = urlsplit(url).hostname or ""
    if host == ENGLISH_HOST:
        return ENGLISH_SOURCE
    return f"{ENGLISH_SOURCE}_{host.split('.', 1)[0]}"


def global_voices_versions(
    links_dir: Path, bylines_dir: Path
) -> tuple[dict[str, dict[str, dict]], Counter[str]]:
    """Source -> URL -> versions for Global Voices, and counts."""
    english_of: dict[str, str] = {}
    for path in sorted(links_dir.glob(f"{ENGLISH_SOURCE}_*.links.json")):
        for m in read_links(path).values():
            english_of[m["url"]] = m["en"]
    translators: dict[str, tuple[str, ...]] = {}
    for path in sorted(bylines_dir.glob(f"{ENGLISH_SOURCE}*.listing.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for url, v in data.items():
            if v.get("translators"):
                translators[url] = tuple(v["translators"])
    groups = version_groups(english_of, translators)
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    counts: Counter[str] = Counter()
    for url, v in groups.items():
        sid = lingua_source(url)
        out[sid][url] = {"other_versions": list(v.other_versions), "original_url": v.original_url}
        counts[f"{sid}:rows_with_versions"] += 1
        counts[f"{sid}:with_original_url"] += int(bool(v.original_url))
    return dict(out), counts


def hreflang_versions(
    pages_root: Path, sources: Mapping[str, Mapping[str, str]] = HREFLANG_SOURCES
) -> tuple[dict[str, dict[str, dict]], Counter[str]]:
    """Source -> URL -> versions for the hreflang sources, from their saved article pages."""
    pages: list[str] = []
    for sid in sorted(sources):
        folder = pages_root / sid
        for path in sorted(folder.glob("*.html")):
            pages.append(path.read_bytes().decode("utf-8", errors="replace"))
    groups = hreflang_groups(pages)
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    counts: Counter[str] = Counter()
    by_lang = {lang: s for mapping in sources.values() for lang, s in mapping.items()}
    for html in pages:
        for lang, url in hreflang_links(html).items():
            sid = by_lang.get(lang)
            key = canonical_url(url)
            if sid is None or key not in groups:
                continue
            out[sid][key] = {"other_versions": list(groups[key]), "original_url": ""}
    for sid, rows in out.items():
        counts[f"{sid}:rows_with_versions"] = len(rows)
    return dict(out), counts


def write_versions(folder: Path, versions: Mapping[str, Mapping[str, dict]]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for sid, rows in versions.items():
        path = folder / f"{sid}.json"
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(dict(sorted(rows.items())), indent=1) + "\n", encoding="utf-8")
        tmp.replace(path)


def load_versions(folder: Path, source_id: str) -> dict[str, dict]:
    path = folder / f"{source_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
