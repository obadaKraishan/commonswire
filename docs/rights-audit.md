# The rights audit

**DRAFT**, for the maintainer's review. Checked on 2026-11-16 (US Central; the pages were
read between 02:16 and 03:07 UTC on 2026-11-17).

CommonsWire takes a publisher's full text only when the publisher's own pages allow it. This
page says how that is checked, what the registry holds after the audit of 2026-11-16, and how
it compares with two other lists of openly licensed news: the news subset of the Common Pile
v0.1 and Open Newswire's feed list.

## What a verdict is, and what it is not
A verdict (`include`, `pending` or `exclude`) is **this project's reading of a publisher's
public pages on the date given**, with the page, the date and the exact words recorded in
`data/sources.csv`.

- **It is not legal advice.** It does not say what a court would decide, and it does not
  replace a user's own reading.
- **It is not a judgment of the publisher or of anyone else's list.** Where another list
  tags a publisher differently, this page reports the difference and the publisher's own
  words, nothing more.
- **It holds for the date given.** Pages change. A verdict is re-read when the publisher's
  pages change, and every included source's credit line and license travel with each row.
- **A reader can conclude** that, on that date, the page quoted said the words quoted, and
  that the four points below were checked against them.
- **A reader cannot conclude** that the publisher agrees with this reading, or that a
  `pending` or `exclude` source may not be reused in other ways (a single story, for
  example, under its own terms).

## How the pages were read
- **The rule.** Full text enters only when all four hold, each read on a primary page of the
  publisher and recorded with the URL, the date and a short exact quote:
  1. a license or public-domain statement that allows redistributing the full text unchanged;
  2. no clause against systematic, wholesale, bulk or automatic republishing, and no
     required tracking pixel or counter;
  3. terms of use and robots.txt that do not forbid automated collection of the pages or
     feeds used;
  4. a way to tell the publisher's own articles from third-party material, which is always
     left out.

  A source that fails 1, 2 or 3 is `exclude`. A source whose pages are silent or unclear on
  any point is `pending`, with the question to settle written in `reason`.
- **The rulings of 2026-11-13.**
  - (a) An invitation ("contact us if you would like to republish regularly") is not a
    condition.
  - (b) A request ("we urge you to link") is not a restriction on public-domain text.
  - (c) A site with no terms page passes point 3 when its robots.txt allows the paths used.
  - (d) Silence on bulk use passes only under public domain, CC0, CC BY and CC BY-SA; under
    NonCommercial or NoDerivatives licenses, and under a publisher's own permission with no
    named license, it stays `pending`.
- **Requests.**
  - Every page was read through the project's polite client: one request at a time per host,
    at least 2 seconds apart, robots.txt and crawl-delays honored, a User-Agent naming the
    project, every request logged.
  - Each page was saved once, unchanged.
  - A site that refused scripted requests (HTTP 401 or 403, a bot check, or robots.txt
    unreachable) was not read any other way. Its row stays `pending`, and the address is
    listed for a person to read.
- **Which pages.**
  - The license statement, the terms, the republishing page where there is one, robots.txt,
    and one or two article pages (for the license link and the byline).
  - Rows already `include` or `exclude` were re-read, and their quoted words checked against
    the new copies.
- **Quotes.** `commonswire sources check` confirms that every quote in the registry appears
  word for word on a saved page of its publisher.

## Reason codes
Every row has one `reason_code` saying why it has its status. The free-text `reason` stays.

