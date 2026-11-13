"""Sources whose license changed over time: the license of an article depends on its date.

Each schedule is read on the source's own license page and recorded in ``data/sources.csv``
(``quote_license``); the registry row's ``license`` is the license of most of the archive.
"""

from __future__ import annotations

from datetime import date, datetime

from commonswire.sources import PUBLIC_DOMAIN

#: source_id -> list of (first day, license), oldest first. An article takes the license of the
#: last entry whose first day is on or before its publication date (UTC).
#:
#: Wikinews: "All material published on Wikinews after December 16, 2024 is licensed under the
#: terms of the Creative Commons Attribution 4.0 License. Material published prior December 16,
#: 2024 but after September 25, 2005 is licensed under the terms of the Creative Commons
#: Attribution 2.5 License." Earlier material is in the public domain. On the two boundary days
#: the more restrictive of the two licenses is used.
LICENSE_SCHEDULES: dict[str, list[tuple[date, str]]] = {
    "wikinews_en": [
        (date.min, PUBLIC_DOMAIN),
        (date(2005, 9, 25), "CC-BY-2.5"),
        (date(2024, 12, 17), "CC-BY-4.0"),
    ],
}


def license_on(source_id: str, published_at: datetime, default: str) -> str:
    """The license of a source's article published at ``published_at``."""
    schedule = LICENSE_SCHEDULES.get(source_id)
    if not schedule:
        return default
    day = published_at.date()
    current = default
    for first_day, lic in schedule:
        if first_day <= day:
            current = lic
    return current
