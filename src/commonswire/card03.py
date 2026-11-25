"""The dataset card (README.md) and LICENSES.md of series 0.3 on: many languages, editions.

Series 0.1 and 0.2 keep the card of :mod:`commonswire.release_text` byte for byte (their
weekly versions must give the same files); :func:`commonswire.release_text.card` hands a
series 0.3 version to :func:`card`. As there, the words are fixed here and every number comes
from the release itself, so the same rows give the same card.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from commonswire import citation
from commonswire.licensing import LICENSE_SCHEDULES, UNPLACED
from commonswire.lingua import ENGLISH_NOT_RELEASED, NO_ENGLISH, RULE_CODE
from commonswire.release import (
    CONFIGURATIONS,
    Release,
    columns,
    source_table,
)
from commonswire.release_text import (
    FLOW_DAYS,
    HELD_TEXT,
    HF_ID,
    ISSUE_FORM,
    SHORT_REASONS,
    SHORT_TEXT,
    _join,
    _n,
    _rows,
    _size_category,
    _wrap,
    config_text,
    facts,
    language_tags,
)
from commonswire.sources import PUBLIC_DOMAIN, Source, license_label
from commonswire.wikieditions import OWN_NOTICE

COMMUNITY = f"{citation.HF_URL}/discussions"
#: The English names of the row languages (BCP 47 tags as the rows give them).
LANGUAGE_NAMES = {
    "ar": "Arabic",
    "ay": "Aymara",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "fa": "Persian",
    "fil": "Filipino",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kk": "Kazakh",
    "km": "Khmer",
    "ko": "Korean",
    "ku": "Kurdish",
    "mg": "Malagasy",
    "mk": "Macedonian",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "or": "Odia",
    "pa": "Punjabi",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "te": "Telugu",
    "tet": "Tetum",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "zh": "Chinese",
    "zh-Hans": "Chinese (Simplified)",
    "zh-Hant": "Chinese (Traditional)",
}
#: What waits for a later version, in the card's words (each decided by the maintainer).
WAITING = (
    "**Global Voices in Spanish** waits until its republishing guidelines are read and the "
    "site can be collected by its public route alone.",
    "**Russian Wikinews** waits for its own download allowance (its dump is over 1 GB), and "
    "**Swedish Wikinews** for a way to tell its published articles apart (most pages carry no "
    "publication mark).",
)
#: How the publishers' kinds read in the card.
KIND_WORDS = {
    "news": "news",
    "fact-check": "fact-checks",
}
_LINGUA_SHORT = {
    NO_ENGLISH: "no English version found",
    ENGLISH_NOT_RELEASED: "English not released",
}


def _are(n: int) -> str:
    """'1 row is' or '12 rows are'."""
    return f"{_n(n)} row is" if n == 1 else f"{_n(n)} rows are"


def _many(n: int, word: str) -> str:
    """'1 language' or '50 languages'."""
    return f"{_n(n)} {word}" if n == 1 else f"{_n(n)} {word}s"


def _day(d: date) -> str:
    return d.isoformat()


def license_periods(source_id: str) -> list[tuple[str, str]]:
    """A Wikinews edition's licenses by date, in words: (period, license)."""
    sched = LICENSE_SCHEDULES.get(source_id, [])
    out = []
    for i, (first, lic) in enumerate(sched):
        nxt = sched[i + 1][0] if i + 1 < len(sched) else None
        if first == date.min:
            period = f"before {_day(nxt)}" if nxt else "every date"
        elif nxt:
            period = f"{_day(first)} to {_day(nxt - timedelta(days=1))}"
        else:
            period = f"from {_day(first)}"
        out.append((period, "held (not settled)" if lic == UNPLACED else license_label(lic)))
    return out


def _publisher(registry: dict[str, Source], s: str) -> str:
    return registry[s].edition_of or s


def pub_name(registry: dict[str, Source], p: str) -> str:
    """A publisher's name as the card writes it (its main site's name, without the language
    a registry name may carry: "Wikinews (English)" is "Wikinews")."""
    return registry[p].name.removesuffix(" (English)")


def _possessive(name: str) -> str:
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def _language_of(registry: dict[str, Source], s: str) -> str:
    lang = registry[s].languages[0] if registry[s].languages else ""
    return LANGUAGE_NAMES.get(lang, lang)


def _edition_label(registry: dict[str, Source], s: str) -> str:
    """A source as the card names it: its publisher, with the language of an edition
    ("Global Voices in French")."""
    src = registry[s]
    if not src.edition_of:
        return pub_name(registry, s)
    return f"{pub_name(registry, src.edition_of)} in {_language_of(registry, s)}"


