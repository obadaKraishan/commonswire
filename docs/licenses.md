# Licenses

The license classes and the release split below were accepted on 2026-11-13 (maintainer's
decision), and version 0.1.0 is built on them. This is not legal advice.

## 1. The code
The CommonsWire software (`src/`, `tests/`) and the reference tables (`data/sources.csv`,
`data/candidates.csv`, the evidence metadata in `data/evidence/`) are licensed under the Apache
License 2.0 (`LICENSE`, `NOTICE`).

## 2. The articles keep their own licenses
CommonsWire does not relicense anyone's writing. Each article row carries:
- `license`: the license of that article, as an SPDX id (`CC-BY-4.0`) or `public-domain`;
- `credit_line`: the attribution the source asks for, filled in for that article (title,
  authors or the source's name, link, license), from the template in `data/sources.csv`;
- `url`: the link to the article at its source;
- `license_url`: the link to the license's legal text (for example
  <https://creativecommons.org/licenses/by/4.0/>, or the Public Domain Mark for public-domain
  rows).

A source's articles enter only when the source passes the clean-source rule on its own pages
(`docs/sources.md`). Third-party material (wire copy, partner stories, syndicated pieces) is
never included, because the source cannot license it.

## 3. License classes and the release split
The release is split into one configuration per class, so each user can take only what their
own use allows.

| Class | Licenses | What the dataset itself must do | How the schema meets it | What users must do |
|---|---|---|---|---|
| `pd` | `public-domain` (in version 0.1.0: English Wikinews articles published before 2005-09-25, which Wikinews' own copyright page places in the public domain; in general also, for example, US federal government works), `CC0-1.0` | Nothing is required by law; CommonsWire still credits the source as a courtesy and says where the public-domain status comes from | `license`, `credit_line`, `url`; the data card names the basis | Nothing required. Public-domain status under US law may not hold in every country; users outside the US should check their own law |
| `by` | CC BY 2.0, 2.5, 3.0 and 4.0 (and their ports) | Keep, for every article: the creator and source credit, the title, a link to the article, the license name and a link to the license, and a note that the text was taken from its page without photos, captions or embeds and with no words changed | `credit_line` (credit, title, link, license name), `license` and `license_url`, the data card's "changes" note | Keep each row's credit line and license with anything they share; say if they changed the text |
| `by-sa` | CC BY-SA 2.0 to 4.0 | As `by`. Share-alike binds adaptations of the text, not a collection that holds the text unchanged; each BY-SA row stays BY-SA | As `by`; the class is its own configuration so users can see which rows are BY-SA | As `by`, and release any adaptation of a BY-SA text (a translation, an edited version) under BY-SA |
| `nc-nd` | CC BY-NC, BY-ND, BY-NC-ND, BY-NC-SA, only for sources with `status=include` (that is, sources whose pages allow bulk, automatic reuse) | As `by`, never change the text, and never sell access to the class | As `by`; text is stored unchanged; the class is distributed free of charge, in its own configuration, with its NC and ND terms in the data card | Use it only for noncommercial purposes (NC); do not share changed versions of the text (ND) |

- **Version 0.1.0 holds only `pd`, `by` and `by-sa` rows.** NonCommercial and NoDerivatives
  sources that are silent on bulk reuse stay `pending`, so `nc-nd` is not built until a source
  allows bulk reuse in writing.
- **Coded variables** (topic, frame, types of sources, tone) are planned for a later version.
  When they are added, they are CommonsWire's own labels and will be released under CC BY 4.0,
  with the codebooks' terms noted (section 5).
- **Formats are not changes.** Section 2(a)(4) of CC BY 4.0 lets licensees use the material
  "in all media and formats whether now known or hereafter created" and "make technical
  modifications necessary to do so", and adds: "simply making modifications authorized by this
  Section 2(a)(4) never produces Adapted Material"
  (<https://creativecommons.org/licenses/by/4.0/legalcode.en>, read on 2026-11-14). Storing
  the text as plain paragraphs in a data file is such a change. The 2.5 and 3.0 licenses, which
  most `by` rows carry, have no such clause, so the data card and `LICENSES.md` also state the
  changes made, for every class. Leaving out photos and captions, which are separate works that
  the sources often do not license, removes material without changing the text.

### NoDerivatives works in a collection
The Creative Commons FAQ says: "Note that the ND licenses do allow you to reproduce the material
in unmodified form together with other material in a collection, as indicated in the next FAQ."
(<https://creativecommons.org/faq/#if-i-derive-or-adapt-material-offered-under-a-creative-commons-license-which-cc-licenses-can-i-use>).
On collections it adds: "You may choose a license for the collection, however this does not
change the license applicable to the original material." and "you still must adhere to the
license conditions governing your use of the material incorporated"
(<https://creativecommons.org/faq/#if-i-create-a-collection-that-includes-a-work-offered-under-a-cc-license-which-licenses-may-i-choose-for-the-collection>).

So a dataset can hold ND articles unchanged, each under its own license. What keeps most ND and
NC newsrooms out of CommonsWire is not the license but their own pages, which often ask
republishers to pick stories one at a time and not to republish automatically.

## 4. What users must do, in short
1. Keep each row's `credit_line`, `license` and `url` with anything you share.
2. Use only the classes your use allows (for example, leave out `nc-nd` for commercial work).
3. If you change a text (translate, edit, summarize it in a way that adapts it), mark the
   change, and for BY-SA texts release the change under BY-SA.
4. Do not claim the newsrooms endorse your work.
5. Watch new versions: an article corrected at its source gets its new text and the status
   `changed`, and an article removed at its source or taken down on request is left out. Please
   do the same in your copies (`index.csv` of the latest version lists every article in it).

## 5. Codebooks and gold data for the planned coded variables
- **IPTC Media Topics** (the topic scheme): CC BY 4.0 ("All NewsCodes vocabularies are copyright
  IPTC and licenced under the Creative Commons Attribution 4.0 licence"); credited in the data
  card. CAP codes are used only as an optional internal crosswalk and are not published (their
  "topic code variables" are CC BY-NC-SA 4.0).
- **Policy Frames Codebook:** no license stated; "We encourage the free, attributed use of the
  data collected using the Policy Frames Codebook for publications, instructional use, policy
  analysis, and other non-commercial purposes." Cited as the codebook asks.
- **Gold data** (`docs/method.md` §3.1) is used for internal checks only; only aggregate
  metrics are published, never the gold texts or labels.

## 6. Models
When coded values are published, they will come from models under Apache-2.0 or MIT, and each
value will record the model and its license. Version 0.1.0 has no coded values.
