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
- **Configurations:** `pd`, `by`, `by-sa` (and `nc-nd`, empty until a source allows it); see
  `docs/release-layout.md`.
- **Languages:** English only in version 1.
- **Size (working copy, 2026-11-13, before Global Voices):** 47,595 rows from six sources
  (47,495 releasable; 100 held because the article names no person as its author), 22.7 million
  words, 2004-11-13 to 2026-11-13; 0.21 GB of rows, 0.36 GB of raw API answers and 0.59 GB of
  article pages read for bylines. By configuration: `by` 42,892, `by-sa` 2,749, `pd` 1,954.
- **Living flow:** about 4.7 new articles a day over the last 90 days (Factly 2.3, Alt News 1.2,
  The Public Record 0.5, 360info 0.5, Balkan Diskurs 0.2; Wikinews is closed). Global Voices would
  add about 1.5 a day once it can be collected.
- **Versions:** daily commits on Hugging Face, weekly Kaggle versions, quarterly Zenodo
  snapshots with a DOI.

## Sources
- **How sources are admitted:** the clean-source rule (`docs/sources.md`). The evidence for
  each source is in `data/sources.csv`: the pages read, the date and the exact words.
- **Included sources (registry of 2026-11-13):** 12 sources are `include`: Global Voices (CC BY
  3.0), Wikinews in English (public domain, CC BY 2.5 or CC BY 4.0 by date; closed since
  2026-05-04), 360info (CC BY 4.0), The Public Record (CC BY-SA 4.0), Balkan Diskurs (CC BY 3.0,
  English edition), Africa Is a Country (CC BY 4.0), SciDev.Net (CC BY 2.0), Alt News (CC BY 3.0,
  fact-check), Factly (CC BY 4.0, fact-check), EFF Deeplinks and the Freedom of the Press
  Foundation (CC BY 4.0, advocacy) and NIH News Releases (public domain, official). The working
  copy holds six of them; the others are not collected yet (`docs/sources.md`).
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
- Wikinews text comes from each article's wikitext in the Wikimedia dump. The markup is removed
  by rule; templates that show words in the sentence (such as `{{w|...}}`, a link to Wikipedia)
  keep those words, and files, categories, tables, infoboxes and map data are dropped.
- Bylines come from the source's API. Where the API gives none and the source asks for the
  author's name (The Public Record, Balkan Diskurs, some 360info rows), the article's page is
  fetched once and the name is read from the page's own byline block; when a page has no byline
  block, from its JSON-LD or meta tags, except for Balkan Diskurs, whose JSON-LD names the
  account that posted the article. Names are never taken from the body text. A row whose page
  names no person is held, not released.
- Third-party material dropped in the working copy: 65 posts (partner republications, wire
  bylines, rights notes); 39 exact text duplicates dropped; near-duplicates across sources are
  flagged at character 5-gram Jaccard 0.6 (none so far).
- Coding: `docs/method.md` (DRAFT; topics from IPTC Media Topics). TODO: the models, prompts and
  reliability figures.

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
- Wikinews closed on 2026-05-04 and contributes a back-catalogue only. Voice of America's English
  output looked sharply reduced on 2026-11-13 (and VOA is excluded on its own terms).
- Global Voices could not be reached on 2026-11-13 (connection refused on every try); its API
  gives no author names, and its attribution policy asks for the author's name.
- The Public Record and Balkan Diskurs ask for the author's name but their API gives none, so
  their bylines come from their article pages, as do those of 563 360info rows. 100 rows are
  held: 90 Balkan Diskurs pages credit Balkan Diskurs itself, one has an empty byline, and nine
  360info pages name no author.
- Wikinews text is converted from wiki markup by rule. About 60 of its 20,651 articles keep a
  stray bar, bracket or brace, mostly where the wikitext itself has a slip; a bar can also be a
  separator the editors wrote on purpose.
- Fact-check sites quote and describe social-media posts; embedded posts are removed, but the
  quoted claims stay in the text.
- Coded variables are model output, validated as described in `docs/method.md`; their error
  rates are reported per variable.

## Citation
TODO: the Zenodo DOI. Please also credit the newsrooms, as each row's credit line asks.