def card(
    release: Release,
    registry: dict[str, Source],
    third_party: int,
    update: dict[str, object] | None = None,
    series_from: str | None = None,
) -> str:
    """The dataset card of a series 0.3 version (see :func:`commonswire.release_text.card`
    for ``update``); ``series_from`` is the version of the series before that it was built
    from (``release build-from``), named in the section on what changed."""
    f = facts(release, registry, third_party)
    rows = [r for config in release.rows.values() for r in config]
    total = int(f["rows"])  # type: ignore[call-overload]
    counts = release.counts()
    per_config = counts["rows_by_configuration"]
    by_license: dict[str, int] = counts["rows_by_license"]  # type: ignore[assignment]
    by_src: Counter[str] = f["rows_by_source"]  # type: ignore[assignment]
    langs: Counter[str] = f["languages"]  # type: ignore[assignment]
    table = {t["source_id"]: t for t in source_table(release, registry)}
    publishers: dict[str, list[str]] = defaultdict(list)
    for s in release.sources:
        publishers[_publisher(registry, s)].append(s)
    held_pairs: Counter[tuple[str, str]] = release.checks.held_pairs
    held_reasons: dict[str, int] = f["held_reasons"]  # type: ignore[assignment]
    english = langs.get("en", 0)
    as_of = str(f["as_of"])

    # --- The metadata block.
    configs_yaml = "\n".join(
        f"- config_name: {c}\n  data_files:\n  - split: train\n"
        f'    path: "data/{c}/*.parquet"' + ("\n  default: true" if c == "by" else "")
        for c in CONFIGURATIONS
    )
    language_yaml = "\n".join(f"- {t}" for t in language_tags(langs))

    # --- What it is.
    pub_rows = {p: sum(by_src.get(s, 0) for s in ss) for p, ss in publishers.items()}
    largest = max(pub_rows, key=lambda p: (pub_rows[p], p))
    share = pub_rows[largest] / total if total else 0.0
    largest_line = ""
    if share >= 0.4:
        sites = len(publishers[largest])
        largest_line = _wrap(
            f"- **{pub_name(registry, largest)} is "
            + ("most of it" if share > 0.5 else "the largest part of it")
            + f"** ({_n(pub_rows[largest])} of {_n(total)} rows, {round(100 * share)}%, from "
            f"{_n(sites)} {'site' if sites == 1 else 'sites'}): results over the whole corpus "
            + ("mostly describe it." if share > 0.5 else "lean on it.")
        )
    recent: Counter[str] = Counter()
    since = max(r["retrieved_at"] for r in rows) - timedelta(days=FLOW_DAYS)
    for r in rows:
        if r["published_at"] >= since:
            recent[_publisher(registry, r["source_id"])] += 1
    flows = ", ".join(
        f"{pub_name(registry, p)} {recent[p] / FLOW_DAYS:.1f}"
        for p in sorted(publishers, key=lambda p: (-recent[p], p))
        if recent[p]
    )
    flow_line = _wrap(
        f"- **It is small going forward.** Over the last {FLOW_DAYS} days its publishers put out "
        f"about {sum(recent.values()) / FLOW_DAYS:.1f} new articles a day, every language "
        f"together: {flows}."
    )
    if len(langs) > 1:
        language_line = _wrap(
            f"- **It is mostly English.** {_n(english)} of {_n(total)} rows "
            f"({round(100 * english / total) if total else 0}%) are in English; the others are "
            f"in {_many(len(langs) - 1, 'more language')}, most of them Global Voices' own "
            "translations (see Languages)."
        )
    else:
        only = next(iter(langs), "")
        language_line = f"- **It is all in {LANGUAGE_NAMES.get(only, only)}.**"
    wikinews = [s for s in release.sources if s.startswith("wikinews_")]
    wikinews_line = (
        _wrap(
            f"- **Wikinews is a closed archive.** Its {_n(len(wikinews))} editions here stopped "
            "publishing on 2026-05-04; their rows come from the Wikimedia dumps."
        )
        if wikinews
        else ""
    )

    # --- This update, and what changed since the series before.
    update_section = _update_section(release, update)
    changes = _changes_section(
        release, registry, f, series_from, held_pairs, by_src, publishers, rows
    )

    # --- The publishers and the sources.
    pub_lines = []
    for p in sorted(publishers, key=lambda p: (-pub_rows[p], p)):
        ss = publishers[p]
        lic = Counter()
        firsts, lasts = [], []
        for s in ss:
            for k, v in table[s]["licenses"].items():  # type: ignore[union-attr]
                lic[k] += v
            if table[s]["first"]:
                firsts.append(table[s]["first"])
                lasts.append(table[s]["last"])
        languages = sorted({x for s in ss for x in registry[s].languages[:1]})
        pub_lines.append(
            f"| {pub_name(registry, p)} | {registry[p].kind} | {_n(len(ss))} | "
            f"{', '.join(f'`{x}`' for x in languages)} | "
            + "; ".join(f"{k} ({_n(v)})" for k, v in sorted(lic.items()))
            + f" | {_n(pub_rows[p])} | {min(firsts, default='')} to {max(lasts, default='')} |"
        )
    src_lines = "\n".join(
        f"| `{s}` | {_edition_label(registry, s)} | {_n(table[s]['rows'])} | "  # type: ignore[arg-type]
        f"{table[s]['first'][:4]} to {table[s]['last'][:4]} | `{table[s]['credit_template']}` |"  # type: ignore[index]
        for s in release.sources
    )

    # --- Languages.
    lang_lines = "\n".join(
        f"| `{t}` | {LANGUAGE_NAMES.get(t, t)} | {_n(n)} |"
        for t, n in sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))
    )

    # --- Licenses.
    config_lines = "\n".join(
        f"| `{c}` | {config_text(c, release.rows[c])} | {_n(per_config[c])} |"
        for c in CONFIGURATIONS
    )
    license_lines = "\n".join(
        f"| {license_label(k)} | `{k}` | {_n(v)} |" for k, v in sorted(by_license.items())
    )
    by_versions = sorted(
        {license_label(k).removeprefix("CC BY ") for k in by_license if k.startswith("CC-BY-")}
        - {license_label(k).removeprefix("CC BY ") for k in by_license if k.startswith("CC-BY-SA-")}
    )

    # --- The rules.
    rules = _rules_section(release, registry, held_pairs, held_reasons, by_src)

    # --- Limitations: short texts.
    short_lines = ""
    for s in release.sources:
        n, tot = f["short_by_source"].get(s, 0), by_src.get(s, 0)  # type: ignore[union-attr]
        if tot >= 1000 and n / tot >= 0.1:
            short_lines += (
                _wrap(
                    f"- {round(100 * n / tot)}% of the {_edition_label(registry, s)} rows "
                    f"({_n(n)}) have fewer than {SHORT_TEXT} characters of text"
                    + (f": {SHORT_REASONS[s]}" if s in SHORT_REASONS else "")
                    + "; the median row "
                    f"has {f['median_words'][s]} words. Filter by length if you need full "  # type: ignore[index]
                    "stories."
                )
                + "\n"
            )
    variables = ", ".join(f"`{c}`" for c in columns(release.version)[19:])
    withheld = sum(held_reasons.values())
    pairs_word = "pair" if f["near_pairs"] == 1 else "pairs"
    copies = sum(release.checks.copies.values())
    words = int(f["words"]) / 1e6  # type: ignore[call-overload]
    lang_count = _n(len(langs))
    intro = _wrap(
        f"Version {release.version} holds {_n(total)} articles ({words:.1f} million words) in "
        f"{_many(len(langs), 'language')}, from {_many(len(publishers), 'publisher')} "
        f"({_many(len(release.sources), 'source')}: their main sites and their language "
        "editions), "
        f"published from {f['first']} to {f['last']} and collected up to {as_of}."
    )
    license_bullet = _wrap(
        "- **License:** each article keeps its publisher's license ("
        + _join(
            [license_label(k).replace("Public domain", "public domain") for k in sorted(by_license)]
        )
        + "), on its row; see `LICENSES.md`."
    )
    variables_bullet = _wrap(
        "- **It has no coded variables yet** (topic, frame, types of sources quoted, tone); they "
        "are planned for a later version. It has variables that need no model: the publisher's "
        "own section, categories and tags, the body's links and the hosts they lead to, and an "
        f"article's other-language versions ({variables})."
    )
    by_bullet = _wrap(
        "- **CC BY** (`by`; versions " + _join(by_versions) + "): keep each article's "
        "`credit_line` with it. It names the creator and the source, the title, the link and the "
        "license. Say if you changed the text."
    )
    held_line = _wrap(
        f"{_are(withheld)} held back and not released, each for one reason (counted in "
        "`manifest.json`, `held_rows_by_reason`, with their ids, sources and days in `held_rows`)."
    )
    third = int(f["third_party"])  # type: ignore[call-overload]
    third_bullet = _wrap(
        "- **Third-party material is left out.** Wire copy, partner stories, syndicated pieces, "
        "posts under someone else's rights and copies of another source's articles are dropped; "
        f"{_n(third)} were dropped in this version"
        + (f", {_n(copies)} of them copies (see the rules above)." if copies else ".")
    )
    exact, near = int(f["exact_duplicates"]), int(f["near_pairs"])  # type: ignore[call-overload]
    dups_bullet = _wrap(
        f"- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped: "
        f"{_n(exact)} in this version. Near-duplicates across sources are flagged in "
        f"`near_duplicates`, not dropped: {_n(near)} {pairs_word} in this version."
    )
    by_size = sorted(publishers, key=lambda p: (-pub_rows[p], p))
    mix_bullet = _wrap(
        "- The publishers are a small, uneven set: "
        + _join([f"{pub_name(registry, p)} ({registry[p].kind})" for p in by_size])
        + ". Their mix of countries and topics is not that of mainstream news."
    )
    bylined = int(f["with_byline"])  # type: ignore[call-overload]
    authors_bullet = _wrap(
        f"- `authors` is filled for {_n(bylined)} of {_n(total)} rows. Wikinews articles carry "
        "no bylines, and some articles are credited to the source itself."
    )
    largest_block = largest_line + "\n" if largest_line else ""
    wikinews_block = wikinews_line + "\n" if wikinews_line else ""
    pub_table = "\n".join(pub_lines)
    cite_apa = _wrap(citation.apa(release.version))
    cite_bib = citation.bibtex(release.version)
    cite_doi = _wrap(citation.software_sentence())
    cite_credit = _wrap(citation.credit_request())

    return f"""---
pretty_name: CommonsWire
language:
{language_yaml}
license: other
license_name: per-row-open-licenses
license_link: https://huggingface.co/datasets/obadakr/commonswire/blob/main/LICENSES.md
tags:
- news
- journalism
- multilingual
- creative-commons
- communication-research
size_categories:
- {_size_category(total)}
configs:
{configs_yaml}
---

# CommonsWire {release.version}

CommonsWire is a full-text corpus of news articles whose publishers allow their text to be
shared again. Each row is one article: its body text as published, its metadata, its license,
and the credit line its publisher asks for.

{intro}

- **Curated by:** Obada Kraishan, College of Media and Communication, Texas Tech University
  ({citation.ORCID}).
{license_bullet}
- **Mirror:** the same files on Kaggle, {citation.KAGGLE_URL}
- **Code and source registry:** {citation.REPO} (Apache-2.0).
- **How to cite:** see "How to cite" at the end.

CommonsWire is not affiliated with, endorsed by or sponsored by any of the newsrooms whose
articles it holds.

## What it is, and what it is not
- **It is** each publisher's own articles, as far as its API, its pages or its dump give them,
  with every article's license on its row. More sources join in later versions.
- **It is not every news outlet.** Most newsrooms do not allow their text to be shared again,
  and they are not here. Results from CommonsWire describe these publishers, not "the news".
{flow_line}
{largest_block}{language_line}
{wikinews_block}{variables_bullet}
{update_section}{changes}
## The publishers
| Publisher | Kind | Sources | Languages | Licenses (rows) | Rows | Published |
|---|---|---|---|---|---|---|
{pub_table}

Every source in the registry (included, pending and excluded), with the pages read and the
words quoted as evidence, is in `sources.csv`. Each source of this version, with the credit
line its rows carry:

| Source | Name | Rows | Years | Credit line template |
|---|---|---|---|---|
{src_lines}

`{{authors}}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source. When the source
names translators, `{{authors}}` is followed by ", translated by" and their names; the writers
stay in `authors`, and the translators are in `translators`.

## Languages
`language` is the article's language: its edition's, or the publisher's own label where one
site publishes in several (Factly's Telugu stories are `te`).

| Tag | Language | Rows |
|---|---|---|
{lang_lines}

## Configurations and licenses
Each row carries its own `license`, `license_url` and `credit_line`. The rows are split into
one configuration per license class, so you can load only what your use allows:

| Configuration | Licenses | Rows |
|---|---|---|
{config_lines}

| License | `license` | Rows |
|---|---|---|
{license_lines}

```python
from datasets import load_dataset

by = load_dataset("{HF_ID}", "by", split="train")  # CC BY
by_sa = load_dataset("{HF_ID}", "by-sa", split="train")  # CC BY-SA
pd = load_dataset("{HF_ID}", "pd", split="train")  # public domain
```

**What you must do** (this is a summary, not legal advice; `LICENSES.md` has more):
{by_bullet}
- **CC BY-SA** (`by-sa`): the same, and share anything you adapt from these texts (a
  translation, an edited version) under CC BY-SA.
- **Public domain** (`pd`): nothing is required. The credit line is kept as a courtesy.
  Public-domain status under US law may not hold in every country.
- In every case, do not suggest that a newsroom endorses your work, and drop articles that a
  later version marks as removed or withdrawn.

## The rights rules of this version
{held_line}

{rules}
## Fields
| Field | Meaning |
|---|---|
| `id` | `cw_` and 16 hex digits of the SHA-256 of the canonical URL; stable across versions |
| `source_id`, `kind` | the source, as in `sources.csv`, and its kind (`news`, `fact-check`) |
| `title` | the headline as published |
| `authors` | the bylines as published (empty when the article names no person) |
| `translators` | the translators the source names, apart from the writers (often empty) |
| `published_at`, `updated_at` | UTC, as the source gives them |
| `retrieved_at` | UTC, when CommonsWire fetched the article |
| `language` | the article's language, a BCP 47 tag ({lang_count} in this version) |
| `section` | the source's own section or category, if any |
| `url` | the article at its source |
| `license`, `license_url` | the article's license and a link to its legal text |
| `credit_line` | the attribution to keep with the text |
| `text` | the body text, words unchanged; paragraphs separated by a blank line |
| `content_hash` | SHA-256 of `text`, to spot changed articles between versions |
| `status` | `live`, or `changed` if the source edited the text after it was first collected |
| `near_duplicates` | ids of very similar articles in other sources (5-gram Jaccard 0.6 or more) |
| `publisher_section` | the section label as the publisher printed it, if any |
| `publisher_categories`, `publisher_tags` | the publisher's own categories and tags, as written |
| `n_links`, `n_links_external` | the body's links to web pages, and those to other sites |
| `link_hosts` | the hosts the body links to, each once, without `www.` |
| `original_url` | for a translation, the version it was made from, where the publisher says so |
| `other_versions` | the article's versions in other languages, as the publisher links them |

`index.csv` lists every row's id, source, configuration, URL, license, content hash and
publication time, without text. `changes.csv` records, for every article and version since
0.1.0, when it was new, changed, removed, taken down or withdrawn (ids and dates only).
`manifest.json` gives the row counts and the size and SHA-256 of every file.

## How it was collected
- **Rights first.** A source enters only when its own pages give a license or public-domain
  statement that allows sharing the full text unchanged, do not forbid bulk or automatic
  reuse, and do not forbid automated collection, and when its own articles can be told apart
  from material it republishes. The evidence (page, date, exact words) is in `sources.csv`.
{third_bullet}
- **Text unchanged.** The body text comes from each source's API, its article pages, or (for
  Wikinews) the Wikimedia dumps, with the markup removed by rule. Only whitespace inside
  paragraphs is normalized. Photos, captions, video, audio and embedded posts are not
  collected; they are often separate works the source does not license.
- **Bylines.** From the source's API; where the API gives none and the source asks for the
  author's name, from the byline on the article's own page or in the source's own story
  listing, never from the body text.
{dups_bullet}
- **Politely.** One request at a time, at least 2 seconds apart, robots.txt and crawl-delays
  honored, and a user agent that names the project. Blocks are never worked around.

## Removals and corrections
- **At the source.** Each update asks every source that still publishes for the articles it
  published or edited in the last 30 days. An article edited at its source, however old, gets
  its new text and status `changed` in the next version; an article of the last 30 days that
  was removed at its source is dropped from the next version. For older articles, each update
  compares every WordPress source's post count per year (a language site's total) with the
  counts of the version before; where a count fell, it lists that year's posts and drops each
  article whose page is gone. A removal offset by a back-dated post in the same range is
  missed. The two sources read from their article pages are checked through their sitemaps
  or listings instead.
- **On request.** Publishers, writers and people named in an article can ask for a removal or a
  correction with the [takedown and correction form]({ISSUE_FORM}). Requests are answered
  within 14 days. An article taken down goes on a list of ids (`data/takedowns.csv` in the
  code repository, with no URL or name) and is left out of every later version.
- **Your copy.** If you keep a copy of CommonsWire, please apply removals to it too:
  `index.csv` of the latest version lists every article still in it, and `changes.csv` says
  when each one left.

## Limitations
{mix_bullet}
{short_lines}- Global Voices' language sites are translations of its English stories: the same
  story is often in the corpus in several languages (`other_versions` links them). Count
  stories, not rows, when that matters.
- Wikinews text is converted from wiki markup by rule; a few articles keep a stray bar,
  bracket or brace where the wikitext itself has a slip.
- Fact-check articles and Global Voices stories quote and describe posts from social media and
  blogs. The embedded posts are removed, but the quoted words stay in the text.
{authors_bullet}
- News articles name people. CommonsWire adds nothing to what was published, infers nothing
  about anyone (no gender, ethnicity or other attribute), and offers no search by person.

## Contact
- **Questions and errors:** the [issue tracker]({citation.REPO}/issues).
- **Removals and corrections:** the [takedown and correction form]({ISSUE_FORM}).
- Both forms need a free GitHub account. Without one, open a discussion on this dataset's
  [Community tab]({COMMUNITY}) (a free Hugging Face account).

## How to cite
Please cite the version you used:

{cite_apa}

```bibtex
{cite_bib}
```

{cite_doi}

{cite_credit}

Version {release.version}, collected up to {as_of}. Code: {citation.REPO} (Apache-2.0).
"""


