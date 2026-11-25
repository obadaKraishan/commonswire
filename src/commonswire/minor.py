"""A version of a new series, built from the latest published version plus new sources.

``commonswire update`` stops on a new source, by design: a new series (0.3.0 after 0.2.N)
needs the maintainer. :func:`build_from_previous` is that step. It takes:

- every released row of the sources the previous version has, from the previous version
  itself (so whatever the weekly updates added is kept), with the held rows' ids, the
  third-party count and the post counts carried from its manifest;
- the rows of each new source of the series from ``data/interim/rows/<source>.jsonl`` (built
  from raw pages, no requests), with their held rows and third-party drops;
- for a source the previous version has, the holds for a rights reason that its rows, as
  rebuilt from raw answers with today's rules, carry (:data:`RIGHTS_HOLDS`: series 0.3 holds
  English Wikinews pages whose own notice differs from their date's license); a published
  row held this way is recorded as ``withdrawn`` in ``changes.csv``;
- for a new source read from its pages, the weekly route's state (``page_state``: the newest
  change date of its saved sitemaps, or the ids of its first listing pages) from the saved
  backfill run its build summary names, so the first weekly update reads only what came
  after the backfill.

The version is built through ``release build``'s own checks (:func:`commonswire.release.collect`:
every row validated, credit lines checked, exact and near duplicates across all sources) and
checked again on disk with :func:`commonswire.release.verify`. It sends no request.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from commonswire.changes import CHANGES_FILE, entries, read_changes
from commonswire.changes import to_csv as changes_csv
from commonswire.http import FetchError
from commonswire.release import (
    VARIABLE_COLUMNS,
    Release,
    ReleaseError,
    _read_jsonl,
    collect,
    columns,
    series_sources,
    verify,
    write_release,
)
from commonswire.release_text import card, licenses_md
from commonswire.sources import Source
from commonswire.update import carried_state, read_version

#: The hold reasons (their first words) that a new series carries onto rows an earlier
#: version released: rights reasons found since, never a byline or a date question.
RIGHTS_HOLDS = ("own notice differs",)


def join_rights_holds(prev: dict[str, dict], path: Path) -> list[str]:
    """Hold the published rows (in place) that the rows rebuilt in ``path`` hold for a rights
    reason (:data:`RIGHTS_HOLDS`); return their ids."""
    if not path.exists():
        return []
    out = []
    for d in _read_jsonl(path):
        row = prev.get(d["id"])
        reason = str(d.get("hold_reason") or "")
        if row is None or d.get("releasable", True) or not reason.startswith(RIGHTS_HOLDS):
            continue
        row["releasable"] = False
        row["hold_reason"] = reason
        out.append(d["id"])
    return sorted(out)


def third_party_of(root: Path, source_id: str) -> int:
    """The third-party pages a source's last build dropped (its build summary)."""
    path = root / "data" / "evidence" / "backfill" / f"{source_id}.build.json"
    if not path.exists():
        return 0
    dropped = json.loads(path.read_text(encoding="utf-8")).get("dropped", {})
    return sum(int(n) for k, n in dropped.items() if k.startswith("third_party:"))


def page_states(root: Path, sources: list[str], previous: dict | None) -> dict[str, dict]:
    """The weekly route's state of each page source: carried from the previous version, or
    for a new one read from the backfill run its build summary names (no request)."""
    from commonswire.pagebackfill import PAGE_ROUTES
    from commonswire.pageupdate import page_state_from_backfill

    out: dict[str, dict] = {}
    for sid in sources:
        if sid not in PAGE_ROUTES:
            continue
        if previous and sid in previous:
            out[sid] = previous[sid]
            continue
        summary = root / "data" / "evidence" / "backfill" / f"{sid}.build.json"
        if not summary.exists():
            raise ReleaseError(f"{summary} is missing: build {sid}'s rows first")
        run = json.loads(summary.read_text(encoding="utf-8")).get("run")
        if not run:
            raise ReleaseError(f"{summary} names no backfill run: build {sid}'s rows again")
        try:
            out[sid] = page_state_from_backfill(sid, root / "data" / "raw" / "backfill" / sid / run)
        except FetchError as exc:
            raise ReleaseError(f"{sid}: {exc}") from exc
    return out