| Code | Status | Meaning |
|---|---|---|
| `license_allows` | include | A license or public-domain statement allows unchanged redistribution, and nothing on the publisher's pages conflicts |
| `released_with_english` | include | A license allows unchanged redistribution, and third-party material is told on the English pages: a row is released only when its English version is a released row of the corpus (the Lingua rule, 2026-11-23; editions only) |
| `bulk_clause` | exclude | A clause against systematic, wholesale, bulk or automatic republishing |
| `tracker_required` | exclude | Republishing requires a tracking pixel or counter |
| `terms_forbid_automation` | exclude | The terms of use forbid automated collection |
| `robots_forbid` | exclude | robots.txt forbids the pages or feeds used |
| `third_party_portal` | exclude | A portal of other outlets' stories, with no license to them |
| `rights_reserved` | exclude | All rights reserved: no license allows redistribution |
| `nc_or_nd` | pending | A NonCommercial or NoDerivatives license, silent on bulk use |
| `no_license` | pending | No license is named (no statement, or a permission of the publisher's own) |
| `conflicting_statements` | pending | The publisher's own pages contradict each other on the license |
| `partial_license` | pending | The license covers only some of the publisher's articles, which needs the maintainer's decision |
| `extra_conditions` | pending | Conditions added to the license that the corpus cannot meet |
| `third_party_unclear` | pending | No way to tell the publisher's own articles from third-party ones |
| `refused_requests` | pending | The site refused scripted requests, so its pages could not be read |
| `site_unavailable` | pending | The site was not there to read (suspended or gone) |

A code must fit its row: `sources check` refuses, for example, `bulk_clause` on a row whose
`bulk_clause` field is not `forbids`, or `refused_requests` on a row whose robots.txt answered.

## The registry after the audit
- **66 publishers:** 13 `include`, 36 `pending`, 17 `exclude`.
- **By reason:**

| Status | Reason code | Publishers |
|---|---|---|
| include | `license_allows` | 13 |
| exclude | `bulk_clause` | 11 |
| exclude | `tracker_required` | 2 |
| exclude | `rights_reserved` | 2 |
| exclude | `terms_forbid_automation` | 1 |
| exclude | `third_party_portal` | 1 |
| pending | `nc_or_nd` | 12 |
| pending | `refused_requests` | 10 |
| pending | `no_license` | 3 |
| pending | `partial_license` | 3 |
| pending | `site_unavailable` | 3 |
| pending | `conflicting_statements` | 2 |
| pending | `third_party_unclear` | 2 |
| pending | `extra_conditions` | 1 |

- **Kinds.** 45 news, 4 fact-checking, 8 state agencies, 4 official, 2 advocacy, 2 portals,
  1 church agency. Publishers of other kinds than news and fact-checking get a verdict, so
  the audit is complete, but are not collected in 0.3.0.
- **What the audit of 2026-11-16 changed:**
  - **Verdicts:** none.
    - The 13 rows already `include` or `exclude` that either outside list tags as openly
      licensed were re-read, and their quoted words are unchanged.
    - The pending rows were read again and their questions stand. Sites that had refused
      before refused again, or were still down.
  - **New rows:** eight, the publishers in Open Newswire's English open-license feeds that
    the registry did not have.
    - One `include`: Salaam Times, a state-funded outlet, so it is not collected.
    - Two `exclude`: SINC and Mehr News Agency.
    - Five `pending`: Al-Jumhuriya, Caravanserai, Pakistan Forward, PanARMENIAN.Net and
      Project Multatuli.
  - **Kinds:** Agenzia Fides became `church-agency`; Tasnim, Agência Brasil and Voice of
    America became `state-agency`.

## Comparison with other lists
`data/audit/other_lists.csv` holds every fact read from the two lists, with the date of the
list's own data, the address and the time it was read. `data/audit/comparison.csv` has one
row per publisher: what each list says and the date of that list's data
(`common_pile_data_date`, `open_newswire_data_date`), and this project's license class,
status, reason code and the date its pages were read (`checked_on`). `commonswire audit
compare` rebuilds it with no request.

- **The dates differ, and the comparison keeps each one.** The Common Pile's news data were
  added to Hugging Face in May 2024 (its 17 data files, on 2024-05-27). Open Newswire's feed
  list is dated 2025-11-11 (the file's last change). The publishers' own pages were read in
  November 2026 (2026-11-13 and 2026-11-16). A list's tag is its reading on its own date,
  and pages change, so a difference today does not show that a tag was wrong when it was
  made.

- **The Common Pile v0.1, news subset.** It describes its sources as "news sites that
  publish content under CC BY or CC BY-SA according to opennewswire". Facts were read from:
  - its dataset card, `common-pile/news` on Hugging Face, which names 20 publishers;
  - its paper (arXiv 2506.05209v1, Appendix E), which lists 17 publishers under CC BY and 3
    under CC BY-SA;
  - its collection code (`sources/news/parse-pages.sh` in the r-three/common-pile
    repository), which gives one license tag per site;
  - its data files: 17 files, one per publisher;
  - the dataset viewer's statistics, which give the documents per publisher (172,308 in
    all) without downloading the corpus.
- **Open Newswire.** Its feed list (`scripts/data/feeds.csv` in its repository, last changed
  2025-11-11) has 546 feeds. 31 English feeds are tagged CC BY, CC BY-SA or Public Domain, one
  publisher each. The table also records the English feeds, under other tags, of 12 more
  publishers in the registry.

### Counts
- **Publishers either list tags as openly licensed (CC BY, CC BY-SA or public domain): 31.**
  Every one of them is in the registry.

| This project | Reason code | Publishers |
|---|---|---|
| include | `license_allows` | 10 |
| pending | `refused_requests` | 5 |
| pending | `site_unavailable` | 3 |
| pending | `conflicting_statements` | 2 |
| pending | `partial_license` | 2 |
| pending | `third_party_unclear` | 2 |
| pending | `no_license` | 1 |
| exclude | `bulk_clause` | 4 |
| exclude | `rights_reserved` | 2 |

- **The Common Pile names 23 publishers** (on its card, in its paper, in its code or in its
  data): 9 `include`, 11 `pending`, 3 `exclude`. Its 172,308 documents, grouped by this
  project's verdict on each publisher:
  - 123,949 (71.9%) come from publishers that are `include`;
  - 16,207 (9.4%) from publishers that are `pending`;
  - 32,152 (18.7%) from publishers that are `exclude`.
- **Open Newswire tags 31 publishers** as openly licensed in English: 10 `include`, 15
  `pending`, 6 `exclude`.
- **Tag versus license class.** For 5 of the 31, the class of a list's tag differs from the
  license the publisher's own pages state (`lists_agree` is `no`). For 8 more, the pages
  could not be read (`unread`).

### Each difference, in the publisher's own words
Where the lists' tag and this project's status differ, the reason is the publisher's own
page, quoted as read on the date checked.

- **Excluded:**
  - **Milwaukee Neighborhood News Service.** Both lists tag it CC BY. Its article pages say
    "This work is licensed under a Creative Commons Attribution-NoDerivatives 4.0
    International License." and "Don’t extract, store or resell Milwaukee Neighborhood News
    Service content as a database." (`bulk_clause`).
  - **EduCeleb.** Both lists tag it CC BY-SA. Its terms say "This website and its content
    are copyrights of EduCeleb.com. All rights reserved." (`rights_reserved`).
  - **The Solutions Journalism Exchange.** Both lists tag it CC BY. It is a portal of
    member newsrooms' stories, and its publisher's terms say "Republication, systematic
    reproduction, posting in electronic form on servers, or other uses of the Content, except
    to the extent permissible under fair use principles, requires permission or license from
    SJN or the third-party copyright holder, as applicable." (`bulk_clause`).
  - **Voice of America.** Open Newswire tags it Public Domain. Its usage-requests page says
    "VOA does not grant U.S. domestic media permission for the blanket, standing or
    recurring use of original VOA content." (`bulk_clause`).
  - **SINC.** Open Newswire tags it CC BY. Its license page says CC BY 4.0 "does not, under
    any circumstances, authorize the exploitation, whether for commercial purposes or
    otherwise, of SINC content to create publications, in any medium, when they are chiefly
    made up of content from agenciasinc.es." The clause forbids publications made up chiefly
    of SINC's content. A filter on this corpus to SINC's rows would make one, and the corpus
    cannot pass that condition on to its users, so the row stays `exclude` (`bulk_clause`).
  - **Mehr News Agency.** Open Newswire tags it CC BY and marks its feed inactive. The two
    pages read carry only "© 2017 Mehr News Agency. All rights reserved"
    (`rights_reserved`).
- **Pending, with the publisher's words:**
  - **Liberty TV Radio.** Both lists tag it CC BY-SA. An article page says "This work is
    licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.",
    while every footer says "© 2025 Liberty TV/Radio. All Rights Reserved."
    (`conflicting_statements`).
  - **PanARMENIAN.Net.** Open Newswire tags it CC BY. Its terms say "The content of PAN.am
    (PanARMENIAN.Net) is licensed under the Creative Commons Attribution 4.0 license." and
    also "This license shall automatically terminate if you violate any of these
    restrictions, and may be terminated by PAN Media LLC at any time."
    (`conflicting_statements`).
  - **Meduza.** Both lists tag it CC BY. Its About page says "All materials published by
    Meduza belong to Meduza. You cannot republish our content without prior approval from
    our newsroom." and that it "regularly releases its content under a Creative Commons CC
    BY license", which it calls "these select materials" (`partial_license`).
  - **Propastop.** Both lists tag it CC BY-SA. Its terms say "Texts, images and videos of
    propastop.org can be mostly used under the Creative Commons licence."
    (`partial_license`).
  - **Minority Africa.** Both lists tag it CC BY. Its About page says "Our stories are
    published under a Creative Commons License." without naming the license, and
    "Currently, media organizations can republish our content for free within the Advance
    framework." (`no_license`).
  - **Agenzia Fides.** Both lists tag it CC BY. Its footer says "The contents of the site
    are licensed under Creative Commons Attribution 4.0 International License", but no page
    read says how texts by others are marked (`third_party_unclear`). It is a church agency.
  - **Oxpeckers.** Both lists tag it CC BY-SA. Its footer licenses "Content on this site,
    made by the Oxpeckers Center for Investigative Environmental Journalism", and no page
    says how partners' pieces are marked (`third_party_unclear`).
  - **Mekong Eye, New Canadian Media, Tasnim News Agency, Al-Jumhuriya and Project
    Multatuli.** The lists tag them CC BY. Their sites refused this project's client
    (`refused_requests`), so no reading can be compared.
  - **ZimFact, Caravanserai and Pakistan Forward.** The lists tag them CC BY (ZimFact) or
    Public Domain. On 2026-11-16 ZimFact showed a hosting "Suspended" page, and the other
    two "This website is no longer available" (`site_unavailable`).
- **Included:**
  - **The 10 included publishers.** Each list's tag is in the same class as the license on
    the publisher's pages (CC BY: 360info, Africa Is a Country, Alt News, Balkan Diskurs,
    Factly, the Freedom of the Press Foundation, Global Voices, SciDev.Net; CC BY-SA: The
    Public Record; public domain: Salaam Times).
  - The versions can differ from a list's generic tag. SciDev.Net's media page names CC BY
    2.0, Global Voices' footer CC BY 3.0, 360info's CC BY 4.0. The registry and every row
    carry the version the publisher states.
  - SciDev.Net's republishing box, on every article page, says "You have to credit our
    authors.", so its rows with no byline are held. Of its embed code, which carries a Google
    Analytics event script, the box says "The easiest way to get the article on your site is
    to embed the code below.": the code is offered, not required, so no tracker is required.
    Its "Supported content" pages are kept only with SciDev.Net's own byline, the site's
    license line and no other holder named (101 of 107; the other 6 are left out as
    third-party or sponsored material).
