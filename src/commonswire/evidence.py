"""Collect the evidence for the source registry: robots.txt, the homepage and policy pages.

For each candidate source (``data/candidates.csv``) :func:`fetch_evidence` reads robots.txt, the
homepage, the seed URLs and up to a few policy pages linked from the homepage (republishing,
license, copyright, terms). Every page is fetched through :class:`~commonswire.http.PoliteClient`
and saved once, unchanged, under ``data/raw/evidence/<date>/<source_id>/`` on the data drive.
The tracked files hold only metadata:

- ``data/evidence/pages.csv``: one row per page (URL, status, bytes, SHA-256, outcome);
- ``data/evidence/robots.csv``: one row per source (the robots.txt answer and what it allows);
- ``data/evidence/license_links.csv``: Creative Commons and ``rel=license`` links seen on pages.

:func:`extract_evidence` turns the saved pages into text and keyword lines in ``data/interim/``
for reading, and :func:`page_texts` gives the text of every saved page of a source, which the
registry check uses to confirm that each quote is verbatim.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from commonswire.html import links, page_text
from commonswire.http import Blocked, BudgetExceeded, Disallowed, FetchError, PoliteClient

CANDIDATE_FIELDS = ["source_id", "name", "homepage", "kind", "seed_urls", "notes"]
PAGE_FIELDS = [
    "checked_on",
    "source_id",
    "role",
    "url",
    "final_url",
    "status",
    "bytes",
    "sha256",
    "outcome",
    "file",
]
ROBOTS_FIELDS = [
    "checked_on",
    "source_id",
    "host",
    "robots_status",
    "state",
    "home_allowed",
    "feed_allowed",
    "wp_json_allowed",
    "crawl_delay",
    "ai_crawlers_shut_out",
]
LICENSE_LINK_FIELDS = ["checked_on", "source_id", "page_url", "license_url", "link_text"]

#: Link texts or addresses that point at a policy page, best first.
POLICY_PATTERNS: list[tuple[int, re.Pattern[str]]] = [
    (0, re.compile(r"republish|re-publish|reprint|steal[- ]our|syndicat|share our|use our", re.I)),
    (1, re.compile(r"licen[cs]|copyright|creative ?commons|reuse|re-use|permission", re.I)),
    (2, re.compile(r"terms|legal|conditions|policies|editorial[- ]polic", re.I)),
]
_SOCIAL = re.compile(
    r"facebook\.com|twitter\.com|x\.com/|linkedin\.com|instagram\.com|whatsapp|t\.me/|"
    r"reddit\.com|mailto:|javascript:|tel:",
    re.I,
)
_CC_LICENSE = re.compile(r"creativecommons\.org/(licenses|publicdomain)/", re.I)

#: Words that make a line worth reading in the extracted evidence.
KEYWORDS = re.compile(
    r"republish|reprint|licen[cs]|creative commons|\bCC[ -]?BY|CC0|public domain|copyright|"
    r"all rights reserved|automat|bulk|wholesale|systematic|scrap|crawl|robot|spider|harvest|"
    r"pixel|tracking|counter|analytics|attribut|credit|wire|associated press|\bAP\b|reuters|"
    r"\bAFP\b|syndicat|partner|third[- ]party|originally (published|appeared)|machine learning|"
    r"artificial intelligence|\bAI\b|train|text and data mining|data mining|commercial|"
    r"non-?commercial|derivative|unchanged|edit|in full|entire|individual|database|archive",
    re.I,
)


@dataclass(frozen=True)
class Candidate:
    source_id: str
    name: str
    homepage: str
    kind: str
    seed_urls: tuple[str, ...]
    notes: str = ""


def read_candidates(path: Path) -> list[Candidate]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for n, row in enumerate(rows, start=2):
        missing = [f for f in ("source_id", "name", "homepage", "kind") if not row.get(f)]
        if missing:
            raise ValueError(f"{path}, line {n}: fill in {', '.join(missing)}")
        out.append(
            Candidate(
                source_id=row["source_id"].strip(),
                name=row["name"].strip(),
                homepage=row["homepage"].strip(),
                kind=row["kind"].strip(),
                seed_urls=tuple((row.get("seed_urls") or "").split()),
                notes=(row.get("notes") or "").strip(),
            )
        )
    ids = [c.source_id for c in out]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"{path}: source_id used twice: {', '.join(dupes)}")
    return out


def site_key(host: str) -> str:
    """A host without ``www.``, used to keep link discovery on the source's own site."""
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url: str, homepage: str) -> bool:
    a = site_key(urlsplit(url).hostname or "")
    b = site_key(urlsplit(homepage).hostname or "")
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def normalize_link(href: str, base: str) -> str | None:
    """An absolute http(s) URL without its fragment, or None for links not worth following."""
    if not href or _SOCIAL.search(href):
        return None
    url = urljoin(base, href.strip())
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def policy_links(html: str, base: str, homepage: str) -> list[str]:
    """Policy-page links on the source's own site, best first, without duplicates."""
    ranked: list[tuple[int, int, str]] = []
    for order, (href, text) in enumerate(links(html)):
        url = normalize_link(href, base)
        if url is None or not same_site(url, homepage) or _CC_LICENSE.search(url):
            continue
        hay = f"{text} {urlsplit(url).path}"
        for rank, pattern in POLICY_PATTERNS:
            if pattern.search(hay):
                ranked.append((rank, order, url))
                break
    seen: set[str] = set()
    out = []
    for _, _, url in sorted(ranked):
        if url not in seen and url.rstrip("/") != homepage.rstrip("/"):
            seen.add(url)
            out.append(url)
    return out


