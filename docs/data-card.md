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

# DRAFT for version 0.3.0 (not the published card)

**DRAFT.** These numbers come from a local test build (never uploaded) of the published
0.2.2 plus the two new sources, with every page of both read. The real 0.3.0 is built at
release time from the latest published 0.2.N, so it also holds what the weekly updates add
until then.

## Changes since 0.2.x (planned)
- **Two new sources, read from their article pages** (their APIs do not give their articles):
  - **SciDev.Net** (news on science and development, CC BY 2.0): 10,571 rows, 2001-05-15 to
    2026-11-16. Its republishing box asks republishers to "credit our authors", so a page
    with no byline is held (2,607 rows). Its "Supported content" pages are kept only with
    SciDev.Net's own byline, the site's license line and no other holder named (101 of 107).
    78 pieces that say they first appeared elsewhere, 1 with another holder's copyright line
    and the 6 other supported-content pages are left out.
  - **Africa Is a Country** (essays and news analysis, CC BY 4.0): 2,485 rows, 2009-08-06 to
    2026-11-13. 30 pieces that say they first appeared elsewhere are left out.
- **A new license version in `by`: CC BY 2.0** (SciDev.Net). The `by` configuration then
  holds CC BY 2.0, 2.5, 3.0 and 4.0, each article with its own.
- **A weekly route for the two new sources:** SciDev.Net's newest sitemap (the articles
  changed since the previous version) and Africa Is a Country's listing pages 1 and 2 (the
  stories the previous version does not have). Each page is read once.
- **New columns, the variables that need no model** (read from each article as its
  publisher gave it):
  - `publisher_section`, `publisher_categories`, `publisher_tags`: the publisher's own
    labels, as written (the WordPress archives' tags were read once, apart from their text).
  - `n_links`, `n_links_external`, `link_hosts`: the body's links that lead to a web page,
    those to other sites, and every host once (lower case, without `www.`). They are null
    where the body is not known.
  - `other_versions`: the addresses of the article's versions in other languages, as the
    publisher links them.
  - `original_url`: for a translation, the version it was made from, set only where exactly
    one version of the story credits no translator (the English version is not assumed to be
    the original).
- **`language` per row:** Factly's Telugu stories, labelled `en` in 0.1.0 to 0.2.2, are `te`,
  from Factly's own "Telugu" category. They stay Factly rows.
- **Other languages.** Each language edition is a source of its own, ruled on its own pages:
  - **Balkan Diskurs in Bosnian**, under its own Bosnian attribution policy (CC BY);
  - **Global Voices' language sites** (CC BY 3.0, the footer of each site and the publisher's
    policy for "our sites"), under **the Lingua rule**: a row is released only when its
    English version is a released row of this dataset, because the English pages are where
    republished partner pieces are detected. Every other row of these sites is held and
    counted, by site. The English version is found from the links and images a translation
    keeps from it;
  - **Wikinews' language editions** whose copyright page dates its licenses: each article
    carries the license of its creation date, and an article the page's dates do not place is
    held.

  Editions whose license statement could not be read with confidence, or whose pages leave a
  question, stay out; `sources.csv` gives each one's question.
- **The record of changes, `changes.csv`:** one line per article and version where something
  happened (new, changed, removed at the source, taken down on request), with the date. It
  holds ids only.
- **SciDev.Net's checks hold for every section:** a page that lacks the site's license line,
  or names another license outside an image's caption, is left out.
- **The rights audit.** `sources.csv` gains a `reason_code` column (one code from a fixed list
  for every publisher's status), and the registry holds 66 publishers: 13 include, 36 pending,
  17 exclude. How each was read, and how this compares with the Common Pile's news sources
  and Open Newswire's tags, is in the repository's `docs/rights-audit.md`.

## Test build (2026-11-17, with the new columns)
| | 0.2.2 (published) | 0.3.0 test build |
|---|---|---|
| Rows | 149,164 | 162,212 |
| `by` / `by-sa` / `pd` | 144,456 / 2,754 / 1,954 | 157,504 / 2,754 / 1,954 |
| CC BY 2.0 / 2.5 / 3.0 / 4.0 | 0 / 18,466 / 108,250 / 17,740 | 10,563 / 18,466 / 108,250 / 20,225 |
| Words | 55.2 million | 64.5 million |
| Sources | 7 | 9 |
| First and last day | 2004-10-27 to 2026-11-16 | 2001-05-15 to 2026-11-16 |
| Held back | 275 | 2,885 (2,610 more: SciDev.Net pages with no byline) |
| Third-party pieces left out | 2,476 | 2,603 |
| Exact duplicates left out | 107 | 119 (12 more, each a SciDev.Net text at a second address) |
| Near-duplicate pairs across sources | 1 | 6 (5 new: SciDev.Net and Wikinews) |
| Rows with link counts / with an external link | | 99.99% / 95.3% (120,329 hosts in all) |
| Record of changes | | 162,215 lines (0.1.0 to 0.3.0) |
| Size | 220.2 MB | 267.0 MB |

The `by`, `by-sa` and `pd` counts are those of `release check`, which passed on the test
build.
