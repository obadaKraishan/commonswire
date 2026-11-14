# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- A backfill page could be lost silently: when the data drive dropped off the bus a moment
  after a page was written, the write had reached only the operating system's cache, the file
  was gone after the drive came back, and the run ended "not finished" with no reason given.
  Raw answers are now flushed to the disk (file and folder) before `save_once` returns, each
  page is looked up again after it is saved (a page that is not on disk stops the run and is
  named), and a run that ends with any page missing names the pages (`missing_pages`).
  `commonswire backfill SOURCE --run RUN --check` checks a saved run for gaps with no request.
- The dataset card's `license_link` is the full https URL of `LICENSES.md` in the Hugging Face
  dataset: the Hub accepts a file name there only when it is `LICENSE` or `LICENSE.md`, and
  refused the card's metadata with the relative name `LICENSES.md`.

### Added
- The release build (`commonswire release build --version X.Y.Z`): a dataset version written
  from the built rows with no request, into `data/release/X.Y.Z/`: one Parquet configuration per
  license class (`pd`, `by`, `by-sa`; `by` is the default), releasable rows only, exact
  duplicates dropped and near-duplicates flagged within the version's fixed list of sources
  (series 0.1.x: Wikinews, 360info, The Public Record, Balkan Diskurs, Factly, Alt News),
  `index.csv` (ids, URLs, hashes and licenses, no text), the registry as `sources.csv`,
  `LICENSES.md`, the dataset card with its Hugging Face metadata (`license: other`, with
  `LICENSES.md` as the license link, since every row keeps its own license) and a manifest with
  the size and SHA-256 of every file. Every row is checked first (schema, releasable, not
  third-party or removed, credit line exactly its template filled in); the same input gives the
  same bytes. `release check` verifies a written version; `release kaggle` prepares the Kaggle
  mirror's folder (license `other`, the only single value Kaggle accepts that fits mixed
  licenses); `release zenodo` prepares a record with the code, the registry, the card and the
  index, and no article text. Nothing is uploaded by any of them.
- A takedown list (`data/takedowns.csv`: article id, date of the request and its basis, never a
  URL or a name): the release build leaves those articles out of every later version.
- Bylines from a paged story listing (`commonswire listing-bylines`), for Global Voices: its
  listing names every story's writers, co-authors included, about 21 stories a page, so the
  archive takes about 5,000 requests instead of one article page per story.
- `daily` saves a small record of each removal it finds, and `build` replays the saved daily
  answers after the backfill, so a rebuild keeps the rows that `daily` added, changed or
  removed (maintainer's decision, 2026-11-13).
- Bylines from article pages (`commonswire page-bylines`), for sources whose attribution
  policy asks for the author's name and whose API gives none (The Public Record, Balkan Diskurs,
  360info): the page of each row with no byline is fetched once and saved, and the name is read
  from the source's own byline block (the article's meta block only, never related posts), then
  from JSON-LD `Person` entries, then from meta tags. When the page has the byline block, only
  that block counts, so a page that credits the source itself is not given a name from its
  metadata; Balkan Diskurs is read from its byline block only, since its JSON-LD names the
  account that posted the article. A name that is the source's own or an account such as
  "admin" names no person, and the row stays held. `build` and `daily` read the names in;
  `daily` fetches the page of a new post that has no byline.
- Backfills (`commonswire backfill`, `build`): whole archives through the WordPress REST API,
  oldest first, resumable, raw answers written once, rows built with no requests; fetchers for
  The Public Record, Balkan Diskurs (English edition), Factly and Alt News.
- The Wikinews dump reader (`commonswire wikinews-dump`): one download checked against the
  dump's md5, published articles only, wiki markup stripped, every skip counted.
- Deduplication (`commonswire dedup`): exact by canonical URL and text hash; near-duplicates
  across sources flagged (never dropped) by MinHash LSH on character 5-grams, threshold 0.6.
- The daily fetch as a local command (`commonswire daily`): new, changed and removed articles.
- `commonswire bylines` (open WordPress users endpoints), `corpus-report` (aggregates only) and
  `store` (Parquet by source and year, with `kind`, `license_class`, `license_url` and
  near-duplicate flags); `docs/release-layout.md` (DRAFT).
- Rows may be stored but not releasable (`releasable`, `hold_reason`), as when a source's
  attribution policy asks for an author's name that its API does not give.
- An optional `corpus` extra (numpy, pyarrow): Parquet output and fast hashing for
  deduplication need them; the core package still depends on pydantic and requests only.

### Changed
- Registry: Global Voices' attribution policy, read again on 2026-11-14 (same text, saved as
  evidence), asks for translations only the link and the author's name, and does not mention
  translators; the note records that translators named on the site will also be credited.