def _update_section(release: Release, update: dict[str, object] | None) -> str:
    if not update:
        return ""
    new = int(update["new"])  # type: ignore[call-overload]
    counted = update.get("count_check")
    count_text = ""
    if isinstance(counted, dict) and counted.get("baseline"):
        count_text = (
            " This version is the first to record each source's post counts, so the next "
            "update can check older articles for removals."
        )
    elif isinstance(counted, dict):
        drops, gone = int(counted["drops"]), int(counted["rows_removed"])
        count_text = (
            f" The post counts of {_n(int(counted['sources']))} sources were compared with "
            f"{update['from_version']}'s ({_n(int(counted['years_checked']))} years, and each "
            f"language site's total, recorded for the first time where it had none): "
            f"{_n(drops)} fell, and {_n(gone)} older "
            f"{'article was' if gone == 1 else 'articles were'} found removed (counted above)."
        )
    versions = update.get("versions_added")
    version_text = (
        f" {_n(int(versions))} rows gained an other-language version."  # type: ignore[call-overload]
        if versions
        else ""
    )
    return (
        "\n## This update\n"
        + _wrap(
            f"Version {release.version} updates {update['from_version']} with what the sources "
            f"published, edited or removed in the {update['window_days']} days up to "
            f"{update['as_of']}: {_n(new)} new {'row' if new == 1 else 'rows'}, "
            f"{_n(int(update['changed']))} changed, {_n(int(update['removed']))} removed at "  # type: ignore[call-overload]
            f"their source, and {_n(int(update['taken_down']))} taken down on request."  # type: ignore[call-overload]
            + version_text
            + count_text
        )
        + "\n"
    )


