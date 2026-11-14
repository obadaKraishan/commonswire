"""The dataset card (README.md) and LICENSES.md of a release, filled in from its numbers.

The words are fixed here and the numbers come from the release itself, so the card always
matches the files it describes, and the same rows give the same card.
"""

from __future__ import annotations

import textwrap
from collections import Counter
from datetime import timedelta

from commonswire.release import CONFIGURATIONS, Release, columns, source_table
from commonswire.sources import Source, license_label

REPO = "https://github.com/obadaKraishan/commonswire"
ISSUE_FORM = f"{REPO}/issues/new?template=takedown.yml"
HF_ID = "obadakr/commonswire"
HF_URL = f"https://huggingface.co/datasets/{HF_ID}"
FLOW_DAYS = 90

#: A text shorter than this many characters counts as short (as in ``commonswire validate``).
SHORT_TEXT = 200
#: How the limitations describe a source: (one of them, several of them).
SOURCE_PHRASES = {
    "globalvoices": (
        "an international citizen-media newsroom",
        "international citizen-media newsrooms",
    ),
    "factly": ("a fact-checking site in India", "fact-checking sites in India"),
    "altnews": ("a fact-checking site in India", "fact-checking sites in India"),
    "360info": ("an open-access research newswire", "open-access research newswires"),
    "thepublicrecord": (
        "a local newsroom in Hamilton (Canada)",
        "local newsrooms in Hamilton (Canada)",
    ),
    "balkandiskurs": ("an outlet in Bosnia and Herzegovina", "outlets in Bosnia and Herzegovina"),
    "wikinews_en": ("a closed citizen-journalism wiki", "closed citizen-journalism wikis"),
}
#: Why a source has many short texts, where that is known.
SHORT_REASONS = {
    "globalvoices": "short posts of a sentence or two, most of them with a link, from its first "
    "years",
}
#: The words for a held row's reason (the first words of its hold_reason).
HELD_TEXT = {
    "no byline": "name no author on the article's page or in the source's story listing",
    "credited to an account, not a person": 'are credited only to an account such as "Guest '
    'Contributor", which names no person',
}
#: Series whose card has a "Changes since" section, and the version it compares with.
CHANGES_SINCE = {(0, 2): "0.1.0"}
_NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

CONFIG_TEXT = {
    "by": "Creative Commons Attribution (CC BY 2.5, 3.0 and 4.0)",
    "by-sa": "Creative Commons Attribution-ShareAlike (CC BY-SA 4.0)",
    "pd": "public domain",
}


def _n(x: int) -> str:
    return f"{x:,}"


def _rows(x: int) -> str:
    return f"{x:,} row" if x == 1 else f"{x:,} rows"


def _size_category(n: int) -> str:
    for lo, hi, name in (
        (1_000, 10_000, "1K<n<10K"),
        (10_000, 100_000, "10K<n<100K"),
        (100_000, 1_000_000, "100K<n<1M"),
    ):
        if lo <= n < hi:
            return name
    return "n<1K" if n < 1_000 else "1M<n<10M"


def _wrap(text: str) -> str:
    """A bullet or a sentence wrapped at 95 characters, continuation lines indented for a
    bullet (Markdown reads them as one paragraph either way)."""
    indent = "  " if text.startswith("- ") else ""
    return "\n".join(
        textwrap.fill(line, 95, subsequent_indent=indent, break_on_hyphens=False)
        for line in text.split("\n")
    )


def _join(parts: list[str]) -> str:
    if len(parts) <= 2:
        return " and ".join(parts)
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def _mix(release: Release, registry: dict[str, Source], rows_by_source: Counter[str]) -> str:
    """The sources in words, largest first: "an international citizen-media newsroom, two
    fact-checking sites in India, ..."."""
    groups: dict[tuple[str, str], int] = {}
    count: Counter[tuple[str, str]] = Counter()
    for s in release.sources:
        src = registry[s]
        phrase = SOURCE_PHRASES.get(s, (f"{src.name} ({src.kind})", f"{src.name} ({src.kind})"))
        groups[phrase] = groups.get(phrase, 0) + rows_by_source.get(s, 0)
        count[phrase] += 1
    ordered = sorted(groups, key=lambda k: -groups[k])
    return _join(
        [
            k[0] if count[k] == 1 else f"{_NUMBER_WORDS.get(count[k], count[k])} {k[1]}"
            for k in ordered
        ]
    )


