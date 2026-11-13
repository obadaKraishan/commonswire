# Release layout (DRAFT)

**DRAFT: a design for the first release; nothing is uploaded.** The working copy is built by
`commonswire store` under `data/interim/parquet/<source>/<year>.parquet`.

## Configurations
One configuration per license class (`docs/licenses.md`), so a user can take only what their
own use allows:

| Configuration | Licenses | Rows on 2026-11-13 |
|---|---|---|
| `pd` | Public domain, CC0 | 1,954 (Wikinews before 2005-09-25) |
| `by` | CC BY 2.0 to 4.0 | 42,884 |
| `by-sa` | CC BY-SA 2.0 to 4.0 | 2,749 (The Public Record) |
| `nc-nd` | NonCommercial or NoDerivatives, only for sources that allow bulk reuse | 0 (empty in version 1) |

Only rows with `releasable = true` are released; rows held for a missing byline stay in the
working copy until the byline is found.

## Files
```text
<configuration>/<source_id>/<year>.parquet     e.g. by/globalvoices/2024.parquet
sources.csv                                    the registry, with the evidence for every source
CHANGES.md                                     new, changed and removed rows in this release
README.md                                      the data card
```

## Columns
| Column | Type | Notes |
|---|---|---|
| `id` | string | `cw_` and 16 hex digits of the SHA-256 of the canonical URL |
| `source_id` | string | as in `sources.csv` |
| `kind` | string | `news`, `fact-check`, `advocacy` or `official` |
| `url` | string | the article at its source |
| `title` | string | as published |
| `authors` | list of strings | bylines as published |
| `published_at`, `updated_at`, `retrieved_at` | timestamp (UTC) | |
| `language` | string | `en` in version 1 |
| `section` | string | the source's own section, if any |
| `text` | string | body text, words unchanged, paragraphs separated by a blank line |
| `license` | string | SPDX id or `public-domain` |
| `license_class` | string | the configuration (`pd`, `by`, `by-sa`, `nc-nd`) |
| `license_url` | string | the license's legal text (the Public Domain Mark for public domain) |
| `credit_line` | string | the attribution to keep with the text |
| `content_hash` | string | SHA-256 of the text |
| `status` | string | `live`, `changed` or `removed` (removed rows have no text) |
| `near_duplicates` | list of strings | ids of rows in other sources with character 5-gram Jaccard of 0.6 or more |
| `codings` | list of structs | added in S3: variable, value, codebook version, model, model license, prompt version, time, provenance |

Not released: `releasable` and `hold_reason` (only releasable rows are published) and
`third_party` (always false; third-party material never enters the corpus).

## Cadence
Weekly commits to the Hugging Face dataset to start, a weekly Kaggle version, a quarterly Zenodo
snapshot with a DOI (`docs/automation.md`).
