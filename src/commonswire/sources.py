"""The source registry (``data/sources.csv``): one row per source, with the evidence for its status.

The clean-source rule. A source's full text may enter the corpus only when all four hold, each
read on a primary page of that source and recorded with the URL, the date and a short exact
quote:

1. a license or public-domain statement that allows redistributing the full text unchanged;
2. no clause against systematic, wholesale, bulk or automatic republishing, and no required
   tracking pixel or counter;
3. its terms of use and robots.txt do not forbid automated collection of the pages or feeds
   used;
4. a way to tell the source's own articles from third-party material (wire copy, partner
   stories, syndicated pieces), which is always left out.

A source that fails 1, 2 or 3 is ``exclude``. A source whose pages are silent or unclear on any
point is ``pending``. A site-wide CC BY, CC BY-SA, CC0 or public-domain statement is itself the
permission, so silence on bulk reuse passes point 2 for those licenses; silence stays
``pending`` when the permission is a bespoke republishing page with no named license, or when
the license is NonCommercial or NoDerivatives.

:func:`validate_sources` checks every rule and returns plain-language problems;
:func:`check_quotes` confirms that each quote is verbatim on a saved page of its source.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

SOURCE_FIELDS = [
    "source_id",
    "name",
    "kind",
    "homepage",
    "country",
    "languages",
    "license",
    "license_url",
    "terms_url",
    "checked_on",
    "quote_license",
    "quote_bulk",
    "quote_attribution",
    "quote_terms",
    "bulk_clause",
    "robots",
    "terms_automation",
    "tracking_required",
    "third_party_rule",
    "access",
    "est_articles_per_day",
    "archive_from",
    "credit_line",
    "status",
    "reason",
    "notes",
]

QUOTE_FIELDS = ("quote_license", "quote_bulk", "quote_attribution", "quote_terms")
MAX_QUOTE = 300

PUBLIC_DOMAIN = "public-domain"
NO_LICENSE = "NOASSERTION"
ALL_RIGHTS_RESERVED = "LicenseRef-all-rights-reserved"

#: Licenses that allow verbatim redistribution of the full text by anyone, for any purpose.
OPEN_LICENSES = frozenset(
    {
        PUBLIC_DOMAIN,
        "CC0-1.0",
        "CC-PDDC",
        "CC-BY-2.0",
        "CC-BY-2.5",
        "CC-BY-3.0",
        "CC-BY-3.0-US",
        "CC-BY-3.0-IGO",
        "CC-BY-4.0",
        "CC-BY-SA-2.0",
        "CC-BY-SA-2.5",
        "CC-BY-SA-3.0",
        "CC-BY-SA-3.0-IGO",
        "CC-BY-SA-4.0",
    }
)
#: Creative Commons licenses with NonCommercial or NoDerivatives terms. They allow verbatim,
#: noncommercial redistribution, so they pass point 1, but silence on bulk use leaves them
#: pending.
RESTRICTED_LICENSES = frozenset(
    {
        f"CC-{kind}-{version}"
        for kind in ("BY-NC", "BY-ND", "BY-NC-ND", "BY-NC-SA")
        for version in ("2.0", "2.5", "3.0", "3.0-US", "3.0-IGO", "4.0")
    }
)
KNOWN_LICENSES = OPEN_LICENSES | RESTRICTED_LICENSES | {NO_LICENSE, ALL_RIGHTS_RESERVED}

Kind = Literal["news", "official", "advocacy", "fact-check", "portal"]
Clause = Literal["allows", "silent", "forbids"]
Robots = Literal["allows", "forbids", "none", "blocked"]
Status = Literal["include", "pending", "exclude"]
ACCESS = frozenset({"dump", "api", "feed", "sitemap"})

_ID = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
_COUNTRY = re.compile(r"^([A-Z]{2}|INTL)$")
_URL = re.compile(r"^https?://[^\s/]+\.[^\s]+$")
_YEAR_OR_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


class Source(BaseModel):
    """One registry row. Field-level checks are here; the rules that link fields are in
    :func:`rule_problems`."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    source_id: str
    name: str = Field(min_length=1)
    kind: Kind
    homepage: str
    country: str
    languages: tuple[str, ...]
    license: str
    license_url: str = ""
    terms_url: str = ""
    checked_on: date
    quote_license: str = ""
    quote_bulk: str = ""
    quote_attribution: str = ""
    quote_terms: str = ""
    bulk_clause: Clause
    robots: Robots
    terms_automation: Clause
    tracking_required: Literal["yes", "no"]
    third_party_rule: str = ""
    access: tuple[str, ...] = ()
    est_articles_per_day: float | None = None
    archive_from: str = ""
    credit_line: str = ""
    status: Status
    reason: str = ""
    notes: str = ""

    @field_validator("source_id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not _ID.match(v):
            raise ValueError("use lowercase letters, digits and underscores, like global_voices")
        return v

    @field_validator("homepage")
    @classmethod
    def _homepage(cls, v: str) -> str:
        if not _URL.match(v):
            raise ValueError("give the full address, starting with https://")
        return v

    @field_validator("license_url", "terms_url")
    @classmethod
    def _optional_url(cls, v: str) -> str:
        if v and not _URL.match(v):
            raise ValueError("give the full address, starting with https://, or leave it blank")
        return v

    @field_validator("country")
    @classmethod
    def _country(cls, v: str) -> str:
        if not _COUNTRY.match(v):
            raise ValueError("use a two-letter country code such as US, or INTL")
        return v

    @field_validator("languages", "access", mode="before")
    @classmethod
    def _split(cls, v: object) -> object:
        if isinstance(v, str):
            return tuple(p.strip() for p in v.split(";") if p.strip())
        return v

    @field_validator("languages")
    @classmethod
    def _languages(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if not v:
            raise ValueError("list at least one language, such as en (separate several with ;)")
        bad = [x for x in v if not _LANG.match(x)]
        if bad:
            raise ValueError(f"not a language tag: {', '.join(bad)} (use codes like en or pt-BR)")
        return v

    @field_validator("access")
    @classmethod
    def _access(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        bad = [x for x in v if x not in ACCESS]
        if bad:
            raise ValueError(f"unknown access {', '.join(bad)}; use {', '.join(sorted(ACCESS))}")
        return v

    @field_validator("license")
    @classmethod
    def _license(cls, v: str) -> str:
        if v in KNOWN_LICENSES or v.startswith("LicenseRef-"):
            return v
        raise ValueError(
            f"unknown license {v!r}: use an SPDX id such as CC-BY-4.0, public-domain, "
            "NOASSERTION (no license named) or a LicenseRef- name"
        )

    @field_validator("est_articles_per_day", mode="before")
    @classmethod
    def _blank_number(cls, v: object) -> object:
        return None if v == "" else v

    @field_validator("est_articles_per_day")
    @classmethod
    def _per_day(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("articles per day can't be negative")
        return v

    @field_validator("archive_from")
    @classmethod
    def _archive(cls, v: str) -> str:
        if v and not _YEAR_OR_DATE.match(v):
            raise ValueError("use a year or a date: 2005, 2005-09 or 2005-09-25")
        return v

    @field_validator(*QUOTE_FIELDS)
    @classmethod
    def _quote(cls, v: str) -> str:
        if len(v) > MAX_QUOTE:
            raise ValueError(f"keep quotes short: {len(v)} characters, at most {MAX_QUOTE}")
        if "\n" in v:
            raise ValueError("a quote must be on one line")
        return v

    # ---- what the evidence says, point by point ----

    @property
    def license_family(self) -> str:
        """``open``, ``restricted`` (NC or ND), ``none`` (no license named) or ``closed``."""
        if self.license in OPEN_LICENSES:
            return "open"
        if self.license in RESTRICTED_LICENSES:
            return "restricted"
        if self.license == NO_LICENSE or self.license.startswith("LicenseRef-republish"):
            return "none"
        return "closed"

    def failed_points(self) -> list[str]:
        """The points of the rule this source fails outright (which makes it ``exclude``)."""
        failed = []
        if self.license_family == "closed":
            failed.append("1: no license allows redistributing the full text")
        if self.bulk_clause == "forbids":
            failed.append("2: forbids bulk or automatic republishing")
        if self.tracking_required == "yes":
            failed.append("2: requires a tracking pixel or counter")
        if self.robots == "forbids":
            failed.append("3: robots.txt forbids the pages or feeds used")
        if self.terms_automation == "forbids":
            failed.append("3: the terms forbid automated collection")
        return failed

    def open_points(self) -> list[str]:
        """The points on which the evidence is silent or unclear (which makes it ``pending``)."""
        open_ = []
        if self.license_family == "none":
            open_.append("1: no license is named")
        if self.license_family == "restricted" and self.bulk_clause != "allows":
            open_.append("2: a NonCommercial or NoDerivatives license, silent on bulk use")
        if self.license_family == "none" and self.bulk_clause == "silent":
            open_.append("2: bespoke republishing terms, silent on bulk use")
        if self.robots == "blocked":
            open_.append("3: the site refused scripted requests")
        if not self.third_party_rule:
            open_.append("4: no way to tell the source's own articles from third-party material")
        if not self.quote_license:
            open_.append("1: no quote for the license")
        return open_


def rule_problems(src: Source, today: date | None = None) -> list[str]:
    """Plain-language problems with one row, beyond the field checks."""
    today = today or date.today()
    out: list[str] = []
    if src.checked_on > today:
        out.append(f"checked_on {src.checked_on} is in the future")
    if src.bulk_clause in ("allows", "forbids") and not src.quote_bulk:
        out.append(f"bulk_clause is {src.bulk_clause}: give the exact words in quote_bulk")
    if src.terms_automation == "forbids" and not src.quote_terms:
        out.append("terms_automation is forbids: give the exact words in quote_terms")
    if src.license_family in ("open", "restricted") and not src.license_url:
        out.append("give license_url: the page where the license is stated")
    if src.tracking_required == "yes" and not (src.quote_bulk or src.quote_attribution):
        out.append("tracking_required is yes: quote the words that require it")
    failed = src.failed_points()
    open_ = src.open_points()
    if src.status == "include":
        if failed:
            out.append(f"status is include, but the source fails point {failed[0]}")
        if open_:
            out.append(f"status is include, but point {open_[0]} (that makes it pending)")
        if not src.credit_line:
            out.append("status is include: give the credit_line every row must carry")
        if not src.access:
            out.append("status is include: say how articles are collected in access")
        if not src.terms_url:
            out.append("status is include: give terms_url (the terms of use that were read)")
    elif src.status == "exclude":
        if not src.reason:
            out.append("status is exclude: say why in reason")
        if not failed:
            out.append(
                "status is exclude, but no point fails outright; use pending if the evidence "
                "is only silent or unclear"
            )
    else:  # pending
        if failed:
            out.append(f"status is pending, but the source fails point {failed[0]}: exclude it")
        if "?" not in src.reason:
            out.append("status is pending: write the exact question to settle in reason")
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != SOURCE_FIELDS:
            missing = [f for f in SOURCE_FIELDS if f not in (reader.fieldnames or [])]
            extra = [f for f in (reader.fieldnames or []) if f not in SOURCE_FIELDS]
            detail = []
            if missing:
                detail.append(f"missing {', '.join(missing)}")
            if extra:
                detail.append(f"unexpected {', '.join(extra)}")
            raise ValueError(
                f"{path}: the header must list the registry columns in order"
                + (f" ({'; '.join(detail)})" if detail else "")
            )
        return list(reader)


def parse_row(row: Mapping[str, str]) -> Source:
    return Source.model_validate(dict(row))


def _plain_errors(exc: ValidationError) -> list[str]:
    out = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"]) or "row"
        msg = err["msg"].removeprefix("Value error, ")
        out.append(f"{field}: {msg}")
    return out


def validate_sources(path: Path, today: date | None = None) -> tuple[list[Source], list[str]]:
    """Read and check the registry. Returns the valid rows and every problem found."""
    rows = read_rows(path)
    sources: list[Source] = []
    problems: list[str] = []
    seen: dict[str, int] = {}
    homes: dict[str, int] = {}
    for line, row in enumerate(rows, start=2):
        label = f"{Path(path).name}, line {line} ({row.get('source_id') or '?'})"
        try:
            src = parse_row(row)
        except ValidationError as exc:
            problems += [f"{label}: {m}" for m in _plain_errors(exc)]
            continue
        if src.source_id in seen:
            problems.append(f"{label}: source_id is also on line {seen[src.source_id]}")
        seen.setdefault(src.source_id, line)
        if src.homepage in homes:
            problems.append(f"{label}: homepage is also on line {homes[src.homepage]}")
        homes.setdefault(src.homepage, line)
        problems += [f"{label}: {m}" for m in rule_problems(src, today)]
        sources.append(src)
    return sources, problems


_QUOTE_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
)


def normalize_for_match(text: str) -> str:
    """Fold typographic quotes, dashes and whitespace so a quote can be found on its page."""
    text = unicodedata.normalize("NFKC", text).translate(_QUOTE_MAP)
    return re.sub(r"\s+", " ", text).strip()


def check_quotes(
    sources: Iterable[Source], texts_for: Callable[[str], Mapping[str, str]]
) -> list[str]:
    """Every quote must appear verbatim on a saved page of its source."""
    problems = []
    for src in sources:
        quotes = [(f, getattr(src, f)) for f in QUOTE_FIELDS if getattr(src, f)]
        if not quotes:
            continue
        pages = {k: normalize_for_match(v) for k, v in texts_for(src.source_id).items()}
        if not pages:
            problems.append(f"{src.source_id}: no saved pages to check its quotes against")
            continue
        for field, quote in quotes:
            needle = normalize_for_match(quote)
            if not any(needle in page for page in pages.values()):
                problems.append(
                    f"{src.source_id}: {field} is not on any saved page of the source, "
                    f'word for word: "{quote[:80]}"'
                )
    return problems


def load_sources(path: Path) -> dict[str, Source]:
    """The registry as a dict by source_id; raises ValueError if any row has a problem."""
    sources, problems = validate_sources(path)
    if problems:
        raise ValueError(f"{path} has {len(problems)} problem(s); the first: {problems[0]}")
    return {s.source_id: s for s in sources}
