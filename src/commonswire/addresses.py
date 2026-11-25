"""Article addresses in the tracked files: what counts as one, and its id in its place.

An article's address carries its headline's words, so the tracked files name an article page
by its id (``cw_`` and 16 hex digits of the SHA-256 of its canonical URL: the rows' own ids),
never by its address. The files are the request log (``data/usage_log.csv``, its ``path``),
the evidence pages (``data/evidence/pages.csv``, ``url``, ``final_url`` and the snapshot's
``file`` name) and the license links seen on them (``data/evidence/license_links.csv``,
``page_url``).

An address is an article's when it is:

- a dated permalink: a path with ``/YYYY/MM/`` or ``/YYYY/MM/DD/`` and a name after it, as
  WordPress writes them (with any prefix before the date); or
- a Wikinews page in the main namespace (``/wiki/`` and a title with no ``Namespace:``
  prefix).

A page that is not an article keeps its address: a source's home or main page (the evidence's
``home`` rows, where they lead, and the registry's ``homepage``), a page the registry cites
for a source's license or terms (``license_url``, ``terms_url``), even when it is a dated
post, and a page that refused scripted requests (blocked or disallowed), which is listed for
the maintainer to read in a browser. Namespace pages (copyright and policy pages, categories,
templates) are never articles.

:func:`rewrite` is the one-off change of 2026-11-25 for the rows written before the log
named article pages by id: the full files and the map from each address to its id go to the
data drive first (``data/raw/logs/``), never tracked, so the evidence can still be traced.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from commonswire.schema import article_id, canonical_url

DATED = re.compile(r"/(?:19|20)\d{2}/\d{2}(?:/\d{2})?/[^/?#]+")
_ID = re.compile(r"^cw_[0-9a-f]{16}$")
LOG = "data/usage_log.csv"
PAGES = "data/evidence/pages.csv"
LINKS = "data/evidence/license_links.csv"
#: The evidence outcomes of a page that refused scripted requests.
REFUSED = ("blocked", "disallowed")


def _canon(url: str) -> str:
    try:
        return canonical_url(url)
    except ValueError:
        return url


def kind(url: str) -> str:
    """``dated``, ``wiki`` (a Wikinews main-namespace page) or empty: the shape of an article
    address, before the kept pages are set aside."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    path = parts.path or "/"
    if host.endswith("wikinews.org") and path.startswith("/wiki/"):
        title = unquote(path[len("/wiki/") :])
        return "wiki" if title and ":" not in title else ""
    return "dated" if DATED.search(path) else ""


def kept_addresses(root: Path) -> set[str]:
    """The addresses that are not articles' (canonical forms): home and main pages, and the
    pages the registry cites for a license or terms."""
    keep: set[str] = set()
    reg = root / "data" / "sources.csv"
    if reg.exists():
        for r in _read(reg)[1]:
            for col in ("homepage", "license_url", "terms_url"):
                if r.get(col):
                    keep.add(_canon(r[col]))
    pages = root / PAGES
    if pages.exists():
        for r in _read(pages)[1]:
            if r.get("role") == "home" or r.get("outcome") in REFUSED:
                keep.update(_canon(r[c]) for c in ("url", "final_url") if r.get(c))
    return keep


def is_article_address(url: str, kept: set[str]) -> bool:
    """True for an article's address (see the module docstring); an id is not an address."""
    if not url or _ID.match(url):
        return False
    return bool(kind(url)) and _canon(url) not in kept


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(buf.getvalue(), encoding="utf-8", newline="")
    tmp.replace(path)


def log_url(row: dict[str, str]) -> str:
    """The address a request-log row names (its host and path; no query values are kept)."""
    return f"https://{row['host']}{row['path']}"


@dataclass
class Found:
    """Article addresses found in the tracked files, counted by file, field and kind."""

    counts: Counter[tuple[str, str, str]] = field(default_factory=Counter)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def lines(self) -> list[str]:
        return [f"{f} {col} {k}: {n}" for (f, col, k), n in sorted(self.counts.items())]


