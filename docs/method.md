# Method (DRAFT)

**DRAFT: not accepted yet.** This describes how CommonsWire will code and validate its
variables and how it keeps the corpus current. Nothing here has been run.

## 1. Unit and scope
- **Unit:** one article row (`src/commonswire/schema.py`): the body text as published, without
  boilerplate, captions or media, from a source whose status is `include` in
  `data/sources.csv`.
- **Out of scope:** third-party material (wire copy, partner stories, syndicated pieces) is
  dropped before any coding and counted per source.
- **Languages:** to be decided for version 1: English only, or every language the clean sources
  publish (Global Voices publishes in more than 40).

## 2. Variables
Every coded value is stored on its row with its provenance: the codebook version, the model and
its license, the prompt version, the time it was coded, and whether a person checked it
(`Coding` in `schema.py`). Published coded values use Apache-2.0 or MIT models.

### 2.1 Topic
- **Scheme:** the Comparative Agendas Project (CAP) major topics, Master Topics Codebook
  version 1.1 (2022-08-09): 1 Macroeconomics, 2 Civil Rights, 3 Health, 4 Agriculture, 5 Labor,
  6 Education, 7 Environment, 8 Energy, 9 Immigration, 10 Transportation, 12 Law and Crime,
  13 Social Welfare, 14 Housing, 15 Domestic Commerce, 16 Defense, 17 Technology, 18 Foreign
  Trade, 19 International Affairs, 20 Government Operations, 21 Public Lands, 23 Culture.
- **Additions for news,** following the CAP media datasets (for example the US New York Times
  Index codebook): arts and entertainment, sports and recreation, weather and natural
  disasters, religion, and "other or human interest", plus "no policy content".
- **Coding:** one primary topic per article, and up to two secondary topics.
- **Terms (to settle):** the CAP page says "Datasets and codebooks available on this site are ©
  Comparative Agendas Project 2015" and that the "topic code variables as well as other
  Project-generated variables" are under CC BY-NC-SA 4.0
  (<https://comparativeagendas.net/pages/Copyright-and-Legal>). Whether coding new texts with
  the topic list counts as reuse of those variables is not stated. The plan is to use the codes
  and names with the requested citation, write CommonsWire's own short definitions, and ask CAP
  before release whether CommonsWire's topic labels may be released under CC BY 4.0.

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
| CAP media datasets (Pennsylvania newspaper headlines and abstracts 1979 to 2015; The Times front-page headlines 1960 to 2008; New York Times Index descriptions 1946 to 2016) | CAP major topics | CC BY-NC-SA 4.0 for the codes; the source texts keep their copyright | Topic check on short texts, internal only; publish aggregate metrics, never the texts |
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
- **New:** each daily fetch adds the articles published since the last fetch (by the source's
  API or feed), after the third-party filter.
- **Changed:** an article whose text hash differs from the stored one is marked `changed`, its
  new text replaces the old in the next release, and its coded variables are coded again.
  Sources that report edits (for example a modified date in their API) are checked first.
- **Removed or corrected away:** an article that its source has removed (404 or 410, or gone
  from the source's API), or that its publisher asks to remove, is marked `removed`; its row
  stays with its metadata and its text is dropped in the next release.
- **Monthly check:** once a month, every article of the past year is checked against its
  source's API listing (dates and ids only, no text), and a rotating share of older articles is
  checked by URL, politely.
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
