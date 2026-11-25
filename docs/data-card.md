# Data card: CommonsWire 0.2.0

This is the text of the dataset card of version 0.2.0, as `commonswire release build --version
0.2.0` writes it (`data/release/<version>/README.md`, the card on Hugging Face). Version 0.2.0
was published on 2026-11-14 (tag `v0.2.0`); the card of version 0.1.0 stays under the tag
`v0.1.0`. The weekly versions after it (0.2.1, 0.2.2, ...) have the same card with their own
counts and a section "This update"; the current one is on Hugging Face. The paragraph on
removals at the source (under "Removals and corrections") is given below as the card has it
from the version after 0.2.2, when the count check of older articles was added; 0.2.0's card
said that older articles were not checked again yet. Version 0.2.0's metadata block, which Hugging Face reads for the license and the configurations,
is:

```yaml
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
- 100K<n<1M
configs:
- config_name: by
  data_files:
  - split: train
    path: "data/by/*.parquet"
  default: true
- config_name: by-sa
  data_files:
  - split: train
    path: "data/by-sa/*.parquet"
- config_name: pd
  data_files:
  - split: train
    path: "data/pd/*.parquet"
```

---

# CommonsWire 0.2.0

CommonsWire is a full-text corpus of news articles whose publishers allow their text to be
shared again. Each row is one article: its body text as published, its metadata, its license,
and the credit line its publisher asks for.

Version 0.2.0 holds 149,147 articles (55.2 million words)
from 7 sources, published from 2004-10-27 to 2026-11-13 and collected
up to 2026-11-14.

- **Curated by:** Obada Kraishan, College of Media and Communication, Texas Tech University.
- **License:** each article keeps its publisher's license (public domain, CC BY or CC BY-SA),
  on its row; see `LICENSES.md`.
- **Contact:** the [issue tracker](https://github.com/obadaKraishan/commonswire/issues).

CommonsWire is not affiliated with, endorsed by or sponsored by any of the newsrooms whose
articles it holds.

## What it is, and what it is not
- **It is** each source's own articles, as far as its API or dump gives them, with every
  article's license on its row. More sources join in later versions.
- **It is not every news outlet.** Most newsrooms do not allow their text to be shared again,
  and they are not here. Results from CommonsWire describe these sources, not "the news".
- **It is small going forward.** Over the last 90 days the sources published about 6.2 new
  articles a day: 360info 0.5, The Public Record 0.5, Balkan Diskurs 0.2, Factly 2.3, Alt News
  1.2, Global Voices 1.4. Fact-checks are most of that flow (about 56%).
- **Global Voices is most of it** (101,562 of 149,147 rows, 68%): results over the whole corpus
  mostly describe it.
- **Wikinews is a closed archive.** English Wikinews stopped publishing on 2026-05-04.
- **It is English only.**
- **It has no coded variables yet** (topic, frame, types of sources quoted, tone). They are
  planned for a later version.

## Changes since 0.1.0
- **A new source: Global Voices** (101,562 rows, CC BY 3.0, 2004 to 2026), an international
  citizen-media newsroom; its writers' names come from its own story listing, which names every
  writer of a story, and its translators apart.
- **A new field, `translators`:** the translators the source names, apart from the writers in
  `authors` (4,962 rows); the credit line names them ("..., by A, translated by B, ...").
- **Rows credited only to an account are held back** (264): an account such as "Guest
  Contributor" names no person.
- **Near-duplicates across sources:** 1 pair in this version.

## The sources
| Source | Kind | License | Rows | Published | Credit line template |
|---|---|---|---|---|---|
| Wikinews (English) | news | CC BY 2.5 (18,466); CC BY 4.0 (231); Public domain (1,954) | 20,651 | 2004-11-13 to 2026-05-03 | `{title}, Wikinews ({url}), {license}` |
| 360info | news | CC BY 4.0 | 2,400 | 2021-11-22 to 2026-11-12 | `{title}, written by {authors}. Originally published under Creative Commons by {source} ({url}), {license}` |
| The Public Record | news | CC BY-SA 4.0 | 2,749 | 2013-06-28 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |
| Balkan Diskurs | news | CC BY 3.0 | 879 | 2014-06-04 to 2026-11-13 | `{title}, by {authors}, originally published by {source} ({url}), {license}` |
| Factly | fact-check | CC BY 4.0 | 15,103 | 2014-12-14 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |
| Alt News | fact-check | CC BY 3.0 | 5,803 | 2016-04-10 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |
| Global Voices | news | CC BY 3.0 | 101,562 | 2004-10-27 to 2026-11-13 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |

`{authors}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source.
When the source names translators (Global Voices, for 4,962 rows), `{authors}` is followed by
", translated by" and their names; the writers stay in `authors`, and the translators are in
`translators`.
275 more rows are held back because the source asks for the author's name: 264 are credited
only to an account such as "Guest Contributor", which names no person; 11 name no author on the
article's page or in the source's story listing.

Every source in the registry (included, pending and excluded), with the pages read and the
words quoted as evidence, is in `sources.csv`.

## Configurations and licenses
Each row carries its own `license`, `license_url` and `credit_line`. The rows are split into
one configuration per license class, so you can load only what your use allows:

| Configuration | Licenses | Rows |
|---|---|---|
| `by` | Creative Commons Attribution (CC BY 2.5, 3.0 and 4.0) | 144,444 |
| `by-sa` | Creative Commons Attribution-ShareAlike (CC BY-SA 4.0) | 2,749 |
| `pd` | public domain | 1,954 |

```python
from datasets import load_dataset

by = load_dataset("obadakr/commonswire", "by", split="train")  # CC BY
by_sa = load_dataset("obadakr/commonswire", "by-sa", split="train")  # CC BY-SA
pd = load_dataset("obadakr/commonswire", "pd", split="train")  # public domain
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
| `translators` | the translators the source names, apart from the writers (empty when it names none) |
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
  under someone else's rights are dropped; 2,476 were dropped in this version.
- **Text unchanged.** The body text comes from each source's API (Wikinews: from the
  Wikimedia dump, with the wiki markup removed by rule). Only whitespace inside paragraphs is
  normalized. Photos, captions, video, audio and embedded posts are not collected; they are
  often separate works the source does not license.
