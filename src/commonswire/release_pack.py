"""Folders for the Kaggle mirror and a Zenodo record of a release. Nothing is uploaded here.

- **Kaggle** (``data/release/<version>-kaggle/``): the release's files under flat names, and
  ``dataset-metadata.json``. Kaggle takes exactly one license per dataset and its list has no
  entry for mixed licenses, CC BY 2.5 or the Public Domain Mark, so the license is ``other`` and
  the description says that every row carries its own license (``LICENSES.md``). The dataset id
  is left as ``KAGGLE_USERNAME/commonswire``; the publish step fills in the account.
- **Zenodo** (``data/release/<version>-zenodo/``): **no article text.** A Zenodo record cannot
  be withdrawn, which does not fit the promise to remove an article on request. The record
  holds the code (a ``git archive`` of the commit), the source registry, the dataset card,
  ``LICENSES.md``, the manifest, and ``index.csv`` (ids, URLs, content hashes and licenses),
  with ``zenodo-metadata.json`` for the deposit.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from commonswire.release_text import HF_URL, REPO

KAGGLE_ID = "KAGGLE_USERNAME/commonswire"
KAGGLE_TITLE = "CommonsWire: openly licensed news text"
KAGGLE_SUBTITLE = "Full-text news articles their publishers allow to share, each with its license"
CREATOR = {"name": "Kraishan, Obada", "affiliation": "Texas Tech University"}
KEYWORDS = ["news", "journalism", "corpus", "creative commons", "communication research"]
_FRONT = re.compile(r"\A---\n.*?\n---\n+", re.S)


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


def _clean(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    stale = [p.name for p in folder.iterdir()]
    if stale:
        raise FileExistsError(
            f"{folder} is not empty ({len(stale)} files); prepare into a new, empty folder"
        )


def kaggle_folder(release: Path, folder: Path) -> Path:
    """Copy a release's files into ``folder`` under flat names, with dataset-metadata.json."""
    manifest = json.loads((release / "manifest.json").read_text())
    _clean(folder)
    resources = []
    for f in [*manifest["files"], {"path": "manifest.json"}]:
        name = _flat_name(f["path"])
        shutil.copyfile(release / f["path"], folder / name)
        resources.append({"path": name, "description": _describe(f["path"])})
    meta = {
        "title": KAGGLE_TITLE,
        "id": KAGGLE_ID,
        "subtitle": KAGGLE_SUBTITLE,
        "description": card_body((release / "README.md").read_text(encoding="utf-8")),
        "licenses": [{"name": "other"}],
        "keywords": ["news", "nlp", "text"],
        "resources": resources,
    }
    (folder / "dataset-metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return folder


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


def zenodo_folder(release: Path, folder: Path, repo: Path) -> Path:
    """The files and metadata of a Zenodo record with no article text."""
    manifest = json.loads((release / "manifest.json").read_text())
    version = manifest["version"]
    _clean(folder)
    for name in ("sources.csv", "index.csv", "README.md", "LICENSES.md", "manifest.json"):
        shutil.copyfile(release / name, folder / name)
    commit = ""
    archive = folder / f"commonswire-code-{version}.tar.gz"
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
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
                str(archive),
                commit,
            ],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        commit = ""  # not a git checkout: the code archive is left for the deposit step
    rows = manifest["rows"]
    description = (
        f"<p>CommonsWire {version}: the code, the source registry, the dataset card and an "
        f"index of the {rows:,} articles of this version (ids, URLs, content hashes and "
        "licenses). <strong>This record holds no article text.</strong> The articles "
        f'themselves are on Hugging Face (<a href="{HF_URL}">{HF_URL}</a>), where an article '
        "can be removed on request, which a permanent record cannot do.</p>"
        "<p>Each article keeps its publisher's license (public domain, CC BY 2.5, 3.0 or 4.0, "
        "or CC BY-SA 4.0), recorded per row. The files in this record are CommonsWire's own "
        "work under the Apache License 2.0; the short quotes in sources.csv are the "
        "publishers' words, quoted as evidence of their terms.</p>"
    )
    meta = {
        "metadata": {
            "upload_type": "dataset",
            "title": f"CommonsWire {version}: code, source registry and article index "
            "(no article text)",
            "creators": [CREATOR],
            "description": description,
            "access_right": "open",
            "license": "apache-2.0",
            "version": version,
            "keywords": KEYWORDS,
            "related_identifiers": [
                {"relation": "isSupplementTo", "identifier": HF_URL, "resource_type": "dataset"},
                {"relation": "isDerivedFrom", "identifier": REPO, "resource_type": "software"},
            ],
            "notes": f"Code commit: {commit or 'to be added at deposit'}. Made with the "
            "CommonsWire release build; nothing in this record is article text.",
        }
    }
    (folder / "zenodo-metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return folder
