# Data card: CommonsWire (skeleton)

**Skeleton: nothing has been released yet.** Sections marked TODO are filled in at release.

## Summary
CommonsWire is a living, full-text corpus of news articles whose publishers allow their text to
be redistributed. Each row holds one article's body text, its metadata, its license and the
credit line its source asks for, and coded variables (topic, frame, types of sources quoted,
tone) with their provenance. New articles are added daily.

- **Curated by:** Obada Kraishan, College of Media and Communication, Texas Tech University.
- **License:** per row (see `docs/licenses.md`); the coded variables are CC BY 4.0; the code is
  Apache-2.0.
- **Configurations:** `pd`, `by`, `by-sa` (and `nc-nd`, empty until a source allows it).
- **Languages:** TODO (English only, or every language of the included sources).
- **Size:** TODO.
- **Versions:** daily commits on Hugging Face, weekly Kaggle versions, quarterly Zenodo
  snapshots with a DOI.

## Sources
- **How sources are admitted:** the clean-source rule (`docs/sources.md`). The evidence for
  each source is in `data/sources.csv`: the pages read, the date and the exact words.
- **Included sources:** TODO (from `data/sources.csv`, status `include`).
- **What is left out:** third-party material in every source (wire copy, partner stories,
  syndicated pieces), photos, captions, video, audio and embeds. The number of third-party
  items dropped is reported per source and per release.

## Fields
| Field | Meaning |
|---|---|
| `id` | `cw_` and the first 16 hex digits of the SHA-256 of the canonical URL; stable across fetches |
| `source_id` | The source, as in `data/sources.csv` |
| `url` | The article at its source |
| `title` | The headline as published |
| `authors` | Bylines as published (empty when the source gives none); never used to infer anything about a person |
| `published_at`, `updated_at` | As the source gives them, with a time zone |
| `retrieved_at` | When CommonsWire fetched the article |
| `language` | A language tag (en, pt-BR, ...) |
| `section` | The source's own section or category, if any |
| `text` | The body text, words unchanged; paragraphs separated by a blank line |
| `license`, `license_url` | The article's license and a link to its legal text |
| `credit_line` | The attribution to keep with the text |
| `content_hash` | SHA-256 of the text, to spot changed articles |
| `status` | `live`, `changed` or `removed` (removed rows keep their metadata; their text is dropped) |
| `codings` | Coded variables, each with codebook version, model, model license, prompt version, time and provenance |

## Processing
- Collected politely through each source's API or feed: one request at a time, at least 2
  seconds apart, robots.txt and crawl-delays honored, a user agent that names the project.
- The body text is taken from the source's API, with only whitespace normalized inside each
  paragraph; no words are changed. Photos, captions and embeds are removed.
- Coding: `docs/method.md` (DRAFT). TODO: the models, prompts and reliability figures.

## Ethics
- **Text only.** No photos, video, audio or embeds are collected or redistributed.
- **No profiling.** No one's gender, race, ethnicity, religion, age, nationality or any other
  personal attribute is inferred, from names or otherwise. Quoted sources are coded only by the
  role the text gives them (an official, an expert, a resident), and only counts per article
  are released; there is no person-level table.
- **Corrections and removals are honored.** An article that its publisher corrects or removes is
  marked in the next release; a removed article's text is dropped. A monthly check looks for
  removed and changed articles.
- **Takedowns.** Publishers, writers and people named in an article can ask for removal through
  the takedown form in the repository's issues (TODO: confirm the contact). Requests are answered
  within 14 days.
- **Attribution to every newsroom.** Every row carries its source's credit line and a link to the
  original article.
- **Personal information.** News articles name people. CommonsWire adds nothing to what was
  published and offers no search by person. TODO: decide whether to drop articles that name
  private individuals in crime reporting, on request or by rule.

## Limitations
- The corpus covers only sources that allow redistribution; it is not a sample of the news. Its
  mix of outlets, countries and topics differs from mainstream coverage, and results should not
  be read as describing "the news" in general.
- Wikinews closed on 2026-05-04 and contributes a back-catalogue only. TODO: the other closed or
  paused sources.
- Coded variables are model output, validated as described in `docs/method.md`; their error
  rates are reported per variable.

## Citation
TODO: the Zenodo DOI. Please also credit the newsrooms, as each row's credit line asks.
