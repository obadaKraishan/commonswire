# Method (DRAFT)

**DRAFT: not accepted yet.** This describes plans, not what version 0.2.0 does: how
CommonsWire will code and validate its variables and how it will keep the corpus current.
CommonsWire has no coded variables yet; a new version comes about every week from an
automatic run that the maintainer approves (`docs/automation.md`). None of the coding below has
been run.

## 1. Unit and scope
- **Unit:** one article row (`src/commonswire/schema.py`): the body text as published, without
  boilerplate, captions or media, from a source whose status is `include` in
  `data/sources.csv`.
- **Out of scope:** third-party material (wire copy, partner stories, syndicated pieces) is
  dropped before any coding and counted per source.
- **Sources:** every publisher's rights are read on its own pages under the clean-source rule
  (`docs/rights-audit.md`, `docs/sources.md`); only news and fact-checking publishers whose
  status is `include` are collected. Official, advocacy, state and church agencies get a
  verdict but are not collected unless the maintainer decides so.
- **Routes:** a publisher's API where it gives its articles (WordPress), a dump (Wikinews),
  or its article pages, found from its sitemap (SciDev.Net) or its listing pages (Africa Is a
  Country), each page saved once and replayed with no request.
- **Third-party and sponsored pieces:** left out and counted. Besides partner categories,
  republication notes and other holders' copyright lines, SciDev.Net's "Supported content"
  pages (most name a funder) are kept only with SciDev.Net's own byline, the site's license
  line and no other holder named.
- **Languages:** English so far. Several included publishers also publish in other languages
  (Global Voices' Lingua sites, Alt News in Hindi, Factly in Telugu, SciDev.Net's other
  editions). Whether each edition carries the same license, and by which route it can be
  read, is checked edition by edition before it enters.

## 2. Variables
Every coded value is stored on its row with its provenance: the codebook version, the model and
its license, the prompt version, the time it was coded, and whether a person checked it
(`Coding` in `schema.py`). Published coded values use Apache-2.0 or MIT models.

### 2.1 Topic
- **Scheme: IPTC Media Topics**, the news industry's own subject taxonomy, maintained by the
  International Press Telecommunications Council (IPTC). IPTC describes it as its "primary
  subject taxonomy since 2010, with a focus on classification of text", and says "Media Topics
  describe the subject of a news item."
- **License:** CC BY 4.0. The vocabulary file carries `"licenceLink":
  "http://creativecommons.org/licenses/by/4.0/"`, and IPTC's NewsCodes Guidelines say "All
  NewsCodes vocabularies are copyright IPTC and licenced under the Creative Commons Attribution
  4.0 licence." IPTC asks users to "give IPTC credit somewhere on your website"; the data card
  will credit "IPTC Media Topics, © IPTC, International Press Telecommunications Council, CC BY
  4.0". CommonsWire's own labels can then be CC BY 4.0 without the question the CAP terms raise.
- **Structure** (release of 2026-09-30, the `dateReleased` that a coding run pins): 17 top-level
  topics (arts, culture, entertainment and media; crime, law and justice; disaster, accident and
  emergency incident; economy, business and finance; education; environment; health; human
  interest; labour; lifestyle and leisure; politics and government; religion; science and
  technology; society; sport; conflict, war and peace; weather), 1,059 active concepts on up to
  six levels, with mappings to IPTC's older Subject Codes and to Wikidata.
- **Coding:** one primary top-level topic and up to two secondary ones per article, plus the
  second level (120 active concepts) where the model is confident; the codes are stored as
  qcodes (`medtop:11000000`), with the release date in the codebook version.
- **CAP as an optional internal crosswalk.** No published IPTC-to-CAP mapping exists. A
  crosswalk from IPTC's second level to the CAP major topics may be built for internal
  comparison with CAP-coded data; CAP codes are not published (their "topic code variables"
  are CC BY-NC-SA 4.0).
- **Gold data for topic:** MN-DS (Petukhova and Fachada, Data 2023; Zenodo 10.5281/zenodo.7394851),
  10,917 news articles from 2019 labeled by hand with IPTC Media Topics (levels 1 and 2), CC BY
  4.0. Its article texts come from many outlets, so it is used for internal checks only, with
  aggregate metrics published. EMMediaTopic 1.0 (21,000 texts) is labeled by a model, not by
  people, and is not gold.