- **What the Common Pile collected.**
  - Five publishers named on its card have no data file in it: Africa Is a Country, Agenzia
    Fides, Meduza, SciDev.Net and Tasnim. Their lines are commented out in its collection
    code.
  - Two data files are of publishers its card does not name: EduCeleb (5,280 documents) and
    Liberty TV Radio (10,358).
  - Its code also lists Caravanserai as Public Domain, commented out.

## Language editions (read on 2026-11-17)
Each language edition of an included publisher is a registry row of its own (`edition_of`
names the publisher's main row). It is ruled on its own pages: its home page and its license
footer, its robots.txt, one article page, and its policy or copyright page where one was
found. The main row's verdict is never carried over.

A license line is quoted in the edition's own language, word for word, with the address it
links to. An English gloss beside it in the notes is marked "(gloss)" and is this project's.

- **Found:**
  - 51 Global Voices Lingua sites, listed on its Lingua page;
  - 32 Wikinews editions: 31 linked from its portal, and the Russian one, linked from the
    English copyright page;
  - Alt News' Hindi edition, linked from its English home page;
  - Balkan Diskurs' Bosnian site (its `hreflang`).

  Not found on their own pages: SciDev.Net's other editions (its root and sitemap index list
  only `/global/`), and editions of 360info, The Public Record and Africa Is a Country.
