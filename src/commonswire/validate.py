"""``commonswire validate FILE``: check a JSON Lines file of articles.

Errors make the file unusable; warnings are worth a look. Every message names the line.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from commonswire.licensing import LICENSE_SCHEDULES, UNPLACED, license_on
from commonswire.schema import Article
from commonswire.sources import PUBLIC_DOMAIN, Source, render_credit

SHORT_TEXT = 200


@dataclass
class Result:
    articles: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _plain(exc: ValidationError) -> list[str]:
    out = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        msg = err["msg"].removeprefix("Value error, ")
        out.append(f"{loc}: {msg}" if loc else msg)
    return out


def validate_file(path: Path, registry: Mapping[str, Source] | None = None) -> Result:
    """Check every line of a JSON Lines file of articles against the schema and the registry."""
    result = Result()
    ids: dict[str, int] = {}
    hashes: dict[str, int] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            where = f"line {line_no}"
            if not line.strip():
                result.warnings.append(f"{where}: empty line")
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                result.errors.append(f"{where}: not valid JSON ({exc.msg})")
                continue
            try:
                art = Article.model_validate(data)
            except ValidationError as exc:
                result.errors += [f"{where}: {m}" for m in _plain(exc)]
                continue
            result.articles += 1
            if art.id in ids:
                result.errors.append(f"{where}: id {art.id} is also on line {ids[art.id]}")
            ids.setdefault(art.id, line_no)
            if art.third_party:
                result.errors.append(
                    f"{where}: third_party is true; third-party material is dropped and "
                    "counted, never kept"
                )
            if art.status != "removed":
                if art.content_hash in hashes:
                    result.warnings.append(
                        f"{where}: same text as line {hashes[art.content_hash]} (a duplicate?)"
                    )
                hashes.setdefault(art.content_hash, line_no)
                if len(art.text) < SHORT_TEXT:
                    result.warnings.append(f"{where}: text is short ({len(art.text)} characters)")
            if registry is not None:
                result.errors += [f"{where}: {m}" for m in _registry_problems(art, registry)]
    if registry is None:
        result.warnings.append("no source registry given: sources and licenses were not checked")
    return result


def _registry_problems(art: Article, registry: Mapping[str, Source]) -> list[str]:
    src = registry.get(art.source_id)
    if src is None:
        return [f"source_id {art.source_id!r} is not in the source registry"]
    out = []
    if src.status != "include":
        out.append(f"source {art.source_id} is {src.status}, not include; its articles stay out")
    if src.source_id in LICENSE_SCHEDULES:
        expected_license = license_on(src.source_id, art.published_at, src.license)
        if expected_license == UNPLACED:
            # A date the source's table does not settle: the row must be held.
            if art.releasable:
                out.append(
                    f"the license of an article of {art.published_at.date()} is not settled by "
                    "the source's license table, so the row must be held"
                )
        elif art.license != expected_license:
            out.append(
                f"license {art.license} is wrong for an article of {art.published_at.date()}; "
                f"the source's license then was {expected_license}"
            )
    elif art.license not in (src.license, PUBLIC_DOMAIN):
        out.append(f"license {art.license} differs from the source's license {src.license}")
    expected = render_credit(
        src.credit_line,
        title=art.title,
        authors=art.authors,
        source=src.name,
        url=art.url,
        license=art.license,
        translators=art.translators,
    )
    if art.credit_line != expected:
        out.append(f"credit_line should be {expected!r}, as the registry's template gives")
    return out
