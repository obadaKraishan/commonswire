"""Folders for the Kaggle mirror and a Zenodo record of a release. Nothing is uploaded here.

- **Kaggle** (``data/release/<version>-kaggle/``): the release's files under flat names,
  ``dataset-metadata.json`` and ``dataset-cover-image.png``. Kaggle takes exactly one license
  per dataset and its list has no entry for mixed licenses, CC BY 2.5 or the Public Domain Mark,
  so the license is ``other`` and the description says that every row carries its own license
  (``LICENSES.md``). The metadata also gives each file's description, the columns of every
  table (name, description, type, in order), the provenance (``userSpecifiedSources``) and the
  update frequency. Kaggle reads the file and column descriptions, the provenance, the update
  frequency and the cover image only through ``kaggle datasets metadata --update`` (it dropped
  the file descriptions sent with ``create``). The cover image is plain: three bars, one per
  configuration, as long as its row count, with no text and no newsroom's name or logo. The
  dataset id is left as ``KAGGLE_USERNAME/commonswire``; the publish step fills in the account.
- **Zenodo, the GitHub route** (the default): Zenodo archives a GitHub release of the
  repository, reading its metadata from ``.zenodo.json`` (which it reads in place of
  ``CITATION.cff``). :func:`check_zenodo_json` checks that file against what Zenodo's deposit
  metadata accepts and against ``CITATION.cff``, and :func:`archive_problems` checks that the
  release archive carries ``.zenodo.json`` and neither the request log nor any raw, interim or
  release data. A release archive holds the code and the source registry, no article text.
- **Zenodo, the website deposit** (the fallback, ``data/release/<version>-zenodo/``): **no
  article text and no article index.** A Zenodo record cannot be withdrawn, which does not fit
  the promise to remove an article on request, so it holds neither the text nor the list of
  article URLs (``index.csv``). It holds the code (a ``git archive`` of the commit that built
  the version), the source registry, the dataset card, ``LICENSES.md`` and the manifest, with
  ``zenodo-metadata.json`` for the deposit.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import struct
import subprocess
import tarfile
import zlib
from pathlib import Path

from commonswire.release_text import HF_URL, REPO

KAGGLE_ID = "KAGGLE_USERNAME/commonswire"
KAGGLE_TITLE = "CommonsWire: openly licensed news text"
KAGGLE_SUBTITLE = "Full-text news that publishers allow others to share, each with its license"
KAGGLE_UPDATE_FREQUENCY = "monthly"  # the mirror is updated by hand, about once a month
KAGGLE_COVER = "dataset-cover-image.png"
COVER_SIZE = (1120, 560)  # 2:1, at least Kaggle's 560 by 280
CREATOR = {"name": "Kraishan, Obada", "affiliation": "Texas Tech University"}
KEYWORDS = ["news", "journalism", "corpus", "creative commons", "communication research"]
ZENODO_FILES = ("sources.csv", "README.md", "LICENSES.md", "manifest.json")
KAGGLE_URL = "https://www.kaggle.com/datasets/obadakraishan/commonswire"
ZENODO_JSON = ".zenodo.json"
#: Zenodo's deposit metadata (developers.zenodo.org, "Deposit metadata"), as read on
#: 2026-11-14: the upload types, the relation types and the HTML tags a description may use.
ZENODO_UPLOAD_TYPES = frozenset(
    [
        "publication",
        "poster",
        "presentation",
        "dataset",
        "image",
        "video",
        "software",
        "lesson",
        "physicalobject",
        "other",
    ]
)
ZENODO_RELATIONS = frozenset(
    [
        "isCitedBy",
        "cites",
        "isSupplementTo",
        "isSupplementedBy",
        "isDescribedBy",
        "isNewVersionOf",
        "isPreviousVersionOf",
        "isPartOf",
        "hasPart",
        "isReferencedBy",
        "references",
        "isDocumentedBy",
        "documents",
        "isDerivedFrom",
        "isSourceOf",
        "requires",
        "isRequiredBy",
    ]
)
ZENODO_HTML = frozenset(
    [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "br",
        "code",
        "caption",
        "div",
        "em",
        "i",
        "li",
        "ol",
        "p",
        "pre",
        "span",
        "strike",
        "strong",
        "sub",
        "table",
        "tbody",
        "thead",
        "th",
        "td",
        "tr",
        "u",
        "ul",
    ]
)
#: Paths a release archive must never carry: the request log, and any collected data.
NOT_IN_ARCHIVE = re.compile(r"^[^/]+/data/(usage_log\.csv$|raw/|interim/|release/)")
_FRONT = re.compile(r"\A---\n.*?\n---\n+", re.S)

#: The released columns, in order, with their Kaggle type and description.
ROW_COLUMNS = (
    ("id", "id", "cw_ and 16 hex digits of the SHA-256 of the canonical URL; stable"),
    ("source_id", "string", "The source, as in sources.csv"),
    ("kind", "string", "The source's kind: news or fact-check"),
    ("title", "string", "The headline as published"),
    ("authors", "string", "The bylines as published (a list; empty when no person is named)"),
    ("translators", "string", "The translators the source names (a list; often empty)"),
    ("published_at", "datetime", "When the source published the article (UTC)"),
    ("updated_at", "datetime", "When the source last updated it, if it says (UTC)"),
    ("retrieved_at", "datetime", "When CommonsWire fetched the article (UTC)"),
    ("language", "string", "The language tag (en)"),
    ("section", "string", "The source's own section or category, if any"),
    ("url", "url", "The article at its source"),
    ("license", "string", "The article's license (an SPDX id, or public-domain)"),
    ("license_url", "url", "The license's legal text (the Public Domain Mark for public domain)"),
    ("credit_line", "string", "The attribution to keep with the text, as the source asks"),
    ("text", "string", "The body text, words unchanged; paragraphs separated by a blank line"),
    ("content_hash", "string", "SHA-256 of text, to spot changed articles between versions"),
    ("status", "string", "live, or changed if the source edited the text after collection"),
    ("near_duplicates", "string", "Ids of very similar articles in other sources (a list)"),
)
INDEX_COLUMNS = (
    ("id", "id", "The article's id, as in the Parquet files"),
    ("source_id", "string", "The source, as in sources.csv"),
    ("configuration", "string", "The license class it is in: by, by-sa or pd"),
    ("url", "url", "The article at its source"),
    ("license", "string", "The article's license"),
    ("content_hash", "string", "SHA-256 of the article's text"),
    ("published_at", "datetime", "When the source published it (UTC)"),
)
SOURCE_COLUMNS = (
    ("source_id", "id", "The source's id"),
    ("name", "string", "The source's name"),
    ("kind", "string", "news, fact-check, official, advocacy, portal, state- or church-agency"),
    ("homepage", "url", "The source's home page"),
    ("country", "string", "Where it is based (INTL when international)"),
    ("languages", "string", "The languages it publishes in"),
    ("license", "string", "The license its own pages state for its text"),
    ("license_url", "url", "The page that states the license"),
    ("terms_url", "url", "Its terms of use or republishing page"),
    ("checked_on", "datetime", "When its pages were read"),
    ("quote_license", "string", "The exact words that grant the license"),
    ("quote_bulk", "string", "The exact words on bulk or automatic reuse, if any"),
    ("quote_attribution", "string", "The exact words on how to credit it"),
    ("quote_terms", "string", "The exact words of its terms on automated access, if any"),
    ("bulk_clause", "string", "Whether its pages allow, forbid or are silent on bulk reuse"),
    ("robots", "string", "What its robots.txt allows the CommonsWire client"),
    ("terms_automation", "string", "Whether its terms allow, forbid or are silent on automation"),
    ("tracking_required", "string", "Whether republishing requires a tracking pixel"),
    ("third_party_rule", "string", "How its own articles are told apart from republished ones"),
    ("access", "string", "The route used: api, feed, dump, sitemap or listing"),
    ("est_articles_per_day", "decimal", "About how many articles it publishes a day"),
    ("archive_from", "string", "Where its archive starts"),
    ("credit_line", "string", "The credit line template filled in for every row"),
    ("status", "string", "include, pending or exclude"),
    ("reason_code", "string", "Why it has its status, as one code from a fixed list"),
    ("reason", "string", "Why, for pending and exclude"),
    ("notes", "string", "Other notes from the review"),
)


def card_body(card: str) -> str:
    """The card without its Hugging Face metadata block."""
    return _FRONT.sub("", card, count=1)


def _flat_name(path: str) -> str:
    """data/by/train-00000-of-00001.parquet -> commonswire-by.parquet (several shards keep
    their number)."""
    m = re.match(r"^data/([^/]+)/train-(\d+)-of-(\d+)\.parquet$", path)
    if not m:
        return path.replace("/", "-")
    config, i, n = m.groups()
    return f"commonswire-{config}.parquet" if n == "00001" else f"commonswire-{config}-{i}.parquet"


def _clean(folder: Path, expected: set[str], overwrite: bool = False) -> None:
    """An empty folder, or with ``overwrite`` a folder that holds only files this pack writes
    (so a file a newer pack leaves out cannot linger in it)."""
    folder.mkdir(parents=True, exist_ok=True)
    present = {p.name for p in folder.iterdir()}
    if present and not overwrite:
        raise FileExistsError(
            f"{folder} is not empty ({len(present)} files); give --overwrite to rewrite the "
            "files in place, or prepare into a new folder"
        )
    stale = sorted(present - expected)
    if stale:
        raise FileExistsError(
            f"{folder} holds files this pack does not write ({', '.join(stale)}); move them "
            "away first, so they are not deposited by mistake"
        )


def _fields(columns: tuple[tuple[str, str, str], ...]) -> list[dict[str, str]]:
    return [{"name": n, "type": t, "description": d} for n, t, d in columns]


def _describe(path: str) -> str:
    m = re.match(r"^data/([^/]+)/", path)
    if m:
        return {
            "by": "Articles under CC BY (2.5, 3.0 and 4.0), one row each, with license and credit",
            "by-sa": "Articles under CC BY-SA 4.0, one row each, with license and credit line",
            "pd": "Public-domain articles (Wikinews before 2005-09-25), one row each",
        }.get(m.group(1), "Articles, one row each")
    return {
        "index.csv": "Every row's id, source, configuration, URL, license and hash, without text",
        "sources.csv": "The source registry: every source checked, its evidence and its status",
        "LICENSES.md": "The licenses in this version and what users must do",
        "README.md": "The dataset card",
        "manifest.json": "Row counts and the size and SHA-256 of every file",
    }.get(path, path)


def _schema(path: str, release: Path | None = None) -> tuple[tuple[str, str, str], ...] | None:
    """The columns of a release file, in order. A Parquet file's are read from the file, so
    a version lists exactly the columns it has (0.1.x has no ``translators``)."""
    if path.endswith(".parquet"):
        if release is None:
            return ROW_COLUMNS
        import pyarrow.parquet as pq

        have = pq.read_schema(release / path).names
        by_name = {c[0]: c for c in ROW_COLUMNS}
        return tuple(by_name[n] for n in have)
    if path == "sources.csv" and release is not None:
        # Versions 0.1.x and 0.2.x ship the registry without reason_code: list what is there.
        with (release / path).open(newline="", encoding="utf-8") as fh:
            have = next(csv.reader(fh))
        by_name = {c[0]: c for c in SOURCE_COLUMNS}
        return tuple(by_name[n] for n in have)
    return {"index.csv": INDEX_COLUMNS, "sources.csv": SOURCE_COLUMNS}.get(path)


def provenance(manifest: dict) -> str:
    """Kaggle's ``userSpecifiedSources``: where the rows come from and how (Markdown)."""
    return (
        "Each article comes from its publisher's own site, collected with the publisher's API "
        "(or, for English Wikinews, the Wikimedia dump), one request at a time, at least 2 "
        "seconds apart, with robots.txt and crawl-delays honored. A source enters only when "
        "its own pages give a license or public-domain statement that allows sharing the full "
        "text unchanged; the pages read, the date and the exact words are in `sources.csv`. "
        "Third-party material is left out, and the text is unchanged apart from whitespace. "
        f"Sources in version {manifest['version']}: " + ", ".join(manifest["sources"]) + ". "
        f"Code and method: {REPO}. The same files, with a dataset viewer: {HF_URL}."
    )