### 2.2 Frame
- **Scheme:** the Policy Frames Codebook (Boydstun, Card, Gross, Resnik and Smith, updated July
  2020): Economics; Capacity and Resources; Morality and Ethics; Fairness and Equality;
  Legality, Constitutionality and Jurisdiction; Crime and Punishment; Security and Defense;
  Health and Safety; Quality of Life; Cultural Identity; Public Sentiment; Political Factors and
  Implications; Policy Description, Prescription and Evaluation; External Regulation and
  Reputation; Other.
- **Coding:** the primary frame ("the one that comes across most strongly") and every frame
  present (the dimensions "are NOT intended to be mutually exclusive"). Only articles with a
  policy topic are frame-coded; the rest are "not applicable".
- **Terms:** no license is stated on the codebook. Its "How to Cite" page says "We encourage the
  free, attributed use of the data collected using the Policy Frames Codebook for publications,
  instructional use, policy analysis, and other non-commercial purposes." CommonsWire cites it
  as asked and records the noncommercial wording in `docs/licenses.md`.

### 2.3 Types of sources quoted
- **What is coded:** each person or body quoted or paraphrased with attribution, by the role
  the text gives it:
  - official (government, elected office, public agency, the courts);
  - political actor (party or campaign, not in office);
  - expert (academic, researcher, professional speaking as an expert);
  - business (company, industry group);
  - civil society (nonprofit, advocacy group, union, religious body);
  - citizen (a person speaking for themselves: a resident, a witness);
  - journalist or media;
  - international organization;
  - document or data (a report, a court filing, a statistic, with no speaker);
  - unnamed or anonymous.
- **Rule: roles as stated in the text, never personal attributes.** A role is coded only from
  the words of the article (title, affiliation, "said the mayor"). Nothing is inferred from a
  name, a photo or anything else: no gender, race, ethnicity, religion, age or nationality.
- **What is released:** counts per type per article. Source names are not stored, and there is
  no person-level table.

### 2.4 Tone
- **What is coded:** the overall tone of the article's reporting on its main subject:
  negative, neutral, positive or mixed.
- **Not the same as the codebook's tone:** the Policy Frames Codebook codes tone as a stance on
  a pre-identified side of a policy issue (pro, anti or neutral). That needs the issue's sides
  to be fixed in advance, which a general corpus cannot do, so CommonsWire codes article tone
  instead and says so in the data card.

## 3. Validation without waiting for coders
### 3.1 Existing public gold data
| Gold set | What it labels | License and access | Use in CommonsWire |
|---|---|---|---|
| MN-DS (2019 news, 10,917 articles) | IPTC Media Topics, levels 1 and 2, by hand | CC BY 4.0 (texts from many outlets) | The topic gold set, internal only; aggregate metrics published |
| CAP media datasets (Pennsylvania newspaper headlines and abstracts 1979 to 2015; The Times front-page headlines 1960 to 2008; New York Times Index descriptions 1946 to 2016) | CAP major topics | CC BY-NC-SA 4.0 for the codes; the source texts keep their copyright | Only through the optional crosswalk, internal only |
| Media Frames Corpus (Card et al. 2015), v2 | 15 frames, primary frame, tone | Annotations GPL-3.0; the article texts need Lexis-Nexis; the retrieval tool is deprecated and drives a browser | Not usable as gold; reference for label distributions and agreement figures |
| Gun Violence Frame Corpus (Liu et al. 2019) | 9 frames on 2,990 headlines (1,300 relevant) | No license stated; "please cite" | Only with the authors' permission |
| SemEval-2023 Task 3 | 14 frames, 9 languages | "It may only be used in the context of this shared task"; "Any other use is explicitly prohibited" | Only with written permission from the organizers |
| NewsMTSC (Hamborg and Donnay 2021) | Sentence-level sentiment toward a named person, more than 11,000 sentences | MIT | A sentence-level check of the tone instructions |
| SentiNews 1.0 | Document, paragraph and sentence sentiment, 10,427 Slovenian articles | CC BY-SA 4.0 | Only if Slovenian or cross-language coding is in scope |
| PerSenT (Bastan et al. 2020) | Author sentiment toward the main entity of an article | License not stated | Only with the authors' permission |

