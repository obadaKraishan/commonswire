# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
