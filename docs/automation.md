# Automation

Sections 1 to 3 describe plans (**DRAFT**), not what version 0.2.0 does. Version 0.2.0 has no
scheduled job: the daily fetch and the release build are local commands that the maintainer
runs by hand (section 0), and every publishing step stays behind the maintainer's release
approval.

## 0. Until the jobs run: the manual weekly update
Once a week, on the maintainer's machine with the data drive mounted, three steps:

```bash
uv run commonswire daily                                 # new, changed, removed articles
uv run commonswire release build --version 0.2.N         # the next version, from the rows
# then the maintainer's upload step: the new version to Hugging Face (old Parquet files
# replaced, the version tagged) and a new Kaggle version
```

- `daily` asks each source's API for posts published or modified since the last run, through
  the polite client, and checks the last 30 days for removed articles. Its answers are saved
  once, so `commonswire build` can always rebuild the same rows.
- `release build` writes `data/release/0.2.N/` and checks it (`docs/release-layout.md`). After
  version 0.2.0 (published on 2026-11-14), the version number goes up by one each week (0.2.1,
  0.2.2, ...); a new source starts a new series. Before the upload, `commonswire
  release kaggle --version 0.2.N` prepares the Kaggle folder.
- Global Voices' new stories stay held for now: its API gives no author names, and `daily`
  does not yet read the first page of its story listing, where their writers are named.
- A published version is never rebuilt; the next week gets the next number.

**What the jobs (session S5) will automate:** the daily fetch on a schedule (section 1), the
weekly release build and its checks, the upload behind the release approval (section 3), and a
monthly check of older articles for removals and corrections, which `daily` does not cover yet
(it looks back 30 days).

## 1. The daily fetch on GitHub Actions (DRAFT)
- **Schedule:** one workflow a day (cron, early UTC), plus a manual trigger.
- **What it does:** for each source with `status=include`, ask the source's API or feed for
  articles published since the last fetch, through the same polite client as every other
  request (one request at a time, at least 2 seconds apart, robots.txt and crawl-delays honored,
  the CommonsWire user agent). Drop and count third-party material, build rows, run
  `commonswire validate`, and stop with an error if anything fails.
- **Where the data lands:**
  - the day's raw API answers and new rows go to a private Hugging Face dataset repository used
    as storage (`obadakr/commonswire-staging`, private), never to the code repository;
  - the public dataset (`obadakr/commonswire`) is updated only by the release job (section 3);
  - the request log for the day is attached to the workflow run as an artifact.
- **Secrets:** a Hugging Face write token scoped to the staging repository, stored as a GitHub
  Actions secret; no other secret is needed for collection.
- **Limits:** a run stops after a fixed number of requests and bytes per source, so a site
  change cannot turn the job into a crawl. A source that answers 401, 403 or a bot check is
  skipped and flagged for a person; it is never retried another way.
- **Changed and removed articles:** a weekly job compares the last 30 days in the store with
  each source's API listing (dates and ids only); a monthly job does the same for the past year
  and checks a rotating share of older URLs (`docs/method.md` §4).

## 2. Where the coding could run, and what it costs (DRAFT)
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
The nine included sources publish about 5 to 10 articles a day in all (Global Voices 1.5, The
Public Record 0.6, 360info 0.45, Balkan Diskurs 0.3, Wikinews 0 since its closure; EFF, NIH,
Africa Is a Country and the Freedom of the Press Foundation not yet measured). That is about
20,000 to 45,000 tokens a day, which every option above handles; the cost question is the
backfill, not the daily run.

| Workload | Articles | Tokens | Haiku 5.5 batch | Sonnet 5.5 batch | Kaggle |
|---|---|---|---|---|---|
| Daily, included sources | 5 to 10 | 20,000 to 45,000 | under $0.01 | about $0.05 | minutes |
| Backfill of the measured included sources (Global Voices, 360info, The Public Record, Balkan Diskurs) | about 93,000 after the third-party drop | about 400 million | about $26 | about $510 | to be measured; tens of GPU hours |

If the pending sources with explicit bulk permission are accepted (KFF Health News at 2.3 a day,
the States Newsroom outlets), the daily volume grows several times over; it stays small next to
the backfill.

## 3. Release cadence (DRAFT)
| Where | Cadence | What |
|---|---|---|
| Hugging Face (`obadakr/commonswire`) | Weekly commits to start (daily once the pipeline is stable) | One configuration per license class (`pd`, `by`, `by-sa`), Parquet files by month, the data card, release notes with counts of new, changed and removed rows |
| Kaggle | A weekly version | A mirror of the Hugging Face files, with the same card |
| Zenodo | A record after the first release's checks, then by version series | The code, the source registry and the card, with a DOI for citation, and no article text (a Zenodo record cannot be withdrawn, and articles must stay removable on request) |

Every publishing step needs the maintainer's release approval in the repository, and the
first release is made by hand. A release job would run `commonswire release build` and
`release check` (removed and taken-down rows are left out, every row is checked), write the
release notes, and only then upload.
