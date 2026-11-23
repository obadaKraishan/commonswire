"""Sources whose license changed over time: the license of an article depends on its date.

Each schedule is read on the source's own license page and recorded in ``data/sources.csv``
(``quote_license``); the registry row's ``license`` is the license of most of the archive.
"""

from __future__ import annotations

from datetime import date, datetime

from commonswire.sources import PUBLIC_DOMAIN

#: A period whose license the source's own page does not settle: its articles are held.
UNPLACED = ""

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
    # The Wikinews language editions (the maintainer's answer 3c, 2026-11-23), each read on its
    # own copyright page (saved 2026-11-17; the quotes are in the registry and
    # docs/rights-audit.md). An article takes the license of its creation date (its first
    # revision). A period the page does not settle is UNPLACED: its articles are held and
    # counted. On a boundary day that the wording leaves to both sides, the license that asks
    # more of the reuser is taken, as for the English edition.
    #
    # French: "Le contenu publié avant le 24 septembre 2005 est dans le domaine public." /
    # "... entre le 24 septembre 2005 et le 2 janvier 2025 est sous licence Creative Commons
    # Attribution 2.5" / "Depuis le 2 janvier 2025, ... (CC BY-SA 4.0)."
    "wikinews_fr": [
        (date.min, PUBLIC_DOMAIN),
        (date(2005, 9, 24), "CC-BY-2.5"),
        (date(2025, 1, 2), "CC-BY-SA-4.0"),
    ],
    # Arabic: texts "اعتبارًا من 21 أغسطس 2024" (as of 21 August 2024) CC BY-SA 4.0; texts
    # published "قبل 21 أغسطس 2024" (before) CC BY 2.5.
    "wikinews_ar": [(date.min, "CC-BY-2.5"), (date(2024, 8, 21), "CC-BY-SA-4.0")],
    # Russian: CC BY 4.0, "(публикации до 26.02.2025 распространяются по лицензии CC-BY
    # версии 2.5 ...)" (publications before 26.02.2025: CC BY 2.5).
    "wikinews_ru": [(date.min, "CC-BY-2.5"), (date(2025, 2, 26), "CC-BY-4.0")],
    # Chinese: all text CC BY 4.0; "2025年1月30日之前加入维基新闻的内容也以CC BY 2.5授权"
    # (content added before 30 January 2025: CC BY 2.5).
    "wikinews_zh": [(date.min, "CC-BY-2.5"), (date(2025, 1, 30), "CC-BY-4.0")],
    # Romanian: before 25 September 2005 the GNU FDL (not released here); after it and before
    # 2 January 2025 CC BY 2.5; after 2 January 2025 CC BY 4.0. The day 2005-09-25 is on
    # neither side and goes to the FDL (held); 2025-01-02 goes to CC BY 2.5.
    "wikinews_ro": [
        (date.min, UNPLACED),
        (date(2005, 9, 26), "CC-BY-2.5"),
        (date(2025, 1, 3), "CC-BY-4.0"),
    ],
    # Swedish: contributions before 1 July 2005 "kan ha publicerats under en annan licens"
    # (may have been under another license: held); before 29 January 2025 CC BY 2.5; CC BY-SA
    # 4.0 since.
    "wikinews_sv": [
        (date.min, UNPLACED),
        (date(2005, 7, 1), "CC-BY-2.5"),
        (date(2025, 1, 29), "CC-BY-SA-4.0"),
    ],
    # Korean: before 25 September 2005 public domain; from it CC BY 2.5. The page was last
    # edited on 5 August 2015 and dates no later change, while today's footer names CC BY 4.0,
    # so later articles are not placed.
    "wikinews_ko": [
        (date.min, PUBLIC_DOMAIN),
        (date(2005, 9, 25), "CC-BY-2.5"),
        (date(2015, 8, 6), UNPLACED),
    ],
    # Greek: before 25 September 2005 public domain; from it CC BY 2.5. Last edited on 28
    # December 2018; later articles are not placed (today's footer names CC BY 4.0).
    "wikinews_el": [
        (date.min, PUBLIC_DOMAIN),
        (date(2005, 9, 25), "CC-BY-2.5"),
        (date(2018, 12, 29), UNPLACED),
    ],
}


def license_on(source_id: str, published_at: datetime, default: str) -> str:
    """The license of a source's article published at ``published_at``; :data:`UNPLACED`
    ("") when its schedule does not settle that date."""
    schedule = LICENSE_SCHEDULES.get(source_id)
    if not schedule:
        return default
    day = published_at.date()
    current = default
    for first_day, lic in schedule:
        if first_day <= day:
            current = lic
    return current


#: The release configuration each license belongs to.
CLASS_PD, CLASS_BY, CLASS_BY_SA, CLASS_NC_ND = "pd", "by", "by-sa", "nc-nd"
PD_MARK = "https://creativecommons.org/publicdomain/mark/1.0/"


def license_class(spdx: str) -> str:
    """``pd``, ``by``, ``by-sa`` or ``nc-nd`` (any NonCommercial or NoDerivatives license)."""
    if spdx in (PUBLIC_DOMAIN, "CC0-1.0", "CC-PDDC"):
        return CLASS_PD
    if spdx.startswith("CC-BY-SA-"):
        return CLASS_BY_SA
    if spdx.startswith(("CC-BY-NC", "CC-BY-ND")):
        return CLASS_NC_ND
    if spdx.startswith("CC-BY-"):
        return CLASS_BY
    raise ValueError(f"{spdx} has no release class; only open and CC licenses are released")


def license_url(spdx: str) -> str:
    """The legal text of a license: CC-BY-SA-4.0 -> https://creativecommons.org/licenses/by-sa/4.0/."""
    if spdx == PUBLIC_DOMAIN:
        return PD_MARK
    if spdx == "CC0-1.0":
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if spdx.startswith("CC-"):
        parts = spdx[3:].split("-")
        version_at = next(i for i, p in enumerate(parts) if p[:1].isdigit())
        terms = "-".join(parts[:version_at]).lower()
        version = parts[version_at]
        port = "/" + parts[version_at + 1].lower() if len(parts) > version_at + 1 else ""
        return f"https://creativecommons.org/licenses/{terms}/{version}{port}/"
    raise ValueError(f"no license URL for {spdx}")
