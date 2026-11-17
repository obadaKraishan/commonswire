"""The rights audit: this project's verdict on each publisher next to other lists of open news.

Two outside lists name news publishers as openly licensed: the news subset of the Common Pile
v0.1 (its dataset card, its paper, its collection code and its data files) and Open Newswire's
feed list (``feeds.csv`` in its repository). Every fact read from them is one row of
``data/audit/other_lists.csv``, with the page it was read on and when:

- ``list``: ``common_pile`` or ``open_newswire``;
- ``source_id``: the registry row the publisher maps to;
- ``publisher`` and ``list_homepage``: the name and address as the list gives them;
- ``tag``: the license tag the list gives, as it writes it, and ``tag_from``: where that tag
  was read (``code``, ``paper``, ``card`` or ``feeds.csv``);
- ``documents``: the list's document count for the publisher, when it gives one;
- ``named_in``: where the list names the publisher (``card;paper;code;data`` for the Common
  Pile; the feed's language for Open Newswire), and ``active``: whether the feed is active;
- ``data_date``: the date of the list's own data, as the list gives it (the day the Common
  Pile's data files were added; the day Open Newswire's ``feeds.csv`` was last changed). A
  tag is the list's reading on that day; the publishers' pages were read later, so a
  difference today does not show that the tag was wrong when it was made;
- ``read_from`` and ``read_at``: the address read and the time (UTC).

:func:`compare` joins these with the registry into one row per publisher that the registry or
either list names (``data/audit/comparison.csv``), and :func:`counts` gives the numbers the
docs quote. A verdict is this project's reading of the publisher's own public pages on the date
given, not legal advice; the comparison says where the lists and the pages differ and never
judges anyone else's work.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from pathlib import Path

from commonswire.licensing import license_class
from commonswire.sources import NO_LICENSE, Source

LISTS = ("common_pile", "open_newswire")
OTHER_LIST_FIELDS = [
    "list",
    "source_id",
    "publisher",
    "list_homepage",
    "tag",
    "tag_from",
    "documents",
    "named_in",
    "active",
    "data_date",
    "read_from",
    "read_at",
]
COMPARISON_FIELDS = [
    "source_id",
    "name",
    "kind",
    "homepage",
    "common_pile_named_in",
    "common_pile_tag",
    "common_pile_documents",
    "common_pile_data_date",
    "open_newswire_tag",
    "open_newswire_active",
    "open_newswire_data_date",
    "license_here",
    "class_here",
    "status",
    "reason_code",
    "checked_on",
    "lists_agree",
]
#: The open classes, as this project releases them.
OPEN_CLASSES = ("pd", "by", "by-sa")
#: Reason codes that mean the publisher's pages could not be read at all.
UNREAD_CODES = frozenset({"refused_requests", "site_unavailable"})


def tag_class(tag: str) -> str:
    """A list's license tag as a class: ``pd``, ``by``, ``by-sa``, ``nc-nd`` (any NonCommercial
    or NoDerivatives tag) or ``other`` (for example Open Newswire's "Attribution+")."""
    t = re.sub(r"[\s_]+", "-", tag.strip().lower())
    if t in ("public-domain", "pd", "cc0", "cc0-1.0") or t.startswith("public-domain"):
        return "pd"
    if t.startswith("cc-by"):
        terms = t[3:].split("-")
        if "nc" in terms or "nd" in terms:
            return "nc-nd"
        return "by-sa" if "sa" in terms else "by"
    return "other"


def registry_class(src: Source) -> str:
    """The class of the license the publisher's own pages state: an open class, ``nc-nd``,
    ``none`` (no license named) or ``closed`` (all rights reserved, or a portal's)."""
    if src.license_family in ("open", "restricted"):
        return license_class(src.license)
    if src.license == NO_LICENSE:
        return "none"
    return src.license_family


def read_other_lists(path: Path, registry: Mapping[str, Source]) -> list[dict[str, str]]:
    """The rows of ``other_lists.csv``. Raises ValueError, naming the line, on an unknown
    list, a source id the registry does not have, a count that is not a number or a time that
    is not ISO 8601."""
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != OTHER_LIST_FIELDS:
            raise ValueError(
                f"{path}: the header must be {', '.join(OTHER_LIST_FIELDS)} (in this order)"
            )
        rows = list(reader)
    for line, row in enumerate(rows, start=2):
        where = f"{Path(path).name}, line {line}"
        if row["list"] not in LISTS:
            raise ValueError(f"{where}: list must be {' or '.join(LISTS)}, not {row['list']!r}")
        if row["source_id"] not in registry:
            raise ValueError(
                f"{where}: {row['source_id']!r} is not in the registry; add its row to "
                "data/sources.csv first"
            )
        if row["documents"] and not row["documents"].isdigit():
            raise ValueError(f"{where}: documents must be a whole number or blank")
        try:
            datetime.fromisoformat(row["read_at"].replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"{where}: read_at must be a time like 2026-11-17T02:05:00Z") from None
        try:
            date.fromisoformat(row["data_date"])
        except ValueError:
            raise ValueError(f"{where}: data_date must be a day like 2025-11-11") from None
    return rows


def _join(values: Iterable[str]) -> str:
    return ";".join(sorted({v for v in values if v}))


def compare(registry: Mapping[str, Source], other: Iterable[Mapping[str, str]]) -> list[dict]:
    """One row per registry publisher, with what each list says about it.

    ``lists_agree`` is ``yes`` when every tag a list gives the publisher falls in the class of
    the license on the publisher's own pages, ``no`` when one does not, ``unread`` when the
    publisher's pages could not be read (refused or not there), and blank when no list names
    it."""
    by_source: dict[str, list[Mapping[str, str]]] = {}
    for row in other:
        by_source.setdefault(row["source_id"], []).append(row)
    out = []
    for sid in sorted(registry):
        src = registry[sid]
        rows = by_source.get(sid, [])
        cp = [r for r in rows if r["list"] == "common_pile"]
        onw = [r for r in rows if r["list"] == "open_newswire"]
        here = registry_class(src)
        tags = [r["tag"] for r in rows if r["tag"]]
        agree = ""
        if tags:
            agree = "yes" if all(tag_class(t) == here for t in tags) else "no"
            if here == "none" and src.reason_code in UNREAD_CODES:
                agree = "unread"
        docs = [int(r["documents"]) for r in cp if r["documents"]]
        out.append(
            {
                "source_id": sid,
                "name": src.name,
                "kind": src.kind,
                "homepage": src.homepage,
                "common_pile_named_in": _join(p for r in cp for p in r["named_in"].split(";")),
                "common_pile_tag": _join(r["tag"] for r in cp),
                "common_pile_documents": str(sum(docs)) if docs else "",
                "common_pile_data_date": _join(r["data_date"] for r in cp),
                "open_newswire_tag": _join(r["tag"] for r in onw),
                "open_newswire_active": _join(r["active"] for r in onw),
                "open_newswire_data_date": _join(r["data_date"] for r in onw),
                "license_here": src.license,
                "class_here": here,
                "status": src.status,
                "reason_code": src.reason_code,
                "checked_on": src.checked_on.isoformat(),
                "lists_agree": agree,
            }
        )
    return out


def tagged_open(row: Mapping[str, str], lists: Iterable[str] = LISTS) -> bool:
    """Whether one of ``lists`` tags the publisher with an open class."""
    tags = []
    if "common_pile" in lists:
        tags += [t for t in row["common_pile_tag"].split(";") if t]
    if "open_newswire" in lists:
        tags += [t for t in row["open_newswire_tag"].split(";") if t]
    return any(tag_class(t) in OPEN_CLASSES for t in tags)


def counts(rows: Iterable[Mapping[str, str]]) -> dict[str, object]:
    """The numbers the docs quote: every publisher by status and reason code, and the
    publishers the other lists tag as openly licensed (each list, and either), by this
    project's status and reason code."""
    rows = list(rows)

    def tally(subset: list[Mapping[str, str]]) -> dict[str, object]:
        return {
            "publishers": len(subset),
            "by_status": dict(sorted(Counter(r["status"] for r in subset).items())),
            "by_reason_code": dict(sorted(Counter(r["reason_code"] for r in subset).items())),
            "by_status_and_reason": dict(
                sorted(Counter(f"{r['status']}:{r['reason_code']}" for r in subset).items())
            ),
            "lists_disagree": sum(1 for r in subset if r["lists_agree"] == "no"),
        }

    return {
        "registry": tally(rows),
        "tagged_open_by_common_pile": tally([r for r in rows if tagged_open(r, ["common_pile"])]),
        "tagged_open_by_open_newswire": tally(
            [r for r in rows if tagged_open(r, ["open_newswire"])]
        ),
        "tagged_open_by_either": tally([r for r in rows if tagged_open(r)]),
    }


def write_comparison(rows: Iterable[Mapping[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COMPARISON_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