def _changes_section(
    release: Release,
    registry: dict[str, Source],
    f: dict[str, object],
    series_from: str | None,
    held_pairs: Counter[tuple[str, str]],
    by_src: Counter[str],
    publishers: dict[str, list[str]],
    rows: list[dict],
) -> str:
    if not series_from:
        return ""
    from commonswire.release import series_sources

    try:
        before = set(series_sources(series_from))
    except ValueError:
        before = set()
    new_main = [s for s in release.sources if s not in before and not registry[s].edition_of]
    new_editions = [s for s in release.sources if s not in before and registry[s].edition_of]
    lines = []
    for s in new_main:
        lines.append(
            f"- **A new source: {registry[s].name}** ({_rows(by_src.get(s, 0))}), "
            f"{registry[s].kind}, read from its article pages."
        )
    groups: dict[str, list[str]] = defaultdict(list)
    for s in new_editions:
        groups[registry[s].edition_of].append(s)
    for p, ss in sorted(groups.items(), key=lambda kv: -sum(by_src.get(s, 0) for s in kv[1])):
        rule = (
            " under the Lingua rule (below)"
            if any(registry[s].reason_code == RULE_CODE for s in ss)
            else " with their licenses by date (below)"
            if p.startswith("wikinews")
            else ""
        )
        word = "site" if p == "globalvoices" else "edition"
        which = f", in {_join([_language_of(registry, s) for s in ss])}" if len(ss) <= 6 else ""
        lines.append(
            f"- **{_possessive(pub_name(registry, p))} language "
            f"{'edition' if len(ss) == 1 else 'editions'}:** "
            f"{_n(len(ss))} {word if len(ss) == 1 else word + 's'}{which} "
            f"({_rows(sum(by_src.get(s, 0) for s in ss))}){rule}."
        )
    lines.append(
        "- **New columns:** `publisher_section`, `publisher_categories`, `publisher_tags`, "
        "`n_links`, `n_links_external`, `link_hosts`, `original_url` and `other_versions`, after "
        "`near_duplicates`; and a new file, `changes.csv`."
    )
    te = sum(1 for r in rows if r["source_id"] == "factly" and r["language"] == "te")
    if te:
        lines.append(
            f"- **Factly's Telugu stories are labelled `te`:** {_n(te)} rows were labelled `en` "
            f"in 0.1.0 to {series_from}; their text is unchanged."
        )
    withdrawn = sum(
        n for (s, r), n in held_pairs.items() if s in before and r.startswith(OWN_NOTICE)
    )
    if withdrawn:
        lines.append(
            f"- **{_n(withdrawn)} rows of {series_from} are withdrawn:** English Wikinews pages "
            "whose own license or copyright notice differs from their date's license (the rule "
            "below). Their ids are in `changes.csv` as `withdrawn`; drop them from your copy."
        )
    for s, n in sorted(release.checks.copies.items()):
        if n and s not in before:
            lines.append(
                f"- **{_n(n)} rows of {_edition_label(registry, s)} are left out as copies** of "
                "another source's rows (the rule below)."
            )
    lines.append(
        f"- **Near-duplicates across sources:** {_n(int(f['near_pairs']))} pairs in this version."  # type: ignore[call-overload]
    )
    lines.append(
        "- **The count check covers the language sites:** each update compares a site's total "
        "post count with the version before's (the first update records it)."
    )
    return f"\n## Changes since {series_from}\n" + "\n".join(_wrap(x) for x in lines) + "\n"


