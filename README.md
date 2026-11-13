# CommonsWire

CommonsWire is a living, full-text corpus of news that may legally be redistributed. It
collects articles only from sources whose own pages allow their text to be shared unchanged
(public domain and Creative Commons licenses), updates every day, and adds the variables that
communication and journalism researchers usually code by hand: topic, frame, the types of
sources quoted, and tone.

**Status:** early development. Nothing has been released yet. The source registry, the article
schema and the first fetchers are being built and checked.

## What it is
- **Full text, not links.** Each row holds the article's body text as published, without
  photos, captions, video, audio or embeds.
- **Rights checked per source.** A source's articles enter only when its own pages give a
  license or public-domain statement that allows redistribution, do not forbid bulk or
  automatic reuse, and do not forbid automated collection. Wire copy, partner stories and other
  third-party material are always left out. `data/sources.csv` records the evidence for every
  source: the page, the date it was read, and a short exact quote.
- **Each row carries its own license and credit line.** Users can take only the license
  classes their own use allows (public domain, CC BY, CC BY-SA, and so on). See
  `docs/licenses.md`.
- **Living.** New articles are added daily; corrected or removed articles are marked, and
  their text is dropped in the next release.

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
uv sync
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
```

## Takedowns and corrections
Publishers, writers and people named in an article can ask for it to be removed or corrected
with the takedown form in this repository's issues.

## License
The code and the reference tables are licensed under the Apache License 2.0 (see `LICENSE` and
`NOTICE`). Article texts keep their sources' own licenses, recorded on every row.
