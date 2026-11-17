# Automation

CommonsWire's weekly update is **switched on**. One command, `commonswire update`, builds the
next dataset version from the one published on Hugging Face. Three GitHub Actions workflows
run it and deliver the result:

- `weekly-update.yml`: the update itself, every Monday at 06:17 UTC (and by hand from the
  Actions tab). A version that passes every check reaches Hugging Face as a pull request on
  the dataset, and it is published when the maintainer merges it;
- `kaggle-mirror.yml`: the Kaggle mirror, **off**. The maintainer updates Kaggle by hand, about
  once a month and at each minor release (section 4 says why);
- `failure-issue.yml`: an issue in this repository when an update stops or fails.

Setting `DELIVERY_ENABLED` to `"false"` in `weekly-update.yml` makes every run a dry run
again: it reads the sources and builds and checks the version on GitHub's runner, then uploads
nothing and opens no pull request and no issue. Section 6 lists how it was switched on and how
to stop it.

Section 7 (coding costs) is a **DRAFT** that describes plans: no coding has been run.

## 1. What the platforms allow (read on 2026-11-14)

### GitHub Actions
- **Scheduled runs.** A `schedule` trigger runs on the latest commit of the default branch,
  at most once every 5 minutes. Runs "can be delayed during periods of high loads", the start
  of every hour among them, and some queued jobs may be dropped when the load is high enough.
  [Events that trigger workflows](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows)
- **Scheduled runs stop on their own.** "In a public repository, scheduled workflows are
  automatically disabled when no repository activity has occurred in 60 days." The weekly run
  commits nothing, so 60 days with no commit to this repository switch it off. The monthly
  Dependabot pull requests, once merged, count as activity. A disabled workflow is enabled
  again from the Actions tab or with `gh workflow enable`.
  [Disabling and enabling a workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow)
- **Manual runs.** `workflow_dispatch` adds a "Run workflow" button once the workflow file is
  on the default branch, with up to 25 inputs.