def build_from_previous(
    root: Path,
    prev_dir: Path,
    version: str,
    out: Path,
    *,
    registry_path: Path,
    registry: dict[str, Source],
    takedowns_path: Path,
    baseline_path: Path,
    note: str = "",
    changes: Path | None = None,
) -> tuple[dict[str, object], list[str]]:
    """Write version ``version`` to ``out``; return its manifest and the problems found."""
    if out.exists() and any(out.iterdir()):
        raise ReleaseError(f"{out} is not empty: a version is never overwritten")
    manifest = json.loads((prev_dir / "manifest.json").read_text(encoding="utf-8"))
    problems = verify(prev_dir, ignore_hidden=True)
    if problems:
        raise ReleaseError(f"the previous version fails its own check: {problems[0]}")
    state = carried_state(manifest, prev_dir, baseline_path)
    if state is None:
        raise ReleaseError(f"version {manifest['version']} carries no list of held rows")
    held_prev, third_prev = state
    sources = series_sources(version)
    old = [s for s in manifest["sources"] if s in sources]
    gone = [s for s in manifest["sources"] if s not in sources]
    if gone:
        raise ReleaseError(
            f"version {version} leaves out {', '.join(gone)}: a source is never dropped"
        )
    new = [s for s in sources if s not in manifest["sources"]]
    _, prev_rows = read_version(prev_dir)
    rows_dir = root / "data" / "interim" / "rows"
    missing = [s for s in new if not (rows_dir / f"{s}.jsonl").exists()]
    if missing:
        raise ReleaseError(f"no rows for {', '.join(missing)} in {rows_dir}; build them first")
    joined: dict[str, int] = {}
    if "n_links" in columns(version):
        # The variables that need no model, for the published rows: from each source's rows
        # as rebuilt from its saved answers (a row that has no saved answer keeps none).
        for s in old:
            joined[s] = join_variables(prev_rows.get(s, {}), rows_dir / f"{s}.jsonl")
    withdrawn: dict[str, list[str]] = {}
    for s in old:
        ids = join_rights_holds(prev_rows.get(s, {}), rows_dir / f"{s}.jsonl")
        if ids:
            withdrawn[s] = ids
    rows = {s: list(prev_rows.get(s, {}).values()) for s in old}
    rows.update({s: list(_read_jsonl(rows_dir / f"{s}.jsonl")) for s in new})
    rel = collect(root, version, registry, rows=rows, takedowns_path=takedowns_path)
    if not rel.checks.ok:
        raise ReleaseError("the checks failed: " + "; ".join(rel.checks.problems()))
    held = {k: v for k, v in held_prev.items() if k not in rel.checks.held_ids}
    held.update(rel.checks.held_ids)
    rel.checks.held = Counter(v["source_id"] for v in held.values())
    rel.checks.held_reasons = Counter(v["reason"] for v in held.values())
    rel.checks.held_pairs = Counter((v["source_id"], v["reason"]) for v in held.values())
    for key in ("exact_duplicates", "removed", "taken_down"):
        field = {
            "exact_duplicates": "exact_duplicates_dropped",
            "removed": "removed_rows_not_released",
            "taken_down": "taken_down_rows_not_released",
        }[key]
        setattr(rel.checks, key, Counter(manifest.get(field, {})) + getattr(rel.checks, key))
    # Copies of another source's rows (series 0.3 on) are third-party material too.
    third = third_prev + sum(third_party_of(root, s) for s in new) + len(rel.checks.copy_ids)
    rel.checks.copies = Counter(manifest.get("copies_left_out", {})) + rel.checks.copies
    pages = page_states(root, list(sources), manifest.get("page_state"))
    extra: dict[str, object] = {
        # The version of the series before that this series was built from (its card says
        # what changed since; every later version of the series carries it).
        "series_from": manifest["version"],
        "third_party_dropped": third,
        "held_rows": [{"id": k, **v} for k, v in sorted(held.items())],
        "post_counts": {s: c for s, c in (manifest.get("post_counts") or {}).items() if s in old},
        **({"page_state": pages} if pages else {}),
        "built_from": {
            "from_version": manifest["version"],
            "new_sources": new,
            "rows_from_previous": sum(len(v) for k, v in rows.items() if k in old),
            "rows_of_new_sources": sum(len(v) for k, v in rows.items() if k in new),
        },
    }
    if note:
        extra["not_a_release"] = note
    extra_files: dict[str, bytes] = {}
    if joined:
        extra["built_from"]["variables_joined"] = dict(sorted(joined.items()))  # type: ignore[index]
    if withdrawn:
        extra["built_from"]["withdrawn"] = {s: len(v) for s, v in sorted(withdrawn.items())}  # type: ignore[index]
    if changes is not None or (prev_dir / CHANGES_FILE).exists():
        lines = read_changes(changes if changes is not None else prev_dir / CHANGES_FILE)
        released = {
            r["id"]: r for config in rel.rows.values() for r in config if r["source_id"] in new
        }
        gone = sorted(i for ids in withdrawn.values() for i in ids)
        before = {rid: d for rows_ in prev_rows.values() for rid, d in rows_.items()}
        lines += entries(version, released, new=released)
        lines += entries(
            version, {rid: before[rid] for rid in gone}, withdrawn=gone, as_of=_as_of(rel)
        )
        extra_files[CHANGES_FILE] = changes_csv(lines)
    out_manifest = write_release(
        rel,
        out,
        registry_path,
        registry,
        card=card(rel, registry, third, series_from=manifest["version"]),
        licenses_md=licenses_md(rel, registry),
        extra=extra,
        extra_files=extra_files or None,
    )
    return out_manifest, verify(out)


def _as_of(rel: Release) -> str:
    """A version's own date (the latest retrieval among its rows), as changes.csv writes it."""
    times = [r["retrieved_at"] for config in rel.rows.values() for r in config]
    return max(times).strftime("%Y-%m-%dT%H:%M:%SZ") if times else ""


def join_variables(prev: dict[str, dict], path: Path) -> int:
    """Add the variables of the rows rebuilt in ``path`` to the published rows with the same
    id (in place); return how many rows got them."""
    if not path.exists():
        return 0
    n = 0
    for d in _read_jsonl(path):
        row = prev.get(d["id"])
        if row is None:
            continue
        for col in VARIABLE_COLUMNS:
            if col in d:
                row[col] = d[col]
        n += 1
    return n