- **Bylines.** From the source's API; where the API gives none and the source asks for the
  author's name, from the byline on the article's own page or in the source's own story listing
  (Global Voices), never from the body text.
- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped:
  107 in this version. Near-duplicates across sources are flagged in
  `near_duplicates`, not dropped: 1 pair in this version.
- **Politely.** One request at a time, at least 2 seconds apart, robots.txt and crawl-delays
  honored, and a user agent that names the project. Blocks are never worked around.

## Removals and corrections
- **At the source.** Each update asks every source that still publishes for the articles it
  published or edited in the last 30 days. An article edited at its source, however old, gets
  its new text and status `changed` in the next version; an article of the last 30 days that
  was removed at its source is dropped from the next version. For older articles, each update
  also compares every source's post count per year with the counts of the version before; in
  a year whose count fell, it lists that year's posts and drops each article whose page is
  gone. A removal offset by a back-dated post in the same year is missed.
- **On request.** Publishers, writers and people named in an article can ask for a removal or a
  correction with the [takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml). Requests are answered
  within 14 days. An article taken down goes on a list of ids (`data/takedowns.csv` in the
  code repository, with no URL or name) and is left out of every later version.
- **Your copy.** If you keep a copy of CommonsWire, please apply removals to it too:
  `index.csv` of the latest version lists every article still in it.

## Limitations
- The sources are a small, uneven set: an international citizen-media newsroom, two
  fact-checking sites in India, a closed citizen-journalism wiki, a local newsroom in Hamilton
  (Canada), an open-access research newswire, and an outlet in Bosnia and Herzegovina. Their
  mix of countries and topics is not that of mainstream news.
- 33% of the Global Voices rows (33,123) have fewer than 200 characters of text: short posts of
  a sentence or two, most of them with a link, from its first years (99% of them published
  before 2013). The median Global Voices row has 50 words. Filter by length if you need full
  stories.
- Wikinews text is converted from wiki markup by rule; a few articles keep a stray bar,
  bracket or brace where the wikitext itself has a slip.
- Fact-check articles and Global Voices stories quote and describe posts from social media and
  blogs. The embedded posts are removed, but the quoted words stay in the text.
- `authors` is filled for 128,362 of 149,147 rows. Wikinews articles
  carry no bylines, and some articles are credited to the source itself.
- News articles name people. CommonsWire adds nothing to what was published, infers nothing
  about anyone (no gender, ethnicity or other attribute), and offers no search by person.