def license_links(html: str, base: str) -> list[tuple[str, str]]:
    """Creative Commons and rel=license links on a page, as (URL, link text)."""
    out = []
    for href, text in links(html):
        url = urljoin(base, href.strip()) if href else ""
        if _CC_LICENSE.search(url) or text == "rel=license":
            out.append((url, text[:120]))
    return out


def _slug(url: str) -> str:
    path = urlsplit(url).path.strip("/") or "home"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()
    return slug[:60] or "page"


def _append(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        if new:
            writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@dataclass
class EvidencePaths:
    """Where evidence goes: snapshots on the drive, metadata tracked, readings in interim."""

    root: Path
    checked_on: str

    @property
    def snapshots(self) -> Path:
        return self.root / "data" / "raw" / "evidence" / self.checked_on

    @property
    def tracked(self) -> Path:
        return self.root / "data" / "evidence"

    @property
    def interim(self) -> Path:
        return self.root / "data" / "interim" / "evidence" / self.checked_on


def _save_once(path: Path, body: bytes) -> None:
    """Write a snapshot once; an existing file is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as fh:
        fh.write(body)


def fetch_evidence(
    client: PoliteClient,
    candidates: list[Candidate],
    paths: EvidencePaths,
    *,
    max_policy_pages: int = 5,
    extra_urls: dict[str, list[str]] | None = None,
    progress: Callable[[str], None] = lambda _msg: None,
) -> dict[str, int]:
    """Fetch the evidence pages of each candidate; return counts by outcome.

    Pages already recorded for the same date are skipped, so a run can be resumed.
    ``extra_urls`` adds pages to read for named sources (a second pass after reading).
    """
    pages_csv = paths.tracked / "pages.csv"
    done = {
        (r["checked_on"], r["source_id"], r["url"])
        for r in read_rows(pages_csv)
        if r["checked_on"] == paths.checked_on
    }
    robots_done = {
        (r["checked_on"], r["source_id"])
        for r in read_rows(paths.tracked / "robots.csv")
        if r["checked_on"] == paths.checked_on
    }
    counts: dict[str, int] = {}
    for cand in candidates:
        progress(f"{cand.source_id}: reading robots.txt and pages")
        if (paths.checked_on, cand.source_id) not in robots_done:
            _append(paths.tracked / "robots.csv", ROBOTS_FIELDS, [_robots_row(client, cand, paths)])
        queue: list[tuple[str, str]] = [("home", cand.homepage)]
        queue += [("seed", u) for u in cand.seed_urls]
        queue += [("extra", u) for u in (extra_urls or {}).get(cand.source_id, [])]
        found_budget = max_policy_pages
        seen = {u for _, u in queue}
        index = (
            len(list((paths.snapshots / cand.source_id).glob("*")))
            if (paths.snapshots / cand.source_id).exists()
            else 0
        )
        while queue:
            role, url = queue.pop(0)
            if (paths.checked_on, cand.source_id, url) in done:
                continue
            index += 1
            row, body = _fetch_page(client, cand, paths, role, url, index)
            _append(pages_csv, PAGE_FIELDS, [row])
            done.add((paths.checked_on, cand.source_id, url))
            outcome = str(row["outcome"])
            counts[outcome] = counts.get(outcome, 0) + 1
            if outcome == "budget":
                return counts
            if body is None:
                continue
            html = body.decode("utf-8", errors="replace")
            final = str(row["final_url"])
            cc_rows = [
                {
                    "checked_on": paths.checked_on,
                    "source_id": cand.source_id,
                    "page_url": final,
                    "license_url": lic,
                    "link_text": text,
                }
                for lic, text in license_links(html, final)
            ]
            if cc_rows:
                _append(paths.tracked / "license_links.csv", LICENSE_LINK_FIELDS, cc_rows)
            if role == "home":
                for link in policy_links(html, final, cand.homepage):
                    if found_budget <= 0:
                        break
                    if link not in seen:
                        seen.add(link)
                        queue.append(("found", link))
                        found_budget -= 1
    return counts


def _robots_row(client: PoliteClient, cand: Candidate, paths: EvidencePaths) -> dict[str, object]:
    home = cand.homepage
    rule = client.robots(home)
    base = f"{urlsplit(home).scheme}://{urlsplit(home).netloc}"
    delay = rule.crawl_delay()
    return {
        "checked_on": paths.checked_on,
        "source_id": cand.source_id,
        "host": rule.host,
        "robots_status": rule.status,
        "state": rule.state,
        "home_allowed": _yes(rule.allows(home)),
        "feed_allowed": _yes(rule.allows(base + "/feed/")),
        "wp_json_allowed": _yes(rule.allows(base + "/wp-json/wp/v2/posts")),
        "crawl_delay": "" if delay is None else delay,
        "ai_crawlers_shut_out": ";".join(rule.ai_crawlers_shut_out),
    }


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def _fetch_page(
    client: PoliteClient,
    cand: Candidate,
    paths: EvidencePaths,
    role: str,
    url: str,
    index: int,
) -> tuple[dict[str, object], bytes | None]:
    row: dict[str, object] = {
        "checked_on": paths.checked_on,
        "source_id": cand.source_id,
        "role": role,
        "url": url,
        "final_url": url,
        "status": "",
        "bytes": 0,
        "sha256": "",
        "outcome": "",
        "file": "",
    }
    try:
        resp = client.get(url, note=f"evidence:{cand.source_id}")
    except Disallowed:
        row["outcome"] = "disallowed"
        return row, None
    except Blocked as exc:
        row.update(status=exc.status, outcome="blocked")
        return row, None
    except BudgetExceeded:
        row["outcome"] = "budget"
        return row, None
    except FetchError:
        row["outcome"] = "error"
        return row, None
    row.update(final_url=resp.url, status=resp.status, bytes=len(resp.body))
    if resp.status != 200:
        row["outcome"] = "not_found" if resp.status in (404, 410) else f"http_{resp.status}"
        return row, None
    name = f"{index:02d}-{_slug(resp.url)}.html"
    _save_once(paths.snapshots / cand.source_id / name, resp.body)
    row.update(
        sha256=hashlib.sha256(resp.body).hexdigest(),
        outcome="ok",
        file=f"{paths.checked_on}/{cand.source_id}/{name}",
    )
    return row, resp.body


def snapshot_files(root: Path, source_id: str) -> list[Path]:
    """Every saved evidence page of a source, across all dates."""
    base = root / "data" / "raw" / "evidence"
    if not base.exists():
        return []
    return sorted(base.glob(f"*/{source_id}/*.html"))


def page_texts(root: Path, source_id: str) -> dict[str, str]:
    """The visible text of every saved page of a source, keyed by snapshot path."""
    out = {}
    for path in snapshot_files(root, source_id):
        out[str(path)] = page_text(path.read_bytes().decode("utf-8", errors="replace"))
    return out


def extract_evidence(root: Path, checked_on: str, source_ids: Iterable[str] | None = None) -> int:
    """Write each page's text and its keyword lines to ``data/interim``; return pages read."""
    paths = EvidencePaths(root, checked_on)
    rows = [r for r in read_rows(paths.tracked / "pages.csv") if r["checked_on"] == checked_on]
    wanted = set(source_ids) if source_ids is not None else None
    by_source: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        if wanted is None or r["source_id"] in wanted:
            by_source.setdefault(r["source_id"], []).append(r)
    n = 0
    for source_id, srows in by_source.items():
        out = paths.interim / source_id
        out.mkdir(parents=True, exist_ok=True)
        lines = [f"# {source_id} (evidence of {checked_on})", ""]
        for r in srows:
            lines.append(f"## {r['role']}: {r['url']}")
            lines.append(f"final: {r['final_url']} · status {r['status']} · {r['outcome']}")
            if r["outcome"] != "ok":
                lines.append("")
                continue
            snap = root / "data" / "raw" / "evidence" / r["file"]
            text = page_text(snap.read_bytes().decode("utf-8", errors="replace"))
            (out / (Path(r["file"]).stem + ".txt")).write_text(text, encoding="utf-8")
            n += 1
            seen: set[str] = set()
            for line in text.splitlines():
                if KEYWORDS.search(line) and line not in seen and len(line) > 3:
                    seen.add(line)
                    lines.append(f"- {line[:700]}")
            lines.append("")
        (out / "hits.md").write_text("\n".join(lines), encoding="utf-8")
    return n