def _rules_section(
    release: Release,
    registry: dict[str, Source],
    held_pairs: Counter[tuple[str, str]],
    held_reasons: dict[str, int],
    by_src: Counter[str],
) -> str:
    out = []
    # The bylines.
    named = {k: v for k, v in held_reasons.items() if k in HELD_TEXT}
    if named:
        out.append(
            "### Bylines\n"
            + _wrap(
                f"{_are(sum(named.values()))} held back because the source asks for the "
                "author's name: "
                + "; ".join(
                    f"{_n(v)} {HELD_TEXT[k]}"
                    for k, v in sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))
                )
                + "."
            )
        )
    # The Lingua rule.
    ruled = [s for s in release.sources if registry[s].reason_code == RULE_CODE]
    if ruled:
        held_rule = {k: v for k, v in held_reasons.items() if k in _LINGUA_SHORT}
        site_lines = "\n".join(
            f"| `{s}` | {_language_of(registry, s)} | {_n(by_src.get(s, 0))} | "
            f"{_n(held_pairs.get((s, NO_ENGLISH), 0))} | "
            f"{_n(held_pairs.get((s, ENGLISH_NOT_RELEASED), 0))} |"
            for s in sorted(ruled, key=lambda s: (-by_src.get(s, 0), s))
        )
        out.append(
            "### Global Voices' language sites: the Lingua rule\n"
            + _wrap(
                f"A row of one of Global Voices' {_n(len(ruled))} language sites is released only "
                "when its English version is a released row of this dataset: the English pages "
                "are where Global Voices' own stories are told apart from the partner pieces it "
                "republishes. The link to the English version comes from the article's own "
                "links and images matched against the English bodies, or from its page. "
                f"{_are(sum(held_rule.values()))} held by the rule: "
                f"{_n(held_rule.get(NO_ENGLISH, 0))} with no English version found, and "
                f"{_n(held_rule.get(ENGLISH_NOT_RELEASED, 0))} whose English version is held or "
                "left out."
            )
            + "\n\n| Site | Language | Released | Held: no English version found | Held: "
            "English not released |\n|---|---|---|---|---|\n" + site_lines
        )
    # Wikinews.
    wiki = [s for s in release.sources if s.startswith("wikinews_")]
    if wiki:
        lines = []
        for s in wiki:
            periods = "; ".join(f"{p}: {lic}" for p, lic in license_periods(s))
            unplaced = sum(
                n for (x, r), n in held_pairs.items() if x == s and r.startswith("license date")
            )
            notice = sum(
                n for (x, r), n in held_pairs.items() if x == s and r.startswith(OWN_NOTICE)
            )
            lines.append(
                f"| {_edition_label(registry, s)} | {periods} | {_n(by_src.get(s, 0))} | "
                f"{_n(unplaced)} | {_n(notice)} |"
            )
        kinds = Counter()
        for (x, r), n in held_pairs.items():
            if x in wiki and r.startswith(OWN_NOTICE):
                k = r[len(OWN_NOTICE) :].strip(" ()")
                kinds[k or "other"] += n
        order = ("another license", "public domain", "a third party's copyright", "other")
        kind_text = ", ".join(f"{_n(kinds[k])} {k}" for k in order if kinds.get(k))
        out.append(
            "### Wikinews: licenses by date, and each page's own notice\n"
            + _wrap(
                "Each Wikinews edition's copyright page gives its license by date, so a row takes "
                "the license of its date (for an edition, its page's creation date). A date the "
                "page does not settle is held. A page that carries a license or copyright notice "
                "of its own that differs from its date's license is held too"
                + (f" (by the kind of notice: {kind_text})" if kind_text else "")
                + "."
            )
            + "\n\n| Edition | Licenses by date | Released | Held: date not settled | Held: own "
            "notice |\n|---|---|---|---|---|\n" + "\n".join(lines)
        )
    copies = {s: n for s, n in release.checks.copies.items() if n}
    if copies:
        from commonswire import release as release_module

        parts = []
        for s, n in sorted(copies.items()):
            twin = release_module.REPUBLISHED_COPIES.get(s, "")
            parts.append(
                f"{_n(n)} rows of {_edition_label(registry, s)} are near-copies of rows of "
                f"{_edition_label(registry, twin) if twin in registry else 'another source'}"
            )
        out.append(
            "### Copies of another source's articles\n"
            + _wrap(
                _join(parts)
                + " (Jaccard 0.6 or more): the source republished them, so its copies are left "
                "out as third-party material, and the originals follow their own rules."
            )
        )
    out.append(
        "### What waits for a later version\n"
        + "\n".join(_wrap(f"- {x}") for x in WAITING)
        + "\n"
        + _wrap(
            "- Every edition still pending in the registry (`sources.csv`, status `pending`) waits "
            "for an answer on its own terms."
        )
    )
    return "\n\n".join(out) + "\n"


