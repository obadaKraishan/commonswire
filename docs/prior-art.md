# Prior art

Checked on 2026-11-13. Each row was read on the resource's own pages, its repository or its
Hugging Face card, or through its public API.

## The answer: no living equivalent exists
No resource we found offers a **living, openly licensed, full-text** news corpus that anyone
can download, cite and rebuild. The nearest ones each lack at least one of those properties:

- **Open Newswire** is living and tags licenses, but it is a headline reader: a click
  redirects to the publisher, articles are kept for about 30 days by default, and there is no
  dataset, archive or export. It labels each feed's license from the publisher's statement and
  tells readers to "Always check the conditions of republication at the source site itself."
- **The Common Pile v0.1 `news` subset** has full text with a license, URL and author on each
  row, but it is a one-time scrape (rows added 2024-05-27, last modified 2025-06-06), English
  only, with no coded variables. Its licenses come from Open Newswire's labels, not from a
  check of each site.
- **MOT** (Voice of America) is public-domain full text that was released about every six
  months, but its last release (v1.11) is dated 2025-05-08, and it covers one publisher.
- **Wikinews** closed: the Wikimedia Foundation Board approved closing all editions,
  "effective 2026-05-04". Every Wikinews corpus is now frozen.
- **CC-NEWS** and **infini-news** are living full-text collections, but the article text stays
  under the publishers' copyright. **GDELT** and **Media Cloud** do not give full text.

CommonsWire aims at the combination: full text, a license and credit line on every row,
rights checked on each publisher's own pages, third-party material removed, regular updates,
and validated coded variables (topic, frame, types of sources quoted, tone) with their
provenance. CommonsWire has the first four (a new version about every week, from an automatic
run that the maintainer approves), and the coded variables are planned for a later version.

