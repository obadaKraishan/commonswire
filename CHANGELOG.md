# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **The language editions (series 0.3).**
  - Balkan Diskurs' Bosnian edition (`balkandiskurs_bs`): read like the English edition, with
    Bosnian republication notes left out as well.
  - 47 Global Voices language sites under **the Lingua rule** (reason code
    `released_with_english`): a language-site row is released only when its English version
    is a released row of the corpus, because the English pages are where republished partner
    pieces are detected. `release` holds every other such row and counts it, by edition.
  - The link to the English version comes from the body the API gives
    (`commonswire lingua-link`, no requests). A translation keeps its source's links to other
    sites, its links to English articles and its image file names, so these are matched
    against the saved English bodies. On a study of the pages' own links it was never wrong
    and found 82% (`docs/method.md`).
  - Writers and translators come from each site's own listing, its labels learned from the
    listing; `listing-bylines --plan` reads only the listing pages that may show a story the
    rule could release.
- **`other_versions`** (series 0.3): the addresses of an article's versions in other
  languages, as the publisher links them (Global Voices through the English post, Balkan
  Diskurs from its `hreflang` tags; `commonswire versions`). `original_url` is set only where
  exactly one version in the group credits no translator.
- **Wikinews' editions by date:** license-by-date tables for eight editions, read on their
  own copyright pages (`commonswire.licensing`). An article takes the license of its creation
  date; a date the table does not place is held, and so is a page that carries a license or
  copyright notice of its own that differs from that license (counted by edition). Sixteen
  editions stay pending, each with the question its page leaves. `commonswire
  wikinews-edition` saves an edition's dumps once (md5 checked), counts its templates
  (`--census`), and builds its rows by creation date (the stub history's first revision).
- **Tags:** `backfill --tags` asks new archives for each post's tags and saves the site's tag
  names; `commonswire backfill-tags` reads the tags of an archive saved without them (post
  ids with tag ids, then only the names used). Builds join them by post id.
- **The weekly route of series 0.3** asks for tags and keeps each row's versions. It links a
  new language-site post to its English version by fingerprint against the run's English
  posts, or else from the post's own page (at most 40 pages a site a week). Versions are
  added to their groups after the run. The Wikinews editions are carried as closed. The
  language sites get a count check of their own (below). Series 0.1 and 0.2 ask for the same
  fields and write the same files as before.
- The registry's new reason code `released_with_english`, which needs `edition_of`.
- **Series 0.3's sources:** the Bosnian Balkan Diskurs edition, 46 Global Voices language sites
  and six Wikinews editions (French, Chinese, Arabic, Greek, Romanian, Korean) beside the nine
  of before. Each Wikinews edition's published articles are told by its own publication
  template, found in its dump's template census; Chinese headline digests, made only of
  templates, have no text of their own.
- **Series 0.3's own card and `LICENSES.md`** (`commonswire.card03`; series 0.1 and 0.2 keep
  theirs word for word): a table of the languages, the license versions the rows carry, the
  publishers with their editions and every source's credit line, the Lingua rule with its held
  rows by site, Wikinews' licenses by date with each page's own notice by kind, the copies left
  out, what waits for a later version, and the changes since the series before (new sources
  and editions, the new columns, Factly's Telugu rows, the withdrawn rows). Its "How to cite"
  opens with the data set's citation, then BibTeX, the Zenodo DOI of the code and the registry,
  and the newsrooms' credit request; "Contact" says the forms need a free GitHub account and
  names the dataset's Community tab. Manifests of series 0.3 carry `series_from`.
- **`commonswire.citation`:** the APA 7 data-set citation, the BibTeX entry and the Zenodo
  sentence, defined once for the card, the Kaggle page and the citation files. The ORCID iD
  is in `CITATION.cff` (both author blocks) and `.zenodo.json`, and the Zenodo check compares
  it.
- **The registry by series:** `update` builds a version with its series' own registry. Series
  0.2 keeps a byte copy of the registry its versions were published with
  (`data/series/0.2/sources.csv`), so its weekly updates go on while `data/sources.csv` holds
  series 0.3's; the series comes from the published version, so publishing 0.3.0 moves the
  weekly update to series 0.3. An update never begins a series (`release build-from` does).
- **Copies of another source's articles (series 0.3):** an Arabic Wikinews row whose
  near-duplicate (Jaccard 0.6 or more) is a Global Voices Arabic row, held or released, is left
  out as third-party material and counted (`copies_left_out`, and in `third_party_dropped`);
  no row names a left-out copy in `near_duplicates`. A weekly run that would drop a released
  row this way stops for the maintainer.
- **English Wikinews' own notices (series 0.3):** a page whose own license or copyright notice
  differs from its date's license is held, as in the editions, with the kind of notice in its
  reason (another license, public domain, a third party's copyright, other). `release
  build-from` carries such a hold onto a published row, and `changes.csv` records it with the
  new kind `withdrawn`.
- **A count check for the language sites:** one request a site a run for its total over a
  recorded range, compared with the same range's recorded total; the range moves up once it is
  21 days old. A fall is placed by year (one request a year) and walked like the English
  check's, within the run's ceiling of 200 requests. The first series 0.3 run records the
  totals. `update --max-requests` caps the requests a run sends.
- **`commonswire tracked-addresses`:** counts the article addresses in the tracked request log
  and evidence files (or, once, puts the article's id in place of each, saving the files as
  they were and the map on the data drive). Evidence reads record and log an article page by
  its id, and name its snapshot after it.
- **Backfills and listings hold up better:** an API answer whose JSON follows an HTML notice
  from the site is kept unchanged (`.notjson`) and its posts read; a listing page still
  failing with a server error after the client's retries is asked again after 5 and 15
  minutes; a site that redirects its listing pages only to drop the trailing slash is asked in
  that form; `backfill-tags --missing-from` reads only the posts a run saved without tags.

- **The variables that need no model, as columns from series 0.3** (earlier series keep
  their columns, so a 0.2.x build is unchanged): `publisher_section`,
  `publisher_categories` and `publisher_tags` (the publisher's own labels, as written);
  `n_links`, `n_links_external` and `link_hosts` (the links of the body: relative links
  resolved against the article's address; anchors, mail, telephone, script and data links,
  and addresses with no valid host not counted; hosts lower case, without `www.`, each once);
  `original_url` (for a translation, the article it translates). From series 0.3 `language`
  follows the publisher's own language label where it gives one per article: Factly files
  each story under "Telugu" or "English", so its Telugu stories are `te` (series 0.1 and 0.2
  label every row `en`). The fetchers fill the columns for new rows; `release build-from`
  takes them for the published rows from the rows rebuilt from the saved answers.
- **The record of changes** (`changes.csv`, series 0.3 on): one line per article and version
  where something happened (`new`, `changed`, `removed`, `taken_down`), with the date, ids
  only. `commonswire changes VERSION_DIR ...` derives it from published versions alone (a
  missing version between two is split off by the rows' retrieval times); `release
  build-from --changes` starts it, and `update` adds each version's lines.
- **Language editions in the registry:** the `edition_of` column names a language
  edition's main row (each edition is ruled on its own pages; the main row's verdict is never
  carried over), and the pending code `statement_unread` marks a license statement in a
  language this project could not read with confidence (or a broken template).
- **The rights audit of 2026-11-16** (`docs/rights-audit.md`, DRAFT). The registry has a
  reason code on every row and 66 publishers (13 include, 36 pending, 17 exclude).
  - Eight publishers were added: those in Open Newswire's English open-license feeds that had
    no row.
  - The include and exclude rows that the Common Pile or Open Newswire tags as openly
    licensed were re-read, with their quoted words unchanged; no verdict changed.
  - `data/audit/other_lists.csv` records what the Common Pile's news subset and Open
    Newswire say about each publisher, with where and when it was read.
    `data/audit/comparison.csv` sets that beside this project's status and reason code.
  - Each list's facts carry the date of the list's own data (`data_date`: the Common Pile's
    news files were added on 2024-05-27; Open Newswire's `feeds.csv` was last changed on
    2025-11-11), and the comparison keeps both dates beside the date the publisher's pages
    were read, since a difference today does not show that a tag was wrong when it was made.
  - SINC's reason says what its clause forbids (publications made up chiefly of its
    content) and why the corpus cannot meet it; SciDev.Net's row quotes its republishing
    box on the authors' credit and the embed code. No verdict changed.
- `commonswire release build-from`: a version of a new series, built from the latest
  published version's rows (with its held ids, third-party count and post counts) plus each
  new source's rows, through `release build`'s checks and `release check`. No requests.
  For a new source read from its pages it also writes the weekly route's state
  (`page_state`) from the saved backfill run its build summary names, so the first weekly
  update reads only what came after the backfill.
- Series 0.3 adds SciDev.Net and Africa Is a Country, read from their article pages.
- `docs/sources.md` shows each row's reason code.
- **Reason codes in the source registry.** A `reason_code` column (before `reason`) gives the
  reason for each source's status as one code from a fixed list: `license_allows` for
  `include`; `bulk_clause`, `tracker_required`, `terms_forbid_automation`, `robots_forbid`,
  `third_party_portal` and `rights_reserved` for `exclude`; `nc_or_nd`, `no_license`,
  `conflicting_statements`, `partial_license`, `extra_conditions`, `third_party_unclear`,
  `refused_requests` and `site_unavailable` for `pending`. `sources check` refuses a code that
  does not go with the row's status or with the field it names (for example `bulk_clause`
  without `bulk_clause=forbids`). The free-text `reason` stays. A registry without the column
  (the `sources.csv` that versions 0.1.x and 0.2.x ship) is still read, with no code required,
  so the weekly update of a 0.2.x version is unchanged. The Kaggle metadata lists the columns
  a version's `sources.csv` has.
- Two source kinds, `state-agency` (a news agency or site run or paid for by a state) and
  `church-agency`, and the access route `listing` (archive listing pages). Like `official`
  and `advocacy`, these kinds get a verdict but are not collected unless the maintainer
  decides so.
- `commonswire backfill-pages SOURCE --run RUN`: a source's archive from its article pages,
  for sources whose API does not give their articles. The list of articles comes from the
  source's sitemap index (SciDev.Net) or its listing pages (Africa Is a Country), saved once;
  each article page is then fetched once through the polite client, logged by the article's
  id, and saved unchanged with a record of its answer. A refusal stops the run (never worked
  around), a 404 or 410 is recorded, a failure is tried again on the next run, and `--check`
  names any gap with no request.
- Page fetchers for SciDev.Net and Africa Is a Country (`commonswire.fetchers.pages`), and
  `commonswire build SOURCE --run RUN` for them (no requests). The byline is read from the
  page's own byline block only (SciDev.Net's JSON-LD names the account that posted). A
  SciDev.Net page with no byline is held, since its republishing box asks republishers to
  credit the authors. Pages that say they were first published elsewhere, or that end with
  another holder's copyright line, are dropped and counted; an image's credit line is not
  taken for the article's.
- SciDev.Net's "Supported content" pages (the label its breadcrumb gives them; most name a
  funder) are kept only when they carry SciDev.Net's own byline (every name linked to one of
  its author pages), the site's license line, and no other holder (no Creative Commons link
  in the body outside an image's caption). Any other is left out and counted as third-party
  or sponsored material. Its other sections keep the rules above.
- The weekly route of the sources read from their article pages, used by `commonswire update`
  for a series that has them (0.3 on; series 0.2 has none, so its weekly update is
  unchanged). SciDev.Net: the sitemap index and its newest article sitemap (and the one
  before only while a sitemap starts after the mark), then each article changed after the
  newest change date the previous version saw. Africa Is a Country: listing pages 1 and 2
  (and on, up to 5, until a page shares a story with the previous version), then each story
  the previous version neither has, holds nor saw. Each page once, through the same page
  fetchers; new, changed, held and removed rows by the same rules as the other sources. The
  route's state (`page_state`: a date, or ids) goes into the next manifest. A source that
  would need more than 60 requests in a week stops before reading its pages. Page sources
  have no post counts, so the count check does not cover them.
- SciDev.Net's two license checks hold for every section: a page that lacks the site's
  license line, or names another Creative Commons license outside an image's caption, is left
  out and counted, whatever its section ("Supported content" pages also need SciDev.Net's own
  byline). Two legacy forms in its older bodies are cleaned before the text is taken: the
  angle brackets printed around a link's label, and a paragraph that only shows escaped
  markup (a player's embed code).
- The page route re-reads Africa Is a Country's stories of the last 30 days each week, so
  their edits are seen by text hash as for the other sources.
- The removal check of the page sources: each week every SciDev.Net article sitemap is
  compared with the released rows, and every 28 days Africa Is a Country's whole listing is
  walked. A released row that is no longer listed is read once and marked removed only when
  its own page answers 404 or 410. More than 25 such rows in one run stop the source
  (`over_ceiling`), and the weekly limit of 60 article pages counts these reads too.
  `update-route --only-removals` runs the check alone, as a dry run.
- `commonswire update-route SOURCE --from VERSION --work DIR`: one page source's weekly route
  alone, as a dry run (`--max-requests` caps it; `--offline` replays it). It writes a summary
  of counts and ids, never a version.
- `commonswire audit compare`: joins the registry with `data/audit/other_lists.csv` (what other
  lists of openly licensed news say about each publisher, with where and when it was read)
  into `data/audit/comparison.csv`, one row per publisher, and prints the counts by status and
  reason code, overall and for the publishers each list tags as openly licensed. No requests.
- `commonswire update`: the weekly update in one command, from a published version in a
  folder (downloaded or local) to the next version, built and checked, in another folder,
  with no state of its own. It reads each source that still publishes over the last 30 days
  (the posts published then, the older posts edited then, and the pages of rows that left the
  listing) by `daily`'s rules, keeps the bylines of released rows from the previous version,
  and builds the next version as the previous rows plus the new ones, with the changed ones
  replaced, minus the removed ones and the takedown list, through `release build`'s checks and
  `release check`. It stops before any request on a registry or series change, an open
  takedown request or an open pull request on the dataset, and after the build on a source
  that refused, failed or ran over its budget (skipped and named), a failed check, or a version
  that shrinks by more than 1%. `--dry-run` marks a build as never to be delivered. Every
  answer is saved once, so `--offline` replays a run with no request. It prints and writes
  counts, ids and hosts only. It uploads nothing.
- Three GitHub Actions workflows, merged switched off: the weekly update
  (`weekly-update.yml`), the Kaggle mirror (`kaggle-mirror.yml`) and an issue when an update
  stops or fails (`failure-issue.yml`). Their schedules are commented out and
  `DELIVERY_ENABLED` is `"false"`, so a run started by hand is a dry run that uploads nothing
  and reads no secret. When switched on, one setting (`CW_DELIVERY_MODE`) chooses between a
  pull request on the dataset (the default) and direct publication. Actions are pinned by
  commit, each job has the least permissions it needs, no workflow runs on pull requests, and
  the secrets live in an environment limited to `main`.
- New Global Voices stories take their writers and translators from the listing's first
  pages (`listingbylines.listing_credits`): page 1 on, until every new story is found with a
  credit block or the pages list only older stories, so they are released with their credit
  instead of held.
- The manifest of a version built by `update` carries what the next update needs: the ids of
  held rows (with source, day and reason; no address, no name), the count of third-party posts
  dropped, and the update's counts and requests per host and day (`update`). Version 0.2.0's
  held rows and count are in `data/update-baseline.json`, checked against its manifest and
  card.
- The dataset card of an updated version says what changed since the version it was built
  from ("This update").
- The polite client can save every answer once and serve it again with no request
  (`AnswerCache`), and can refuse to send anything (`offline`).
- A `publish` dependency group (locked) with the Hugging Face and Kaggle command-line tools
  for the workflows, and `six`, which Kaggle's tool imports without declaring.

- The Zenodo DOI of the code and the source registry, `10.5281/zenodo.24231835` (all versions; Zenodo
  archived the GitHub release `v0.2.0` as `10.5281/zenodo.24231836`): a badge and a "How to
  cite" section in the README, `doi` and `identifiers` in `CITATION.cff`, and a line in the
  dataset card from the next version on.

- The count check of older rows, inside `commonswire update` (`commonswire.counts`): for
  each source that still publishes and each year of its archive, one request reads the
  site's post count (`per_page=1`, the `X-WP-Total` header), and the version's manifest keeps
  the counts (`post_counts`). The next update compares the same ranges. A year whose count
  fell is listed (links only), and the page of each released row missing from that listing is
  read once: 404 or 410 removes the row, by the window's own rule, and any other answer leaves
  it in place, counted. A fall the window's own removals explain is not listed, a rise is
  reported (the edited-since listing already takes a back-dated post as a new row), and
  a version with no counts makes the run a baseline run that records them and compares
  nothing. The requests drops may cost in one run have a ceiling (`--max-count-requests`,
  200 by default, over all sources: Global Voices' largest year takes 150 listing pages);
  past it the source stops, named with the year. The
  summary and the pull request's description give one line per source: years checked, drops,
  rises, rows checked and rows removed.

### Changed
- **The request log and the evidence files name article pages by id:** 105 rows of
  `data/usage_log.csv`, 106 rows of `data/evidence/pages.csv` and 250 rows of
  `license_links.csv`, from the rights-evidence reads of 2026-11-13 to 2026-11-17, named an
  article page by its address. Home and main pages, pages the registry cites for a license or
  terms, and pages that refused keep their address. A test fails on any article address left.
- **What a removal does to earlier versions:** the card of series 0.3 ("Removals and
  corrections"), the Kaggle description, the README and `docs/data-card.md` say that earlier
  versions stay in the dataset's history (each minor release under its tag, each weekly
  version as a commit) and on Kaggle, that they still hold the rows later versions withdrew or
  removed, listed in `changes.csv`, and that an article asked to be removed from every version
  is removed by creating the dataset and its Kaggle mirror again without it.
- **`release check` fails on raw HTML outside code in a card** (an autolink is fine).
- **The Kaggle folder** takes its file descriptions and its configuration words from the
  manifest (no fixed list of license versions); series 0.3 gets a description of its own
  (headings, "How to cite" near the top, under 20,000 characters), five tags, each one of
  Kaggle's own, and a 560 by 280 cover. `changes.csv` has its column descriptions.
- `release`: for an edition under the Lingua rule the rule is checked first, so a row it
  holds is counted under it.
- `validate`: a row of a date its source's license table does not place must be held.
- `docs/automation.md` describes the weekly update as built: what GitHub and Hugging Face
  allow (with links), the run's steps and stops, the delivery modes and their risks, the
  tokens, the options for removals older than 30 days with their cost in requests, and the
  first dry run's numbers. The README and `docs/method.md` say the automatic update is built
  and not switched on yet.
- A Global Voices story that the previous version held, and that has not been edited since,
  keeps its recorded reason with no new look at the listing. The first dry run read 13 listing
  pages to look again at six held stories; the same answers replayed need one page.
- The card says that an article edited at its source is updated however old it is (the
  edited-since listing covers every age); only removals are checked for the last 30 days.
- The weekly update is switched on: `weekly-update.yml` runs every Monday at 06:17 UTC with
  `DELIVERY_ENABLED: "true"`, and a version that passes every check reaches Hugging Face as a
  pull request on the dataset, published when the maintainer merges it. The only secret is a
  Hugging Face token that can open pull requests on the one dataset. Weekly versions are not
  tagged; the merge commit and the manifest name them.
- The Kaggle mirror is updated by hand, about once a month and at each minor release, so no
  Kaggle token is kept on GitHub: `kaggle-mirror.yml` stays off, and the weekly update no
  longer calls it (which also drops its `secrets: inherit`). The prepared Kaggle metadata
  gives the update frequency as monthly.
- The README's status line no longer names a version or row counts; it points to the dataset
  card on Hugging Face for the current version. The README and the docs say the dataset is
  updated weekly by an automatic run that the maintainer approves.
- `docs/automation.md`, section 5, describes the count check as built, with its dry run of
  2026-11-17 (a baseline run from 0.2.2: 80 years counted with 80 requests); the README,
  `docs/method.md` and `docs/data-card.md` say how older removals are found.
- `docs/automation.md` records the first weekly run on GitHub (0.2.0 to 0.2.1, 2026-11-15):
  per source, the requests, the checks and the time it took, in place of the estimate, and
  that Hugging Face opens the weekly pull request as a draft.

### Fixed
- A byte budget used up at robots.txt was taken for an unreachable robots.txt and reported as
  a refusal; it is now reported as the budget.
- `release check` of a version built by `update` (its manifest has an `update` block) no
  longer compares the rows with the local corpus report, which describes the last local build
  and so falls short by the week's new rows; it prints one line saying the comparison was
  skipped. A locally built version is compared as before.
- Two rows removed in the same update were taken for copies of each other (a removed row
  keeps the hash of the empty text), so the second was counted as an exact duplicate instead
  of a removal. Removed rows now stay out of the duplicate checks; both were left out of the
  release either way, and no published version had two.

## [0.2.0] - 2026-11-14

The first code release, made with version 0.2.0 of the dataset (published on Hugging Face
and Kaggle on 2026-11-14); it also holds everything that built version 0.1.0 of the dataset.

### Fixed
- The story listing kept a story's first sighting even when it was a featured teaser with no
  credit block (the home page shows several); a story now takes its writers from the first
  sighting that has a credit block. On the saved Global Voices walk it changed no story (11
  stories were seen twice, none first as a teaser), and the counts now say so
  (`seen_again`, `credits_from_later_sighting`).
- A WordPress post whose `date_gmt` is the zero date (given as a time near the Unix epoch) has
  no date: the post is dropped and counted as invalid, never given 1970 as its publication
  date (one Global Voices post).
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
- Version series 0.2: the six sources of 0.1 and Global Voices (`release build --version
  0.2.0`). Its rows gain `translators` (after `authors`): the translators the source names,
  apart from the writers, empty for every source but Global Voices. The credit line names them
  ("This story by A, translated by B, originally appeared on Global Voices: ..."): when an
  article names translators, `{authors}` is followed by ", translated by" and their names, set
  off by commas. Series 0.1 keeps its 18 columns, so a 0.1.x build keeps 0.1.0's columns;
  `release check` refuses a version whose files do not have its series' columns, and the
  Kaggle metadata lists each Parquet file's own columns.
- `.zenodo.json`, the metadata Zenodo reads when it archives a GitHub release of the
  repository (in place of `CITATION.cff`): the title "CommonsWire: code and source registry, no
  article text", the creator and affiliation, Apache-2.0, keywords, a description, and links to
  the dataset on Hugging Face and its Kaggle mirror. Releases are made for code and registry
  milestones only. `CITATION.cff` now describes the repository the same way (same title,
  license and creator) and cites the published dataset, version 0.1.0 of 2026-11-14.
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
- The README, `CITATION.cff` and the docs describe version 0.2.0, published on 2026-11-14:
  the status line, Global Voices and the `translators` field (README); the citation of the
  dataset at 0.2.0 (`CITATION.cff`); the 0.2.0 card (`docs/data-card.md`); series 0.2 and its
  column (`docs/release-layout.md`); and the weekly update from 0.2.1 on, with Global Voices'
  new stories held until `daily` reads the first page of its story listing
  (`docs/automation.md`). The package version is 0.2.0 (it was 0.1.0.dev0), so requests name
  `CommonsWire/0.2.0`.
- A row held because its byline names only an account (such as "Guest Contributor") says so:
  "credited to an account, not a person: ... asks for the author's name"; the story listing
  records the reason as `not_a_person`, as the article-page reader does, and drops accounts
  named as translators. The release manifest counts held rows by reason
  (`held_rows_by_reason`).
- The dataset card follows the release: the sources in words, largest first; which source is
  most of the corpus; the share of short texts per source, with the reason where it is known
  (Global Voices' early link posts); held rows by reason; the `translators` field and its
  credit-line rule; the story listing as a byline route; and, from series 0.2, a "Changes
  since 0.1.0" section.
- `release zenodo` now checks the GitHub route by default: `.zenodo.json` (the fields Zenodo
  needs, in the forms its deposit metadata accepts, and agreement with `CITATION.cff`) and the
  release archive (it must carry `.zenodo.json` and neither the request log nor any collected
  data), and prints the maintainer's steps. The folder for a deposit by hand on Zenodo's
  website is the fallback, `release zenodo --website`.
- The request log (`data/usage_log.csv`) no longer lists article addresses. A request for one
  article's page (a byline read from the page, or the check for a removed article) is logged
  with the article's id (`cw_` and 16 hex digits) in place of its path; listing, API, feed,
  robots.txt and policy-page paths are logged as before. The 4,192 earlier page-byline rows and
  2 route-test rows were rewritten once the same way (the full log is kept, untracked, with the
  raw data). The log is a record of politeness, not a list of articles: an article list in the
  repository would outlive a takedown. Release archives leave the log out
  (`.gitattributes`: `export-ignore`).
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