## Contact
Questions and errors: the [issue tracker](https://github.com/obadaKraishan/commonswire/issues). Removals and corrections: the
[takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml).

## Citation
Please cite the version you used, and credit the newsrooms as each row's credit line asks.

```bibtex
@misc{commonswire_0_2_0,
  author = {Kraishan, Obada},
  title = {CommonsWire: a full-text corpus of openly licensed news},
  version = {0.2.0},
  year = {2026},
  howpublished = {Hugging Face},
  url = {https://huggingface.co/datasets/obadakr/commonswire}
}
```

Version 0.2.0, collected up to 2026-11-14. Code: https://github.com/obadaKraishan/commonswire (Apache-2.0).

---

# DRAFT for version 0.3.0 (built, not yet published)

**DRAFT.** This is the card of version 0.3.0 as built on 2026-11-25 from the published 0.2.3
(`release build-from`, never uploaded yet). It becomes the published card when 0.3.0 is
published; until then the card above is the one in use. Its headings are one level down
here.

CommonsWire is a full-text corpus of news articles whose publishers allow their text to be
shared again. Each row is one article: its body text as published, its metadata, its license,
and the credit line its publisher asks for.

Version 0.3.0 holds 297,287 articles (141.8 million words) in 50 languages, from 9 publishers
(62 sources: their main sites and their language editions), published from 2001-05-15 to
2026-11-24 and collected up to 2026-11-25.

- **Curated by:** Obada Kraishan, College of Media and Communication, Texas Tech University
  (https://orcid.org/0009-0007-7180-8620).
- **License:** each article keeps its publisher's license (CC BY 2.0, CC BY 2.5, CC BY 3.0, CC
  BY 4.0, CC BY-SA 4.0, and public domain), on its row; see `LICENSES.md`.
- **Mirror:** the same files on Kaggle, https://www.kaggle.com/datasets/obadakraishan/commonswire
- **Code and source registry:** https://github.com/obadaKraishan/commonswire (Apache-2.0).
- **How to cite:** see "How to cite" at the end.

CommonsWire is not affiliated with, endorsed by or sponsored by any of the newsrooms whose
articles it holds.

### What it is, and what it is not
- **It is** each publisher's own articles, as far as its API, its pages or its dump give them,
  with every article's license on its row. More sources join in later versions.
- **It is not every news outlet.** Most newsrooms do not allow their text to be shared again,
  and they are not here. Results from CommonsWire describe these publishers, not "the news".
- **It is small going forward.** Over the last 90 days its publishers put out about 11.4 new
  articles a day, every language together: Global Voices 5.9, Factly 2.2, Alt News 1.1, The
  Public Record 0.6, Balkan Diskurs 0.5, 360info 0.5, Africa Is a Country 0.3, SciDev.Net 0.2.
- **Global Voices is most of it** (197,942 of 297,287 rows, 67%, from 47 sites): results over
  the whole corpus mostly describe it.
- **It is mostly English.** 157,673 of 297,287 rows (53%) are in English; the others are in 49
  more languages, most of them Global Voices' own translations (see Languages).
- **Wikinews is a closed archive.** Its 7 editions here stopped publishing on 2026-05-04; their
  rows come from the Wikimedia dumps.
- **It has no coded variables yet** (topic, frame, types of sources quoted, tone); they are
  planned for a later version. It has variables that need no model: the publisher's own
  section, categories and tags, the body's links and the hosts they lead to, and an article's
  other-language versions (`publisher_section`, `publisher_categories`, `publisher_tags`,
  `n_links`, `n_links_external`, `link_hosts`, `original_url`, `other_versions`).

### Changes since 0.2.3
- **A new source: SciDev.Net** (10,563 rows), news, read from its article pages.
- **A new source: Africa Is a Country** (2,485 rows), news, read from its article pages.
- **Global Voices' language editions:** 46 sites (96,359 rows) under the Lingua rule (below).
- **Wikinews' language editions:** 6 editions, in Arabic, Greek, French, Korean, Romanian, and
  Chinese (37,852 rows) with their licenses by date (below).
- **Balkan Diskurs' language edition:** 1 edition, in Bosnian (871 rows).
- **New columns:** `publisher_section`, `publisher_categories`, `publisher_tags`, `n_links`,
  `n_links_external`, `link_hosts`, `original_url` and `other_versions`, after
  `near_duplicates`; and a new file, `changes.csv`.
- **Factly's Telugu stories are labelled `te`:** 4,532 rows were labelled `en` in 0.1.0 to
  0.2.3; their text is unchanged.
- **63 rows of 0.2.3 are withdrawn:** English Wikinews pages whose own license or copyright
  notice differs from their date's license (the rule below). Their ids are in `changes.csv` as
  `withdrawn`; drop them from your copy.
- **1,149 rows of Wikinews in Arabic are left out as copies** of another source's rows (the
  rule below).
- **Near-duplicates across sources:** 53 pairs in this version.
- **The count check covers the language sites:** each update compares a site's total post count
  with the version before's (the first update records it).

