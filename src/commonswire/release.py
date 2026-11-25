"""The release build: one dataset version, written from the built rows with no request.

``commonswire release build --version 0.1.0`` writes ``data/release/<version>/``:

- ``data/<configuration>/train-NNNNN-of-NNNNN.parquet``: one configuration per license class
  (``pd``, ``by``, ``by-sa``), releasable rows only, sorted by publication time and id;
- ``index.csv``: one line per released row (id, source, configuration, URL, license, content
  hash, publication time), with no text;
- ``sources.csv``: the source registry as it is (every source, its evidence and its status);
- ``LICENSES.md`` and ``README.md`` (the dataset card);
- ``manifest.json``: row counts, and the size and SHA-256 of every other file.

Each version series has a fixed list of sources (:data:`SERIES`), so a source collected later
does not slip into an older series. Inside that list, exact duplicates are dropped and
near-duplicates flagged by the same rules as ``commonswire dedup``, computed here from the rows
alone, so the files depend only on the rows and the registry: the same input gives the same
bytes. Before anything is written, every row is checked: it validates against the schema, it is
releasable and not third-party, it is not a removed row, and its credit line is exactly the
source's template filled in for it. Articles on the takedown list (``data/takedowns.csv``:
the article id, the date of the request and its basis, never a URL or a name) are left out of
every version built after the request, and counted.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from commonswire.dedup import Row, exact_duplicates, near_duplicates
from commonswire.licensing import CLASS_NC_ND, license_class, license_url
from commonswire.schema import Article
from commonswire.sources import Source, license_label, render_credit

#: The sources of each version series, (major, minor) -> source ids.
SERIES: dict[tuple[int, int], tuple[str, ...]] = {
    (0, 1): ("wikinews_en", "360info", "thepublicrecord", "balkandiskurs", "factly", "altnews"),
    (0, 2): (
        "wikinews_en",
        "360info",
        "thepublicrecord",
        "balkandiskurs",
        "factly",
        "altnews",
        "globalvoices",
    ),
    # Series 0.3 adds the publishers read from their article pages (rights audit of
    # 2026-11-16): SciDev.Net and Africa Is a Country.
    (0, 3): (
        "wikinews_en",
        "360info",
        "thepublicrecord",
        "balkandiskurs",
        "factly",
        "altnews",
        "globalvoices",
        "scidevnet",
        "africasacountry",
        # The language editions collected in 2026-11 (the rights audit's answers of
        # 2026-11-23): Balkan Diskurs in Bosnian, 46 Global Voices language sites under the
        # Lingua rule (Spanish waits), and six Wikinews editions with their license-by-date
        # tables (Russian and Swedish wait).
        "balkandiskurs_bs",
        "globalvoices_ar",
        "globalvoices_aym",
        "globalvoices_bg",
        "globalvoices_bn",
        "globalvoices_ca",
        "globalvoices_cs",
        "globalvoices_da",
        "globalvoices_de",
        "globalvoices_el",
        "globalvoices_eo",
        "globalvoices_fa",
        "globalvoices_fil",
        "globalvoices_fr",
        "globalvoices_he",
        "globalvoices_hi",
        "globalvoices_hr",
        "globalvoices_hu",
        "globalvoices_id",
        "globalvoices_it",
        "globalvoices_jp",
        "globalvoices_kk",
        "globalvoices_km",
        "globalvoices_ko",
        "globalvoices_ku",
        "globalvoices_mg",
        "globalvoices_mk",
        "globalvoices_my",
        "globalvoices_ne",
        "globalvoices_nl",
        "globalvoices_or",
        "globalvoices_pa",
        "globalvoices_pl",
        "globalvoices_pt",
        "globalvoices_ro",
        "globalvoices_ru",
        "globalvoices_sq",
        "globalvoices_sr",
        "globalvoices_sv",
        "globalvoices_sw",
        "globalvoices_tet",
        "globalvoices_tr",
        "globalvoices_uk",
        "globalvoices_ur",
        "globalvoices_uz",
        "globalvoices_zhs",
        "globalvoices_zht",
        "wikinews_ar",
        "wikinews_el",
        "wikinews_fr",
        "wikinews_ko",
        "wikinews_ro",
        "wikinews_zh",
    ),
}
#: The first series whose rows carry ``translators`` (after ``authors``); older series keep
#: the columns they were published with.
TRANSLATORS_FROM = (0, 2)
#: The order configurations are listed in; ``by`` is the default.
CONFIGURATIONS = ("by", "by-sa", "pd")
NEAR_DUPLICATE_THRESHOLD = 0.6
ROWS_PER_SHARD = 50_000
ROW_GROUP = 2_000
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_ID = re.compile(r"^cw_[0-9a-f]{16}$")
TAKEDOWN_FIELDS = ("id", "requested_on", "basis")


def load_takedowns(path: Path) -> set[str]:
    """The article ids on the takedown list; a malformed line is an error, never skipped."""
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != TAKEDOWN_FIELDS:
            raise ReleaseError(f"{path}: the header must be {','.join(TAKEDOWN_FIELDS)}")
        for n, line in enumerate(reader, start=2):
            rid = (line.get("id") or "").strip()
            if not _ID.match(rid):
                raise ReleaseError(
                    f"{path}, line {n}: {rid!r} is not an article id (cw_ and 16 hex digits); "
                    "give the id, never the URL"
                )
            ids.add(rid)
    return ids


#: The released columns, in order.
COLUMNS = (
    "id",
    "source_id",
    "kind",
    "title",
    "authors",
    "published_at",
    "updated_at",
    "retrieved_at",
    "language",
    "section",
    "url",
    "license",
    "license_url",
    "credit_line",
    "text",
    "content_hash",
    "status",
    "near_duplicates",
)


class ReleaseError(ValueError):
    """The release cannot be built as asked; the message says what to fix."""


def _series(version: str) -> tuple[int, int]:
    m = _VERSION.match(version)
    if not m:
        raise ReleaseError(f"version {version!r} is not of the form 0.1.0")
    return int(m.group(1)), int(m.group(2))


#: The variables that need no model (``commonswire.variables``), released from series 0.3.
VARIABLE_COLUMNS = (
    "publisher_section",
    "publisher_categories",
    "publisher_tags",
    "n_links",
    "n_links_external",
    "link_hosts",
    "original_url",
    "other_versions",
)
VARIABLES_FROM = (0, 3)
#: The variables released as lists.
LIST_VARIABLES = frozenset(
    {"publisher_categories", "publisher_tags", "link_hosts", "other_versions"}
)


def columns(version: str) -> tuple[str, ...]:
    """The released columns of a version, in order: series 0.2 and later add ``translators``
    after ``authors``; series 0.3 and later add the variables that need no model at the end;
    series 0.1 keeps the 18 columns version 0.1.0 was published with."""
    if _series(version) < TRANSLATORS_FROM:
        return COLUMNS
    i = COLUMNS.index("authors") + 1
    cols = (*COLUMNS[:i], "translators", *COLUMNS[i:])
    if _series(version) >= VARIABLES_FROM:
        cols = (*cols, *VARIABLE_COLUMNS)
    return cols


def series_sources(version: str) -> tuple[str, ...]:
    """The sources of a version: ``0.1.0`` and ``0.1.7`` share the list of series 0.1."""
    key = _series(version)
    if key not in SERIES:
        known = ", ".join(f"{a}.{b}.x" for a, b in SERIES)
        raise ReleaseError(
            f"version {version} belongs to series {key[0]}.{key[1]}, which has no source list; "
            f"known series: {known}. Add its sources to SERIES in release.py first."
        )
    return SERIES[key]


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class Checks:
    """What the checks before writing found (all must be zero but ``held`` and ``removed``)."""

    rows_in: int = 0
    exact_duplicates: Counter[str] = field(default_factory=Counter)
    held: Counter[str] = field(default_factory=Counter)
    #: Held rows by the first words of their hold reason ("no byline", "credited to an
    #: account, not a person").
    held_reasons: Counter[str] = field(default_factory=Counter)
    removed: Counter[str] = field(default_factory=Counter)
    taken_down: Counter[str] = field(default_factory=Counter)
    invalid: list[str] = field(default_factory=list)
    credit_mismatch: list[str] = field(default_factory=list)
    third_party: list[str] = field(default_factory=list)
    unreleasable_class: list[str] = field(default_factory=list)
    #: Ids only (no text, no address): the held rows with their source, day and reason, and
    #: the rows dropped as exact duplicates, removed or taken down.
    held_ids: dict[str, dict[str, str]] = field(default_factory=dict)
    duplicate_ids: list[str] = field(default_factory=list)
    removed_ids: list[str] = field(default_factory=list)
    taken_down_ids: list[str] = field(default_factory=list)
    #: Series 0.3 on: rows left out as copies of another source's rows (third-party), by
    #: source, and their ids (:data:`REPUBLISHED_COPIES`).
    copies: Counter[str] = field(default_factory=Counter)
    copy_ids: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.invalid or self.credit_mismatch or self.third_party or self.unreleasable_class
        )

    def problems(self) -> list[str]:
        out = []
        for name in ("invalid", "credit_mismatch", "third_party", "unreleasable_class"):
            items = getattr(self, name)
            if items:
                out.append(f"{len(items)} rows {name.replace('_', ' ')}: {', '.join(items[:5])}")
        return out


@dataclass
class Release:
    version: str
    sources: tuple[str, ...]
    rows: dict[str, list[dict]]  # configuration -> rows, in release order
    checks: Checks
    near_duplicate_pairs: int = 0

    def counts(self) -> dict[str, object]:
        by_source: dict[str, Counter[str]] = defaultdict(Counter)
        by_license: Counter[str] = Counter()
        for config, rows in self.rows.items():
            for r in rows:
                by_source[r["source_id"]][config] += 1
                by_license[r["license"]] += 1
        return {
            "rows": sum(len(v) for v in self.rows.values()),
            "rows_by_configuration": {c: len(self.rows[c]) for c in CONFIGURATIONS},
            "rows_by_source": {s: dict(sorted(by_source[s].items())) for s in self.sources},
            "rows_by_license": dict(sorted(by_license.items())),
        }


#: Series 0.3 on: a source that republished another's articles, and that other source. A row
#: of the first whose near-duplicate (at the release's threshold) is a row of the second, held
#: or released, is a copy: it is left out as third-party material and counted, and the other
#: row follows its own rules (Arabic Wikinews carried Global Voices' Arabic translations).
REPUBLISHED_COPIES: dict[str, str] = {"wikinews_ar": "globalvoices_ar"}
COPIES_FROM = (0, 3)


def copies_of(pairs: list, threshold: float) -> dict[str, str]:
    """The rows that are copies of another source's rows (:data:`REPUBLISHED_COPIES`): copy id
    -> its source id."""
    out: dict[str, str] = {}
    for a, b, sa, sb, j, _t in pairs:
        if j < threshold:
            continue
        if REPUBLISHED_COPIES.get(sa) == sb:
            out[a] = sa
        elif REPUBLISHED_COPIES.get(sb) == sa:
            out[b] = sb
    return out


def _flags(
    pairs: list, threshold: float, left_out: Iterable[str] = ()
) -> tuple[dict[str, list[str]], int]:
    """The near-duplicate flags across sources, and the pairs counted, without the rows left
    out."""
    gone = set(left_out)
    flags: dict[str, list[str]] = defaultdict(list)
    n = 0
    for a, b, sa, sb, j, _t in pairs:
        if sa != sb and j >= threshold and a not in gone and b not in gone:
            flags[a].append(b)
            flags[b].append(a)
            n += 1
    return {k: sorted(v) for k, v in flags.items()}, n


def _read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def collect(
    root: Path,
    version: str,
    registry: dict[str, Source],
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
    *,
    rows: Mapping[str, Iterable[dict]] | None = None,
    takedowns_path: Path | None = None,
) -> Release:
    """Read, deduplicate, check and group the rows of a version (nothing is written).

    The rows come from ``data/interim/rows/<source>.jsonl`` under ``root``, or from ``rows``
    (source id -> rows) when given, as ``commonswire update`` does; the takedown list from
    ``data/takedowns.csv`` under ``root``, or ``takedowns_path``."""
    sources = series_sources(version)
    takedowns = load_takedowns(takedowns_path or root / "data" / "takedowns.csv")
    rows_dir = root / "data" / "interim" / "rows"
    if rows is None:
        missing = [s for s in sources if not (rows_dir / f"{s}.jsonl").exists()]
        if missing:
            raise ReleaseError(
                f"no rows for {', '.join(missing)} in {rows_dir}; build them first "
                "(commonswire build SOURCE, or commonswire wikinews-dump)"
            )
        given: Mapping[str, Iterable[dict]] = {
            s: _read_jsonl(rows_dir / f"{s}.jsonl") for s in sources
        }
    else:
        missing = [s for s in sources if s not in rows]
        if missing:
            raise ReleaseError(f"no rows were given for {', '.join(missing)}")
        given = rows
    unknown = [s for s in sources if s not in registry]
    if unknown:
        raise ReleaseError(f"{', '.join(unknown)} not in the registry (data/sources.csv)")
    checks = Checks()
    with_translators = "translators" in columns(version)
    with_variables = "n_links" in columns(version)
    data: dict[str, dict] = {}
    by_id: dict[str, Row] = {}
    order = sorted(sources)
    for source in order:
        for d in given[source]:
            checks.rows_in += 1
            if d["source_id"] != source:
                checks.invalid.append(f"{d['id']} (source_id {d['source_id']!r})")
                continue
            if d["id"] in data:
                checks.exact_duplicates[f"same_url:{source}"] += 1
                continue
            data[d["id"]] = d
            if d.get("status") == "removed":
                # A removed row has no text, so it stays out of the duplicate checks: two rows
                # removed in one update share the hash of the empty text.
                if d["id"] in takedowns:
                    checks.taken_down[source] += 1
                    checks.taken_down_ids.append(d["id"])
                else:
                    checks.removed[source] += 1
                    checks.removed_ids.append(d["id"])
                continue
            by_id[d["id"]] = Row(
                id=d["id"],
                source_id=source,
                published_at=d["published_at"],
                content_hash=d["content_hash"],
                text=d["text"],
                title=d.get("title", ""),
            )
    exact = exact_duplicates(by_id.values(), order)
    checks.exact_duplicates.update(exact.dropped_by)
    checks.duplicate_ids = sorted(exact.dropped)
    pairs, _ = near_duplicates(by_id, exact.kept_ids)
    copies: dict[str, str] = {}
    if _series(version) >= COPIES_FROM:
        copies = {r: s for r, s in copies_of(pairs, threshold).items() if s in sources}
    checks.copies.update(copies.values())
    checks.copy_ids = sorted(copies)
    flags, n_pairs = _flags(pairs, threshold, copies)
    grouped: dict[str, list[dict]] = {c: [] for c in CONFIGURATIONS}

    def hold(rid: str, d: dict, why: str) -> None:
        reason = why.split(":", 1)[0]
        checks.held[d["source_id"]] += 1
        checks.held_reasons[reason] += 1
        checks.held_ids[rid] = {
            "source_id": d["source_id"],
            "published_on": d["published_at"][:10],
            "reason": reason,
        }

    # The Lingua rule (``commonswire.lingua``): an edition marked with its reason code is
    # released only where its English version is released, so its rows come last.
    from commonswire.lingua import (
        ENGLISH_NOT_RELEASED,
        ENGLISH_SOURCE,
        NO_ENGLISH,
        RULE_CODE,
        english_version,
    )
    from commonswire.schema import article_id

    ruled = {s for s in sources if registry[s].reason_code == RULE_CODE}
    if ruled and ENGLISH_SOURCE not in sources:
        raise ReleaseError(
            f"{', '.join(sorted(ruled))} are released only with their English versions, but "
            f"series {version} has no {ENGLISH_SOURCE}"
        )
    kept = [r for r in exact.kept_ids if data[r]["source_id"] not in ruled and r not in copies]
    kept += [r for r in exact.kept_ids if data[r]["source_id"] in ruled and r not in copies]
    english_released: set[str] | None = None
    for rid in kept:
        d = data[rid]
        src = registry[d["source_id"]]
        if rid in takedowns:
            checks.taken_down[d["source_id"]] += 1
            checks.taken_down_ids.append(rid)
            continue
        if d["source_id"] in ruled:
            # The rule comes first: a row it holds is counted under it, whatever else the
            # row lacks (its listing page may not have been read, by the plan).
            if english_released is None:
                english_released = {
                    r["id"]
                    for rows in grouped.values()
                    for r in rows
                    if r["source_id"] == ENGLISH_SOURCE
                }
            english = english_version(d.get("other_versions") or ())
            if not english:
                hold(rid, d, NO_ENGLISH)
                continue
            if article_id(english) not in english_released:
                hold(rid, d, ENGLISH_NOT_RELEASED)
                continue
        if not d.get("releasable", True):
            hold(rid, d, d.get("hold_reason") or "held")
            continue
        if d.get("third_party"):
            checks.third_party.append(rid)
            continue
        try:
            Article.model_validate(d)
        except ValueError as exc:
            checks.invalid.append(f"{rid} ({str(exc).splitlines()[0][:60]})")
            continue
        translators = list(d.get("translators") or [])
        if translators and not with_translators:
            checks.invalid.append(f"{rid} (names translators; series {version} has no column)")
            continue
        expected = render_credit(
            src.credit_line,
            title=d["title"],
            authors=d["authors"],
            source=src.name,
            url=d["url"],
            license=d["license"],
            translators=translators,
        )
        if d["credit_line"] != expected:
            checks.credit_mismatch.append(rid)
            continue
        config = license_class(d["license"])
        if config == CLASS_NC_ND or config not in grouped:
            checks.unreleasable_class.append(f"{rid} ({d['license']})")
            continue
        variables_out: dict[str, object] = {}
        out = {
            "id": rid,
            "source_id": d["source_id"],
            "kind": src.kind,
            "title": d["title"],
            "authors": list(d["authors"]),
        }
        if with_translators:
            out["translators"] = translators
        language = d["language"]
        if with_variables:
            from commonswire.variables import row_language

            language = row_language(d["source_id"], d.get("publisher_categories") or (), language)
            for col in VARIABLE_COLUMNS:
                value = d.get(col)
                if col in LIST_VARIABLES:
                    value = list(value or [])
                elif col in ("publisher_section", "original_url"):
                    value = value or ""
                variables_out[col] = value
        grouped[config].append(
            {
                **out,
                **variables_out,
                "published_at": _ts(d["published_at"]),
                "updated_at": _ts(d.get("updated_at")),
                "retrieved_at": _ts(d["retrieved_at"]),
                "language": language,
                "section": d.get("section", ""),
                "url": d["url"],
                "license": d["license"],
                "license_url": license_url(d["license"]),
                "credit_line": d["credit_line"],
                "text": d["text"],
                "content_hash": d["content_hash"],
                "status": d.get("status", "live"),
                "near_duplicates": flags.get(rid, []),
            }
        )
    for config in grouped.values():
        config.sort(key=lambda r: (r["published_at"], r["id"]))
    return Release(
        version=version, sources=sources, rows=grouped, checks=checks, near_duplicate_pairs=n_pairs
    )


def _schema(cols: tuple[str, ...] = COLUMNS):  # type: ignore[no-untyped-def]
    import pyarrow as pa

    ts = pa.timestamp("s", tz="UTC")
    text = pa.string()
    types = {
        "authors": pa.list_(text),
        "translators": pa.list_(text),
        "near_duplicates": pa.list_(text),
        "publisher_categories": pa.list_(text),
        "publisher_tags": pa.list_(text),
        "link_hosts": pa.list_(text),
        "other_versions": pa.list_(text),
        "n_links": pa.int64(),
        "n_links_external": pa.int64(),
        "published_at": ts,
        "updated_at": ts,
        "retrieved_at": ts,
    }
    nullable = ("updated_at", "n_links", "n_links_external")
    return pa.schema([pa.field(c, types.get(c, text), nullable=c in nullable) for c in cols])


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _parquet_bytes(rows: list[dict], cols: tuple[str, ...] = COLUMNS) -> bytes:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist(rows, schema=_schema(cols))
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="zstd", row_group_size=ROW_GROUP)
    return sink.getvalue()


def _csv_bytes(header: list[str], lines: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(lines)
    return buf.getvalue().encode("utf-8")


def _iso(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_table(release: Release, registry: dict[str, Source]) -> list[dict[str, object]]:
    """One line per source of the release: kind, licenses, rows, dates, credit template."""
    out = []
    for s in release.sources:
        src = registry[s]
        rows = [r for config in release.rows.values() for r in config if r["source_id"] == s]
        licenses = Counter(r["license"] for r in rows)
        dates = [r["published_at"] for r in rows]
        out.append(
            {
                "source_id": s,
                "name": src.name,
                "kind": src.kind,
                "homepage": src.homepage,
                "licenses": {license_label(k): v for k, v in sorted(licenses.items())},
                "rows": len(rows),
                "first": min(dates).date().isoformat() if dates else "",
                "last": max(dates).date().isoformat() if dates else "",
                "credit_template": src.credit_line,
                "held": release.checks.held.get(s, 0),
                "removed": release.checks.removed.get(s, 0),
            }
        )
    return out


def write_release(
    release: Release,
    out: Path,
    registry_path: Path,
    registry: dict[str, Source],
    *,
    card: str,
    licenses_md: str,
    extra: Mapping[str, object] | None = None,
    extra_files: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    """Write the files of a checked release under ``out`` and return the manifest. ``extra``
    adds keys to the manifest (an update's counts), before the list of files; ``extra_files``
    adds files (series 0.3: ``changes.csv``)."""
    if not release.checks.ok:
        raise ReleaseError("the checks failed: " + "; ".join(release.checks.problems()))
    files: dict[str, bytes] = {}
    shards: dict[str, list[str]] = {}
    for config in CONFIGURATIONS:
        rows = release.rows[config]
        n = max(1, -(-len(rows) // ROWS_PER_SHARD))
        shards[config] = []
        for i in range(n):
            name = f"data/{config}/train-{i:05d}-of-{n:05d}.parquet"
            files[name] = _parquet_bytes(
                rows[i * ROWS_PER_SHARD : (i + 1) * ROWS_PER_SHARD], columns(release.version)
            )
            shards[config].append(name)
    index = [
        [
            r["id"],
            r["source_id"],
            config,
            r["url"],
            r["license"],
            r["content_hash"],
            _iso(r["published_at"]),
        ]
        for config in CONFIGURATIONS
        for r in release.rows[config]
    ]
    index.sort(key=lambda x: (x[6], x[0]))
    files["index.csv"] = _csv_bytes(
        ["id", "source_id", "configuration", "url", "license", "content_hash", "published_at"],
        index,
    )
    files["sources.csv"] = registry_path.read_bytes()
    files["LICENSES.md"] = licenses_md.encode("utf-8")
    files["README.md"] = card.encode("utf-8")
    files.update(extra_files or {})
    all_rows = [r for config in release.rows.values() for r in config]
    as_of = max((r["retrieved_at"] for r in all_rows), default=None)
    out.mkdir(parents=True, exist_ok=True)
    for name, body in sorted(files.items()):
        _write_atomic(out / name, body)
    manifest = {
        "name": "CommonsWire",
        "version": release.version,
        "as_of": _iso(as_of),
        "sources": list(release.sources),
        "configurations": {c: shards[c] for c in CONFIGURATIONS},
        **release.counts(),
        "held_rows_not_released": dict(sorted(release.checks.held.items())),
        "held_rows_by_reason": dict(sorted(release.checks.held_reasons.items())),
        "removed_rows_not_released": dict(sorted(release.checks.removed.items())),
        "taken_down_rows_not_released": dict(sorted(release.checks.taken_down.items())),
        "exact_duplicates_dropped": dict(sorted(release.checks.exact_duplicates.items())),
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "near_duplicate_pairs_across_sources": release.near_duplicate_pairs,
        # Series 0.3 on (an older version's manifest keeps the keys it was published with).
        **(
            {"copies_left_out": dict(sorted(release.checks.copies.items()))}
            if _series(release.version) >= COPIES_FROM
            else {}
        ),
        **(extra or {}),
        "files": [
            {"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            for name, body in sorted(files.items())
        ],
    }
    _write_atomic(out / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


def verify(
    out: Path, corpus_report: dict | None = None, *, ignore_hidden: bool = False
) -> list[str]:
    """Check a written release against its manifest (and the corpus report, if given):
    every file's size and hash, the row counts in the Parquet files, each id once, each row in
    its license's configuration, and each credit line exactly its source's template (from the
    release's own sources.csv) filled in. Returns the problems found (empty when all is
    well)."""
    import pyarrow.parquet as pq

    problems: list[str] = []
    manifest = json.loads((out / "manifest.json").read_text())
    for f in manifest["files"]:
        path = out / f["path"]
        if not path.exists():
            problems.append(f"{f['path']} is missing")
            continue
        if path.stat().st_size != f["bytes"] or sha256(path) != f["sha256"]:
            problems.append(f"{f['path']} differs from the manifest")
    listed = {f["path"] for f in manifest["files"]} | {"manifest.json"}
    for path in sorted(out.rglob("*")):
        rel_path = path.relative_to(out)
        if ignore_hidden and any(part.startswith(".") for part in rel_path.parts):
            continue  # a download's own files (.gitattributes, .cache/), not the release's
        if path.is_file() and str(rel_path) not in listed:
            problems.append(f"{rel_path} is not in the manifest")
    from commonswire.sources import load_sources

    registry = load_sources(out / "sources.csv")
    seen: set[str] = set()
    by_source: Counter[str] = Counter()
    wanted = ["id", "source_id", "title", "authors", "url", "license", "credit_line"]
    for config, names in manifest["configurations"].items():
        n = 0
        for name in names:
            have = pq.read_schema(out / name).names
            if have != list(columns(manifest["version"])):
                problems.append(
                    f"{name}: its columns are not those of version {manifest['version']}"
                )
            cols = wanted + (["translators"] if "translators" in have else [])
            for r in pq.read_table(out / name, columns=cols).to_pylist():
                n += 1
                by_source[r["source_id"]] += 1
                if r["id"] in seen:
                    problems.append(f"{r['id']} is in the release twice")
                seen.add(r["id"])
                if license_class(r["license"]) != config:
                    problems.append(f"{r['id']} ({r['license']}) is in the {config} configuration")
                src = registry.get(r["source_id"])
                want = src and render_credit(
                    src.credit_line,
                    title=r["title"],
                    authors=r["authors"],
                    source=src.name,
                    url=r["url"],
                    license=r["license"],
                    translators=r.get("translators") or (),
                )
                if r["credit_line"] != want:
                    problems.append(f"{r['id']}: the credit line is not its source's template")
        if n != manifest["rows_by_configuration"][config]:
            problems.append(
                f"{config}: {n} rows in the files, {manifest['rows_by_configuration'][config]} in "
                "the manifest"
            )
    if corpus_report is not None:
        for s in manifest["sources"]:
            v = corpus_report["sources"].get(s, {})
            removed = manifest["removed_rows_not_released"].get(s, 0)
            removed += manifest.get("taken_down_rows_not_released", {}).get(s, 0)
            want = v.get("releasable_rows", 0) - removed
            if by_source[s] != want:
                problems.append(
                    f"{s}: {by_source[s]} rows released, but the corpus report has {want} "
                    "releasable rows (run commonswire dedup and corpus-report again?)"
                )
    return problems