def _png(width: int, height: int, pixels: bytes) -> bytes:
    """A PNG file of 8-bit RGB pixels (rows of ``width * 3`` bytes), with the standard library."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    stride = width * 3
    raw = b"".join(b"\x00" + pixels[y * stride : (y + 1) * stride] for y in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def cover_image(rows_by_configuration: dict[str, int], size: tuple[int, int] = COVER_SIZE) -> bytes:
    """A plain cover: three horizontal bars on a dark ground, one per configuration (by,
    by-sa, pd), each as long as its share of the rows, at least a sliver. No text, no logo."""
    width, height = size
    ground = bytes((0x1F, 0x29, 0x37))
    colors = [bytes((0x5B, 0x9B, 0xD5)), bytes((0x70, 0xAD, 0x47)), bytes((0xED, 0xB1, 0x20))]
    counts = [rows_by_configuration.get(c, 0) for c in ("by", "by-sa", "pd")]
    total = max(sum(counts), 1)
    margin, gap = width // 10, height // 14
    bar_h = (height - 2 * margin - 2 * gap) // 3
    usable = width - 2 * margin
    lengths = [max(usable // 40, usable * n // total) if n else 0 for n in counts]
    rows = []
    for y in range(height):
        line = bytearray(ground * width)
        for i, length in enumerate(lengths):
            top = margin + i * (bar_h + gap)
            if top <= y < top + bar_h and length:
                line[margin * 3 : (margin + length) * 3] = colors[i] * length
        rows.append(bytes(line))
    return _png(width, height, b"".join(rows))


def kaggle_folder(release: Path, folder: Path, *, overwrite: bool = False) -> Path:
    """Copy a release's files into ``folder`` under flat names, with dataset-metadata.json and
    the cover image."""
    manifest = json.loads((release / "manifest.json").read_text())
    entries = [*manifest["files"], {"path": "manifest.json"}]
    names = {_flat_name(f["path"]) for f in entries}
    _clean(folder, names | {"dataset-metadata.json", KAGGLE_COVER}, overwrite)
    resources = []
    for f in entries:
        name = _flat_name(f["path"])
        shutil.copyfile(release / f["path"], folder / name)
        resource: dict[str, object] = {"path": name, "description": _describe(f["path"])}
        columns = _schema(f["path"], release)
        if columns:
            resource["schema"] = {"fields": _fields(columns)}
        resources.append(resource)
    meta = {
        "title": KAGGLE_TITLE,
        "id": KAGGLE_ID,
        "subtitle": KAGGLE_SUBTITLE,
        "description": card_body((release / "README.md").read_text(encoding="utf-8")),
        "isPrivate": False,
        "licenses": [{"name": "other"}],
        "keywords": ["news", "nlp", "text"],
        "expectedUpdateFrequency": KAGGLE_UPDATE_FREQUENCY,
        "userSpecifiedSources": provenance(manifest),
        "resources": resources,
    }
    (folder / "dataset-metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (folder / KAGGLE_COVER).write_bytes(cover_image(manifest["rows_by_configuration"]))
    return folder


def zenodo_folder(
    release: Path,
    folder: Path,
    repo: Path,
    *,
    overwrite: bool = False,
    commit: str = "HEAD",
) -> Path:
    """The files and metadata of a Zenodo record with no article text and no article index.
    The code is a ``git archive`` of ``commit`` (the commit that built the version)."""
    manifest = json.loads((release / "manifest.json").read_text())
    version = manifest["version"]
    archive_name = f"commonswire-code-{version}.tar.gz"
    _clean(folder, set(ZENODO_FILES) | {archive_name, "zenodo-metadata.json"}, overwrite)
    for name in ZENODO_FILES:
        shutil.copyfile(release / name, folder / name)
    sha = ""
    try:
        sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "archive",
                "--format=tar.gz",
                f"--prefix=commonswire-{version}/",
                "-o",
                str(folder / archive_name),
                sha,
            ],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        sha = ""  # not a git checkout, or no such commit: the code archive is left out
    rows = manifest["rows"]
    description = (
        f"<p>CommonsWire {version}: the code that built this version, the source registry, the "
        "dataset card, the licenses and the manifest (row counts, and the size and SHA-256 of "
        "every file). <strong>This record holds no article text and no list of "
        f"articles.</strong> The {rows:,} articles are on Hugging Face "
        f'(<a href="{HF_URL}">{HF_URL}</a>), where an article can be removed on request, which '
        "a permanent record cannot do.</p>"
        "<p>Each article keeps its publisher's license (public domain, CC BY 2.5, 3.0 or 4.0, "
        "or CC BY-SA 4.0), recorded per row. The files in this record are CommonsWire's own "
        "work under the Apache License 2.0; the short quotes in sources.csv are the "
        "publishers' words, quoted as evidence of their terms.</p>"
    )
    related = [{"relation": "isSupplementTo", "identifier": HF_URL, "resource_type": "dataset"}]
    if sha:
        related.append(
            {
                "relation": "isSupplementTo",
                "identifier": f"{REPO}/tree/{sha}",
                "resource_type": "software",
            }
        )
    meta = {
        "metadata": {
            "upload_type": "dataset",
            "title": f"CommonsWire {version}: code, source registry and dataset card "
            "(no article text)",
            "creators": [CREATOR],
            "description": description,
            "access_right": "open",
            "license": "apache-2.0",
            "version": version,
            "keywords": KEYWORDS,
            "related_identifiers": related,
            "notes": f"Code commit: {sha or 'to be added at deposit'}. Made with the "
            "CommonsWire release build; nothing in this record is article text.",
        }
    }
    (folder / "zenodo-metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return folder


def _citation_fields(text: str) -> dict[str, str]:
    """The top-level title and license of a CITATION.cff, and its first author's names and
    affiliation (enough to compare with .zenodo.json; no YAML parser needed)."""
    out: dict[str, str] = {}
    in_authors = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = not line.startswith((" ", "-"))
        if top:
            in_authors = line.startswith("authors:")
        m = re.match(r"^(title|license):\s*\"?(.*?)\"?\s*$", line)
        if m and top:
            out[m.group(1)] = m.group(2)
        m = re.match(r"^\s*-?\s*(family-names|given-names|affiliation):\s*\"?(.*?)\"?\s*$", line)
        if m and in_authors:
            out.setdefault(m.group(1), m.group(2))
    return out


def check_zenodo_json(repo: Path) -> list[str]:
    """What is wrong with the repository's ``.zenodo.json`` for Zenodo's GitHub route (empty
    when nothing is): the fields Zenodo needs, in the forms its deposit metadata accepts, a
    title that says the record holds no article text, links to the dataset on Hugging Face and
    Kaggle, and the same title, license and creator as ``CITATION.cff``."""
    path = repo / ZENODO_JSON
    if not path.exists():
        return [f"{path} is missing; Zenodo would fall back to CITATION.cff and GitHub's data"]
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}, line {exc.lineno}: not valid JSON ({exc.msg})"]
    if not isinstance(meta, dict):
        return [f"{path}: the file must hold one JSON object"]
    problems = [
        f"{path}: {key} is missing or empty"
        for key in ("title", "upload_type", "description", "creators", "license", "keywords")
        if not meta.get(key)
    ]
    title = str(meta.get("title", ""))
    if "no article text" not in title:
        problems.append(f"{path}: the title must say that the record holds no article text")
    if meta.get("upload_type") and meta["upload_type"] not in ZENODO_UPLOAD_TYPES:
        problems.append(f"{path}: upload_type {meta['upload_type']!r} is not one Zenodo knows")
    for n, c in enumerate(meta.get("creators") or [], 1):
        if not isinstance(c, dict) or ", " not in str(c.get("name", "")):
            problems.append(f"{path}: creator {n} needs a name of the form 'Family, Given'")
    tags = {
        t.lower() for t in re.findall(r"</?\s*([A-Za-z][A-Za-z0-9]*)", meta.get("description", ""))
    }
    if tags - ZENODO_HTML:
        problems.append(
            f"{path}: the description uses HTML that Zenodo does not allow: "
            + ", ".join(sorted(tags - ZENODO_HTML))
        )
    links = set()
    for n, r in enumerate(meta.get("related_identifiers") or [], 1):
        if not isinstance(r, dict) or r.get("relation") not in ZENODO_RELATIONS:
            problems.append(f"{path}: related identifier {n} has a relation Zenodo does not know")
            continue
        if not str(r.get("identifier", "")).startswith("https://"):
            problems.append(f"{path}: related identifier {n} is not an https link")
        links.add(r.get("identifier"))
    for url, what in ((HF_URL, "the Hugging Face dataset"), (KAGGLE_URL, "the Kaggle mirror")):
        if url not in links:
            problems.append(f"{path}: no related identifier links {what} ({url})")
    cff_path = repo / "CITATION.cff"
    if cff_path.exists():
        cff = _citation_fields(cff_path.read_text(encoding="utf-8"))
        creator = (meta.get("creators") or [{}])[0]
        name = f"{cff.get('family-names', '')}, {cff.get('given-names', '')}"
        pairs = (
            ("title", cff.get("title", ""), title),
            ("license", cff.get("license", "").lower(), str(meta.get("license", "")).lower()),
            ("creator", name, creator.get("name", "") if isinstance(creator, dict) else ""),
            (
                "affiliation",
                cff.get("affiliation", ""),
                creator.get("affiliation", "") if isinstance(creator, dict) else "",
            ),
        )
        for field_name, want, got in pairs:
            if want != got:
                problems.append(
                    f"{path}: the {field_name} ({got!r}) differs from CITATION.cff ({want!r})"
                )
    return problems


def archive_names(repo: Path, commit: str = "HEAD") -> list[str]:
    """The files a ``git archive`` of ``commit`` holds (what a GitHub release would carry),
    under the prefix ``commonswire/``."""
    data = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", "--prefix=commonswire/", commit],
        check=True,
        capture_output=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        return [m.name for m in tar.getmembers() if m.isfile()]


def archive_problems(names: list[str]) -> list[str]:
    """What a release archive must not carry (the request log, collected data), and must."""
    problems = [f"{n} is in the archive" for n in names if NOT_IN_ARCHIVE.match(n)]
    if not any(n.endswith("/" + ZENODO_JSON) and n.count("/") == 1 for n in names):
        problems.append(f"{ZENODO_JSON} is not in the archive (commit it first)")
    return problems