def facts(release: Release, registry: dict[str, Source], third_party: int) -> dict[str, object]:
    """The numbers the card uses, all computed from the release's rows."""
    rows = [r for config in release.rows.values() for r in config]
    as_of = max(r["retrieved_at"] for r in rows)
    since = as_of - timedelta(days=FLOW_DAYS)
    recent = Counter(r["source_id"] for r in rows if r["published_at"] >= since)
    kinds = {s: registry[s].kind for s in release.sources}
    flow = sum(recent.values()) / FLOW_DAYS
    fact_checks = sum(v for s, v in recent.items() if kinds[s] == "fact-check") / FLOW_DAYS
    return {
        "rows": len(rows),
        "words": sum(len(r["text"].split()) for r in rows),
        "as_of": as_of.date().isoformat(),
        "first": min(r["published_at"] for r in rows).date().isoformat(),
        "last": max(r["published_at"] for r in rows).date().isoformat(),
        "flow": flow,
        "flow_fact_checks": fact_checks,
        "flow_by_source": {s: recent.get(s, 0) / FLOW_DAYS for s in release.sources},
        "with_byline": sum(1 for r in rows if r["authors"]),
        "with_translators": sum(1 for r in rows if r.get("translators")),
        "translators_by_source": Counter(r["source_id"] for r in rows if r.get("translators")),
        "rows_by_source": Counter(r["source_id"] for r in rows),
        "short_by_source": Counter(r["source_id"] for r in rows if len(r["text"]) < SHORT_TEXT),
        "short_before_2013": Counter(
            r["source_id"]
            for r in rows
            if len(r["text"]) < SHORT_TEXT and r["published_at"].year < 2013
        ),
        "median_words": {
            s: sorted(len(r["text"].split()) for r in rows if r["source_id"] == s)[
                sum(1 for r in rows if r["source_id"] == s) // 2
            ]
            for s in release.sources
            if any(r["source_id"] == s for r in rows)
        },
        "held": sum(release.checks.held.values()),
        "held_reasons": dict(release.checks.held_reasons),
        "exact_duplicates": sum(release.checks.exact_duplicates.values()),
        "third_party": third_party,
        "near_pairs": release.near_duplicate_pairs,
    }


def _license_cell(licenses: dict[str, int]) -> str:
    if len(licenses) == 1:
        return next(iter(licenses))
    return "; ".join(f"{k} ({_n(v)})" for k, v in licenses.items())


