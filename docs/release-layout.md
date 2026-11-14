# Release layout

How `commonswire release build --version X.Y.Z` lays out a dataset version
(`data/release/X.Y.Z/`, never committed). The same rows and registry give the same bytes.

## Sources per version series
Each series has a fixed list of sources (`SERIES` in `src/commonswire/release.py`), so a source
collected later cannot slip into an older series:

| Series | Sources |
|---|---|
| 0.1.x | English Wikinews, 360info, The Public Record, Balkan Diskurs, Factly, Alt News |
| 0.2.x | planned: the 0.1.x sources and Global Voices |

## Configurations
One configuration per license class (`docs/licenses.md`), so a user can take only what their
own use allows. `by` is the default.

| Configuration | Licenses | Rows in 0.1.0 |
|---|---|---|
| `by` | CC BY 2.5, 3.0 and 4.0 | 42,882 |
| `by-sa` | CC BY-SA 4.0 | 2,749 |
| `pd` | Public domain (Wikinews before 2005-09-25) | 1,954 |
| `nc-nd` | NonCommercial or NoDerivatives | not built; no source in version 1 has these licenses |

Released rows are releasable, not third-party, not removed at their source and not on the
takedown list (`data/takedowns.csv`). Exact duplicates are dropped and near-duplicates flagged,
computed within the version's own sources.

## Files
```text
data/<configuration>/train-NNNNN-of-NNNNN.parquet   the rows (zstd; 50,000 rows a file at most)
index.csv                                           id, source, configuration, URL, license,
                                                    content hash, publication time; no text
sources.csv                                         the registry: every source, its evidence, status
LICENSES.md                                         the licenses in this version, what users must do
README.md                                           the dataset card (Hugging Face metadata on top)
manifest.json                                       row counts; size and SHA-256 of every file
```

`release kaggle` copies these files under flat names (`commonswire-by.parquet`, ...) into
`data/release/X.Y.Z-kaggle/` with `dataset-metadata.json`. `release zenodo` writes
`data/release/X.Y.Z-zenodo/`: the code (`git archive`), `sources.csv`, `index.csv`, the card,
`LICENSES.md`, the manifest and `zenodo-metadata.json`, and **no article text**.

## Columns
| Column | Type | Notes |
|---|---|---|
| `id` | string | `cw_` and 16 hex digits of the SHA-256 of the canonical URL |
| `source_id` | string | as in `sources.csv` |
| `kind` | string | `news` or `fact-check` in 0.1.0 |
| `title` | string | as published |
| `authors` | list of strings | bylines as published |
| `published_at`, `updated_at`, `retrieved_at` | timestamp (UTC; whole seconds, stored in milliseconds) | `updated_at` may be null |
| `language` | string | `en` |
| `section` | string | the source's own section, if any |
| `url` | string | the article at its source |
| `license` | string | SPDX id or `public-domain` |
| `license_url` | string | the license's legal text (the Public Domain Mark for public domain) |
| `credit_line` | string | the attribution to keep with the text; exactly the source's template filled in |
| `text` | string | body text, words unchanged, paragraphs separated by a blank line |
| `content_hash` | string | SHA-256 of the text |
| `status` | string | `live` or `changed` |
| `near_duplicates` | list of strings | ids of rows in other sources with character 5-gram Jaccard of 0.6 or more |

Not released: `releasable` and `hold_reason` (only releasable rows are published),
`third_party` (always false), and `codings` (empty until coded variables exist).

## Checks before and after writing
Before: every row validates against the schema, is releasable and not third-party, and its
credit line is exactly its source's template filled in; a failing row stops the build. After
(`release check`): every file matches its size and SHA-256, every id appears once, every row is
in its license's configuration, every credit line re-renders from the release's own
`sources.csv`, and the rows per source match the corpus report.