### The publishers
| Publisher | Kind | Sources | Languages | Licenses (rows) | Rows | Published |
|---|---|---|---|---|---|---|
| Global Voices | news | 47 | `ar`, `ay`, `bg`, `bn`, `ca`, `cs`, `da`, `de`, `el`, `en`, `eo`, `fa`, `fil`, `fr`, `he`, `hi`, `hr`, `hu`, `id`, `it`, `ja`, `kk`, `km`, `ko`, `ku`, `mg`, `mk`, `my`, `ne`, `nl`, `or`, `pa`, `pl`, `pt`, `ro`, `ru`, `sq`, `sr`, `sv`, `sw`, `tet`, `tr`, `uk`, `ur`, `uz`, `zh-Hans`, `zh-Hant` | CC BY 3.0 (197,942) | 197,942 | 2004-10-27 to 2026-11-24 |
| Wikinews | news | 7 | `ar`, `el`, `en`, `fr`, `ko`, `ro`, `zh` | CC BY 2.5 (55,326); CC BY 4.0 (501); CC BY-SA 4.0 (272); Public domain (2,341) | 58,440 | 2004-11-13 to 2026-05-06 |
| Factly | fact-check | 1 | `en` | CC BY 4.0 (15,124) | 15,124 | 2014-12-14 to 2026-11-23 |
| SciDev.Net | news | 1 | `en` | CC BY 2.0 (10,563) | 10,563 | 2001-05-15 to 2026-11-16 |
| Alt News | fact-check | 1 | `en` | CC BY 3.0 (5,812) | 5,812 | 2016-04-10 to 2026-11-23 |
| The Public Record | news | 1 | `en` | CC BY-SA 4.0 (2,765) | 2,765 | 2013-06-28 to 2026-11-23 |
| Africa Is a Country | news | 1 | `en` | CC BY 4.0 (2,485) | 2,485 | 2009-08-06 to 2026-11-13 |
| 360info | news | 1 | `en` | CC BY 4.0 (2,403) | 2,403 | 2021-11-22 to 2026-11-23 |
| Balkan Diskurs | news | 2 | `bs`, `en` | CC BY 3.0 (1,753) | 1,753 | 2014-06-04 to 2026-11-20 |

Every source in the registry (included, pending and excluded), with the pages read and the
words quoted as evidence, is in `sources.csv`. Each source of this version, with the credit
line its rows carry:

| Source | Name | Rows | Years | Credit line template |
|---|---|---|---|---|
| `wikinews_en` | Wikinews | 20,588 | 2004 to 2026 | `{title}, Wikinews ({url}), {license}` |
| `360info` | 360info | 2,403 | 2021 to 2026 | `{title}, written by {authors}. Originally published under Creative Commons by {source} ({url}), {license}` |
| `thepublicrecord` | The Public Record | 2,765 | 2013 to 2026 | `{title}, by {authors}, {source} ({url}), {license}` |
| `balkandiskurs` | Balkan Diskurs | 882 | 2014 to 2026 | `{title}, by {authors}, originally published by {source} ({url}), {license}` |
| `factly` | Factly | 15,124 | 2014 to 2026 | `{title}, by {authors}, {source} ({url}), {license}` |
| `altnews` | Alt News | 5,812 | 2016 to 2026 | `{title}, by {authors}, {source} ({url}), {license}` |
| `globalvoices` | Global Voices | 101,583 | 2004 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `scidevnet` | SciDev.Net | 10,563 | 2001 to 2026 | `{title}, by {authors}, {source} ({url}), {license}` |
| `africasacountry` | Africa Is a Country | 2,485 | 2009 to 2026 | `{title}, by {authors}, {source} ({url}), {license}` |
| `balkandiskurs_bs` | Balkan Diskurs in Bosnian | 871 | 2014 to 2026 | `{title}, by {authors}, originally published by {source} ({url}), {license}` |
| `globalvoices_ar` | Global Voices in Arabic | 3,568 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_aym` | Global Voices in Aymara | 535 | 2009 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_bg` | Global Voices in Bulgarian | 217 | 2012 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_bn` | Global Voices in Bengali | 6,148 | 2007 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ca` | Global Voices in Catalan | 673 | 2010 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_cs` | Global Voices in Czech | 556 | 2013 to 2022 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_da` | Global Voices in Danish | 326 | 2009 to 2023 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_de` | Global Voices in German | 2,286 | 2007 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_el` | Global Voices in Greek | 6,862 | 2011 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_eo` | Global Voices in Esperanto | 482 | 2013 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_fa` | Global Voices in Persian | 306 | 2007 to 2024 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_fil` | Global Voices in Filipino | 226 | 2009 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_fr` | Global Voices in French | 13,901 | 2007 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_he` | Global Voices in Hebrew | 18 | 2009 to 2016 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_hi` | Global Voices in Hindi | 109 | 2007 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_hr` | Global Voices in Croatian | 20 | 2025 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_hu` | Global Voices in Hungarian | 455 | 2010 to 2023 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_id` | Global Voices in Indonesian | 572 | 2008 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_it` | Global Voices in Italian | 8,430 | 2007 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_jp` | Global Voices in Japanese | 2,295 | 2007 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_kk` | Global Voices in Kazakh | 8 | 2020 to 2025 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_km` | Global Voices in Khmer | 30 | 2010 to 2013 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ko` | Global Voices in Korean | 341 | 2010 to 2024 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ku` | Global Voices in Kurdish | 4 | 2018 to 2018 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_mg` | Global Voices in Malagasy | 14,845 | 2007 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_mk` | Global Voices in Macedonian | 2,010 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_my` | Global Voices in Burmese | 76 | 2010 to 2018 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ne` | Global Voices in Nepali | 241 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_nl` | Global Voices in Dutch | 1,760 | 2009 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_or` | Global Voices in Odia | 27 | 2014 to 2020 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_pa` | Global Voices in Punjabi | 91 | 2017 to 2024 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_pl` | Global Voices in Polish | 1,686 | 2008 to 2023 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_pt` | Global Voices in Portuguese | 4,923 | 2005 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ro` | Global Voices in Romanian | 596 | 2015 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ru` | Global Voices in Russian | 7,373 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_sq` | Global Voices in Albanian | 602 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_sr` | Global Voices in Serbian | 1,477 | 2008 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_sv` | Global Voices in Swedish | 327 | 2011 to 2020 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_sw` | Global Voices in Swahili | 1,254 | 2008 to 2022 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_tet` | Global Voices in Tetum | 8 | 2016 to 2016 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_tr` | Global Voices in Turkish | 222 | 2009 to 2021 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_uk` | Global Voices in Ukrainian | 1,022 | 2010 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_ur` | Global Voices in Urdu | 142 | 2008 to 2023 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_uz` | Global Voices in Uzbek | 10 | 2019 to 2021 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_zhs` | Global Voices in Chinese (Simplified) | 4,403 | 2005 to 2024 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `globalvoices_zht` | Global Voices in Chinese (Traditional) | 4,896 | 2005 to 2026 | `This story by {authors} originally appeared on {source}: {title} ({url}), {license}` |
| `wikinews_ar` | Wikinews in Arabic | 4,743 | 2009 to 2026 | `{title}, Wikinews ({url}), {license}` |
| `wikinews_el` | Wikinews in Greek | 3,029 | 2009 to 2018 | `{title}, Wikinews ({url}), {license}` |
| `wikinews_fr` | Wikinews in French | 18,276 | 2005 to 2026 | `{title}, Wikinews ({url}), {license}` |
| `wikinews_ko` | Wikinews in Korean | 432 | 2009 to 2015 | `{title}, Wikinews ({url}), {license}` |
| `wikinews_ro` | Wikinews in Romanian | 1,221 | 2005 to 2026 | `{title}, Wikinews ({url}), {license}` |
| `wikinews_zh` | Wikinews in Chinese | 10,151 | 2006 to 2026 | `{title}, Wikinews ({url}), {license}` |

