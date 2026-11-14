"""The dataset card (README.md) and LICENSES.md of a release, filled in from its numbers.

The words are fixed here and the numbers come from the release itself, so the card always
matches the files it describes, and the same rows give the same card.
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta

from commonswire.release import CONFIGURATIONS, Release, source_table
from commonswire.sources import Source, license_label

REPO = "https://github.com/obadaKraishan/commonswire"
ISSUE_FORM = f"{REPO}/issues/new?template=takedown.yml"
HF_ID = "obadakr/commonswire"
HF_URL = f"https://huggingface.co/datasets/{HF_ID}"
FLOW_DAYS = 90

CONFIG_TEXT = {
    "by": "Creative Commons Attribution (CC BY 2.5, 3.0 and 4.0)",
    "by-sa": "Creative Commons Attribution-ShareAlike (CC BY-SA 4.0)",
    "pd": "public domain",
}


def _n(x: int) -> str:
    return f"{x:,}"


def _size_category(n: int) -> str:
    for lo, hi, name in (
        (1_000, 10_000, "1K<n<10K"),
        (10_000, 100_000, "10K<n<100K"),
        (100_000, 1_000_000, "100K<n<1M"),
    ):
        if lo <= n < hi:
            return name
    return "n<1K" if n < 1_000 else "1M<n<10M"


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
        "held": sum(release.checks.held.values()),
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
    size = _size_category(int(f["rows"]))  # type: ignore[call-overload]
    held_note = (
        f"{_n(f['held'])} more rows are held back because the source asks for the author's name "
        "and the article's page names no author."
        if f["held"]
        else ""
    )
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
- **It is small going forward.** Over the last {FLOW_DAYS} days the sources published about
  {f["flow"]:.1f} new articles a day: {flows}. Fact-checks are most of that flow (about
  {fact_share}%).
- **Wikinews is a closed archive.** English Wikinews stopped publishing on 2026-05-04; its
  articles are the largest part of the back catalogue.
- **It is English only.**
- **It has no coded variables yet** (topic, frame, types of sources quoted, tone). They are
  planned for a later version.

## The sources
| Source | Kind | License | Rows | Published | Credit line template |
|---|---|---|---|---|---|
{src_lines}

`{{authors}}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source.
{held_note}

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
| `published_at`, `updated_at` | UTC, as the source gives them |
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
- **Bylines.** From the source's API; where the API gives none and the source asks for the
  author's name, from the byline on the article's own page, never from the body text.
- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped:
  {_n(f["exact_duplicates"])} in this version. Near-duplicates across sources are flagged in
  `near_duplicates`, not dropped: {_n(f["near_pairs"])} pairs in this version.
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
- The sources are a small, uneven set: two fact-checking sites in India, an open-access
  research newswire, a local newsroom in Hamilton (Canada), an outlet in Bosnia and
  Herzegovina, and a closed citizen-journalism wiki. Their mix of countries and topics is not
  that of mainstream news.
- Wikinews text is converted from wiki markup by rule; a few articles keep a stray bar,
  bracket or brace where the wikitext itself has a slip.
- Fact-check articles quote and describe social-media posts. The embedded posts are removed,
  but the quoted claims stay in the text.
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