def find(root: Path, kept: set[str] | None = None) -> Found:
    """The article addresses left in the tracked files (counts only, never the addresses)."""
    kept = kept_addresses(root) if kept is None else kept
    out = Found()
    if (root / LOG).exists():
        for r in _read(root / LOG)[1]:
            if not _ID.match(r["path"]) and is_article_address(log_url(r), kept):
                out.counts[(LOG, "path", kind(log_url(r)))] += 1
    for name, cols in ((PAGES, ("url", "final_url")), (LINKS, ("page_url",))):
        if not (root / name).exists():
            continue
        for r in _read(root / name)[1]:
            for col in cols:
                if is_article_address(r.get(col, ""), kept):
                    out.counts[(name, col, kind(r[col]))] += 1
    return out


def snapshot_name(file: str, rid: str) -> str:
    """A snapshot's name with the article's id in place of the address it was named after
    (``2026-11-17/src/03-a-headline.html`` -> ``2026-11-17/src/03-cw_....html``)."""
    folder, _, name = file.rpartition("/")
    index = name.split("-", 1)[0]
    return f"{folder}/{index}-{rid}.html"


def rewrite(root: Path, save_to: Path) -> dict[str, object]:
    """Put each article address's id in its place in the three tracked files, after copying
    the files as they are and the map (address, id, file and field) to ``save_to``; a snapshot
    named after an article's address is copied to a name with its id (the original stays).
    Returns counts only."""
    kept = kept_addresses(root)
    save_to.mkdir(parents=True, exist_ok=True)
    for name in (LOG, PAGES, LINKS):
        if (root / name).exists():
            target = save_to / Path(name).name
            if target.exists():
                raise FileExistsError(f"{target} exists: a saved copy is never overwritten")
            shutil.copyfile(root / name, target)
    mapping: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    def to_id(url: str, where: str) -> str:
        rid = article_id(url)
        mapping.append({"file": where, "address": url, "id": rid})
        counts[f"{where} {kind(url)}"] += 1
        return rid

    fields, rows = _read(root / LOG)
    for r in rows:
        if not _ID.match(r["path"]) and is_article_address(log_url(r), kept):
            r["path"] = to_id(log_url(r), f"{LOG} path")
            r["query_keys"] = ""
    _write(root / LOG, fields, rows)

    fields, rows = _read(root / PAGES)
    snapshots = root / "data" / "raw" / "evidence"
    for r in rows:
        url_id = ""
        for col in ("url", "final_url"):
            if is_article_address(r[col], kept):
                rid = to_id(r[col], f"{PAGES} {col}")
                url_id = url_id or rid
                r[col] = rid
        if url_id and r.get("file"):
            new = snapshot_name(r["file"], article_id_of_row(r, url_id))
            src, dst = snapshots / r["file"], snapshots / new
            if src.exists() and not dst.exists():
                shutil.copyfile(src, dst)
                counts["snapshot copied with its id"] += 1
            elif not src.exists():
                counts["snapshot not on the drive"] += 1
            mapping.append({"file": f"{PAGES} file", "address": r["file"], "id": new})
            r["file"] = new
    _write(root / PAGES, fields, rows)

    fields, rows = _read(root / LINKS)
    for r in rows:
        if is_article_address(r["page_url"], kept):
            r["page_url"] = to_id(r["page_url"], f"{LINKS} page_url")
    _write(root / LINKS, fields, rows)

    _write(save_to / "address-ids.csv", ["file", "address", "id"], mapping)
    (save_to / "README.txt").write_text(
        "The tracked files as they were before their article addresses were replaced by ids, "
        "and the map from each address to its id. Never tracked, never published.\n",
        encoding="utf-8",
    )
    return {"changed": dict(sorted(counts.items())), "left": find(root, kept).total}


def article_id_of_row(row: dict[str, str], url_id: str) -> str:
    """The id a snapshot is named after: the page it ended at (``final_url``) when that is an
    article's, else the one asked for."""
    return row["final_url"] if _ID.match(row["final_url"]) else url_id


def summary_json(result: dict[str, object]) -> str:
    return json.dumps(result, indent=1, sort_keys=True)