- **Factly's Telugu stories are on its main site,** in its "Telugu" category (4,532 posts),
  not on an edition of their own. Versions 0.1.0 to 0.2.2 label them `en`; series 0.3 takes
  the language from Factly's own category.
- **Verdicts:** 1 `include` and 84 `pending`; none excluded.
  - **Balkan Diskurs (Bosnian): `include`.** Its own attribution policy, in Bosnian, puts
    "Sav sadržaj kreiran na Balkan Diskursu" (all content created on Balkan Diskurs) under
    CC BY.
  - **47 Global Voices editions: `pending` (`third_party_unclear`).** Each footer states
    CC BY 3.0 in its own language and links it; robots.txt allows the pages and the API. But
    the edition's own pages read do not say how others' material is marked. The question is
    whether Global Voices' attribution policy, on its English site ("all content published on
    Global Voices", "our sites"), covers them.
  - **4 Global Voices editions: `pending` (`statement_unread`).**
    - Amharic, Igbo and Santali: statements this project could not read with confidence.
    - Yoruba: its footer shows an unfilled template placeholder where the license should be
      named.
  - **32 Wikinews editions: `pending` (`partial_license`).**
    - All are closed and read-only since 4 May 2026 (the Foundation's notice), so their route
      is the dump.
    - Each footer names today's license: CC BY 4.0 on 26, CC BY-SA 4.0 on Arabic, Persian,
      French and Swedish, CC BY 2.5 on German, CC BY 3.0 on Hungarian.
    - Older articles carry other licenses, or are in the public domain, by dates that differ
      from edition to edition. These are read from each copyright page where one was found
      (25 of 32).
  - **Alt News (Hindi): `pending` (`conflicting_statements`).** Its footer says both "CC BY
    3.0 के तहत लाइसेंस प्राप्त" (licensed under CC BY 3.0) and "सर्वाधिकार सुरक्षित" (all rights
    reserved), with no license link.