`{authors}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source. When the source
names translators, `{authors}` is followed by ", translated by" and their names; the writers
stay in `authors`, and the translators are in `translators`.

### Languages
`language` is the article's language: its edition's, or the publisher's own label where one
site publishes in several (Factly's Telugu stories are `te`).

| Tag | Language | Rows |
|---|---|---|
| `en` | English | 157,673 |
| `fr` | French | 32,177 |
| `mg` | Malagasy | 14,845 |
| `zh` | Chinese | 10,151 |
| `el` | Greek | 9,891 |
| `it` | Italian | 8,430 |
| `ar` | Arabic | 8,311 |
| `ru` | Russian | 7,373 |
| `bn` | Bengali | 6,148 |
| `pt` | Portuguese | 4,923 |
| `zh-Hant` | Chinese (Traditional) | 4,896 |
| `te` | Telugu | 4,532 |
| `zh-Hans` | Chinese (Simplified) | 4,403 |
| `ja` | Japanese | 2,295 |
| `de` | German | 2,286 |
| `mk` | Macedonian | 2,010 |
| `ro` | Romanian | 1,817 |
| `nl` | Dutch | 1,760 |
| `pl` | Polish | 1,686 |
| `sr` | Serbian | 1,477 |
| `sw` | Swahili | 1,254 |
| `uk` | Ukrainian | 1,022 |
| `bs` | Bosnian | 871 |
| `ko` | Korean | 773 |
| `ca` | Catalan | 673 |
| `sq` | Albanian | 602 |
| `id` | Indonesian | 572 |
| `cs` | Czech | 556 |
| `ay` | Aymara | 535 |
| `eo` | Esperanto | 482 |
| `hu` | Hungarian | 455 |
| `sv` | Swedish | 327 |
| `da` | Danish | 326 |
| `fa` | Persian | 306 |
| `ne` | Nepali | 241 |
| `fil` | Filipino | 226 |
| `tr` | Turkish | 222 |
| `bg` | Bulgarian | 217 |
| `ur` | Urdu | 142 |
| `hi` | Hindi | 109 |
| `pa` | Punjabi | 91 |
| `my` | Burmese | 76 |
| `km` | Khmer | 30 |
| `or` | Odia | 27 |
| `hr` | Croatian | 20 |
| `he` | Hebrew | 18 |
| `uz` | Uzbek | 10 |
| `kk` | Kazakh | 8 |
| `tet` | Tetum | 8 |
| `ku` | Kurdish | 4 |

### Configurations and licenses
Each row carries its own `license`, `license_url` and `credit_line`. The rows are split into
one configuration per license class, so you can load only what your use allows:

| Configuration | Licenses | Rows |
|---|---|---|
| `by` | Creative Commons Attribution (CC BY 2.0, 2.5, 3.0 and 4.0) | 291,909 |
| `by-sa` | Creative Commons Attribution-ShareAlike (CC BY-SA 4.0) | 3,037 |
| `pd` | public domain | 2,341 |

| License | `license` | Rows |
|---|---|---|
| CC BY 2.0 | `CC-BY-2.0` | 10,563 |
| CC BY 2.5 | `CC-BY-2.5` | 55,326 |
| CC BY 3.0 | `CC-BY-3.0` | 205,507 |
| CC BY 4.0 | `CC-BY-4.0` | 20,513 |
| CC BY-SA 4.0 | `CC-BY-SA-4.0` | 3,037 |
| Public domain | `public-domain` | 2,341 |

```python
from datasets import load_dataset