## Table
| Resource | What it holds | Full text? | License | Living or frozen | Last update seen | Variables |
|---|---|---|---|---|---|---|
| [Open Newswire](https://opennewswire.org/) ([code](https://github.com/Open-Newswire/opennewswire)) | RSS and Atom aggregator of "freely-republishable news articles": headline, license tag, language; clicks go to the publisher | No | Code MIT; 8 license tags per feed (CC BY, BY-SA, BY-ND, BY-NC, BY-NC-SA, BY-NC-ND, Public Domain, "Attribution+") | Living (feed), about 30-day retention by default | Repo push 2026-09-04; feed list unchanged since 2025-11-11 | Feed-level license tag, language |
| Open Press Wire | A nonprofit wire launched in December 2024 that publishes its own articles under "a Creative Commons license" | Its own articles only | Which CC license not seen | Not seen | Press release of 2024-12-16 | None |
| [Common Pile v0.1 `news`](https://huggingface.co/datasets/common-pile/news) ([paper](https://arxiv.org/abs/2506.05209)) | 172,308 documents (0.4 GB) from 20 sites that publish "under CC BY or CC BY-SA according to opennewswire" | Yes | Per row (CC BY or CC BY-SA) | Frozen | 2025-06-06 | id, text, source, added, created, license, url, author |
| Common Pile v0.1 `wikimedia` | English Wikimedia wikis, including Wikinews | Yes | CC BY, CC BY-SA | Frozen | 2025-06-06 | Per-row license |
| [MOT](https://arxiv.org/abs/2201.05609) ([code](https://github.com/bltlab/mot)) | Voice of America sites in 43 to 44 languages, about 2.8 million articles in release 1 (2001 to 2022) | Yes (paragraphs) | Source public domain; collection CC BY 4.0 | Was released about every six months; none since 2025-05 | v1.11, 2025-05-08 | Paragraphs, site, language, document type |
| OPUS GlobalVoices | Sentence-aligned parallel corpus from Global Voices, 46 languages | Aligned sentences | Not seen on OPUS | Frozen | v2018q4 | Alignments |
| [Parallel Global Voices](https://nlp.ilsp.gr/pgv/) | 302,617 document pairs in 756 language pairs | Yes | Content CC BY; alignments CC BY 4.0 | Frozen (crawled 2015 to 2016) | Not seen | Alignments |
| [Wikinews](https://meta.wikimedia.org/wiki/Proposal_for_Closing_Wikinews) | Citizen news wiki, all editions | Yes | CC BY 2.5 for text after 2005-09-25 | **Closed** "effective 2026-05-04"; pages stay visible | Closure page edited 2026-06-12 | Categories, sources |
| Wikinews datasets on Hugging Face (`malteos/wikinews`, `qikp/wikinews-2026-*`, `izumi-lab/wikinews-en-20230728` and others) | Wikinews dumps in one or more languages | Yes | CC BY 2.5 (some tags differ) | Frozen | 2026-06-27 (malteos) | Page and revision ids, dates, categories |
| [CC-NEWS](https://commoncrawl.org/blog/news-dataset-available) | Daily WARC files of crawled news pages | Raw HTML | No license to the content; crawled content "may be subject to separate terms of use" | Living | October 2026 | None |
| infini-news (University of Graz; `ruggsea/infini-news-corpus`) | 1.37 billion articles from CC-NEWS, 2016 to 2026, with a search API | Yes | Derived columns CC BY 4.0; "article text subject to publishers' copyright" | Versioned, not daily | 2026-10-18 | Language and topic predictions |
| NELA-GT (2018 to 2022) | Yearly collections; 2022 holds 1,778,361 articles from 361 outlets | Yes | Not seen | Frozen; 2022 is the latest edition found | 2023-03 | Outlet-level reliability labels |
| All the News 1.0 and 2.0 | 2.0: 2,688,878 articles from 27 US publications, 2016 to 2020 | Yes | Research only, "non-commercial" (scraped copyrighted outlets) | Frozen | Not seen | None |
| [GDELT](https://www.gdeltproject.org/about.html) | Events and Global Knowledge Graph records derived from world news | No | Open use with citation | Living | Daily | Events, themes, emotions, places |
| [Media Cloud](https://mediacloud.org/documentation/faqs) | Searchable news index | No ("we cannot release the actual text of a story") | URL lists | Living | Not seen | Metadata |
| [Newswire](https://huggingface.co/datasets/dell-research-harvard/newswire) (Dell et al., NeurIPS 2024) | 2.7 million public-domain US wire articles, 1878 to 1977 | Yes | CC BY 4.0 (texts public domain) | Frozen | 2025-08-30 | Places, topic flags, Comparative Agendas topic, people linked to Wikidata |
| [American Stories](https://huggingface.co/datasets/dell-research-harvard/AmericanStories) | Article texts from the public-domain Chronicling America scans, 1774 to 1963 | Yes (OCR) | CC BY 4.0 | Frozen | 2025-03-26 | Newspaper, date, page, headline, byline |
| "Daily" news datasets on Hugging Face tagged CC BY | Single-outlet feeds, or scrapes of copyrighted outlets with a CC BY tag | Varies | Tags not credible for scraped copyrighted outlets | Living | November 2026 | None or few |

## Notes
- **Open Newswire's feed list** is published in its MIT-licensed repository
  (`scripts/data/feeds.csv`: 546 feed rows, 512 active, 91 languages; no separate data terms
  stated). It is a useful list of leads. CommonsWire does not copy its labels: every source is
  checked again on its own pages, because labels can disagree with the publisher's current
  terms. For example, several newsrooms it tags CC BY-NC-ND ask republishers not to republish
  automatically.
- **License laundering.** The Common Pile defines it as "where a copyrighted work is
  redistributed (typically by a non-rights holder) with an incorrect license", and its news
  card warns that it may have assigned some licenses wrongly. CommonsWire's answer is the
  per-source evidence in `data/sources.csv`: the page, the date it was read and the exact
  words, and the drop of third-party material on every row.
- **Wikinews and Voice of America** can still seed a historical back-catalogue: Wikinews pages
  stay visible after the closure, and VOA's own text is in the public domain. Neither is a
  safe living source on its own (`docs/sources.md`).
