# Data card: CommonsWire 0.1.0

This is the text of the dataset card of version 0.1.0, as `commonswire release build --version
0.1.0` writes it (`data/release/<version>/README.md`, the card on Hugging Face). Its metadata
block, which Hugging Face reads for the license and the configurations, is:

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
- 10K<n<100K
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

# CommonsWire 0.1.0

CommonsWire is a full-text corpus of news articles whose publishers allow their text to be
shared again. Each row is one article: its body text as published, its metadata, its license,
and the credit line its publisher asks for.

Version 0.1.0 holds 47,585 articles (22.7 million words)
from 6 sources, published from 2004-11-13 to 2026-11-13 and collected
up to 2026-11-13.

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
- **It is small going forward.** Over the last 90 days the sources published about
  4.7 new articles a day: 360info 0.5, The Public Record 0.5, Balkan Diskurs 0.2, Factly 2.3, Alt News 1.2. Fact-checks are most of that flow (about
  73%).
- **Wikinews is a closed archive.** English Wikinews stopped publishing on 2026-05-04; its
  articles are the largest part of the back catalogue.
- **It is English only.**
- **It has no coded variables yet** (topic, frame, types of sources quoted, tone). They are
  planned for a later version.

## The sources
| Source | Kind | License | Rows | Published | Credit line template |
|---|---|---|---|---|---|
| Wikinews (English) | news | CC BY 2.5 (18,466); CC BY 4.0 (231); Public domain (1,954) | 20,651 | 2004-11-13 to 2026-05-03 | `{title}, Wikinews ({url}), {license}` |
| 360info | news | CC BY 4.0 | 2,400 | 2021-11-22 to 2026-11-12 | `{title}, written by {authors}. Originally published under Creative Commons by {source} ({url}), {license}` |
| The Public Record | news | CC BY-SA 4.0 | 2,749 | 2013-06-28 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |
| Balkan Diskurs | news | CC BY 3.0 | 879 | 2014-06-04 to 2026-11-13 | `{title}, by {authors}, originally published by {source} ({url}), {license}` |
| Factly | fact-check | CC BY 4.0 | 15,103 | 2014-12-14 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |
| Alt News | fact-check | CC BY 3.0 | 5,803 | 2016-04-10 to 2026-11-13 | `{title}, by {authors}, {source} ({url}), {license}` |

`{authors}` is the byline as the page gives it; where an article names no person and the
source's own byline is the source itself, the credit line names the source.
10 more rows are held back because the source asks for the author's name and the article's page names no author.

Every source in the registry (included, pending and excluded), with the pages read and the
words quoted as evidence, is in `sources.csv`.

## Configurations and licenses
Each row carries its own `license`, `license_url` and `credit_line`. The rows are split into
one configuration per license class, so you can load only what your use allows:

| Configuration | Licenses | Rows |
|---|---|---|
| `by` | Creative Commons Attribution (CC BY 2.5, 3.0 and 4.0) | 42,882 |
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
  under someone else's rights are dropped; 65 were dropped in this version.
- **Text unchanged.** The body text comes from each source's API (Wikinews: from the
  Wikimedia dump, with the wiki markup removed by rule). Only whitespace inside paragraphs is
  normalized. Photos, captions, video, audio and embedded posts are not collected; they are
  often separate works the source does not license.
- **Bylines.** From the source's API; where the API gives none and the source asks for the
  author's name, from the byline on the article's own page, never from the body text.
- **Duplicates.** Exact duplicates (the same URL or the same text) are dropped:
  39 in this version. Near-duplicates across sources are flagged in
  `near_duplicates`, not dropped: 0 pairs in this version.
- **Politely.** One request at a time, at least 2 seconds apart, robots.txt and crawl-delays
  honored, and a user agent that names the project. Blocks are never worked around.

## Removals and corrections
- **At the source.** Each update looks again at the last 30 days of every source that still
  publishes: an article
  edited at its source gets its new text and status `changed` in the next version, and an
  article removed at its source is dropped from the next version. Older articles are not
  checked again yet; a monthly check is planned.
- **On request.** Publishers, writers and people named in an article can ask for a removal or a
  correction with the [takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml). Requests are answered
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
- `authors` is filled for 26,833 of 47,585 rows. Wikinews articles
  carry no bylines, and some articles are credited to the source itself.
- News articles name people. CommonsWire adds nothing to what was published, infers nothing
  about anyone (no gender, ethnicity or other attribute), and offers no search by person.

## Contact
Questions and errors: the [issue tracker](https://github.com/obadaKraishan/commonswire/issues). Removals and corrections: the
[takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml).

## Citation
Please cite the version you used, and credit the newsrooms as each row's credit line asks.

```bibtex
@misc{commonswire_0_1_0,
  author = {Kraishan, Obada},
  title = {CommonsWire: a full-text corpus of openly licensed news},
  version = {0.1.0},
  year = {2026},
  howpublished = {Hugging Face},
  url = {https://huggingface.co/datasets/obadakr/commonswire}
}
```

Version 0.1.0, collected up to 2026-11-13. Code: https://github.com/obadaKraishan/commonswire (Apache-2.0).