- **Translations.** Global Voices editions credit the writer and the translator in separate,
  localized credit sections (for example "Escrito por" and "Traducido por"). An article lists
  the story's other language versions; 43 of the 47 article pages read link a post on
  another Global Voices site. The markup read does not mark which version is the original.

## The editions after the maintainer's answers (2026-11-23)
- **Global Voices: 47 editions `include` under the Lingua rule (`released_with_english`).**
  Their footers and the publisher's attribution policy, which names "our sites", settle the
  license (CC BY 3.0). Third-party material is settled mechanically: a Lingua row is released
  only when its English version is a released row of the corpus, because the English pages
  are where republished partner pieces are detected. Every other Lingua row is held and
  counted, by edition. The quotes of 2026-11-17 are kept.
  - The link from a Lingua post to its English version is found from the bodies the API
    gives (their links and images), against the saved English bodies; `docs/method.md` says
    how, and how well it agreed with the pages' own links.
- **Global Voices: Amharic, Igbo, Santali and Yoruba stay `pending`** (`statement_unread`):
  no reader is sought.
- **Alt News (Hindi) stays `pending`** (`conflicting_statements`): nobody is contacted.
- **Wikinews: a license-by-date table for each edition whose copyright page dates its
  licenses.** An article takes the license of its creation date (its first revision in the
  dump); a date the table does not place is held and counted. On a boundary day the wording
  leaves to both sides, the license that asks more of the reuser is taken, as for the English
  edition. Eight editions are `include`:

  | Edition | Table | The page's words (one of them; all are in the registry and were checked word for word) |
  |---|---|---|
  | French | public domain before 2005-09-24; CC BY 2.5; CC BY-SA 4.0 from 2025-01-02 | "Le contenu publié entre le 24 septembre 2005 et le 2 janvier 2025 est sous licence Creative Commons Attribution 2.5, sauf mention contraire." |
  | Arabic | CC BY 2.5; CC BY-SA 4.0 from 2024-08-21 | "جميع النصوص المنشورة قبل 21 أغسطس 2024 تخضع لرخصة رخصة المشاع الإبداعي الملزمة بنسبة العمل لمؤلفه 2.5." |
  | Russian | CC BY 2.5; CC BY 4.0 from 2025-02-26 | "(публикации до 26.02.2025 распространяются по лицензии CC-BY версии 2.5, если не указано иное)" |
  | Chinese | CC BY 2.5; CC BY 4.0 from 2025-01-30 | "2025年1月30日之前加入维基新闻的内容也以CC BY 2.5授权。" |
  | Romanian | GNU FDL before 2005-09-26 (held); CC BY 2.5; CC BY 4.0 from 2025-01-03 | "Materialul publicat înainte de 2 ianuarie 2025, dar după 25 septembrie 2005, este licențiat în conformitate cu termenii licenței Creative Commons Attribution 2.5 License." |
  | Swedish | before 2005-07-01 not placed (held); CC BY 2.5; CC BY-SA 4.0 from 2025-01-29 | "Bidrag som publicerats före den 1 juli 2005 kan ha publicerats under en annan licens (och bidrag före 29 januari 2025 har publicerats under den äldre versionen Creative Commons Attribution 2.5)." |
  | Korean | public domain before 2005-09-25; CC BY 2.5 to the page's last edit (2015-08-05); later not placed (held) | "2005년 9월 25일을 기점으로, 이 이후에 위키뉴스에서 발행된 모든 내용은 크리에이티브 커먼즈 저작자표시 2.5 라이선스로 배포됩니다." |
  | Greek | public domain before 2005-09-25; CC BY 2.5 to the page's last edit (2018-12-28); later not placed (held) | "Από τις 25 Σεπτεμβρίου όλα τα περιεχόμενα που δημοσιεύονται στα Βικινέα αδειοδοτούνται με τους όρους της Αναφορά προέλευσης 2.5 Γενικό (CC BY 2.5)." |

  Each of the eight pages also bars copyrighted text (quoted in `third_party_rule`), as the
  English edition's does. **A page with a notice of its own** (the maintainer's rule,
  2026-11-23): a page that carries a license or copyright notice of its own that differs from
  its edition's license for its creation date is held and counted, by edition; the table's
  license applies only to pages with no notice of their own, or with one that agrees with it.
  An image's caption or gallery is the image's notice, not the page's. (The English row says
  the same of its pages, which the dump reader of versions 0.1.0 to 0.2.x did not check.)
