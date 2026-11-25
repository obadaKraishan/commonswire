"""The record of changes: one line per article and version where something happened.

``changes.csv`` (series 0.3 on) has the columns ``id``, ``source_id``, ``version``, ``change``
and ``date``. A change is one of:

- ``new``: the article entered the corpus in that version;
- ``changed``: its text differs from the version before (its source edited it);
- ``removed``: its source removed it (its page answers 404 or 410); the row is no longer
  released;
- ``taken_down``: it was left out on request (``data/takedowns.csv``);
- ``withdrawn``: an earlier version released it, and this version holds it back or leaves it
  out for a rights reason found since (series 0.3 on: a Wikinews page whose own notice differs
  from its date's license); the reason is counted in the manifest's held rows.

``date`` is when CommonsWire saw it: the row's ``retrieved_at`` for new and changed rows, the
version's own date (its ``as_of``) for removals, takedowns and withdrawals. The table holds
ids and dates only, never an address, a title or a name.

:func:`history` derives the table from published versions alone (their Parquet files and
manifests), oldest first. When a version is missing between two of them, the later version's
rows are split by their ``retrieved_at``: the ones it retrieved itself (at its ``as_of``) are
its own, and the others are the missing version's, named by the later version's
``update.from_version``. Only one missing version can be split that way. Removed and
taken-down rows have no ids in the release files, so :func:`history` checks that the
manifests count none, and fails otherwise.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from pathlib import Path

CHANGE_FIELDS = ("id", "source_id", "version", "change", "date")
CHANGES_FILE = "changes.csv"
KINDS = ("new", "changed", "removed", "taken_down", "withdrawn")


def _iso(value: object) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")  # type: ignore[union-attr]
    return str(value or "")


def version_rows(folder: Path) -> tuple[dict, dict[str, dict]]:
    """A version's manifest and, per id, its source, text hash and retrieval time."""
    import pyarrow.parquet as pq

    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows: dict[str, dict] = {}
    for names in manifest["configurations"].values():
        for name in names:
            t = pq.read_table(
                folder / name, columns=["id", "source_id", "content_hash", "retrieved_at"]
            )
            for r in t.to_pylist():
                rows[r["id"]] = {
                    "source_id": r["source_id"],
                    "content_hash": r["content_hash"],
                    "retrieved_at": _iso(r["retrieved_at"]),
                }
    return manifest, rows


def _none_removed(manifest: dict) -> None:
    for key in ("removed_rows_not_released", "taken_down_rows_not_released"):
        if sum((manifest.get(key) or {}).values()):
            raise ValueError(
                f"version {manifest['version']} counts rows in {key}, whose ids its files do not "
                "hold: the record of changes needs them"
            )


def history(folders: Iterable[Path]) -> list[dict[str, str]]:
    """The record of changes of published versions, oldest first (see the module)."""
    out: list[dict[str, str]] = []
    prev: dict[str, dict] | None = None
    prev_version = ""
    for folder in folders:
        _none_removed(json.loads((folder / "manifest.json").read_text(encoding="utf-8")))
        manifest, rows = version_rows(folder)
        version = manifest["version"]
        update = manifest.get("update") or {}
        gap = bool(update) and update.get("from_version") not in ("", prev_version)
        if gap and prev is None:
            raise ValueError(f"version {version} is not the first: give the versions before it")
        as_of = str(manifest.get("as_of", ""))
        for rid in sorted(rows):
            r = rows[rid]
            if prev is not None and rid in prev:
                if prev[rid]["content_hash"] == r["content_hash"]:
                    continue
                change = "changed"
            else:
                change = "new"
            when = r["retrieved_at"]
            name = version
            if gap and when < as_of:
                name = str(update["from_version"])  # the missing version in between
            out.append(
                {
                    "id": rid,
                    "source_id": r["source_id"],
                    "version": name,
                    "change": change,
                    "date": when,
                }
            )
        prev, prev_version = rows, version
    return sorted(out, key=_order)


def _order(row: dict[str, str]) -> tuple:
    major, minor, patch = (int(x) for x in row["version"].split("."))
    return (major, minor, patch, row["date"], row["id"])


def entries(
    version: str,
    rows: dict[str, dict],
    *,
    new: Iterable[str] = (),
    changed: Iterable[str] = (),
    removed: Iterable[str] = (),
    taken_down: Iterable[str] = (),
    withdrawn: Iterable[str] = (),
    as_of: str = "",
) -> list[dict[str, str]]:
    """The lines a new version adds: ``rows`` maps an id to its stored row (source and
    retrieval time)."""
    out = []
    for kind, ids in (
        ("new", new),
        ("changed", changed),
        ("removed", removed),
        ("taken_down", taken_down),
        ("withdrawn", withdrawn),
    ):
        for rid in sorted(set(ids)):
            d = rows.get(rid, {})
            when = _iso(d.get("retrieved_at")) if kind in ("new", "changed") else as_of
            out.append(
                {
                    "id": rid,
                    "source_id": str(d.get("source_id", "")),
                    "version": version,
                    "change": kind,
                    "date": when or as_of,
                }
            )
    return out


def to_csv(rows: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CHANGE_FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(sorted(rows, key=_order))
    return buf.getvalue().encode("utf-8")


def read_changes(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != CHANGE_FIELDS:
            raise ValueError(f"{path}: the header must be {', '.join(CHANGE_FIELDS)}")
        rows = list(reader)
    for line, r in enumerate(rows, start=2):
        if r["change"] not in KINDS:
            raise ValueError(f"{path}, line {line}: change must be one of {', '.join(KINDS)}")
    return rows


def counts(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Lines by version and kind."""
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["version"], {}).setdefault(r["change"], 0)
        out[r["version"]][r["change"]] += 1
    return {
        v: dict(sorted(k.items()))
        for v, k in sorted(
            out.items(), key=lambda x: _order({"version": x[0], "date": "", "id": ""})
        )
    }
