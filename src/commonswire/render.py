"""Write ``docs/sources.md`` from the registry and the evidence log, so the two never disagree."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from commonswire.sources import Source, license_label

STATUS_ORDER = ("include", "pending", "exclude")
STATUS_TITLE = {
    "include": "Included",
    "pending": "Pending: a question to settle first",
    "exclude": "Excluded",
}

RULE = """\
A source's full text may enter the corpus only when all four hold, each read on a primary page
of that source and recorded with the URL, the date and a short exact quote:

1. a license or public-domain statement that allows redistributing the full text unchanged;
2. no clause against systematic, wholesale, bulk or automatic republishing, and no required
   tracking pixel or counter;
3. its terms of use and robots.txt do not forbid automated collection of the pages or feeds
   used;
4. a way to tell the source's own articles from third-party material (wire copy, partner
   stories, syndicated pieces), which is always left out.

A source that fails 1, 2 or 3 is **exclude**. A source whose pages are silent or unclear on any
point is **pending**, and is never included until the question is settled.

How the rule is read (rulings of 2026-11-13):

- (a) **An invitation is not a condition.** "Contact us if you would like to republish
  regularly" does not limit a CC BY license.
- (b) **A request is not a restriction.** "We urge you to link" does not limit public-domain
  text.
- (c) **No terms page.** A site with no terms of use page passes point 3 when its robots.txt
  allows the pages or feeds used.
- (d) **Silence on bulk use** passes only under public domain, CC0, CC BY and CC BY-SA, where
  the license itself grants it. Under NonCommercial or NoDerivatives licenses and under bespoke
  permissions, silence stays pending."""


def _quote(label: str, text: str) -> str:
    return f'{label}: "{text}"' if text else ""


def paragraph(src: Source) -> str:
    lines = [f"### {src.name} (`{src.source_id}`)", ""]
    langs = ", ".join(src.languages)
    lines.append(
        f"{src.kind.capitalize()}, {src.country}, {langs}. "
        f"Home: <{src.homepage}>. Checked on {src.checked_on.isoformat()}."
    )
    lic = (
        license_label(src.license)
        if src.license_family in ("open", "restricted")
        else ("no license named" if src.license_family == "none" else "all rights reserved")
    )
    lic_line = f"- **License:** {lic}"
    if src.license_url:
        lic_line += f" (<{src.license_url}>)"
    if src.quote_license:
        lic_line += f'; "{src.quote_license}"'
    lines += ["", lic_line]
    bulk = f"- **Bulk or automatic reuse:** {src.bulk_clause}"
    if src.quote_bulk:
        bulk += f'; "{src.quote_bulk}"'
    if src.tracking_required == "yes":
        bulk += "; a tracking pixel or counter is required"
    lines.append(bulk)
    terms = f"- **Automated collection:** robots.txt {src.robots}; terms {src.terms_automation}"
    if src.terms_url:
        terms += f" (<{src.terms_url}>)"
    else:
        terms += " (no terms of use page found)"
    if src.quote_terms:
        terms += f'; "{src.quote_terms}"'
    lines.append(terms)
    if src.quote_attribution:
        lines.append(f'- **Credit asked:** "{src.quote_attribution}"')
    lines.append(f"- **Third-party material:** {src.third_party_rule or 'not stated'}")
    status = f"- **Status: {src.status}.**"
    if src.reason:
        status += f" {src.reason}"
    lines.append(status)
    if src.notes:
        lines.append(f"- **Notes:** {src.notes}")
    return "\n".join(lines)


def render_sources_md(
    sources: Iterable[Source], blocked_pages: Iterable[dict[str, str]] = ()
) -> str:
    srcs = list(sources)
    counts = Counter(s.status for s in srcs)
    out = [
        "# Sources",
        "",
        "This file is generated from `data/sources.csv` by `commonswire sources render`; edit",
        "the registry, not this file.",
        "",
        "## The clean-source rule",
        "",
        RULE,
        "",
        "## Summary",
        "",
        f"{len(srcs)} sources checked: "
        + ", ".join(f"{counts[k]} {k}" for k in STATUS_ORDER)
        + ".",
        "",
        "| Source | Kind | License | Bulk | Robots | Terms | Tracking | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    ordered = sorted(srcs, key=lambda s: (STATUS_ORDER.index(s.status), s.name.lower()))
    for s in ordered:
        out.append(
            f"| {s.name} | {s.kind} | {license_label(s.license)} | {s.bulk_clause} | "
            f"{s.robots} | {s.terms_automation} | {s.tracking_required} | {s.status} |"
        )
    for status in STATUS_ORDER:
        group = [s for s in ordered if s.status == status]
        if not group:
            continue
        out += ["", f"## {STATUS_TITLE[status]}", ""]
        out += ["\n\n".join(paragraph(s) for s in group)]
    blocked = list(blocked_pages)
    if blocked:
        out += [
            "",
            "## Pages that refused scripted requests",
            "",
            "These pages answered 401 or 403, showed a bot check, or are closed to the CommonsWire",
            "user agent by robots.txt. They were not fetched any other way; they need to be read",
            "by a person.",
            "",
            "| Source | Page | Answer |",
            "|---|---|---|",
        ]
        for row in blocked:
            answer = row.get("answer") or (
                f"HTTP {row['status']}" if row.get("status") else row["outcome"]
            )
            out.append(f"| {row['source_id']} | <{row['url']}> | {answer} |")
    return "\n".join(out) + "\n"