def licenses_md(release: Release, registry: dict[str, Source]) -> str:
    """LICENSES.md of a series 0.3 version: the licenses it holds and what users must do."""
    counts = release.counts()
    by_license: dict[str, int] = counts["rows_by_license"]  # type: ignore[assignment]
    lines = []
    for c in CONFIGURATIONS:
        lic = Counter(r["license"] for r in release.rows[c])
        names = ", ".join(f"{license_label(k)} ({v:,})" for k, v in sorted(lic.items()))
        lines.append(f"| `{c}` | {names or 'none'} | {counts['rows_by_configuration'][c]:,} |")
    by = [
        license_label(k)
        for k in sorted(by_license)
        if k.startswith("CC-BY-") and not k.startswith("CC-BY-SA-")
    ]
    by_sa = [license_label(k) for k in sorted(by_license) if k.startswith("CC-BY-SA-")]
    pd_sources = sorted(
        {r["source_id"] for r in release.rows["pd"]},
        key=lambda s: (-sum(1 for r in release.rows["pd"] if r["source_id"] == s), s),
    )
    pd_words = []
    for s in pd_sources:
        sched = LICENSE_SCHEDULES.get(s, [])
        ends = [sched[i + 1][0] for i, (_, lic) in enumerate(sched[:-1]) if lic == PUBLIC_DOMAIN]
        when = f" published before {ends[0].isoformat()}" if ends else ""
        pd_words.append(f"{_edition_label(registry, s)} articles{when}")
    pd_text = (
        _join(pd_words) + ", which their editions' own copyright pages place in the public domain"
        if pd_words
        else "none in this version"
    )
    by_bullet = _wrap(
        f"- **{_join(by)}** (`by`): when you share an article or part of it, keep its "
        "`credit_line`: it names the creator (or the source), the source, the title, the "
        "link and the license. If you change the text, say so."
    )
    by_sa_bullet = _wrap(
        f"- **{_join(by_sa) or 'CC BY-SA'}** (`by-sa`): the same as CC BY, and anything you "
        "adapt from the text (a translation, an edited or shortened version) must be shared "
        "under the same license too. Keeping the text unchanged inside a larger dataset does "
        "not make that dataset CC BY-SA."
    )
    pd_bullet = _wrap(
        f"- **Public domain** (`pd`): {pd_text}. Nothing is required; the credit line is kept "
        "as a courtesy. Public-domain status may differ outside the United States."
    )
    table = "\n".join(lines)
    return f"""# Licenses in CommonsWire {release.version}

CommonsWire does not relicense anyone's writing. Every article keeps its publisher's license,
recorded on its row as `license` (an SPDX id, or `public-domain`) with `license_url`, the
link to the license's legal text (the Public Domain Mark for public-domain rows). The dataset
as a whole has no single license, which is why its metadata says `other`.

| Configuration | Licenses (rows) | Rows |
|---|---|---|
{table}

## What you must do
This is a summary, not legal advice. The license texts at each row's `license_url` govern.

{by_bullet}
{by_sa_bullet}
{pd_bullet}
- **Always:** do not suggest that a newsroom or writer endorses your work, and when a later
  version drops an article (removed or taken down at its source, or withdrawn), drop it from
  your copy too.

## Changes CommonsWire made
The words of each article are unchanged. Whitespace inside paragraphs is normalized,
paragraphs are separated by a blank line, and photos, captions, video, audio and embedded
posts are left out. Wikinews articles are converted from wiki markup to plain text by rule.

## CommonsWire's own files
The code ({citation.REPO}), `sources.csv`, `index.csv`, `changes.csv`, `manifest.json`, the
dataset card and this file are CommonsWire's own work under the Apache License 2.0. The short
quotes in `sources.csv` are the publishers' words, quoted as evidence of their terms.
"""