by = load_dataset("obadakr/commonswire", "by", split="train")  # CC BY
by_sa = load_dataset("obadakr/commonswire", "by-sa", split="train")  # CC BY-SA
pd = load_dataset("obadakr/commonswire", "pd", split="train")  # public domain
```

**What you must do** (this is a summary, not legal advice; `LICENSES.md` has more):
- **CC BY** (`by`; versions 2.0, 2.5, 3.0, and 4.0): keep each article's `credit_line` with it.
  It names the creator and the source, the title, the link and the license. Say if you changed
  the text.
- **CC BY-SA** (`by-sa`): the same, and share anything you adapt from these texts (a
  translation, an edited version) under CC BY-SA.
- **Public domain** (`pd`): nothing is required. The credit line is kept as a courtesy.
  Public-domain status under US law may not hold in every country.
- In every case, do not suggest that a newsroom endorses your work, and drop articles that a
  later version marks as removed or withdrawn.

### The rights rules of this version
44,206 rows are held back and not released, each for one reason (counted in `manifest.json`,
`held_rows_by_reason`, with their ids, sources and days in `held_rows`).

### Bylines
3,063 rows are held back because the source asks for the author's name: 2,801 name no author on
the article's page or in the source's story listing; 262 are credited only to an account such
as "Guest Contributor", which names no person.

### Global Voices' language sites: the Lingua rule
A row of one of Global Voices' 46 language sites is released only when its English version is a
released row of this dataset: the English pages are where Global Voices' own stories are told
apart from the partner pieces it republishes. The link to the English version comes from the
article's own links and images matched against the English bodies, or from its page. 40,516
rows are held by the rule: 31,691 with no English version found, and 8,825 whose English
version is held or left out.

| Site | Language | Released | Held: no English version found | Held: English not released |
|---|---|---|---|---|
| `globalvoices_mg` | Malagasy | 14,845 | 4,627 | 1,157 |
| `globalvoices_fr` | French | 13,901 | 6,667 | 1,070 |
| `globalvoices_it` | Italian | 8,430 | 1,350 | 897 |
| `globalvoices_ru` | Russian | 7,373 | 1,222 | 965 |
| `globalvoices_el` | Greek | 6,862 | 3,021 | 964 |
| `globalvoices_bn` | Bengali | 6,148 | 2,265 | 314 |
| `globalvoices_pt` | Portuguese | 4,923 | 2,480 | 493 |
| `globalvoices_zht` | Chinese (Traditional) | 4,896 | 1,138 | 182 |
| `globalvoices_zhs` | Chinese (Simplified) | 4,403 | 1,097 | 107 |
| `globalvoices_ar` | Arabic | 3,568 | 2,241 | 538 |
| `globalvoices_jp` | Japanese | 2,295 | 362 | 248 |
| `globalvoices_de` | German | 2,286 | 847 | 183 |
| `globalvoices_mk` | Macedonian | 2,010 | 471 | 74 |
| `globalvoices_nl` | Dutch | 1,760 | 276 | 243 |
| `globalvoices_pl` | Polish | 1,686 | 244 | 105 |
| `globalvoices_sr` | Serbian | 1,477 | 229 | 240 |
| `globalvoices_sw` | Swahili | 1,254 | 436 | 49 |
| `globalvoices_uk` | Ukrainian | 1,022 | 86 | 285 |
| `globalvoices_ca` | Catalan | 673 | 151 | 50 |
| `globalvoices_sq` | Albanian | 602 | 203 | 85 |
| `globalvoices_ro` | Romanian | 596 | 79 | 105 |
| `globalvoices_id` | Indonesian | 572 | 131 | 45 |
| `globalvoices_cs` | Czech | 556 | 70 | 50 |
| `globalvoices_aym` | Aymara | 535 | 265 | 40 |
| `globalvoices_eo` | Esperanto | 482 | 290 | 79 |
| `globalvoices_hu` | Hungarian | 455 | 135 | 31 |
| `globalvoices_ko` | Korean | 341 | 43 | 18 |
| `globalvoices_sv` | Swedish | 327 | 23 | 14 |
| `globalvoices_da` | Danish | 326 | 53 | 14 |
| `globalvoices_fa` | Persian | 306 | 687 | 16 |
| `globalvoices_ne` | Nepali | 241 | 15 | 41 |
| `globalvoices_fil` | Filipino | 226 | 68 | 7 |
| `globalvoices_tr` | Turkish | 222 | 21 | 37 |
| `globalvoices_bg` | Bulgarian | 217 | 102 | 19 |
| `globalvoices_ur` | Urdu | 142 | 47 | 6 |
| `globalvoices_hi` | Hindi | 109 | 150 | 12 |
| `globalvoices_pa` | Punjabi | 91 | 13 | 17 |
| `globalvoices_my` | Burmese | 76 | 48 | 8 |
| `globalvoices_km` | Khmer | 30 | 2 | 0 |
| `globalvoices_or` | Odia | 27 | 7 | 1 |
| `globalvoices_hr` | Croatian | 20 | 4 | 9 |
| `globalvoices_he` | Hebrew | 18 | 12 | 3 |
| `globalvoices_uz` | Uzbek | 10 | 1 | 0 |
| `globalvoices_kk` | Kazakh | 8 | 6 | 3 |
| `globalvoices_tet` | Tetum | 8 | 6 | 1 |
| `globalvoices_ku` | Kurdish | 4 | 0 | 0 |

### Wikinews: licenses by date, and each page's own notice
Each Wikinews edition's copyright page gives its license by date, so a row takes the license of
its date (for an edition, its page's creation date). A date the page does not settle is held. A
page that carries a license or copyright notice of its own that differs from its date's license
is held too (by the kind of notice: 30 another license, 1 public domain, 10 a third party's
copyright, 82 other).

| Edition | Licenses by date | Released | Held: date not settled | Held: own notice |
|---|---|---|---|---|
| Wikinews | before 2005-09-25: Public domain; 2005-09-25 to 2024-12-16: CC BY 2.5; from 2024-12-17: CC BY 4.0 | 20,588 | 0 | 63 |
| Wikinews in Arabic | before 2024-08-21: CC BY 2.5; from 2024-08-21: CC BY-SA 4.0 | 4,743 | 0 | 2 |
| Wikinews in Greek | before 2005-09-25: Public domain; 2005-09-25 to 2018-12-28: CC BY 2.5; from 2018-12-29: held (not settled) | 3,029 | 23 | 0 |
| Wikinews in French | before 2005-09-24: Public domain; 2005-09-24 to 2025-01-01: CC BY 2.5; from 2025-01-02: CC BY-SA 4.0 | 18,276 | 0 | 56 |
| Wikinews in Korean | before 2005-09-25: Public domain; 2005-09-25 to 2015-08-05: CC BY 2.5; from 2015-08-06: held (not settled) | 432 | 387 | 0 |
| Wikinews in Romanian | before 2005-09-26: held (not settled); 2005-09-26 to 2025-01-02: CC BY 2.5; from 2025-01-03: CC BY 4.0 | 1,221 | 94 | 0 |
| Wikinews in Chinese | before 2025-01-30: CC BY 2.5; from 2025-01-30: CC BY 4.0 | 10,151 | 0 | 2 |

### Copies of another source's articles
1,149 rows of Wikinews in Arabic are near-copies of rows of Global Voices in Arabic (Jaccard
0.6 or more): the source republished them, so its copies are left out as third-party material,
and the originals follow their own rules.

### What waits for a later version
- **Global Voices in Spanish** waits until its republishing guidelines are read and the site
  can be collected by its public route alone.
- **Russian Wikinews** waits for its own download allowance (its dump is over 1 GB), and
  **Swedish Wikinews** for a way to tell its published articles apart (most pages carry no
  publication mark).
- Every edition still pending in the registry (`sources.csv`, status `pending`) waits for an
  answer on its own terms.

### Fields
| Field | Meaning |
|---|---|
| `id` | `cw_` and 16 hex digits of the SHA-256 of the canonical URL; stable across versions |
| `source_id`, `kind` | the source, as in `sources.csv`, and its kind (`news`, `fact-check`) |
| `title` | the headline as published |
| `authors` | the bylines as published (empty when the article names no person) |
| `translators` | the translators the source names, apart from the writers (often empty) |
| `published_at`, `updated_at` | UTC, as the source gives them |
| `retrieved_at` | UTC, when CommonsWire fetched the article |
| `language` | the article's language, a BCP 47 tag (50 in this version) |
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

### How it was collected
- **Rights first.** A source enters only when its own pages give a license or public-domain
  statement that allows sharing the full text unchanged, do not forbid bulk or automatic
  reuse, and do not forbid automated collection, and when its own articles can be told apart
  from material it republishes. The evidence (page, date, exact words) is in `sources.csv`.
- **Third-party material is left out.** Wire copy, partner stories, syndicated pieces, posts
  under someone else's rights and copies of another source's articles are dropped; 3,827 were
  dropped in this version, 1,149 of them copies (see the rules above).
- **Text unchanged.** The body text comes from each source's API, its article pages, or (for
  Wikinews) the Wikimedia dumps, with the markup removed by rule. Only whitespace inside
  paragraphs is normalized. Photos, captions, video, audio and embedded posts are not
  collected; they are often separate works the source does not license.
- **Bylines.** From the source's API; where the API gives none and the source asks for the
  author's name, from the byline on the article's own page or in the source's own story
  listing, never from the body text.
- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped: 2,513 in this
  version. Near-duplicates across sources are flagged in `near_duplicates`, not dropped: 53
  pairs in this version.
- **Politely.** One request at a time, at least 2 seconds apart, robots.txt and crawl-delays
  honored, and a user agent that names the project. Blocks are never worked around.

### Removals and corrections
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
  correction with the [takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml). Requests are answered
  within 14 days. An article taken down goes on a list of ids (`data/takedowns.csv` in the
  code repository, with no URL or name) and is left out of every later version. If a
  publisher, a writer or a person named in an article asks for it to be removed from every
  version, the dataset and its Kaggle mirror are created again without it, so that no version
  still holds it.
- **Earlier versions.** Earlier versions stay in this dataset's history (each minor release
  under its tag, each weekly version as a commit), and the Kaggle mirror keeps its earlier
  versions. They still hold the rows that later versions withdrew or removed. `changes.csv`
  lists those rows: drop them from your copy.
- **Your copy.** If you keep a copy of CommonsWire, please apply removals to it too:
  `index.csv` of the latest version lists every article still in it, and `changes.csv` says
  when each one left.

### Limitations
- The publishers are a small, uneven set: Global Voices (news), Wikinews (news), Factly
  (fact-check), SciDev.Net (news), Alt News (fact-check), The Public Record (news), Africa Is a
  Country (news), 360info (news), and Balkan Diskurs (news). Their mix of countries and topics
  is not that of mainstream news.
- 33% of the Global Voices rows (33,123) have fewer than 200 characters of text: short posts of
  a sentence or two, most of them with a link, from its first years; the median row has 50
  words. Filter by length if you need full stories.
- 25% of the Wikinews in Chinese rows (2,494) have fewer than 200 characters of text; the
  median row has 5 words. Filter by length if you need full stories.
- Global Voices' language sites are translations of its English stories: the same
  story is often in the corpus in several languages (`other_versions` links them). Count
  stories, not rows, when that matters.
- Wikinews text is converted from wiki markup by rule; a few articles keep a stray bar,
  bracket or brace where the wikitext itself has a slip.
- Fact-check articles and Global Voices stories quote and describe posts from social media and
  blogs. The embedded posts are removed, but the quoted words stay in the text.
- `authors` is filled for 238,657 of 297,287 rows. Wikinews articles carry no bylines, and some
  articles are credited to the source itself.
- News articles name people. CommonsWire adds nothing to what was published, infers nothing
  about anyone (no gender, ethnicity or other attribute), and offers no search by person.

### Contact
- **Questions and errors:** the [issue tracker](https://github.com/obadaKraishan/commonswire/issues).
- **Removals and corrections:** the [takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml).
- Both forms need a free GitHub account. Without one, open a discussion on this dataset's
  [Community tab](https://huggingface.co/datasets/obadakr/commonswire/discussions) (a free Hugging Face account).

### How to cite
Please cite the version you used:

Kraishan, O. (2026). *CommonsWire: A full-text corpus of openly licensed news* (Version 0.3.0)
[Data set]. Hugging Face. https://huggingface.co/datasets/obadakr/commonswire

```bibtex
@misc{kraishan2026commonswire,
  author    = {Kraishan, Obada},
  title     = {{CommonsWire}: A full-text corpus of openly licensed news},
  year      = {2026},
  version   = {0.3.0},
  publisher = {Hugging Face},
  note      = {Data set},
  url       = {https://huggingface.co/datasets/obadakr/commonswire}
}
```

The code and the source registry that build CommonsWire (no article text) are archived on
Zenodo: https://doi.org/10.5281/zenodo.24231835 (all versions; it resolves to the latest).

Please also credit the newsrooms: keep each article's `credit_line` with any of its text you
share, as its license asks.

Version 0.3.0, collected up to 2026-11-25. Code: https://github.com/obadaKraishan/commonswire (Apache-2.0).