- `release zenodo` prepares a record with no article index: `index.csv` (the article URLs) is
  left out, since a Zenodo record cannot be withdrawn; `--commit` archives the code of the
  commit that built the version, and the record links that commit's tree. `release kaggle`
  writes the file and column descriptions of every table, the provenance, a weekly update
  frequency and a plain cover image (three bars, one per configuration, no text) for Kaggle's
  `datasets metadata --update`, which is the only route Kaggle reads them from. A pack folder
  that holds a file the pack no longer writes is refused, not left half-updated.
- The README gives the Kaggle mirror's link and the publication date of version 0.1.0
  (2026-11-14); the request log records the Global Voices backfill and the byline-route tests.
- The README and the docs say only what version 0.1.0 does: new versions are published by the
  maintainer, about weekly for now, a daily automatic update is planned, and the coded variables
  are planned for a later version. `docs/licenses.md` is no longer a draft (its license classes
  were accepted on 2026-11-13) and quotes CC BY 4.0 section 2(a)(4) on format changes;
  `docs/method.md` and `docs/automation.md` say in their first lines that they describe plans;
  the planned Zenodo record holds the code, the registry and the card, and no article text.
- A page whose own byline names the source itself, and no person, is released with no personal
  author, and its credit line names the source, as the page does (maintainer's decision,
  2026-11-13): 90 Balkan Diskurs articles. Pages with an empty byline or no byline block stay
  held (10 rows).
- Pacing: a process that has not yet read a host's robots.txt waits the crawl-delay another
  process last recorded for that host, so its first request never comes in under the delay.
- The registry asks its open questions of "the maintainer" rather than by first name; the
  request log's notes carry no internal labels.
- Docs: `docs/data-card.md` is now the text of the 0.1.0 dataset card; `docs/release-layout.md`
  describes the layout as built; `docs/automation.md` gives the manual weekly update; the README
  has a dataset section with placeholders for the links; `CITATION.cff` cites the dataset.
- The Wikinews markup stripper keeps the words of templates that show them in the sentence
  (`{{w}}`, `{{wikt}}`, `{{nowrap}}`, translated quotes): before, every template was removed, so
  the names and terms Wikinews writes as `{{w|...}}` links were missing from about a third of
  its articles. Templates and links are read innermost first; a template or table that is never
  closed no longer removes the rest of the article; links and `{{w}}` calls with one bracket or
  brace missing are still read; every character reference is decoded; map and chart JSON is
  dropped; and a line break is a break.
- `daily` prints how many new rows are held, and reads the bylines kept from users endpoints and
  article pages.
- Requests are paced per host: one lock and stamp per host, at least 2 seconds or the host's
  crawl-delay, so different hosts can be fetched in parallel.
- The four rulings on reading the clean-source rule (an invitation is not a condition; a
  request is not a restriction; no terms page passes point 3 when robots.txt allows the pages;
  silence on bulk passes only under public domain, CC0, CC BY and CC BY-SA) are in
  `docs/sources.md` and the validator's messages. SciDev.Net, Alt News and Factly are included;
  INN is excluded; 31 pending sources are not pursued for version 1.
- Third-party rules: embedded social posts are removed as embeds, "all rights reserved" notes
  drop a post, and a note that only dates a source's own earlier publication or series is not
  a republication.
- The topic scheme in the method draft is IPTC Media Topics (CC BY 4.0); CAP is an optional
  internal crosswalk.
- The package skeleton: Apache-2.0 license, README, citation draft, CI (ruff and pytest on
  Python 3.10 to 3.13) and Dependabot for the pinned actions.
- `commonswire.http.PoliteClient`: one request at a time across processes, at least 2 seconds
  apart, robots.txt and crawl-delays honored, backoff on 429 and 5xx, blocks never worked
  around, redirects followed by hand, every attempt logged to `data/usage_log.csv`.
- The source registry (`data/sources.csv`, `commonswire.sources`) with the clean-source rule
  checks and a check that every quote is word for word on a saved page of its source;
  `commonswire evidence fetch|extract`, `sources check` and `sources render` (`docs/sources.md`).
  58 sources checked on 2026-11-13: 9 include, 35 pending, 14 exclude.
- The article schema (`commonswire.schema`) with stable ids, content hashes, credit-line
  templates, dated license schedules (`commonswire.licensing`) and coded-variable stubs with
  provenance; `commonswire validate`.
- Fetchers behind one interface for Global Voices and 360info (WordPress API) and Wikinews
  (MediaWiki API, which Wikinews' robots.txt closes to general user agents); third-party posts
  are dropped and counted; `commonswire sample` (with `--replay`), `sample-report` and the
  metadata-only `probe`.
- Docs: prior art, sources, license classes, method (DRAFT), automation (DRAFT) and a data card
  skeleton with its ethics section.