- **Read from their dumps (2026-11-25):** French, Chinese, Arabic, Greek, Romanian and
  Korean. Each edition's published articles are told by its own publication template, found
  in a count of its article pages' templates (`commonswire wikinews-edition --census`). The
  Swedish edition is `include` but not read yet: no template marks most of its pages
  ("publicerad" is on 186 of 3,317). The Russian dump (1.1 GB) waits for a later version.
- **Wikinews editions still `pending`,** each with the question its page leaves:
  - German (`third_party_unclear`): the page dates its licenses but says nothing about text
    copied from elsewhere;
  - Italian (`partial_license`): CC BY from 25 September 2005 with no version named;
  - Catalan, Spanish, Dutch, Norwegian, Turkish, Tamil and Esperanto (`partial_license`):
    one license (CC BY 2.5) and no dates, while today's footer names CC BY 4.0; the
    Esperanto page is marked a proposal;
  - Portuguese, Hebrew and Finnish (`partial_license`): CC BY 4.0 and no dates;
  - Japanese, Polish and Czech (`partial_license`): the page names no license (Czech's is a
    redirect to the English policy);
  - Persian (`conflicting_statements`): the page names the GNU FDL, the footer CC BY-SA 4.0;
  - Shan (`partial_license`): its statement was not read with confidence (answer 3b);
  - the seven editions with no copyright page found (Bosnian, Gun, Hungarian, Limburgish,
    Albanian, Serbian, Ukrainian).
- **The registry now:** 151 rows, 69 `include` (22 `license_allows`, 47
  `released_with_english`), 65 `pending`, 17 `exclude`. The outside lists' figures above are
  unchanged: the editions are on neither list. Each list keeps its own date (Common Pile
  2024-05-27, Open Newswire 2025-11-11).

## The audit in the release
- **Version 0.3.0's `sources.csv`** carries the `reason_code` column. Every published version
  already ships the registry as it was when the version was built.
- **Proposed, not built:** a `sources` configuration on Hugging Face, so the registry can be
  browsed in the dataset viewer and loaded with `load_dataset(..., "sources")`. It would take:
  - one more entry in the card's `configs` (`config_name: sources`, `data_files: sources.csv`);
  - keeping `by` as the default configuration, so the default load still gives articles;
  - a line in the card on what the configuration holds;
  - the same entry in the weekly update's card, since `update` writes the card each week;
  - a check that the viewer reads the 27 columns.

  `data/audit/comparison.csv` could ship the same way (an `audit` configuration). Neither
  changes a row of article data.

## Files and commands
- `data/sources.csv`: the registry (one row per publisher, its evidence, status and reason
  code). `docs/sources.md` is generated from it by `commonswire sources render`.
- `data/audit/other_lists.csv` and `data/audit/comparison.csv`: the comparison, rebuilt by
  `commonswire audit compare`.
- `data/evidence/pages.csv`, `robots.csv` and `license_links.csv`: every page read, with its
  status and SHA-256 (the pages themselves are kept off the repository).
- `commonswire sources check`: every rule, and every quote word for word on a saved page.