- **Secrets.** "With the exception of `GITHUB_TOKEN`, secrets are not passed to the runner
  when a workflow is triggered from a forked repository." A secret that is not set reads as an
  empty string. Logs mask secrets, but "automatic redaction is not guaranteed" for transformed
  values or structured data.
  [Using secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- **Environments.** Free accounts can configure environments for public repositories.
  Environment secrets are "only available to workflow jobs that use the environment". An
  environment can require reviewers and limit which branches may deploy. "Running a workflow
  that references an environment that does not exist will create an environment with the
  referenced name."
  [Managing environments](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)
- **Artifacts.** Downloading a run's artifacts needs only read access to the repository, which
  for a public repository is everyone. Logs and artifacts are kept for 90 days by default (1 to
  90 days for a public repository). So the workflows upload no artifact at all.
  [Downloading artifacts](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/downloading-workflow-artifacts)
- **Limits.** "GitHub Actions usage is free for standard GitHub-hosted runners in public
  repositories". A job may run for 6 hours and a workflow run for 35 days. A queued job not
  picked up by a GitHub-hosted runner within 45 minutes is discarded. An `ubuntu-latest`
  runner for a public repository has 4 CPUs, 16 GB of memory and 14 GB of SSD.
  [Limits](https://docs.github.com/en/actions/reference/limits),
  [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- **Hardening.** Pin actions to a full commit SHA. Give `GITHUB_TOKEN` read access by default
  and more only where needed. "Avoid using the `pull_request_target` workflow trigger if it's
  not necessary". Pass untrusted input through an environment variable, never straight into a
  script.
  [Security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)

### Hugging Face
- **Pull requests on a dataset.** A pull request's commits are stored in refs named like
  `refs/pr/42` on the dataset repository itself. They are not fetched by a plain clone, but
  "they can still be fetched on demand". On a public dataset, a pull request and its files can
  be seen before it is merged.
  [Pull requests and discussions](https://huggingface.co/docs/hub/repositories-pull-requests-discussions)
- **Opening one.** `create_commit` and `upload_folder` take `create_pr=True`, and
  `hf upload` takes `--create-pr`, with `--delete` (patterns of files to delete in the same
  commit) and `--commit-description`. A pull request is merged with `merge_pull_request()`,
  with `hf discussions merge`, or on its page.
  [Upload guide](https://huggingface.co/docs/huggingface_hub/guides/upload),
  [CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli),
  [Community guide](https://huggingface.co/docs/huggingface_hub/guides/community)
- **What a pull request needs.** The Python library's own source (`huggingface_hub` 2.4.0,
  `create_commit`) says "users with read permission should still be able to create PRs even
  if they don't have write permission on the target branch". The permission it names for
  discussions and pull requests is `discussion.write`.
- **Fine-grained tokens** can be limited to specific repositories. A leaked token is deleted
  or refreshed from the Access Tokens settings.
  [User access tokens](https://huggingface.co/docs/hub/security-tokens)
- **Storage.** Storage for public repositories of a free account is "best-effort": "Beyond the
  first few gigabytes, please use this resource responsibly". Each weekly version adds the
  Parquet files that changed to the repository's history. After a pull request is closed or
  merged, its ref can be deleted to free space. `super_squash_history` would reclaim more, but
  it removes old versions (and with them the tags `v0.1.0` and `v0.2.0`), so it is not used.
  [Storage limits](https://huggingface.co/docs/hub/storage-limits)

### Kaggle
- The Kaggle command-line tool (2.2.5) reads an API token from `KAGGLE_API_TOKEN`; the token
  is made under "API" at <https://www.kaggle.com/settings/api>. It acts for the whole account:
  Kaggle offers no narrower scope.
- **File and column descriptions are not saved through the API.** That is Kaggle's own open
  bug ([kaggle-cli#1207](https://github.com/Kaggle/kaggle-cli/issues/1207), opened
  2026-10-01). Descriptions sent with `datasets create`, `datasets version` or `datasets
  metadata --update` are accepted with no error and never saved. The tool's request carries
  them correctly, and descriptions typed in Kaggle's web editor are saved. CommonsWire's
  prepared metadata follows Kaggle's documented format: every column, in order, with types
  from Kaggle's list. So nothing in the metadata needs fixing.
  [Kaggle's dataset metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets_metadata.md)

## 2. What a weekly run does
The run is `commonswire update --from PREV --out NEXT` on GitHub's runner. It uses plain
Python and the repository's own commands, and it keeps no state on the runner or on any
drive.

1. **It starts from the published version.** It downloads, with no token, the latest version
   on the dataset's `main` branch: the Parquet files, `index.csv`, `sources.csv`, the card and
   the manifest. The next version number is the next patch (0.2.0 → 0.2.1 → 0.2.2 …).
2. **It checks before it sends anything.** The run stops at once, with no request to any
   source, when:
   - the downloaded version fails its own manifest check;
   - `data/sources.csv` differs from the registry the published version carries;
   - the next version would have other sources;
   - a takedown request is open (an issue labeled `takedown`);
   - an earlier week's pull request on the dataset is still open;
   - the output folder is not empty.
3. **It reads each source that still publishes**, one source and one request at a time,
   through the polite client, over the last 30 days. Wikinews is closed and gets no request.
   For each source, the run reads:
   - robots.txt;
   - the category names, used to drop partner stories;
   - for Alt News, its users endpoint, where its bylines come from;
   - the posts published in the last 30 days;
   - the older posts edited in those 30 days.

   These are `daily`'s rules:
   - a post that is not in the published version is new;
   - a post whose text hash differs is changed (status `changed`);
   - a row of the 30 days that the listing no longer has, and whose page answers 404 or 410,
     is removed.

   Released rows keep their bylines from the published version, so a changed row needs no
   request for them. New rows take theirs from three places:
   - the API;
   - their own page (360info, The Public Record, Balkan Diskurs: one request each);
   - for Global Voices, its story listing from page 1 on, until every new story is found with
     its credit block. The writers and translators are kept apart.

   Then the **count check** of older rows (section 5): for each year of the source's archive,
   the site's post count, compared with the counts the published version recorded. A year
   whose count fell is listed, and the page of each released row missing from that listing is
   read once (404 or 410: removed).
4. **It builds the next version.** That is the published rows, plus the new ones, with the
   changed ones replaced, minus the removed ones and the takedown list. The build uses
   `release build`'s own code:
   - every row is validated and its credit line checked against its source's template;
   - near-duplicates are flagged over every row, new and old;
   - the card says what changed ("This update");
   - the manifest is written.

   Then `release check` runs on the files, and Hugging Face's validator on the card.
5. **It stops after the build** when:
   - a source refused, failed or ran over its byte budget (100 MB a source, 300 MB a run), or
     a drop in its counts needed more requests than the run allows (section 5). That source's
     rows are carried over unchanged and the source is named; a refusal is never worked
     around;
   - a check failed;
   - the version would shrink by more than 1% in all, or for one source by more than 1% and
     more than 10 rows.

   The maintainer can let a named source be skipped for one manual run (the `allow_skipped`
   input).
6. **It delivers** in the mode the setting gives (section 3). A dry run ends with the
   summary.

**Held rows are not published**, so the manifest carries what the next run needs: the ids of
held rows, with source, day and reason (never an address or a name), the count of
third-party posts dropped, and each source's post counts per year (`post_counts`). Version 0.2.0 was built before updates existed, so its 275 held
rows and its count of 2,476 third-party posts are in `data/update-baseline.json`. That file is
checked against 0.2.0's manifest (by SHA-256) and against its card.

**Edits and removals.** The edited-since listing covers articles of every age, so an article
corrected at its source, however old, gets its new text in the next version. Removals of the
last 30 days are found by the listing; older ones by the count check (section 5).

**What the run shows in public.** The run's log, its job summary and the pull request carry
counts, ids and hosts only: never article text, a title, a name or an article's address. An
error message is cut to the host before it is printed. The run uploads no artifact. Every
request is logged on the runner. Because a run commits nothing to `main`, its requests are
summed per host and day into the new version's manifest (`update.requests`).

**Replays.** Every answer is saved once in the run's answer folder. A stopped run resumes
without asking again, and `commonswire update --offline` replays a finished run with no
request at all.

### Sources read from their article pages (series 0.3 on)
Series 0.3 adds two publishers whose API does not give their articles: SciDev.Net and Africa
Is a Country. Their archives were read page by page (`commonswire backfill-pages`), and their
weekly route reads only what is new or edited, each page once, through the same page
fetchers and the polite client:

- **SciDev.Net:** the sitemap index, then its newest article sitemap. The site lists its
  articles by the date they last changed, oldest first, so the newest sitemap holds the new
  and the edited ones. The one before is read only while a sitemap still starts after the
  mark, and three at most. The pages read are the articles changed after the mark: the
  newest change date the previous version saw.
- **Africa Is a Country:** listing pages 1 and 2, newest first, and one more while the last
  page read shares no story with the previous version (five at most; past that the source
  stops). The pages read are the stories the previous version neither has, holds nor saw on
  these pages last time. Its pages give no date of change, so an edit of an older story is
  not seen.

A page not in the previous version is a new row (held when the byline is missing and the
publisher asks for it). A page whose text hash differs is changed. A released row whose page
now answers 404 or 410 is removed. The mark (a date) and the stories seen (ids) go into the
next manifest as `page_state`. A source that would need more than 60 requests in a week stops
before reading its pages, and is named. Page sources have no post counts per year, so the
count check (section 5) does not cover them: a story that leaves a sitemap or the listing is
not looked for.

`commonswire update-route SOURCE --from VERSION --work DIR` runs one page source's route
alone, as a dry run. `--max-requests` caps it and `--offline` replays it. It writes a summary
of counts and ids, never a version.

### The first dry run (2026-11-14)
One live run on the maintainer's machine, from the published 0.2.0 to an unpublished 0.2.1,
with `--dry-run`. Version 0.2.0 had been collected about 18 hours earlier, so "new" here
covers those 18 hours, not a week; the 30-day listings are the same as in a weekly run.

| Source | Posts listed | New | Changed | Removed | Held | Requests | Bytes |
|---|---|---|---|---|---|---|---|
| Wikinews | closed, no request | | | | | 0 | 0 |
| 360info | 21 | 0 | 0 | 0 | 0 | 4 | 256,044 |
| The Public Record | 23 | 2 (bylines from their pages) | 1 | 0 | 0 | 6 | 583,287 |
| Balkan Diskurs | 8 | 0 | 0 | 0 | 0 | 4 | 133,957 |
| Factly | 62 | 0 | 0 | 0 | 0 | 6 | 853,011 |
| Alt News | 32 | 1 | 1 | 0 | 0 | 5 | 561,404 |
| Global Voices | 79 | 2 (both credited from the listing, one with a translator) | 0 | 0 | 6 (all already held) | 21 | 3,371,672 |

- No source refused: 46 requests, all answered 200 but one redirect, 5.8 MB in all.
- 149,147 rows before and 149,152 after; 275 held rows, as before; 220.2 MB.
- Every check passed: `release check`, Hugging Face's card validator, and the scan for
  article text, titles and names in what the run shows (none).
- It took 510 seconds: about 230 for the build (collect, near-duplicates and the files, 3.2
  GB of memory at most) and the rest for paced requests.
- The published 0.2.0 was read only; its files are unchanged.
- An offline replay of the saved answers sent no request and wrote the same files.

That run read 13 Global Voices listing pages to look again at six stories it already held,
the oldest from 2026-10-21. Since then, a held story that has not been edited since the last
version keeps its recorded reason with no new look at the listing. The replay needed 1 page,
for the 2 new stories, so a weekly run now sends about 34 requests plus one for each new page
byline.

### The first weekly run on GitHub (2026-11-15)
Started by hand at 00:41 UTC, from the published 0.2.0 to 0.2.1, delivered as a pull request on
the dataset and merged by the maintainer at 01:03 UTC.

| Source | Posts listed | New | Changed | Removed | Held | Requests | Bytes |
|---|---|---|---|---|---|---|---|
| Wikinews | closed, no request | | | | | 0 | 0 |
| 360info | 21 | 0 | 0 | 0 | 0 | 4 | 256,044 |
| The Public Record | 23 | 2 (bylines from their pages) | 1 | 0 | 0 | 6 | 583,286 |
| Balkan Diskurs | 8 | 0 | 0 | 0 | 0 | 4 | 133,957 |
| Factly | 62 | 0 | 0 | 0 | 0 | 6 | 853,011 |
| Alt News | 32 | 1 | 1 | 0 | 0 | 5 | 561,404 |
| Global Voices | 79 | 2 (both credited from listing page 1, one with a translator) | 0 | 0 | 6 (all already held, kept without a walk) | 9 | 1,456,420 |

- Every source answered GitHub's runner as it answered the maintainer's machine: 34 requests,
  all 200 but one redirect, 3.8 MB in all, no refusal.
- 149,147 rows before and 149,152 after; 275 held rows, as before; no new third-party post.
- Every check passed on the runner (`release check`, the card validator), and again on a
  signed-out download of the pull request: every 0.2.0 row is in 0.2.1 or counted, the
  149,145 unchanged rows are the same in every column, the configurations and the 19 columns
  are the same, and the held and third-party counts add up.
- Only the six files that changed were uploaded (two of the five Parquet files, `index.csv`,
  the card, `LICENSES.md` and the manifest).
- The job took 8 minutes: 2 seconds to install, 9 seconds to download the 211 MB version,
  7 minutes 48 seconds to read the sources and build (467 seconds), and 4 seconds to open
  the pull request. It fits the free limits for a public repository by a wide margin (the
  job's limit is 6 hours).
- The token that can only open pull requests was enough. Hugging Face opens a pull request
  made through its API as a **draft**: the maintainer takes it out of draft, then merges it.
  A draft counts as open, so it stops the next run until it is merged or closed.

## 3. Delivery: one setting, two modes
The repository variable `CW_DELIVERY_MODE` chooses the mode:

- **`pull-request`** (the default, the value used when the variable is unset, and the mode in
  use). The run uploads the version to Hugging Face as a pull request on the dataset, with the
  summary as its description. The pull request opens as a draft; the maintainer takes it out
  of draft and merges it. Weekly versions are not tagged: the merge commit and the manifest
  name them. Risks:
  - nothing reaches users until the maintainer looks;
  - a pull request on a public dataset can be seen and downloaded before it is merged (it
    has passed every check);
  - a week with no merge holds the next week back, since an open pull request stops the next
    run.
- **`automatic`** (not in use). The run publishes directly when every check passes: it
  uploads to `main` and tags `vX.Y.Z`. Risks:
  - a problem the checks do not catch reaches users at once;
  - the Hugging Face token must be able to write, and it sits in the job that also reads the
    sources' pages.

In both modes the Kaggle mirror is updated by hand (`kaggle-mirror.yml` stays off), about
once a month and at each minor release, and minor releases (0.3.0 and on) are tagged by hand.

In both modes, a stop or a failure opens an issue in this repository (or adds a comment to
the open one). The issue holds the summary and the run's link.

## 4. Tokens and where they go
Secrets go in the environment `release` (Settings → Environments), with deployments limited to
the `main` branch. They are not repository secrets. Only jobs that name the environment can
read them, and only from `main`. No workflow runs on pull requests, so a fork's pull request
never reaches a secret.

| Secret | Mode | Scope |
|---|---|---|
| `HF_TOKEN` | pull-request (in use) | Fine-grained, on the one dataset `obadakr/commonswire`, with only the permission to open pull requests (`discussion.write`, "interact with discussions / open pull requests"). It cannot publish by itself. This is the only secret on GitHub. |
| `HF_TOKEN` | automatic (not in use) | Fine-grained, on the one dataset, with write access to its contents (needed to upload to `main` and to tag). |
| `KAGGLE_API_TOKEN` | not on GitHub | Kaggle's API token acts for the whole account (Kaggle has no narrower scope), so it stays off GitHub, and the Kaggle mirror is updated by hand. |
| `HF_WRITE_TOKEN` | not on GitHub | Would let the mirror tag weekly versions. Without it, weekly versions are not tagged; the merge commit and the manifest name them. |

`GITHUB_TOKEN` (the workflow's own token, no secret to add) reads issues to count open
takedown requests and writes the failure issue.

## 5. Removed and corrected articles older than 30 days
Edits of any age are already caught (section 2). A WordPress site lists no deleted posts, so
older removals take extra requests. Three options were weighed, with their weekly cost in
requests as estimated on 2026-11-14 (the dry run below counted 80 years, not 67):

| Option | Requests a week | Finds |
|---|---|---|
| A. Count check per year: the site's post count per year of archive (`per_page=1`, read from the `X-WP-Total` header), compared with last week's, kept in the manifest. A drop in a year triggers a listing of that year's ids and a page check of the rows gone from it. | about 67 (one per source and year: Global Voices 23, Factly 13, Alt News 10, Balkan Diskurs 9, 360info 6, The Public Record 6), a few KB each, about 4 minutes; plus about 10 to 100 more in a week when a count drops | any removal, in the week it happens; a removal offset by a back-dated new post in the same year is missed |
| B. Rolling re-check: a fixed number of old article pages a week, oldest checked first. | 200 (about 20 MB) | about 200 of 149,000 rows a week, so the whole corpus every 14 years: an estimate of the removal rate, not a check |
| C. Full id listing (`_fields=id,link`, 100 a page) once a month. | about 1,500 a month (Global Voices alone has 1,045 pages, about 3 hours at its 10-second crawl-delay) | every removal, up to a month late |

**A is built** (`commonswire.counts`, inside `commonswire update`; merged after its dry run of
2026-11-17). How it works:

- **The counts.** For each source that still publishes and each year of its archive (from
  the year of its oldest released row), one request:
  `/wp-json/wp/v2/posts?per_page=1&after=...&before=...&_fields=id`, read from the
  `X-WP-Total` header. A past year is counted whole; the current year up to the day before the
  run, since every site's time zone has published those days by then. The manifest keeps the
  counts (`post_counts`: per source and year, the count and the day its range ends).
- **The comparison.** The next update reads the same ranges again. The current year takes
  one more request: the days the previous version counted (to compare) and the longer range
  (to record). The compared range reaches past the start of the 30-day window, so every
  older post is covered by one or the other.
- **No counts yet.** A version without `post_counts` (0.2.2 and every version before it)
  makes the run a baseline run: it records the counts and compares nothing, and says so in
  its summary and in the card. The run of 2026-11-23 is the baseline run; the run of
  2026-11-30 is the first to compare.
- **A count that fell.** The run lists that year's posts (links only, 100 a page, with two
  days added on each side, so that a row's day in UTC and the site's own day cannot fall on
  different sides of the edge) and reads, once, the page of each released row missing from
  that listing, logged by its id. 404 or 410: the row is removed, as in the window. Any other
  answer: the row stays and is counted (`rows_kept`). A fall that the window's own removals
  explain (a removal of the last 30 days inside the compared range) is not listed. Rows the
  run has already read (listed in the window, edited or checked) are not checked again.
- **A count that rose.** A back-dated or restored post. Today's rules already take it: its
  modified date falls in the window, so the edited-since listing reads it, and `daily`'s rules
  make it a new row (or hold or drop it). Nothing more is done; the rise is reported.
- **The ceiling.** The requests that drops may cost in one run (listing pages and page
  checks, over all sources) are limited to 200 (`--max-count-requests`). The largest year of
  any source, Global Voices' 2007 (14,967 posts), takes 150 listing pages, which leaves 50
  page checks; at its 10-second crawl-delay that is about 33 minutes. Before a year is
  listed, the run checks that its pages fit (its count divided by 100, plus 2), and before the
  page checks, that the missing rows fit. Past the ceiling the source stops, named with the
  year (status `over_ceiling`): a removal on that scale is for the maintainer to look at.
  Its rows and its previous counts are carried over, so the drop is still there the next
  week. A manual run with `allow_skipped` delivers the other sources meanwhile.
- **A source that refuses the count requests** is skipped like any refusing source
  (section 2, step 5), and its previous counts are carried over.
- **What it misses.** A removal offset by a back-dated post in the same range in the same
  week; and older posts published between two runs more than 29 days apart, which the window
  no longer reaches and the previous counts did not cover.
- **What it shows.** The summary and the pull request's description get one line per
  source: years checked, drops (year and size), rises, rows checked and rows removed. Counts
  and years only.

### The count check's dry run (2026-11-17)
One dry run from the maintainer's Mac, from version 0.2.2 as published on Hugging Face's
`main` (commit `b61cbc8d`), on 2026-11-17 from 00:05:54 UTC. It was a baseline run, since
0.2.2 has no counts: 80 years were recorded and nothing was compared.

| Source | Years | Count requests | All requests | Bytes | Posts counted | Rows released (0.2.2) |
|---|---|---|---|---:|---:|---:|
| 360info | 2021 to 2026 (6) | 6 | 10 | 267,761 | 2,425 | 2,401 |
| Alt News | 2016 to 2026 (11) | 11 | 16 | 530,126 | 5,822 | 5,804 |
| Balkan Diskurs | 2014 to 2026 (13) | 13 | 17 | 147,076 | 897 | 880 |
| Factly | 2014 to 2026 (13) | 13 | 19 | 883,079 | 15,161 | 15,108 |
| Global Voices | 2004 to 2026 (23) | 23 | 32 | 1,424,106 | 104,481 | 101,566 |
| The Public Record | 2013 to 2026 (14) | 14 | 20 | 604,341 | 2,773 | 2,754 |
| **All** | 80 | 80 | 114 | 3,856,489 | 131,559 | 128,513 |

- 114 requests (80 of them counts, 1,133 bytes of answers between them), 3.86 MB, 782 s
  (13 minutes; the update of 2026-11-16 took 430 s on GitHub's runner, and the first dry
  run, with no counts, 510 s from the same Mac). Every
  answer was 200 but Global Voices' usual 301; no source refused.
- 0.2.2 to 0.2.3: 4 new, 2 changed, 0 removed, 275 held; every check passed. Being a dry
  run, it was never to be delivered, and its folder is never uploaded.
- The sites count a little more than the released rows (Global Voices 104,481 posts, 101,566
  rows): their counts include the third-party and held posts.
- **The weekly cost from 2026-11-30:** 86 count requests (80, plus one for each source's
  current year), about 5 minutes more per run, most of it Global Voices' 24 at 10 seconds. A week with a
  drop costs up to 200 more.

## 6. Switching it on, and off
It is switched on in mode `pull-request`, with:

1. the environment `release`, with deployments limited to `main`, holding the one token
   `HF_TOKEN` (section 4);
2. no `CW_DELIVERY_MODE` (so `pull-request`);
3. `DELIVERY_ENABLED: "true"` in `weekly-update.yml` and its schedule uncommented
   (`kaggle-mirror.yml` stays off);
4. a first run started by hand from the Actions tab, then the Monday schedule.

To stop it, disable the workflow in the Actions tab (or with `gh workflow disable`), set
`DELIVERY_ENABLED` back to `"false"`, or delete the token.

## 7. Where the coding could run, and what it costs (DRAFT)
Coding is never run in a development session. Each option below would run as a script with
its own log of tokens and cost.

**Tokens per article** (to be measured in the coding pilot): about 1,500 input tokens of article
text (from the sample's median length) plus about 2,500 tokens of codebook instructions, and
about 300 output tokens for the four variables: about 4,300 tokens in all. For 1,000 articles,
about 4.0 million input and 0.3 million output tokens.

| Option | Models | Cost per 1,000 articles | Daily capacity | Fit |
|---|---|---|---|---|
| Hugging Face Inference Providers on the PRO credits | Open models (Apache-2.0 or MIT) served by providers | Provider prices vary by model; PRO includes "$2.00" of monthly credits, then pay as you go | Covers only a small daily volume within the included credits | Simple to call; check each provider's terms; the credits are small |
| OpenRouter free models | Free variants of some open models | $0 | 50 requests a day without purchased credits, 1,000 a day after a one-time purchase of 10 credits (as of 2026-11-12) | Free tiers may log prompts (the texts are public news, so this is acceptable); models and limits change without notice; licenses vary by model |
| An open model in a scheduled Kaggle notebook | An Apache-2.0 or MIT model of about 8 billion parameters on two T4 GPUs | $0 | To be measured; the weekly GPU quota is set per account | The default for published labels: open license, reproducible, no spend |
| Claude Batch API | Claude Haiku 5.5 or Claude Sonnet 5.5 | Haiku 5.5: about $0.55 standard, about $0.28 batch; Sonnet 5.5: about $11 standard, about $5.50 batch (less with prompt caching of the codebook) | Large | A strong second coder for validation; needs approved spend; its labels are not released as the published values, which use Apache-2.0 or MIT models |

Prices: Claude Haiku 5.5 is $0.10 per million input tokens and $0.50 per million output tokens,
Claude Sonnet 5.5 $2.00 and $10.00, with a 50% discount through the Batch API (Anthropic's
price list as of 2026-11-03). Thinking tokens, if used, add to the output count.

**Recommendation:** the Kaggle notebook codes every article with an open model (published
values); the Claude Batch API codes a stratified sample as the second coder for reliability
(about 1,000 articles a quarter, under $6 at Sonnet 5.5 batch prices), after the spend is
approved.

**Tokens per day, from the sample of 2026-11-13.** The median article is 1,198 words at Global
Voices and 1,130 at 360info (about 1,500 to 1,600 tokens), which matches the assumption above.
The sources publish about 5 to 10 articles a day in all, about 20,000 to 45,000 tokens a day,
which every option above handles; the cost question is the backfill, not the weekly run.

| Workload | Articles | Tokens | Haiku 5.5 batch | Sonnet 5.5 batch | Kaggle |
|---|---|---|---|---|---|
| Daily, included sources | 5 to 10 | 20,000 to 45,000 | under $0.01 | about $0.05 | minutes |
| Backfill of the measured included sources (Global Voices, 360info, The Public Record, Balkan Diskurs) | about 93,000 after the third-party drop | about 400 million | about $26 | about $510 | to be measured; tens of GPU hours |