def card(release: Release, registry: dict[str, Source], third_party: int) -> str:
    """The dataset card of a release, with the Hugging Face metadata block on top."""
    f = facts(release, registry, third_party)
    counts = release.counts()
    per_config = counts["rows_by_configuration"]
    table = source_table(release, registry)
    configs_yaml = []
    for c in CONFIGURATIONS:
        configs_yaml.append(
            f"- config_name: {c}\n  data_files:\n  - split: train\n"
            f'    path: "data/{c}/*.parquet"' + ("\n  default: true" if c == "by" else "")
        )
    flows = ", ".join(
        f"{registry[s].name} {f['flow_by_source'][s]:.1f}"  # type: ignore[index]
        for s in release.sources
        if f["flow_by_source"][s]  # type: ignore[index]
    )
    src_lines = "\n".join(
        f"| {t['name']} | {t['kind']} | {_license_cell(t['licenses'])} | {_n(t['rows'])} | "
        f"{t['first']} to {t['last']} | `{t['credit_template']}` |"
        for t in table
    )
    config_lines = "\n".join(
        f"| `{c}` | {CONFIG_TEXT[c]} | {_n(per_config[c])} |" for c in CONFIGURATIONS
    )
    fact_share = round(100 * f["flow_fact_checks"] / f["flow"]) if f["flow"] else 0  # type: ignore[operator]
    fact_words = (
        f"Fact-checks are most of that flow (about {fact_share}%)."
        if fact_share > 50
        else f"Fact-checks are about {fact_share}% of that flow."
    )
    size = _size_category(int(f["rows"]))  # type: ignore[call-overload]
    by_src: Counter[str] = f["rows_by_source"]  # type: ignore[assignment]
    total = int(f["rows"])  # type: ignore[call-overload]
    held_note = ""
    if f["held"]:
        reasons = sorted(f["held_reasons"].items(), key=lambda kv: (-kv[1], kv[0]))  # type: ignore[union-attr]
        held_note = _wrap(
            f"{_n(f['held'])} more rows are held back because the source asks for the author's "
            "name: " + "; ".join(f"{_n(v)} {HELD_TEXT.get(k, k)}" for k, v in reasons) + "."
        )
    largest = max(release.sources, key=lambda x: (by_src.get(x, 0), x))
    share = by_src.get(largest, 0) / total if total else 0.0
    largest_line = ""
    if share >= 0.4:
        largest_line = (
            _wrap(
                f"- **{registry[largest].name} is "
                + ("most of it" if share > 0.5 else "the largest part of it")
                + f"** ({_n(by_src[largest])} of {_n(total)} rows, {round(100 * share)}%): "
                + ("results over the whole corpus mostly describe it." if share > 0.5 else "")
                + ("results over the whole corpus lean on it." if share <= 0.5 else "")
            )
            + "\n"
        )
    wikinews_line = (
        "- **Wikinews is a closed archive.** English Wikinews stopped publishing on 2026-05-04.\n"
        if "wikinews_en" in release.sources
        else ""
    )
    short_lines = ""
    for s in release.sources:
        n, tot = f["short_by_source"].get(s, 0), by_src.get(s, 0)  # type: ignore[union-attr]
        if tot and n / tot >= 0.1:
            name = registry[s].name
            why = SHORT_REASONS.get(s, "")
            early = f["short_before_2013"].get(s, 0)  # type: ignore[union-attr]
            reason = (
                f": {why} ({round(100 * early / n)}% of them published before 2013)" if why else ""
            )
            short_lines += (
                _wrap(
                    f"- {round(100 * n / tot)}% of the {name} rows ({_n(n)}) have fewer than "
                    f"{SHORT_TEXT} characters of text{reason}. The median {name} row has "
                    f"{f['median_words'][s]} words. Filter by length if you need full stories."  # type: ignore[index]
                )
                + "\n"
            )
    with_tr = "translators" in columns(release.version)
    tr_field = (
        "| `translators` | the translators the source names, apart from the writers (empty when "
        "it names none) |\n"
        if with_tr
        else ""
    )
    tr_note = ""
    if f["with_translators"]:
        names = _join([registry[x].name for x in sorted(f["translators_by_source"])])  # type: ignore[call-overload]
        tr_note = (
            _wrap(
                f"When the source names translators ({names}, for {_n(f['with_translators'])} "
                + ("row" if f["with_translators"] == 1 else "rows")
                + '), `{authors}` is followed by ", translated by" and their names; the writers '
                "stay in `authors`, and the translators are in `translators`."
            )
            + "\n"
        )
    from commonswire.listingbylines import LISTING_MARKUP
    from commonswire.release import series_sources

    listing = [registry[x].name for x in release.sources if x in LISTING_MARKUP]
    listing_words = f" or in the source's own story listing ({_join(listing)})" if listing else ""
    quoters = [registry[x].name for x in release.sources if x in ("globalvoices",)]
    quote_line = _wrap(
        f"- Fact-check articles and {_join(quoters)} stories quote and describe posts from social "
        "media and blogs. The embedded posts are removed, but the quoted words stay in the text."
        if quoters
        else "- Fact-check articles quote and describe social-media posts. The embedded posts are "
        "removed, but the quoted claims stay in the text."
    )
    flow_line = _wrap(
        f"- **It is small going forward.** Over the last {FLOW_DAYS} days the sources published "
        f"about {f['flow']:.1f} new articles a day: {flows}. {fact_words}"
    )
    mix_line = _wrap(
        f"- The sources are a small, uneven set: {_mix(release, registry, by_src)}. Their mix of "
        "countries and topics is not that of mainstream news."
    )
    bylines_line = _wrap(
        "- **Bylines.** From the source's API; where the API gives none and the source asks for "
        f"the author's name, from the byline on the article's own page{listing_words}, never "
        "from the body text."
    )
    pairs_word = "pair" if f["near_pairs"] == 1 else "pairs"
    wikinews_markup = (
        "- Wikinews text is converted from wiki markup by rule; a few articles keep a stray bar,\n"
        "  bracket or brace where the wikitext itself has a slip.\n"
        if "wikinews_en" in release.sources
        else ""
    )
    changes = ""
    major, minor = (int(x) for x in release.version.split(".")[:2])
    since = CHANGES_SINCE.get((major, minor))
    if since:
        lines = []
        for x in release.sources:
            if x in series_sources(since):
                continue
            t = next(t for t in table if t["source_id"] == x)
            what = SOURCE_PHRASES.get(x, (registry[x].kind,))[0]
            how = (
                "; its writers' names come from its own story listing, which names every writer "
                "of a story, and its translators apart"
                if x in LISTING_MARKUP
                else ""
            )
            lines.append(
                f"- **A new source: {t['name']}** ({_rows(t['rows'])}, "
                f"{_license_cell(t['licenses'])}, {t['first'][:4]} to {t['last'][:4]}), {what}"
                f"{how}."
            )
        if with_tr and "translators" not in columns(since):
            lines.append(
                "- **A new field, `translators`:** the translators the source names, apart from "
                f"the writers in `authors` ({_rows(f['with_translators'])}); the credit line "
                'names them ("..., by A, translated by B, ...").'
            )
        account = f["held_reasons"].get("credited to an account, not a person", 0)  # type: ignore[union-attr]
        if account:
            lines.append(
                f"- **Rows credited only to an account are held back** ({_n(account)}): an "
                'account such as "Guest Contributor" names no person.'
            )
        lines.append(
            f"- **Near-duplicates across sources:** {_n(f['near_pairs'])} {pairs_word} in this "
            "version."
        )
        changes = f"\n## Changes since {since}\n" + "\n".join(_wrap(x) for x in lines) + "\n"
    return f"""---
pretty_name: CommonsWire
language:
- en
license: other
license_name: per-row-open-licenses
license_link: https://huggingface.co/datasets/obadakr/commonswire/blob/main/LICENSES.md
tags:
- news
- journalism
- fact-checking
- creative-commons
- communication-research
size_categories:
- {size}
configs:
{chr(10).join(configs_yaml)}
---

# CommonsWire {release.version}

CommonsWire is a full-text corpus of news articles whose publishers allow their text to be
shared again. Each row is one article: its body text as published, its metadata, its license,
and the credit line its publisher asks for.

Version {release.version} holds {_n(f["rows"])} articles ({f["words"] / 1e6:.1f} million words)
from {len(release.sources)} sources, published from {f["first"]} to {f["last"]} and collected
up to {f["as_of"]}.

- **Curated by:** Obada Kraishan, College of Media and Communication, Texas Tech University.
- **License:** each article keeps its publisher's license (public domain, CC BY or CC BY-SA),
  on its row; see `LICENSES.md`.
- **Contact:** the [issue tracker]({REPO}/issues).

CommonsWire is not affiliated with, endorsed by or sponsored by any of the newsrooms whose
articles it holds.

## What it is, and what it is not
- **It is** each source's own articles, as far as its API or dump gives them, with every
  article's license on its row. More sources join in later versions.
- **It is not every news outlet.** Most newsrooms do not allow their text to be shared again,
  and they are not here. Results from CommonsWire describe these sources, not "the news".
{flow_line}
{largest_line}{wikinews_line}- **It is English only.**
- **It has no coded variables yet** (topic, frame, types of sources quoted, tone). They are
  planned for a later version.
{changes}
## The sources
| Source | Kind | License | Rows | Published | Credit line template |
|---|---|---|---|---|---|
{src_lines}

`{{authors}}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source.
{tr_note}{held_note}

Every source in the registry (included, pending and excluded), with the pages read and the
words quoted as evidence, is in `sources.csv`.

## Configurations and licenses
Each row carries its own `license`, `license_url` and `credit_line`. The rows are split into
one configuration per license class, so you can load only what your use allows:

| Configuration | Licenses | Rows |
|---|---|---|
{config_lines}

```python
from datasets import load_dataset

by = load_dataset("{HF_ID}", "by", split="train")  # CC BY
by_sa = load_dataset("{HF_ID}", "by-sa", split="train")  # CC BY-SA
pd = load_dataset("{HF_ID}", "pd", split="train")  # public domain
```

**What you must do** (this is a summary, not legal advice; `LICENSES.md` has more):
- **CC BY** (`by`): keep each article's `credit_line` with it. It names the creator and the
  source, the title, the link and the license. Say if you changed the text.
- **CC BY-SA** (`by-sa`): the same, and share anything you adapt from these texts (a
  translation, an edited version) under CC BY-SA.
- **Public domain** (`pd`): nothing is required. The credit line is kept as a courtesy.
  Public-domain status under US law may not hold in every country.
- In every case, do not suggest that a newsroom endorses your work, and drop articles that a
  later version marks as removed.

## Fields
| Field | Meaning |
|---|---|
| `id` | `cw_` and 16 hex digits of the SHA-256 of the canonical URL; stable across versions |
| `source_id`, `kind` | the source, as in `sources.csv`, and its kind (`news`, `fact-check`) |
| `title` | the headline as published |
| `authors` | the bylines as published (empty when the article names no person) |
{tr_field}| `published_at`, `updated_at` | UTC, as the source gives them |
| `retrieved_at` | UTC, when CommonsWire fetched the article |
| `language` | `en` |
| `section` | the source's own section or category, if any |
| `url` | the article at its source |
| `license`, `license_url` | the article's license and a link to its legal text |
| `credit_line` | the attribution to keep with the text |
| `text` | the body text, words unchanged; paragraphs separated by a blank line |
| `content_hash` | SHA-256 of `text`, to spot changed articles between versions |
| `status` | `live`, or `changed` if the source edited the text after it was first collected |
| `near_duplicates` | ids of very similar articles in other sources (5-gram Jaccard 0.6 or more) |

`index.csv` lists every row's id, source, configuration, URL, license, content hash and
publication time, without text. `manifest.json` gives the row counts and the size and SHA-256 of
every file.

## How it was collected
- **Rights first.** A source enters only when its own pages give a license or public-domain
  statement that allows sharing the full text unchanged, do not forbid bulk or automatic
  reuse, and do not forbid automated collection, and when its own articles can be told apart
  from material it republishes. The evidence (page, date, exact words) is in `sources.csv`.
- **Third-party material is left out.** Wire copy, partner stories, syndicated pieces and posts
  under someone else's rights are dropped; {_n(f["third_party"])} were dropped in this version.
- **Text unchanged.** The body text comes from each source's API (Wikinews: from the
  Wikimedia dump, with the wiki markup removed by rule). Only whitespace inside paragraphs is
  normalized. Photos, captions, video, audio and embedded posts are not collected; they are
  often separate works the source does not license.
{bylines_line}
- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped:
  {_n(f["exact_duplicates"])} in this version. Near-duplicates across sources are flagged in
  `near_duplicates`, not dropped: {_n(f["near_pairs"])} {pairs_word} in this version.
- **Politely.** One request at a time, at least 2 seconds apart, robots.txt and crawl-delays
  honored, and a user agent that names the project. Blocks are never worked around.

## Removals and corrections
- **At the source.** Each update looks again at the last 30 days of every source that still
  publishes: an article
  edited at its source gets its new text and status `changed` in the next version, and an
  article removed at its source is dropped from the next version. Older articles are not
  checked again yet; a monthly check is planned.
- **On request.** Publishers, writers and people named in an article can ask for a removal or a
  correction with the [takedown and correction form]({ISSUE_FORM}). Requests are answered
  within 14 days. An article taken down goes on a list of ids (`data/takedowns.csv` in the
  code repository, with no URL or name) and is left out of every later version.
- **Your copy.** If you keep a copy of CommonsWire, please apply removals to it too:
  `index.csv` of the latest version lists every article still in it.

## Limitations
{mix_line}
{short_lines.rstrip(chr(10))}
{wikinews_markup}{quote_line}
- `authors` is filled for {_n(f["with_byline"])} of {_n(f["rows"])} rows. Wikinews articles
  carry no bylines, and some articles are credited to the source itself.
- News articles name people. CommonsWire adds nothing to what was published, infers nothing
  about anyone (no gender, ethnicity or other attribute), and offers no search by person.

## Contact
Questions and errors: the [issue tracker]({REPO}/issues). Removals and corrections: the
[takedown and correction form]({ISSUE_FORM}).

## Citation
Please cite the version you used, and credit the newsrooms as each row's credit line asks.

```bibtex
@misc{{commonswire_{release.version.replace(".", "_")},
  author = {{Kraishan, Obada}},
  title = {{CommonsWire: a full-text corpus of openly licensed news}},
  version = {{{release.version}}},
  year = {{{f["as_of"][:4]}}},
  howpublished = {{Hugging Face}},
  url = {{{HF_URL}}}
}}
```

Version {release.version}, collected up to {f["as_of"]}. Code: {REPO} (Apache-2.0).
"""


