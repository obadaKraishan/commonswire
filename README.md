# CommonsWire

CommonsWire is a full-text corpus of news that may legally be redistributed. It collects
articles only from sources whose own pages allow their text to be shared unchanged (public
domain and Creative Commons licenses), and it keeps each article's license and credit line on
its row. New versions are published by the maintainer, about weekly for now; a daily automatic
update is planned. The variables that communication and journalism researchers usually code by
hand (topic, frame, the types of sources quoted, and tone) are planned for a later version.

**Status:** version 0.1.0, published on 2026-11-14: 47,585 articles from six sources, no
coded variables yet.

## The dataset
- **Hugging Face:** <https://huggingface.co/datasets/obadakr/commonswire>
- **Kaggle (a mirror):** <https://www.kaggle.com/datasets/obadakraishan/commonswire>

Version 0.1.0 holds the full text of 47,585 articles (22.7 million words, 2004 to 2026) from six
sources: English Wikinews (a closed archive), 360info, The Public Record, Balkan Diskurs, and
the fact-checkers Factly and Alt News. There is one configuration per license class: `by`
(CC BY, 42,882 rows), `by-sa` (CC BY-SA, 2,749) and `pd` (public domain, 1,954). Every row
carries its license, a link to the license and the credit line its publisher asks for. The
dataset card (`docs/data-card.md`) has the details and the limits.

```python
from datasets import load_dataset

articles = load_dataset("obadakr/commonswire", "by", split="train")
print(articles[0]["title"], articles[0]["credit_line"])
```

## What it is
- **Full text, not links.** Each row holds the article's body text as published, without
  photos, captions, video, audio or embeds.
- **Rights checked per source.** A source's articles enter only when its own pages give a
  license or public-domain statement that allows redistribution, do not forbid bulk or
  automatic reuse, and do not forbid automated collection. Wire copy, partner stories and other
  third-party material are always left out. `data/sources.csv` records the evidence for every
  source it checked: the pages read, the date, and short exact quotes.
- **Each row carries its own license and credit line.** Users can take only the license
  classes their own use allows (public domain, CC BY or CC BY-SA in version 0.1.0). See
  `docs/licenses.md`.
- **Updated by hand for now.** New versions are published by the maintainer, about weekly; a
  daily automatic update is planned. Each update checks the last 30 days of every source that
  still publishes: an article corrected at its source gets its new text and the status
  `changed`, and an article removed at its source, or taken down on request, is left out of
  the next version.

## What it is not
- It is **not every news outlet.** Most news sites do not allow redistribution, and they are
  not in CommonsWire.
- It is **not a scraper of copyrighted sites**, and it never works around a block. It sends one
  request at a time, follows robots.txt, and names itself in every request.
- It does **not profile people.** No one's gender, race, ethnicity, religion or other personal
  attribute is inferred, and there are no person-level tables.

## Using the code
CommonsWire needs Python 3.10 or later and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/obadaKraishan/commonswire
cd commonswire
uv sync --extra corpus
uv run commonswire --help
uv run commonswire sources check        # validate the source registry
uv run commonswire validate FILE.jsonl  # validate a file of articles
```

Collecting and building the corpus (needs the `corpus` extra: `uv sync --extra corpus`):

```bash
uv run commonswire backfill SOURCE      # a source's whole archive, resumable
uv run commonswire build SOURCE         # rows from the saved archive, with no requests
uv run commonswire page-bylines SOURCE  # bylines from article pages, each page fetched once
uv run commonswire wikinews-dump --download
uv run commonswire dedup                # exact duplicates dropped, near-duplicates flagged
uv run commonswire daily                # new, changed and removed articles since the last run
uv run commonswire corpus-report        # counts only
uv run commonswire store                # Parquet by source and year
uv run commonswire listing-bylines SOURCE  # bylines from a paged story listing
```

Building a dataset version from the built rows (no requests):

```bash
uv run commonswire release build --version 0.1.0   # data/release/0.1.0/
uv run commonswire release check --version 0.1.0   # files, hashes, counts, credit lines
uv run commonswire release kaggle --version 0.1.0  # a folder for the Kaggle mirror
uv run commonswire release zenodo --version 0.1.0  # a folder for a record with no article text
```

## Takedowns and corrections
Publishers, writers and people named in an article can ask for it to be removed or corrected
with the [takedown and correction form](https://github.com/obadaKraishan/commonswire/issues/new?template=takedown.yml).
An article taken down is listed by id in `data/takedowns.csv` and left out of every later
version.

## License
The code and the reference tables are licensed under the Apache License 2.0 (see `LICENSE` and
`NOTICE`). Article texts keep their sources' own licenses, recorded on every row.