No public gold set labels the **types** of sources quoted with a clear license. PolNeAR
labels attribution spans (who is quoted) but not types, and states no license; Spangher et al.
(2023, 2024) is the closest scheme, with data access unclear. Source types are therefore
validated by the hand-coded sheet in 3.3.

### 3.2 Reliability with reliacode
- Two independent model coders (different open models, Apache-2.0 or MIT) code the same
  articles; one of them also codes a fixed subset twice for stability.
- reliacode computes Krippendorff's alpha per variable, with bootstrap intervals, between the
  model coders, between each model and the gold sets above, and between the models and the
  hand-coded sheet.
- Targets: alpha of at least 0.67 for a variable to be released as provisional, and 0.80 to be
  called validated. A variable below 0.67 is not released.
- Coding is run as a script on Kaggle or a local model, never in a development session.

### 3.3 A small hand-coded sheet (optional, by the maintainer)
About 100 CommonsWire articles, stratified by source and topic, coded by the maintainer for the
four variables (about 3 to 4 hours). It is the only gold for source types, and it checks topic,
frame and tone on the corpus's own texts. A second human coder can be added later for a
human-human alpha.

## 4. Update rules
- **New:** each weekly update adds the articles of the last 30 days that the previous version
  does not have (by the source's API), after the third-party filter. Sources read from their
  article pages (series 0.3) have a route of their own: SciDev.Net's newest sitemap (the
  articles changed since the previous version), and Africa Is a Country's listing pages 1 and
  2 (the stories the previous version does not have). Each page is read once.
- **New series:** a source enters only with a new series (0.3.0 after 0.2.N), built by
  `commonswire release build-from` from the latest published version plus the new sources'
  rows, so whatever the weekly updates added is kept.
- **Changed:** an article whose text hash differs from the stored one is marked `changed`, its
  new text replaces the old in the next release, and its coded variables are coded again.
  Sources that report edits (for example a modified date in their API) are checked first.
- **Removed or corrected away:** an article that its source has removed (404 or 410, or gone
  from the source's API), or that its publisher asks to remove, is marked `removed`; its row
  stays with its metadata and its text is dropped in the next release.
- **Older removals:** an edit of any age is caught by the source's edited-since listing.
  Removals older than 30 days are found by the count check: each update compares every
  source's post count per year with the counts of the version before, and in a year whose
  count fell it lists the year and checks the page of each released row missing from it
  (`docs/automation.md`, section 5).
- **Takedowns:** requests through the takedown form are answered within 14 days and applied in
  the next release.

## 5. References
- Bastan, M., Koupaee, M., Son, Y., Sicoli, R., and Balasubramanian, N. (2020). Author's
  sentiment prediction. COLING.
- Boydstun, A. E., Card, D., Gross, J. H., Resnik, P., and Smith, N. A. (2020). The Policy
  Frames Codebook.
- Card, D., Boydstun, A. E., Gross, J. H., Resnik, P., and Smith, N. A. (2015). The Media
  Frames Corpus: Annotations of frames across issues. ACL-IJCNLP.
- Comparative Agendas Project (2022). Master Topics Codebook, version 1.1.
- IPTC (2026). Media Topics NewsCodes, release of 2026-09-30. http://cv.iptc.org/newscodes/mediatopic/
- Petukhova, A., and Fachada, N. (2023). MN-DS: A multilabeled news dataset for news articles
  hierarchical classification. Data 8(5), 74.
- Gilardi, F., Alizadeh, M., and Kubli, M. (2023). ChatGPT outperforms crowd workers for
  text-annotation tasks. PNAS 120(30).
- Hamborg, F., and Donnay, K. (2021). NewsMTSC: A dataset for (multi-)target-dependent
  sentiment classification in political news articles. EACL.
- Liu, S., Guo, L., Mays, K., Betke, M., and Wijaya, D. T. (2019). Detecting frames in news
  headlines and its application to analyzing news framing trends surrounding U.S. gun
  violence. CoNLL.
- Piskorski, J., Stefanovitch, N., Da San Martino, G., and Nakov, P. (2023). SemEval-2023
  Task 3. SemEval.
- Sebők, M., Máté, Á., Ring, O., Kovács, V., and Lehoczki, R. (2024). Leveraging open large
  language models for multilingual policy topic classification: The Babel Machine approach.
  Social Science Computer Review.