def licenses_md(release: Release, registry: dict[str, Source]) -> str:
    """A short LICENSES.md: the licenses in this version and what users must do."""
    counts = release.counts()
    lines = []
    for c in CONFIGURATIONS:
        lic = Counter(r["license"] for r in release.rows[c])
        names = ", ".join(f"{license_label(k)} ({v:,})" for k, v in sorted(lic.items()))
        lines.append(f"| `{c}` | {names or 'none'} | {counts['rows_by_configuration'][c]:,} |")
    return f"""# Licenses in CommonsWire {release.version}

CommonsWire does not relicense anyone's writing. Every article keeps its publisher's license,
recorded on its row as `license` (an SPDX id, or `public-domain`) with `license_url`, the
link to the license's legal text (the Public Domain Mark for public-domain rows). The dataset
as a whole has no single license, which is why its metadata says `other`.

| Configuration | Licenses (rows) | Rows |
|---|---|---|
{chr(10).join(lines)}

## What you must do
This is a summary, not legal advice. The license texts at each row's `license_url` govern.

- **CC BY 2.5, 3.0 and 4.0** (`by`): when you share an article or part of it, keep its
  `credit_line`: it names the creator (or the source), the source, the title, the link and the
  license. If you change the text, say so.
- **CC BY-SA 4.0** (`by-sa`): the same as CC BY, and anything you adapt from the text (a
  translation, an edited or shortened version) must be shared under CC BY-SA 4.0 too. Keeping
  the text unchanged inside a larger dataset does not make that dataset CC BY-SA.
- **Public domain** (`pd`): English Wikinews articles published before 2005-09-25, which
  Wikinews' own copyright page places in the public domain. Nothing is required; the credit
  line is kept as a courtesy. Public-domain status may differ outside the United States.
- **Always:** do not suggest that a newsroom or writer endorses your work, and when a later
  version drops an article (removed or taken down at its source), drop it from your copy too.

## Changes CommonsWire made
The words of each article are unchanged. Whitespace inside paragraphs is normalized,
paragraphs are separated by a blank line, and photos, captions, video, audio and embedded
posts are left out. Wikinews articles are converted from wiki markup to plain text by rule.

## CommonsWire's own files
The code ({REPO}), `sources.csv`, `index.csv`, `manifest.json`, the dataset card and this file
are CommonsWire's own work under the Apache License 2.0. The short quotes in `sources.csv` are
the publishers' words, quoted as evidence of their terms.
"""
