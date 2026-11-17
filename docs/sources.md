# Sources

This file is generated from `data/sources.csv` by `commonswire sources render`; edit
the registry, not this file.

## The clean-source rule

A source's full text may enter the corpus only when all four hold, each read on a primary page
of that source and recorded with the URL, the date and a short exact quote:

1. a license or public-domain statement that allows redistributing the full text unchanged;
2. no clause against systematic, wholesale, bulk or automatic republishing, and no required
   tracking pixel or counter;
3. its terms of use and robots.txt do not forbid automated collection of the pages or feeds
   used;
4. a way to tell the source's own articles from third-party material (wire copy, partner
   stories, syndicated pieces), which is always left out.

A source that fails 1, 2 or 3 is **exclude**. A source whose pages are silent or unclear on any
point is **pending**, and is never included until the question is settled.

How the rule is read (rulings of 2026-11-13):

- (a) **An invitation is not a condition.** "Contact us if you would like to republish
  regularly" does not limit a CC BY license.
- (b) **A request is not a restriction.** "We urge you to link" does not limit public-domain
  text.
- (c) **No terms page.** A site with no terms of use page passes point 3 when its robots.txt
  allows the pages or feeds used.
- (d) **Silence on bulk use** passes only under public domain, CC0, CC BY and CC BY-SA, where
  the license itself grants it. Under NonCommercial or NoDerivatives licenses and under bespoke
  permissions, silence stays pending.

## Summary

151 sources checked: 14 include, 120 pending, 17 exclude.

| Source | Kind | License | Bulk | Robots | Terms | Tracking | Status |
|---|---|---|---|---|---|---|---|
| 360info | news | CC BY 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Africa Is a Country | news | CC BY 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Alt News | fact-check | CC BY 3.0 | silent | allows | silent | no | include (`license_allows`) |
| Balkan Diskurs | news | CC BY 3.0 | silent | allows | silent | no | include (`license_allows`) |
| Balkan Diskurs (Bosnian) | news | CC BY 3.0 | silent | allows | silent | no | include (`license_allows`) |
| EFF Deeplinks | advocacy | CC BY 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Factly | fact-check | CC BY 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Freedom of the Press Foundation | advocacy | CC BY 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Global Voices | news | CC BY 3.0 | silent | allows | silent | no | include (`license_allows`) |
| NIH News Releases | official | Public domain | silent | allows | silent | no | include (`license_allows`) |
| Salaam Times | state-agency | Public domain | silent | allows | silent | no | include (`license_allows`) |
| SciDev.Net | news | CC BY 2.0 | allows | allows | silent | no | include (`license_allows`) |
| The Public Record | news | CC BY-SA 4.0 | silent | allows | silent | no | include (`license_allows`) |
| Wikinews (English) | news | CC BY 2.5 | silent | allows | allows | no | include (`license_allows`) |
| Agenzia Fides | church-agency | CC BY 4.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Agência Brasil | state-agency | NOASSERTION | silent | allows | silent | no | pending (`no_license`) |
| Al-Jumhuriya | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Alt News (Hindi) | fact-check | CC BY 3.0 | silent | allows | silent | no | pending (`conflicting_statements`) |
| Arizona Mirror (States Newsroom) | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Caravanserai | state-agency | NOASSERTION | silent | allows | silent | no | pending (`site_unavailable`) |
| Chalkbeat | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Democracy Now! | news | CC BY-NC-ND 3.0 US | silent | allows | silent | no | pending (`nc_or_nd`) |
| DOD News | official | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Florida Phoenix (States Newsroom) | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Georgia Recorder (States Newsroom) | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Global Voices (am) | news | CC BY 3.0 | silent | allows | silent | no | pending (`statement_unread`) |
| Global Voices (ar) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ay) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (bg) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (bn) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ca) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (cs) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (da) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (de) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (el) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (eo) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (es) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (fa) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (fil) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (fr) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (he) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (hi) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (hr) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (hu) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (id) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ig) | news | CC BY 3.0 | silent | allows | silent | no | pending (`statement_unread`) |
| Global Voices (it) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ja) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (kk) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (km) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ko) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ku) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (mg) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (mk) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (my) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ne) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (nl) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (or) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (pa) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (pl) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (pt) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ro) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ru) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (sat) | news | CC BY 3.0 | silent | allows | silent | no | pending (`statement_unread`) |
| Global Voices (sq) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (sr) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (sv) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (sw) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (tet) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (tr) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (uk) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (ur) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (uz) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (yo) | news | CC BY 3.0 | silent | allows | silent | no | pending (`statement_unread`) |
| Global Voices (zh-Hans) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Global Voices (zh-Hant) | news | CC BY 3.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Healthbeat | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| KFF Health News | news | CC BY-NC-ND 4.0 | allows | allows | silent | no | pending (`nc_or_nd`) |
| Liberty TV Radio | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`conflicting_statements`) |
| Maryland Matters | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Meduza (English) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Mekong Eye | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Minority Africa | news | NOASSERTION | silent | allows | silent | no | pending (`no_license`) |
| Mississippi Today | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Mongabay | news | CC BY-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| NASA News | official | Public domain | silent | allows | silent | no | pending (`partial_license`) |
| New Canadian Media | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Ohio Capital Journal (States Newsroom) | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Oxpeckers | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`third_party_unclear`) |
| Pakistan Forward | state-agency | NOASSERTION | silent | allows | silent | no | pending (`site_unavailable`) |
| PanARMENIAN.Net | news | CC BY 4.0 | silent | none | silent | no | pending (`conflicting_statements`) |
| Project Multatuli | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Propastop | fact-check | CC BY-SA 3.0 | silent | allows | silent | no | pending (`partial_license`) |
| South Dakota News Watch | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`extra_conditions`) |
| Stateline | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| States Newsroom | news | NOASSERTION | allows | allows | silent | no | pending (`no_license`) |
| Tasnim News Agency (English) | state-agency | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| The 19th | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| The Marshall Project | news | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| US Department of State press releases | official | NOASSERTION | silent | blocked | silent | no | pending (`refused_requests`) |
| Votebeat | news | CC BY-NC-ND 4.0 | silent | allows | silent | no | pending (`nc_or_nd`) |
| Wikinews (ar) | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (bs) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ca) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (cs) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (de) | news | CC BY 2.5 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (el) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (eo) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (es) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (fa) | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (fi) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (fr) | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (guw) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (he) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (hu) | news | CC BY 3.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (it) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ja) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ko) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (li) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (nl) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (no) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (pl) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (pt) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ro) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ru) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (shn) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (sq) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (sr) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (sv) | news | CC BY-SA 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (ta) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (tr) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (uk) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| Wikinews (zh) | news | CC BY 4.0 | silent | allows | silent | no | pending (`partial_license`) |
| ZimFact | fact-check | NOASSERTION | silent | none | silent | no | pending (`site_unavailable`) |
| CalMatters | news | NOASSERTION | silent | allows | forbids | no | exclude (`terms_forbid_automation`) |
| Common Dreams | news | CC BY-NC-ND 3.0 | forbids | allows | silent | no | exclude (`bulk_clause`) |
| EduCeleb | news | LicenseRef-all-rights-reserved | silent | allows | silent | no | exclude (`rights_reserved`) |
| Grist | news | NOASSERTION | silent | allows | silent | yes | exclude (`tracker_required`) |
| Inside Climate News | news | CC BY-NC-ND 3.0 | forbids | allows | silent | yes | exclude (`bulk_clause`) |
| Institute for Nonprofit News | portal | LicenseRef-member-newsrooms | silent | blocked | silent | no | exclude (`third_party_portal`) |
| Mehr News Agency | state-agency | LicenseRef-all-rights-reserved | silent | allows | silent | no | exclude (`rights_reserved`) |
| Milwaukee Neighborhood News Service | news | CC BY-ND 4.0 | forbids | allows | silent | no | exclude (`bulk_clause`) |
| openDemocracy | news | CC BY-NC 4.0 | forbids | allows | silent | no | exclude (`bulk_clause`) |
| ProPublica | news | CC BY-NC-ND 3.0 US | forbids | allows | silent | yes | exclude (`bulk_clause`) |
| SINC | state-agency | CC BY 4.0 | forbids | allows | silent | no | exclude (`bulk_clause`) |
| The Conversation (US) | news | CC BY-ND 4.0 | forbids | allows | silent | yes | exclude (`bulk_clause`) |
| The Solutions Journalism Exchange | portal | NOASSERTION | forbids | allows | silent | no | exclude (`bulk_clause`) |
| The Texas Tribune | news | NOASSERTION | silent | allows | forbids | yes | exclude (`tracker_required`) |
| Truthout | news | CC BY-NC-ND 4.0 | forbids | allows | forbids | no | exclude (`bulk_clause`) |
| Undark | news | NOASSERTION | forbids | allows | silent | yes | exclude (`bulk_clause`) |
| Voice of America | state-agency | Public domain | forbids | allows | silent | no | exclude (`bulk_clause`) |

## Included

### 360info (`360info`)

News, INTL, en. Home: <https://360info.org/>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://360info.org/about-us/disclaimer-and-copyright/>); "Except where otherwise noted, content on this site is licensed under a Creative Commons Attribution 4.0 International license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://360info.org/about-us/terms-of-use/>)
- **Credit asked:** "If you republish an article , you must always attribute the Author/s and 360info as the creator of the material."
- **Third-party material:** Articles are commissioned from named university researchers; third-party copyright material 'will be noted with the content' (Terms of Use), and that material is left out
- **Status: include.** Reason code `license_allows`.
- **Notes:** Open-access research newswire with launch funding from Monash University (Australia); the terms add 'No additional restrictions' from CC BY; the terms of use are silent on automated access Re-read on 2026-11-16: the quoted words are unchanged.

### Africa Is a Country (`africasacountry`)

News, INTL, en. Home: <https://africasacountry.com/>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://africasacountry.com/about>); "Unless otherwise noted, all the content on Africa Is a Country is published under a Creative Commons BY 4.0 license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** content under other terms is 'otherwise noted' (About page); no separate rule for pieces first published elsewhere
- **Status: include.** Reason code `license_allows`. Site-wide CC BY 4.0 'unless otherwise noted' on the About page.
- **Notes:** the license sentence is on the About page; the home page footer shows only a CC BY 4.0 link with no text; pan-African outlet with no stated base No terms of use page exists on the site, so no terms forbid automated collection (point 3 passes, as for a silent terms page). Re-read on 2026-11-16: the quoted words are unchanged. No API, feed or sitemap: articles are read from the front-page listing (/category/front-page?page=N, 126 pages of 20 on 2026-11-16).

### Alt News (`altnews`)

Fact-check, IN, en, hi. Home: <https://www.altnews.in/>. Checked on 2026-11-16.

- **License:** CC BY 3.0 (<https://www.altnews.in/about/>); "All the content on the Alt News website, except where otherwise noted, is licensed under the Creative Commons Attribution 3.0 Unported License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.altnews.in/terms-and-conditions/>)
- **Third-party material:** Embedded social-media posts (tweets, Facebook, Instagram, YouTube) are third-party and are removed as embeds; other material is 'otherwise noted'; videos are not collected
- **Status: include.** Reason code `license_allows`. The explicit CC BY 3.0 grant on the About page and in every footer ('Content licensed under CC BY 3.0') governs; the 'All rights reserved' line next to it is boilerplate (ruling of 2026-11-13).
- **Notes:** the Terms and Conditions page covers donations only (silent on site use); Hindi edition at /hindi/; fact-checks embed social media posts, which are not collected English site only (the Hindi edition at /hindi/ is not collected). Re-read on 2026-11-16: the quoted words are unchanged.

### Balkan Diskurs (`balkandiskurs`)

News, BA, en, bs. Home: <https://balkandiskurs.com/en/>. Checked on 2026-11-16.

- **License:** CC BY 3.0 (<https://balkandiskurs.com/en/republishing-guidelines/>); "This site is licensed as Creative Commons Attribution 3.0."
- **Bulk or automatic reuse:** silent; "if you’re interested in republishing our articles on a regular basis or under special terms"
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You are free to share, republish, translate or remix our stories so long as you clearly attribute and link to Balkan Diskurs and the author as the original source."
- **Third-party material:** the license covers 'All content created by Balkan Diskurs'; photos, video and audio follow it 'unless otherwise stated'; how partner pieces are marked is not stated
- **Status: include.** Reason code `license_allows`. Site-wide CC BY 3.0; the request to write in before republishing 'on a regular basis' is read as an invitation, as for Global Voices (to confirm).
- **Notes:** the guidelines' example credit is 'This article was originally published by Balkan Diskurs'; published with the Post-Conflict Research Center; Bosnian edition beside English No terms of use page exists on the site, so no terms forbid automated collection (point 3 passes, as for a silent terms page). Re-read on 2026-11-16: the quoted words are unchanged.

### Balkan Diskurs (Bosnian) (`balkandiskurs_bs`)

News, BA, bs. Home: <https://balkandiskurs.com/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0>); "Sav sadržaj kreiran na Balkan Diskursu je objavljen pod licencom Creative Commons Attribution Only"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://balkandiskurs.com/attribution-policy/>)
- **Credit asked:** "Imate pravo da dijelite, ponovo objavljujete, prevodite ili preradite naše priče, uz oznaku da je originalni izvor platforma Balkan Diskurs i uz navođenje autora."
- **Third-party material:** the license covers 'Sav sadržaj kreiran na Balkan Diskursu' (gloss: all content created on Balkan Diskurs); how partner pieces are marked is not stated
- **Status: include.** Reason code `license_allows`. Its own attribution policy (in Bosnian) puts all content created on Balkan Diskurs under CC BY ('Creative Commons Attribution Only'); its footer says 'This site is licensed as Creative Commons Attribution 3.0'; robots.txt allows the pages and the API.
- **Notes:** The Bosnian edition (the site's default language, hreflang bs). (gloss) 'All content created on Balkan Diskurs is published under the Creative Commons Attribution Only license. You may share, republish, translate or adapt our stories, noting Balkan Diskurs as the original source and naming the author.' Its root API lists 878 posts; whether it lists the Bosnian posts apart from the English ones is not established.

### EFF Deeplinks (`eff`)

Advocacy, US, en. Home: <https://www.eff.org/deeplinks>. Checked on 2026-11-13.

- **License:** CC BY 4.0 (<https://www.eff.org/copyright>); "Any and all original material on the EFF website may be freely distributed at will under the Creative Commons Attribution 4.0 International License (CC-BY), unless otherwise noted."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.eff.org/policy>)
- **Credit asked:** "If you redistribute something you got from the EFF site, it is appreciated if you make it known where the file originated, so people can get more info or updated versions."
- **Third-party material:** Only 'original material' is CC BY; material not original to EFF is noted ('unless otherwise noted') and left out
- **Status: include.** Reason code `license_allows`.
- **Notes:** Advocacy organization's blog; robots.txt crawl-delay 30 s; no separate terms of use exists (the privacy policy was read and is silent on automated access)

### Factly (`factly`)

Fact-check, IN, en, te. Home: <https://factly.in/>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://factly.in/faqs/>); "Except where otherwise noted, content on Factly is licensed under a Creative Commons Attribution 4.0 International License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give appropriate credit, provide a link to the license, and indicate if changes were made."
- **Third-party material:** Videos are outside the license; embedded social-media posts are third-party and are removed as embeds; other material is 'otherwise noted'
- **Status: include.** Reason code `license_allows`. Site-wide CC BY 4.0 'except where otherwise noted' (FAQ and every footer); no terms page was found and robots.txt allows the feeds and API (ruling c).
- **Notes:** the footer says 'Except for videos'; the FAQ adds 'We would also like to be informed about the kind of use' (a request); Telugu section English site only (the Telugu section is not collected). Re-read on 2026-11-16: the quoted words are unchanged.

### Freedom of the Press Foundation (`freedompress`)

Advocacy, US, en. Home: <https://freedom.press/>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://freedom.press/>); "Licensed under Creative Commons CC-BY 4.0 where not otherwise indicated."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** material under other terms is 'otherwise indicated'; photo credits name agencies (for example 'via AP'); photos are not collected
- **Status: include.** Reason code `license_allows`. Site-wide CC BY 4.0 'where not otherwise indicated' in the footer.
- **Notes:** robots.txt sets crawl-delay 10; the license is stated only in the footer; no feed link on the home page No terms of use page exists on the site, so no terms forbid automated collection (point 3 passes, as for a silent terms page). Re-read on 2026-11-16: the quoted words are unchanged.

### Global Voices (`globalvoices`)

News, INTL, en. Home: <https://globalvoices.org/>. Checked on 2026-11-16.

- **License:** CC BY 3.0 (<https://globalvoices.org/about/global-voices-attribution-policy/>); "This site is licensed as Creative Commons Attribution 3.0. Please read our attribution policy to learn about freely redistributing our work"
- **Bulk or automatic reuse:** silent; "If you would like to republish our stories regularly or under special terms, please contact us."
- **Automated collection:** robots.txt allows; terms silent (<https://globalvoices.org/privacy/>)
- **Credit asked:** "When you share, republish or translate our stories, you must include a link to the original Global Voices story and the name of the author at the top of the republished post."
- **Third-party material:** The license covers 'all content created by Global Voices' unless otherwise stated; it runs reciprocal republication partnerships, so items carrying another outlet's credit or 'otherwise stated' terms are left out; photos, video and audio from other creators are excluded
- **Status: include.** Reason code `license_allows`. Site-wide CC BY 3.0; the 'contact us to republish regularly' line is read as an invitation, not a condition (to confirm).
- **Notes:** robots.txt crawl-delay 10 s; no separate terms of use exists (the privacy policy was read and is silent on automated access; it says misbehaving bots are blocked by a firewall); the policy page shows the license as 'Attribution-Only' and links CC BY 3.0; Lingua sites in about 50 other languages carry the same footer; the attribution policy, read again on 2026-11-14 with the same text, asks for translations only what it asks for every republication (the link and the author's name, quote_attribution) and does not mention translators; translators named on the site will also be named in the credit line (maintainer's decision, 2026-11-14) Re-read on 2026-11-16: the quoted words are unchanged.

### NIH News Releases (`nih`)

Official, US, en. Home: <https://www.nih.gov/news-events/news-releases>. Checked on 2026-11-13.

- **License:** Public domain (<https://www.nih.gov/about-nih/frequently-asked-questions>); "Most of the information on our site is in the public domain and can be used without charge or restriction."
- **Bulk or automatic reuse:** silent; "For that reason, we urge you to link to our resource documents rather than re-posting. If you do re-post, please check back periodically to see if there are revisions."
- **Automated collection:** robots.txt allows; terms silent (<https://www.nih.gov/web-policies-notices>)
- **Third-party material:** Third-party items carry their own copyright statement (FAQ); press releases are posted only if developed by or for NIH (web policies page)
- **Status: include.** Reason code `license_allows`. Site-wide public-domain statement on the NIH FAQ page; bulk silent, which passes under a public-domain statement.
- **Notes:** An official US government source. The Web Policies and Notices page says nothing on copyright or reuse of text; the statement is in the FAQ's Copyright section, which also says copyrighted materials 'will include a copyright statement'. The FAQ urges linking rather than re-posting health publications and asks re-posters to check back for revisions (the monthly correction check covers this). Images are third-party licensed (text only anyway).

### Salaam Times (`salaamtimes`)

State-agency, US, en, prs, ps. Home: <https://afghanistan.asia-news.com/en_GB/>. Checked on 2026-11-16.

- **License:** Public domain (<https://afghanistan.asia-news.com/en_GB/pages/about>); "Unless a copyright is indicated, information on the site is in the public domain and may be copied and distributed without permission."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://afghanistan.asia-news.com/en_GB/pages/about>)
- **Credit asked:** "Citation of the original source of the information is appreciated."
- **Third-party material:** material under someone else's copyright is marked ('Unless a copyright is indicated'); photos and graphics with a copyright need the source's permission
- **Status: include.** Reason code `license_allows`. Site-wide public-domain statement on the About page; citation is asked, not required (ruling b). A state-funded outlet (kind state-agency): not collected unless the maintainer decides so.
- **Notes:** The About page: 'Salaam Times is a product of an international media organization publicly funded from the budget of the United States Government.' Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag it Public Domain. Its feed (the one Open Newswire lists) was not probed in this session.

### SciDev.Net (`scidevnet`)

News, GB, en, fr, es, ar. Home: <https://www.scidev.net/global/>. Checked on 2026-11-16.

- **License:** CC BY 2.0 (<https://www.scidev.net/global/content/media.html>); "SciDev.Net makes the written content of this website available for use by others under a Creative Commons Attribution 2.0 licence."
- **Bulk or automatic reuse:** allows; "If you are interested in taking more than one article from our site our customisable webfeeds might be the answer for you."
- **Automated collection:** robots.txt allows; terms silent (<https://www.scidev.net/global/content/policies.html>)
- **Credit asked:** "SciDev.Net must be credited as the original source of the article at the start, no more than three paragraphs in"
- **Third-party material:** Material owned by others is marked 'unless otherwise stated' and its source is indicated within the document or photo
- **Status: include.** Reason code `license_allows`. Every article page carries the line 'All site content, except where otherwise noted, is licensed under a Creative Commons Attribution License', linked to the media page, which names CC BY 2.0; rows take CC BY 2.0 (ruling of 2026-11-13).
- **Notes:** Run by CABI (Wallingford, UK); both versions allow verbatim redistribution with credit; the terms are silent on automated access; editions in English, French, Spanish and Arabic Article pages (2026-11-13): 'All site content, except where otherwise noted, is licensed under a Creative Commons Attribution License', linked to https://www.scidev.net/content/media/; the terms page says 'Creative Commons Attribution 3.0 licence'. The CC links on article pages (CC BY 2.0, CC BY-ND 2.0) are photo credits; photos are never collected. English edition (/global/) only. Re-read on 2026-11-16: the quoted words are unchanged. Every article page's republishing box (article pages saved 2026-11-13 and 2026-11-17) says 'You have to credit our authors.' and 'You have to credit SciDev.Net — where possible include our logo with a link back to the original article.', so rows with no byline are held (maintainer, 2026-11-17). Of its embed code, which carries a Google Analytics event script, the box says 'The easiest way to get the article on your site is to embed the code below.': the code is offered, not required, so no tracker is required (ruling a; maintainer, 2026-11-17). Its 'Supported content' pages (the breadcrumb's label) are kept only with SciDev.Net's own byline, the site's license line and no other holder named; the others are left out as third-party or sponsored material (maintainer, 2026-11-17). Its articles are a custom post type the API does not give, so they are read from the 14 article sitemaps (13,302 pages on 2026-11-16) and the article pages.

### The Public Record (`thepublicrecord`)

News, CA, en. Home: <https://thepublicrecord.ca/>. Checked on 2026-11-16.

- **License:** CC BY-SA 4.0 (<https://thepublicrecord.ca/use-our-content-our-licensing/>); "© 2026 Unless otherwise stated, All Original Content is Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
- **Bulk or automatic reuse:** silent; "if you are planning to use our content under the terms of our CC-BY-SA license, you don’t have to contact us for permission, the license grants it"
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "We ask that you please identify our work using the author’s name and “The Public Record”."
- **Third-party material:** only 'All Original Content' is licensed, 'unless otherwise stated'; work used from other sites keeps its own license and is credited (licensing page, code of ethics)
- **Status: include.** Reason code `license_allows`. Site-wide CC BY-SA 4.0 on a dedicated licensing page that says no permission is needed.
- **Notes:** the clearest case in this group: a dedicated licensing page that waives any need to ask; the privacy policy uses IP addresses 'to identify automated traffic and abuse' (no ban); Hamilton, Ontario local news No terms of use page exists on the site, so no terms forbid automated collection (point 3 passes, as for a silent terms page). Re-read on 2026-11-16: the quoted words are unchanged.

### Wikinews (English) (`wikinews_en`)

News, INTL, en. Home: <https://en.wikinews.org/>. Checked on 2026-11-13.

- **License:** CC BY 2.5 (<https://en.wikinews.org/wiki/Wikinews:Copyright>); "All material published on Wikinews after December 16, 2024 is licensed under the terms of the Creative Commons Attribution 4.0 License. Material published prior December 16, 2024 but after September 25, 2005 is licensed under the terms of the Creative Commons Attribution 2.5 License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms allows (<https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use>); "We make available a set of APIs, which include documentation and associated tools, to enable users to build products that promote free knowledge."
- **Credit asked:** "This work may be attributed to "Wikinews"."
- **Third-party material:** Text is written by volunteer editors; the copyright policy bars copyrighted and other-Wikimedia text, and the footer license applies 'unless otherwise noted', so pages with a different notice are left out
- **Status: include.** Reason code `license_allows`. CC BY 2.5 for 2005-09-25..2024-12-16, CC BY 4.0 after, public domain before; set each article's license by its date.
- **Notes:** CLOSED: the Wikimedia Foundation closed all Wikinews editions; read-only since 2026-05-04 (main page: 'Wikinews has been made read-only'), so a fixed archive with no new articles; the footer says CC BY 4.0 'unless otherwise noted'; the WMF Terms of Use bar automated uses that are abusive, break usage policies 'or have not been approved by the Wikimedia community', and bind API users to the User-Agent and Robot policies; collect through the API or dumps under those policies Each article's license follows its date (commonswire.licensing): public domain before 2005-09-25, CC BY 2.5 to 2024-12-16, CC BY 4.0 after. Paths (2026-11-13): en.wikinews.org/robots.txt disallows /w/ (the MediaWiki API) and allows /wiki/ article pages for general user agents; CommonsWire reads only the dump from https://dumps.wikimedia.org/enwikinews/, which that host's robots.txt allows.

## Pending: a question to settle first

### Agenzia Fides (`fides`)

Church-agency, VA, it, en, es, fr, de, zh. Home: <https://www.fides.org/en>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://www.fides.org/en>); "The contents of the site are licensed under Creative Commons Attribution 4.0 International License"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. No terms-of-use page was found and no page says how texts by others (Vatican documents, other agencies) are marked: may Fides be included on its footer CC BY 4.0 line, and how would third-party texts be told apart?
- **Notes:** information service of the Pontifical Mission Societies, in Vatican City (a Holy See body); the license is stated only in the footer; RSS at /en/news/rss Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged. The news agency of the Pontifical Mission Societies (kind church-agency); its footer line was read again on the home, an article and the About page.

### Agência Brasil (`agenciabrasil`)

State-agency, BR, pt-BR, en, es. Home: <https://agenciabrasil.ebc.com.br/>. Checked on 2026-11-13.

- **License:** no license named (<https://agenciabrasil.ebc.com.br/en/about>); "All content produced by Agência Brasil may be reproduced free of charge, as long as the source is properly credited."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.ebc.com.br/termos-de-uso-e-condicoes-gerais-do-portal-da-ebc>); "é proibida a adoção de técnicas de clonagem ou de framing"
- **Credit asked:** "Reprodução autorizada mediante indicação da fonte."
- **Third-party material:** not stated
- **Status: pending.** Reason code `no_license`. Agência Brasil lets anyone reproduce its own content free with credit but names no license (the footer reads 'Todos os direitos reservados pela EBC' and the EBC terms limit portal use to personal, non-commercial ends), and it mixes in partner-agency content without a stated marker: is this bespoke permission enough, and how should partner content be told apart?
- **Notes:** Public news agency of EBC (state-owned); robots.txt crawl-delay 10 s; the EBC licensing page sells licenses for EBC works; the EBC terms bar probing security, 'clonagem' (cloning) and framing aimed at harming the portal's protections, which reads as a security clause, not a scraping ban; WebSearch shows 2006-2013 pages that named CC BY (2.5, then 3.0 Brasil), no longer on the current site (not fetched) Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Al-Jumhuriya (`aljumhuriya`)

News, INTL, ar, en. Home: <https://www.aljumhuriya.net/en/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. The home page answered 403 to our client on 2026-11-16, so no page could be read: can the maintainer read https://www.aljumhuriya.net/en/ in a browser for its license line (Open Newswire quotes an Arabic line that names a Creative Commons license without saying which)?
- **Notes:** Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag it CC BY. robots.txt answered 200 and shuts out several AI crawlers by name, not this client. Where it is based was not read.

### Alt News (Hindi) (`altnews_hi`)

Fact-check, IN, hi. Home: <https://www.altnews.in/hindi/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://www.altnews.in/hindi/>); "CC BY 3.0 के तहत लाइसेंस प्राप्त"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found); "© 2026 ऑल्ट न्यूज़. सर्वाधिकार सुरक्षित."
- **Third-party material:** not stated
- **Status: pending.** Reason code `conflicting_statements`. Its footer says 'licensed under CC BY 3.0' and also 'All rights reserved' (gloss of 'सर्वाधिकार सुरक्षित'), with no license link. Which one holds for its articles?
- **Notes:** The Hindi edition of Alt News, linked from https://www.altnews.in/ as 'हिंदी'. (gloss) '© 2026 Alt News. All rights reserved. Pravda Media Foundation ... licensed under CC BY 3.0'. Its API lists 5180 posts (2017-04-02 to 2026-11-13).

### Arizona Mirror (States Newsroom) (`azmirror`)

News, US, en. Home: <https://azmirror.com/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://azmirror.com/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Arizona Mirror credit, including https://azmirror.com and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Arizona Mirror's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Caravanserai (`caravanserai`)

State-agency, INTL, en. Home: <https://central.asia-news.com/en_GB/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `site_unavailable`. The home and About pages show only 'This website is no longer available' on 2026-11-16, so there is no license or terms to read: drop it, or keep it pending in case it returns?
- **Notes:** Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag it Public Domain, quoting 'Unless a copyright is indicated, information on the site is in the public domain'. It is on the same platform as Salaam Times, whose About page says it is 'publicly funded from the budget of the United States Government' (kind state-agency).

### Chalkbeat (`chalkbeat`)

News, US, en. Home: <https://www.chalkbeat.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://www.chalkbeat.org/pages/republishing/>); "Unless otherwise noted, Chalkbeat stories are free to republish through a Creative Commons CC BY-NC-ND 4.0 license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.civicnews.org/tos>)
- **Credit asked:** "Please include this line at the top of the story: “This story was originally published by Chalkbeat. Sign up for their newsletters at ckbe.at/newsletters”."
- **Third-party material:** Stories are CC 'unless otherwise noted'; the page does not say how partner or wire stories are noted
- **Status: pending.** Reason code `nc_or_nd`. Chalkbeat licenses its stories CC BY-NC-ND 4.0 'unless otherwise noted' and is silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); may an NC-ND source silent on bulk enter the corpus?
- **Notes:** Published by Civic News Company; its Terms of Service (civicnews.org/tos, read as a Chalkbeat page) defer to the republishing policy, are silent on automated access and say the Services are intended for US users only. Per-story republish pages were not read (they hold article text). Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Democracy Now! (`democracynow`)

News, US, en, es. Home: <https://www.democracynow.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 3.0 US (<https://www.democracynow.org/2026/11/11/headlines/federal_appeals_court_rules_trump_admin_illegally_fired_head_of_voice_of_america>); "The original content of this program is licensed under a Creative Commons Attribution-Noncommercial-No Derivative Works 3.0 United States License."
- **Bulk or automatic reuse:** silent; "Our creative commons copyright encourages YOU to republish DN! transcripts in any way YOU can."
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "Please attribute legal copies of this work to democracynow.org."
- **Third-party material:** not stated
- **Status: pending.** Reason code `nc_or_nd`. Democracy Now! licenses its original program content CC BY-NC-ND 3.0 US and invites reprinting transcripts 'in any way YOU can', but says only that incorporated works 'may be separately licensed' without marking them; may this NC-ND source enter, and how would third-party material be told apart?
- **Notes:** The license line is on every program page, not on a site-wide policy page. robots.txt sets crawl-delay 10. Pages are broadcast transcripts and headlines; a Spanish edition is at /es/. No terms of use page was found. Not pursued for version 1 (maintainer's decision, 2026-11-13).

### DOD News (`dodnews`)

Official, US, en. Home: <https://www.defense.gov/News/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. defense.gov answered 403 to robots.txt, so the project client read no page there; could the maintainer read the site's copyright or privacy-and-security notice in a browser and confirm that DOD News text is public domain or free to copy and distribute, with no terms against automated collection?
- **Notes:** An official US government source. robots.txt answered 403, so every page is refused by the client; nothing was saved. Search results show defense.gov pages now titled 'Department of War'. Not pursued for version 1 (maintainer's decision, 2026-11-13). robots.txt answered 403 again on 2026-11-16.

### Florida Phoenix (States Newsroom) (`floridaphoenix`)

News, US, en. Home: <https://floridaphoenix.com/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://floridaphoenix.com/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Florida Phoenix credit, including https://floridaphoenix.com and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Florida Phoenix's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Georgia Recorder (States Newsroom) (`georgiarecorder`)

News, US, en. Home: <https://georgiarecorder.com/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://georgiarecorder.com/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Georgia Recorder credit, including https://georgiarecorder.com and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Georgia Recorder's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Global Voices (am) (`globalvoices_am`)

News, INTL, am. Home: <https://am.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "ይህ ድረገጽ ንብረትነቱ የጋራ ፈጠራዎች ባሕርያት 3.0 Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `statement_unread`. The footer statement is in Amharic, which this project could not read with confidence; its link names CC BY 3.0. Does the statement grant CC BY 3.0 as the link says?
- **Notes:** A Lingua edition of Global Voices at https://am.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 73 posts (newest 2020-09-01); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ar) (`globalvoices_ar`)

News, INTL, ar. Home: <https://ar.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ar>); "هذا الموقع مرخص المشاع الإبداعي - النسبة 3.0 بعض الحقوق محفوظة"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ar.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ar. Its API lists 6512 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ay) (`globalvoices_aym`)

News, INTL, ay. Home: <https://aym.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Aka sition lisinsyapa Creative Commons Attribution 3.0 Yaqhip Derechos Reservado-naka"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://aym.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 844 posts (newest 2026-09-19); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (bg) (`globalvoices_bg`)

News, INTL, bg. Home: <https://bg.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Този сайт е под лиценз Creative Commons Attribution 3.0 Някои права запазени"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://bg.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 338 posts (newest 2025-09-01); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (bn) (`globalvoices_bn`)

News, INTL, bn. Home: <https://bn.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "এই সাইটটি ক্রিয়েটিভ কমন্স এট্রিবিউশন্স ৩.০ লাইসেন্সের মাধ্যমে প্রকাশিত কিছু অধিকার সংরক্ষিত"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://bn.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 8721 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ca) (`globalvoices_ca`)

News, INTL, ca. Home: <https://ca.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ca>); "Aquest web té la llicència Reconeixement 3.0 No adaptada (CC BY 3.0) Alguns drets reservats"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ca.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ca. Its API lists 874 posts (newest 2026-11-04); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (cs) (`globalvoices_cs`)

News, INTL, cs. Home: <https://cs.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.cs>); "Tato stránka je licencována v rámci Creative Commons Uveďte autora 3.0 Některá práva vyhrazena"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://cs.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.cs. Its API lists 676 posts (newest 2022-02-16); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (da) (`globalvoices_da`)

News, INTL, da. Home: <https://da.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.da>); "Denne side benyttes under følgende licens Creative Commons Tilskrivning 3.0 Nogle rettigheder forbeholdes"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://da.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.da. Its API lists 394 posts (newest 2023-03-11); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (de) (`globalvoices_de`)

News, INTL, de. Home: <https://de.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.de>); "Diese Website ist lizenziert als Creative Commons Namensnennung 3.0 DE Lizenz Einige Rechte vorbehalten"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://de.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.de. Its words say '3.0 DE Lizenz' while the link is the unported 3.0 deed in German; the row follows the link. Its API lists 3318 posts (newest 2025-07-15); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (el) (`globalvoices_el`)

News, INTL, el. Home: <https://el.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/gr/deed.el>); "Το περιεχόμενο του παρόντος ιστοχώρου υπάγεται σε Άδεια Χρήσης Creative Commons Attribution 3.0 Με επιφύλαξη μερικών δικαιωμάτων"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://el.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/gr/deed.el. Its words name 'Creative Commons Attribution 3.0'; its link is the Greek port (by/3.0/gr), which the release does not list as a license of its own yet. Its API lists 10869 posts (newest 2026-11-16); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (eo) (`globalvoices_eo`)

News, INTL, eo. Home: <https://eo.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.eo>); "Ĉi tiu retejo ricevis permesilon per Krea Komunaĵo Atribuado 3.0 Kelkaj rajtoj rezervitaj"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://eo.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.eo. Its API lists 855 posts (newest 2026-11-15); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (es) (`globalvoices_es`)

News, INTL, es. Home: <https://es.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.es>); "Este sitio está licenciado como Atribución Creative Commons 3.0. Por favor lea nuestra Pautas de Republicación para saber cómo redistribuir libremente nuestro trabajo Algunos derechos reservados"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://es.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.es. (gloss) It adds 'Please read our Republishing Guidelines to learn how to freely redistribute our work'; that page was not read. Its API lists 45948 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (fa) (`globalvoices_fa`)

News, INTL, fa. Home: <https://fa.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.fa>); "این سایت تحت مجوز Creative Commons Attribution 3.0 است Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://fa.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.fa. Its API lists 1015 posts (newest 2024-12-20); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (fil) (`globalvoices_fil`)

News, INTL, fil. Home: <https://fil.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "This site is licensed as Creative Commons Attribution 3.0 Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://fil.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 302 posts (newest 2025-04-09); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (fr) (`globalvoices_fr`)

News, INTL, fr. Home: <https://fr.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.fr>); "Ce site est mis à disposition sous une Licence 3.0 Creative Commons (mention de l'auteur, du site et lien) Certains droits réservés"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://fr.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.fr. (gloss) 'Licence 3.0 Creative Commons (mention of the author, the site and a link)'. Its API lists 21691 posts (newest 2026-11-09); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (he) (`globalvoices_he`)

News, INTL, he. Home: <https://he.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "אתר זה מורשה לשימוש תחת קריאייטיב קומונס ייחוס 3.0 חלק מהזכויות שמורות"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://he.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 33 posts (newest 2016-11-27); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (hi) (`globalvoices_hi`)

News, INTL, hi. Home: <https://hi.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.hi>); "यह जालस्थल क्रिएटिव कॉमनस् अधिकार 3.0 अनुज्ञप्ति प्राप्त है कुछ अधिकार सुरक्षित"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://hi.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.hi. (gloss) It names 'Creative Commons rights 3.0'; the link names CC BY 3.0. Its API lists 271 posts (newest 2025-12-14); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (hr) (`globalvoices_hr`)

News, INTL, hr. Home: <https://hr.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.hr>); "Ova stranica je ovlaštena kao Creative Commons Attribution 3.0 Neka prava su rezervirana"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://hr.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.hr. Its API lists 33 posts (newest 2026-09-06); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (hu) (`globalvoices_hu`)

News, INTL, hu. Home: <https://hu.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.hu>); "Az oldal által használt licensz: Creative Commons 3.0 Szerzői jogvédelem alatt"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://hu.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.hu. (gloss) It renders 'Some rights reserved' as 'under copyright protection'. Its API lists 621 posts (newest 2023-05-26); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (id) (`globalvoices_id`)

News, INTL, id. Home: <https://id.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.id>); "Situs ini berlisensi Creative Commons versi 3.0 Sebagian Hak Dilindungi"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://id.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.id. Its API lists 753 posts (newest 2025-09-30); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ig) (`globalvoices_ig`)

News, INTL, ig. Home: <https://ig.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Saitị nwere ikike dịka Ihe njiri mara ihe okike 3.0 Ejikwachitụrụ ụfọdụ ikike"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `statement_unread`. The footer statement is in Igbo, which this project could not read with confidence; its link names CC BY 3.0. Does the statement grant CC BY 3.0 as the link says?
- **Notes:** A Lingua edition of Global Voices at https://ig.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 79 posts (newest 2026-11-12); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (it) (`globalvoices_it`)

News, INTL, it. Home: <https://it.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.it>); "questo sito è coperto dalla Creative Commons Attribuzione 3.0 Alcuni diritti riservati"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://it.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.it. Its API lists 10696 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ja) (`globalvoices_jp`)

News, INTL, ja. Home: <https://jp.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ja>); "このサイトはCreative Commons Attribution 3.0ライセンスで公開しています Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://jp.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ja. Its API lists 2905 posts (newest 2026-11-02); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (kk) (`globalvoices_kk`)

News, INTL, kk. Home: <https://kk.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Сайт «Creative Commons» лицензиясы лиценсиясымен жұмыс істеуде Құқықтар шамалы түрде қорғалған"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://kk.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. (gloss) 'The site works under the Creative Commons license': no version in its words; the link names CC BY 3.0. Its API lists 17 posts (newest 2026-02-21); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (km) (`globalvoices_km`)

News, INTL, km. Home: <https://km.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.km>); "សាយ នេះ ត្រូវបាន ផ្តល់សិទ្ធ ជា Creative Commons Attribution 3.0 Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://km.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.km. Its API lists 32 posts (newest 2013-12-13); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ko) (`globalvoices_ko`)

News, INTL, ko. Home: <https://ko.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ko>); "이 사이트는 크리에이티브 커먼스 저작권 정책을 따르고 있습니다. Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ko.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ko. (gloss) 'This site follows the Creative Commons copyright policy': no version in its words; the link names CC BY 3.0. Its API lists 422 posts (newest 2024-08-29); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ku) (`globalvoices_ku`)

News, INTL, ku. Home: <https://ku.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "This site is licensed as Creative Commons Attribution 3.0 هەندێک مافی پارێزراوە"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ku.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 4 posts (newest 2018-04-29); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (mg) (`globalvoices_mg`)

News, INTL, mg. Home: <https://mg.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Ny marik-ity takelaka ity dia efa voapetraka Creative Commons Attribution 3.0 Zo Sasantsasany Voatokana"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://mg.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 20675 posts (newest 2026-10-23); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (mk) (`globalvoices_mk`)

News, INTL, mk. Home: <https://mk.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Овој сајт е лиценциран под Криејтив комонс - Наведи извор 3.0 Некои права задржани"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://mk.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 2554 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (my) (`globalvoices_my`)

News, INTL, my. Home: <https://my.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "ဤ စာ မျက်နှာ သည် Creative Commons Attribution 3.0 အရ ခွင့် ပြု ချက် ရ ယူထား ပါ သည်။ Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://my.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 132 posts (newest 2018-11-06); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ne) (`globalvoices_ne`)

News, INTL, ne. Home: <https://ne.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "यो साइट क्रियटिभ कमन्स लाइसेन्स अन्तर्गत संचालित छ केही अधिकार सुरक्षित"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ne.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. (gloss) 'This site operates under a Creative Commons license': no version in its words; the link names CC BY 3.0. Its API lists 298 posts (newest 2026-10-14); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (nl) (`globalvoices_nl`)

News, INTL, nl. Home: <https://nl.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.nl>); "Deze site valt onder een Creative Commons Attribution 3.0-licentie Sommige rechten voorbehouden"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://nl.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.nl. Its API lists 2282 posts (newest 2026-11-10); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (or) (`globalvoices_or`)

News, INTL, or. Home: <https://or.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "ଏହି ସାଇଟଟି Creative Commons Attribution 3.0 ରେ ଲାଇସେନ୍ସ ହୋଇଛି କିଛି କପିରାଇଟ ସଂରକ୍ଷିତ"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://or.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 35 posts (newest 2023-02-20); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (pa) (`globalvoices_pa`)

News, INTL, pa. Home: <https://pa.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "ਇਹ ਸਾਈਟ ਕ੍ਰੀਏਟਿਵ ਕਾਮਨਜ਼ ਐਟਰੀਬਿਊਸ਼ਨ 3.0 ਲਸੰਸ ਅਧੀਨ ਹੈ ਕੁਝ ਹੱਕ ਰਾਖਵੇਂ"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://pa.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 121 posts (newest 2025-03-18); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (pl) (`globalvoices_pl`)

News, INTL, pl. Home: <https://pl.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.pl>); "Strona udostępniona na licencji Creative Commons Uznanie autorstwa 3.0 Pewne prawa zastrzeżone"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://pl.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.pl. Its API lists 2044 posts (newest 2023-05-24); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (pt) (`globalvoices_pt`)

News, INTL, pt. Home: <https://pt.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.pt_BR>); "Este site está licenciado como Creative Commons Atribuição 3.0 Alguns direitos reservados"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://pt.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.pt_BR. Its API lists 7902 posts (newest 2026-11-16); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ro) (`globalvoices_ro`)

News, INTL, ro. Home: <https://ro.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ro>); "Acest site funcționează cu licență Atribuire Creative Commons 3.0 Drepturi rezervate"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ro.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ro. Its API lists 780 posts (newest 2026-10-26); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ru) (`globalvoices_ru`)

News, INTL, ru. Home: <https://ru.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.ru>); "Сайт имеет лицензию Creative Commons Атрибуция 3.0 Некоторые права защищены"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ru.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.ru. Its API lists 9573 posts (newest 2026-11-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (sat) (`globalvoices_sat`)

News, INTL, sat. Home: <https://sat.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "ᱱᱚᱣᱟ ᱥᱟᱭᱤᱴ ᱠᱨᱤᱭᱮᱴᱤᱵᱷ ᱠᱳᱢᱳᱱᱥ ᱟᱴᱨᱤᱵᱩᱥᱚᱱ ᱓ᱹ᱐ ᱞᱮᱠᱟᱛᱮ ᱞᱟᱭᱥᱮᱱᱥ ᱟᱠᱟᱱᱟ ᱛᱤᱱᱟᱹᱝ ᱟᱹᱭᱫᱟᱹᱨ ᱨᱟᱠᱷᱟ ᱜᱮᱭᱟ"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `statement_unread`. The footer statement is in Santali (Ol Chiki script), which this project could not read with confidence; its link names CC BY 3.0. Does the statement grant CC BY 3.0 as the link says?
- **Notes:** A Lingua edition of Global Voices at https://sat.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 19 posts (newest 2026-09-12); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (sq) (`globalvoices_sq`)

News, INTL, sq. Home: <https://sq.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Kjo faqe është licensuar si Creative Commons Attribution 3.0 Disa të Drejta të Rezervuara"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://sq.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 889 posts (newest 2025-01-23); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (sr) (`globalvoices_sr`)

News, INTL, sr. Home: <https://sr.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Ова страница је лиценцирана под Нека права задржана"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://sr.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. (gloss) 'This page is licensed under' with no license named in its words; the link names CC BY 3.0. Its API lists 1947 posts (newest 2026-11-15); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (sv) (`globalvoices_sv`)

News, INTL, sv. Home: <https://sv.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.sv>); "Den här sidan är licenserad under Creative Commons Erkännande 3.0 En del rättigheter har reserverats"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://sv.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.sv. Its API lists 364 posts (newest 2020-06-12); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (sw) (`globalvoices_sw`)

News, INTL, sw. Home: <https://sw.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Tovuti hii ina leseni ya Haki Miliki ya Creative Commons 3.0 Haki Kadhaa Zimehifadhiwa"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://sw.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 1748 posts (newest 2022-10-14); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (tet) (`globalvoices_tet`)

News, INTL, tet. Home: <https://tet.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "This site is licensed as Creative Commons Attribution 3.0 Some Rights Reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://tet.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 15 posts (newest 2017-03-01); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (tr) (`globalvoices_tr`)

News, INTL, tr. Home: <https://tr.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.tr>); "Bu site Creative Commons Attribution 3.0 ile lisanslıdır. Bazı hakları saklıdır"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://tr.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.tr. Its API lists 282 posts (newest 2021-04-18); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (uk) (`globalvoices_uk`)

News, INTL, uk. Home: <https://uk.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.uk>); "Сайт має ліцензію Зазначення Авторства 3.0 Деякі права захищені"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://uk.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.uk. Its API lists 1394 posts (newest 2026-09-28); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (ur) (`globalvoices_ur`)

News, INTL, ur. Home: <https://ur.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "کے تحت لائسنسڈ ہے کرئیٹو کامنس ایٹریبیوشنز 3.0یہ سائٹ کچھ حقوق محفوظ ہیں"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://ur.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 196 posts (newest 2023-05-20); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (uz) (`globalvoices_uz`)

News, INTL, uz. Home: <https://uz.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Сайт Creative Commons Attribution 3.0 томонидан лицензиялаштирилган Баъзи ҳуқуқлар ҳимоя қилинган"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://uz.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 11 posts (newest 2021-02-17); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (yo) (`globalvoices_yo`)

News, INTL, yo. Home: <https://yo.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "Àṣẹ ibùdó yìí jẹ́ %cc_license_link Àwọn Àṣẹ Kan J'ẹ́fipamọ́"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `statement_unread`. The footer shows an unfilled template placeholder (%cc_license_link) where the license should be named, though it links CC BY 3.0. Is the link enough?
- **Notes:** A Lingua edition of Global Voices at https://yo.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/. Its API lists 122 posts (newest 2026-10-31); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (zh-Hans) (`globalvoices_zhs`)

News, INTL, zh-Hans. Home: <https://zhs.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.zh_TW>); "本站以創作共用釋出條款 3.0 授權 保留部分权利"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://zhs.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.zh_TW. Its license link is the zh_TW deed of CC BY 3.0. Its API lists 5645 posts (newest 2024-10-03); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Global Voices (zh-Hant) (`globalvoices_zht`)

News, INTL, zh-Hant. Home: <https://zht.globalvoices.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/deed.zh_TW>); "本站以創作共用釋出條款 3.0 授權 CC 保留部分權利"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `third_party_unclear`. Points 1 to 3 hold on its own pages (a site-wide CC BY 3.0 statement, read in its own language; robots.txt allows the pages and the API). Its own pages read (home page and one article) do not say how others' material is marked. Does Global Voices' attribution policy ('all content published on Global Voices', 'our sites') cover this edition's third-party marking?
- **Notes:** A Lingua edition of Global Voices at https://zht.globalvoices.org/. Footer license link: https://creativecommons.org/licenses/by/3.0/deed.zh_TW. Its API lists 6234 posts (newest 2026-11-06); Its article page credits the writer and the translator in separate, localized credit sections, and lists the story's other language versions (class translation-language); the markup read does not mark which version is the original.

### Healthbeat (`healthbeat`)

News, US, en. Home: <https://www.healthbeat.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://www.healthbeat.org/pages/republishing/>); "Unless otherwise noted, Healthbeat stories are free to republish through a Creative Commons CC BY-NC-ND 4.0 license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.civicnews.org/tos>)
- **Credit asked:** "Please include this line at the top of the story: “This story was originally published by Healthbeat. Sign up for their public health newsletters at healthbeat.org/newsletters”."
- **Third-party material:** Stories are CC 'unless otherwise noted'; the page does not say how partner or wire stories are noted
- **Status: pending.** Reason code `nc_or_nd`. Healthbeat licenses its stories CC BY-NC-ND 4.0 'unless otherwise noted' and is silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); may an NC-ND source silent on bulk enter the corpus?
- **Notes:** Published by Civic News Company; its Terms of Service (civicnews.org/tos, read as a Chalkbeat page) defer to the republishing policy, are silent on automated access and say the Services are intended for US users only. Per-story republish pages were not read (they hold article text). Not pursued for version 1 (maintainer's decision, 2026-11-13).

### KFF Health News (`kffhealthnews`)

News, US, en, es. Home: <https://kffhealthnews.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://kffhealthnews.org/syndication/>); "We publish under the Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0) license."
- **Bulk or automatic reuse:** allows; "How do I republish all your stories? We have RSS feeds available that can be ingested to your website or intranet."
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "Include a byline with the reporter’s name and KFF Health News."
- **Third-party material:** Items KFF cannot license are labeled 'All Rights Reserved'; only staff-produced stories are CC; NPR-partnership stories carry partner credits
- **Status: pending.** Reason code `nc_or_nd`. KFF Health News licenses its staff stories CC BY-NC-ND 4.0 and its syndication page explicitly offers all stories by RSS (no 'individually' clause, no pixel requirement); may an NC-ND source with explicit bulk permission enter the corpus as an unchanged, noncommercial class?
- **Notes:** Asks republishers to keep the standard tagline and to share traffic and engagement information 'when possible' (no pixel named). No terms of use page was found on kffhealthnews.org. The per-story republish pages were not read (they hold article text). Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Liberty TV Radio (`libertytvradio`)

News, NG, en. Home: <https://libertytvradio.com/>. Checked on 2026-11-16.

- **License:** CC BY-SA 4.0 (<https://libertytvradio.com/forex-will-go-into-real-development-with-adequate-local-fuel-supply-president-tinubu/>); "This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `conflicting_statements`. An article page's sidebar says 'This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License', while every footer says '© 2025 Liberty TV/Radio. All Rights Reserved.' and the home page names no license: which statement governs, and how would wire stories be told apart?
- **Notes:** the CC BY-SA 4.0 line is a sidebar widget on article pages only; robots.txt disallows wp-json; no terms page found Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### Maryland Matters (`marylandmatters`)

News, US, en. Home: <https://marylandmatters.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://marylandmatters.org/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Maryland Matters credit, including https://marylandmatters.org and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Maryland Matters's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page; part of States Newsroom (its pages say so); it asks, but does not require, a States Newsroom footer on republished articles Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Meduza (English) (`meduza_en`)

News, LV, en. Home: <https://meduza.io/en>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://meduza.io/en/pages/about>); "Meduza regularly releases its content under a Creative Commons CC BY license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "This means you can republish these select materials without prior approval from Meduza‘s newsroom, though you must identify the author (s) and source."
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Meduza says all its materials belong to it and may not be republished without approval, except 'select materials' it releases under CC BY; an article page read on 2026-11-16 carries a 'Creative Commons CC BY' link, so the select materials seem to be marked page by page: should the corpus take only the pages that carry that mark?
- **Notes:** Based in Riga (SIA 'Medusa Project'); the about page says its English stories are translated with an AI model and reviewed by an editor (relevant to provenance); the license excludes photographs; no terms of use page found (only Google reCAPTCHA terms) Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Mekong Eye (`mekongeye`)

News, INTL, en. Home: <https://www.mekongeye.com/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. The home page answered 403 to our client again on 2026-11-16: can the maintainer read https://www.mekongeye.com/about and the 2024 contributor guide in a browser to find the license (search results say stories are under Creative Commons and may be republished 24 hours after publication)?
- **Notes:** robots.txt (200) allows our user agent, but pages answer 403; nothing saved; search results name Internews' Earth Journalism Network as its backer Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Minority Africa (`minorityafrica`)

News, INTL, en. Home: <https://minorityafrica.org/>. Checked on 2026-11-16.

- **License:** no license named (<https://minorityafrica.org/about/>); "Our stories are published under a Creative Commons License. To republish our stories for free, go here."
- **Bulk or automatic reuse:** silent; "Currently, media organizations can republish our content for free within the Advance framework."
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `no_license`. The About page says stories are under 'a Creative Commons License' without naming it and sends republishers to the Advance framework (a pilot with select media organizations since June 2022): which license applies, and may stories be collected outside Advance?
- **Notes:** advance.minorityafrica.org is a script-only page with no readable text; the home and About pages carry an injected block of unrelated SEO links (AI tools, boat plans), so the site may be compromised; search results show one Advance story under CC BY-NC-ND Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### Mississippi Today (`mississippitoday`)

News, US, en. Home: <https://mississippitoday.org/>. Checked on 2026-11-13.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** AP stories carry 'Associated Press' bylines (home page)
- **Status: pending.** Reason code `refused_requests`. mississippitoday.org answered 403 for its terms of service and its republication page (https://mississippitoday.org/about/republication/); could the maintainer read both in a browser and confirm the license and the bulk and tracking terms (search results summarize 'select stories individually, not as a collection', CC BY-ND 4.0 and a tracking code, which would make it exclude)?
- **Notes:** robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider). The home page was read (200); a topic page, the terms of service and the republication page answered 403. Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Mongabay (`mongabay`)

News, US, en. Home: <https://news.mongabay.com/>. Checked on 2026-11-13.

- **License:** CC BY-ND 4.0 (<https://news.mongabay.com/copyright/creative-commons/>); "Mongabay articles are licensed under a Creative Commons Attribution-NoDerivatives 4.0 International License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://news.mongabay.com/terms/>)
- **Credit asked:** "You must credit the author as listed on the original article (ideally in the byline), and Mongabay as the source, and also provide a link back to the specific web address of the article on Mongabay’s website (not the Mongabay homepage)."
- **Third-party material:** Articles under Creative Commons carry a CC badge at the top right of the page (copyright FAQ); third-party images are credited in captions
- **Status: pending.** Reason code `nc_or_nd`. Mongabay's guidelines page says its articles are CC BY-ND 4.0, but its copyright FAQ says only 'many' articles are, marked by a badge, and the terms reserve everything else; with bulk use not addressed, is a NoDerivatives license acceptable, and should we take only badged articles?
- **Notes:** The terms say content is all rights reserved 'unless otherwise stated (e.g. under the published under license near the top of a page or article)'; the FAQ asks for permission for 'extended' use of full articles not covered by an article's terms; translations need permission; the CC links seen on saved pages are image credits only Not pursued for version 1 (maintainer's decision, 2026-11-13).

### NASA News (`nasa`)

Official, US, en. Home: <https://www.nasa.gov/news/>. Checked on 2026-11-16.

- **License:** Public domain (<https://www.nasa.gov/nasa-brand-center/images-and-media/>); "NASA content – images, audio, video, and media files used in the rendition of 3-dimensional models, such as texture maps and polygon data in any format – generally are not subject to copyright in the United States."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.nasa.gov/privacy/>)
- **Credit asked:** "NASA should be acknowledged as the source of the material."
- **Third-party material:** News releases are written by NASA; third-party copyrighted material is marked with the holder's name (media usage page)
- **Status: pending.** Reason code `partial_license`. NASA's media usage page says images, audio, video and media files are generally not under US copyright and lets news outlets use 'NASA content' without permission, but never names text: may we treat NASA news-release text as a US government work in the public domain on that basis?
- **Notes:** An official US government source; the media page also rules on AI ('SI') use: outputs may not be attributed to NASA and use for training implies no endorsement; the important-notices link now redirects to the privacy policy, which bars only unauthorized attempts to upload or change information Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### New Canadian Media (`newcanadianmedia`)

News, CA, en. Home: <https://www.newcanadianmedia.ca/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. robots.txt answered 403 again on 2026-11-16, so our client read no page: can the maintainer read https://www.newcanadianmedia.ca/ in a browser, and is the outlet still publishing (search results show a page saying New Canadian Media, Inc. was dissolved as of Nov. 20, 2024)?
- **Notes:** robots.txt answered 403 (robots.csv state blocked, home_allowed no), so the client treated every page as disallowed; search results suggest older stories carried a Creative Commons notice; the outlet appears to have stopped publishing Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Ohio Capital Journal (States Newsroom) (`ohiocapitaljournal`)

News, US, en. Home: <https://ohiocapitaljournal.com/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://ohiocapitaljournal.com/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Ohio Capital Journal credit, including https://ohiocapitaljournal.com and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Ohio Capital Journal's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page; a saved partner story from The 19th sits outside /repub/, so the byline and the 'originally reported by' line, not the URL alone, must be used to drop partner copy Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Oxpeckers (`oxpeckers`)

News, ZA, en. Home: <https://oxpeckers.org/>. Checked on 2026-11-16.

- **License:** CC BY-SA 4.0 (<https://oxpeckers.org/>); "Content on this site, made by the Oxpeckers Center for Investigative Environmental Journalism, is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** the license covers content 'made by the Oxpeckers Center'; investigations end with a note naming the Oxpeckers author and programme; partner pieces' marking not stated
- **Status: pending.** Reason code `third_party_unclear`. No terms-of-use page was found, and the footer licenses only content 'made by the Oxpeckers Center' without saying how partners' pieces are marked: may Oxpeckers be included, and is the end note naming the Oxpeckers author enough to tell its own articles apart?
- **Notes:** the license is stated only in the footer; its link goes through a google.com redirect to the CC BY-SA 4.0 deed; reportage is also published through media partners (About page) Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### Pakistan Forward (`pakistanforward`)

State-agency, PK, en. Home: <https://pakistan.asia-news.com/en_GB/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `site_unavailable`. The home and About pages show only 'This website is no longer available' on 2026-11-16, so there is no license or terms to read: drop it, or keep it pending in case it returns?
- **Notes:** Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag it Public Domain, with the same statement as Caravanserai and Salaam Times, on the same platform (kind state-agency, as Salaam Times).

### PanARMENIAN.Net (`panarmenian`)

News, AM, en, hy, ru. Home: <https://www.pan.am/en/>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://www.pan.am/en/terms>); "The content of PAN.am (PanARMENIAN.Net) is licensed under the Creative Commons Attribution 4.0 license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt none; terms silent (<https://www.pan.am/en/terms>)
- **Credit asked:** "Credit for any use of PAN.am (PanARMENIAN.Net) material should be given to PAN.am, PanARMENIAN.Net, PanARMENIAN Network, or PAN Photo accordingly"
- **Third-party material:** not stated
- **Status: pending.** Reason code `conflicting_statements`. The terms license the content under CC BY 4.0 but also say 'This license shall automatically terminate if you violate any of these restrictions, and may be terminated by PAN Media LLC at any time' and ask that material not be abridged or edited, while a CC BY 4.0 grant cannot be revoked: which governs, and how are other agencies' stories marked?
- **Notes:** The old address www.panarmenian.net/eng/news/ redirects to www.pan.am; every page read carries 'Content of this site is licensed under a Creative Commons License' linked to CC BY 4.0; robots.txt redirects to the home page (no robots.txt). Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag its English feed CC BY.

### Project Multatuli (`projectmultatuli`)

News, ID, id, en. Home: <https://projectmultatuli.org/en/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. The home page and the About page answered 403 to our client on 2026-11-16: can the maintainer read https://projectmultatuli.org/en/about/ in a browser for its license line?
- **Notes:** Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag both its feeds CC BY, read through a third-party feed service. robots.txt answered 200 and shuts out several AI crawlers by name, not this client.

### Propastop (`propastop`)

Fact-check, EE, et, en, ru. Home: <https://www.propastop.org/en/>. Checked on 2026-11-16.

- **License:** CC BY-SA 3.0 (<https://www.propastop.org/en/terms-of-use/>); "Texts, images and videos of propastop.org can be mostly used under the Creative Commons licence."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.propastop.org/en/terms-of-use/>)
- **Credit asked:** "References must be made in the form of propastop.org and a direct link must be added to the post."
- **Third-party material:** material not under Creative Commons carries 'a relevant reference'; photos or texts where the author is named need the author's consent
- **Status: pending.** Reason code `partial_license`. The terms say texts 'can be mostly used under the Creative Commons licence' (linked to CC BY-SA 3.0), but also that 'texts where the author has been mentioned by name' need the author's consent and that content 'should not be used for commercial purposes': which articles are under CC BY-SA 3.0, and does the noncommercial wish limit the license?
- **Notes:** the license link points to the Estonian CC BY-SA 3.0 deed; the terms say 'Propastop.org operates non-commercially'; English, Estonian and Russian editions Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### South Dakota News Watch (`sdnewswatch`)

News, US, en. Home: <https://www.sdnewswatch.org/>. Checked on 2026-11-16.

- **License:** CC BY-SA 4.0 (<https://www.sdnewswatch.org/republishing-policy/>); "Our stories and photos are licensed under Creative Commons CC BY-SA 4.0, which means you are free to:"
- **Bulk or automatic reuse:** silent; "No ads: Do not sell ads against our stories, but you may post them on pages with ads."
- **Automated collection:** robots.txt allows; terms silent (<https://www.sdnewswatch.org/best-practices/>)
- **Credit asked:** "Attribution: Credit the full story or elements used (poll result, quote, graphic, photo or other content) to South Dakota News Watch."
- **Third-party material:** AP and partner pieces carry their own bylines or credit lines and the 'News service' label (Best Practices Policies)
- **Status: pending.** Reason code `extra_conditions`. South Dakota News Watch licenses its stories CC BY-SA 4.0 but adds 'Do not sell ads against our stories', a noncommercial-style condition that CC BY-SA itself does not have: does that condition bind a free research corpus whose users may include commercial ones, or should the source wait until News Watch confirms plain CC BY-SA?
- **Notes:** The policy adds 'No ads: Do not sell ads against our stories' to the CC BY-SA terms, although CC BY-SA allows commercial use; worth a line in the dataset card. No separate terms of use page exists that we could find; terms_url is the Best Practices Policies page (ethics and privacy), silent on automated access. Not pursued for version 1 (maintainer's decision, 2026-11-13). Re-read on 2026-11-16: the quoted words are unchanged.

### Stateline (`stateline`)

News, US, en. Home: <https://stateline.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://stateline.org/republishing-guidelines/>); "Our stories may be republished online or in print under Creative Commons license CC BY-NC-ND 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must give Stateline credit, including https://stateline.org and author."
- **Third-party material:** Stories from other States Newsroom sites (such as Stateline) sit under /repub/ in the URL; partner stories (such as The 19th) name the partner in the byline and carry an 'originally reported by' line; the outlet's /feed/localFeed carries its own republishable stories
- **Status: pending.** Reason code `nc_or_nd`. Stateline's own pages name CC BY-NC-ND 4.0 and are silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); does the States Newsroom RSS page (statesnewsroom.com/rss-feeds/), which invites republishers to ingest each outlet's /feed/localFeed, settle bulk use, and is a NonCommercial-NoDerivatives license acceptable for the corpus?
- **Notes:** States Newsroom outlet; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); footer links only a privacy, ethics, DEIJ and AI policy (no terms of use read); article pages use the 'Republication Tracker Tool' plugin, but the republish code saved here holds no pixel or script, and no page requires one; AP and Getty images may not be republished; the license is stated in the footer of every page; the national desk of States Newsroom; the home page carries a Ford Foundation series marked 'SPONSORED COMMENTARY' ('This is sponsored content'), which is left out Not pursued for version 1 (maintainer's decision, 2026-11-13).

### States Newsroom (`statesnewsroom`)

News, US, en. Home: <https://statesnewsroom.com/>. Checked on 2026-11-13.

- **License:** no license named (<https://statesnewsroom.com/republishing-guidelines/>)
- **Bulk or automatic reuse:** allows; "States Newsroom RSS feeds allow republishers to ingest free daily state-focused reporting directly into their own news platforms, following our republishing guidelines."
- **Automated collection:** robots.txt allows; terms silent (<https://statesnewsroom.com/privacy-policy-2/>)
- **Credit asked:** "You must give credit to the original source – either the specific newsroom, or News From The States, including the web address and author."
- **Third-party material:** Credit goes to 'the original source' newsroom; on the outlet sites, stories from other outlets sit under /repub/ and name the original outlet; the top-stories feed mixes partner stories
- **Status: pending.** Reason code `no_license`. statesnewsroom.com names no license and publishes press releases, not news, while its outlets name CC BY-NC-ND 4.0 and its RSS page invites republishers to ingest each outlet's /feed/localFeed: should this row stay a network umbrella that is not collected, with each outlet judged on CC BY-NC-ND 4.0 plus this feed permission?
- **Notes:** Network of about 40 state outlets; robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); the republishing guidelines bar selling the story, selling ads against it and paywalls (NonCommercial in effect); the state feeds 'contain all republishable stories published by the newsroom, minus stories from our D.C. or National teams'; the privacy policy is the only legal page found and is silent on automated access; no license or terms of use on the network site Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Tasnim News Agency (English) (`tasnim`)

State-agency, IR, en. Home: <https://www.tasnimnews.com/en>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. robots.txt could not be reached again on 2026-11-16 (connection error), so our client read no page: should the maintainer read https://www.tasnimnews.com/en in a browser for its license line, or should the source be dropped?
- **Notes:** state-affiliated news agency; robots.csv: robots_status error, state unreachable, home_allowed no; search results show a CC BY 4.0 line on its photos page (not read) Not pursued for version 1 (maintainer's decision, 2026-11-13).

### The 19th (`the19th`)

News, US, en. Home: <https://19thnews.org/>. Checked on 2026-11-13.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. 19thnews.org served a bot check page (status 200) for its home page and for https://19thnews.org/republishing-guidelines/; could the maintainer read the guidelines in a browser and confirm the license, any 'individually' or anti-scraping clause and any tracking pixel (search results summarize CC BY-NC-ND, a required pixel and a ban on scraping, which would make it exclude)?
- **Notes:** robots.txt itself allows home and feeds; the pages answer a bot check. tracking 'no' only because no page could be read. Terms of service at https://19thnews.org/terms-of-service/ (not fetched: one try per site). Not pursued for version 1 (maintainer's decision, 2026-11-13).

### The Marshall Project (`marshallproject`)

News, US, en. Home: <https://www.themarshallproject.org/>. Checked on 2026-11-13.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. themarshallproject.org answered 403 to its home page and to a story's republication page; could the maintainer read a republication page in a browser and confirm the license and the bulk and pixel terms (search results summarize CC BY-NC-ND, individual stories only and a required tracking pixel, which would make it exclude)?
- **Notes:** robots.txt itself allows home and feeds; the pages answer 403. tracking 'no' only because no page could be read. Not pursued for version 1 (maintainer's decision, 2026-11-13).

### US Department of State press releases (`stategov`)

Official, US, en. Home: <https://www.state.gov/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `refused_requests`. state.gov answered 403 to robots.txt, so its copyright page (https://www.state.gov/copyright-information/) could not be read; could the maintainer read it in a browser and confirm the public-domain statement for press releases and any terms on automated collection?
- **Notes:** An official US government source. robots.txt answered 403, so every page is refused by the client; nothing was saved. Not pursued for version 1 (maintainer's decision, 2026-11-13). robots.txt answered 403 again on 2026-11-16.

### Votebeat (`votebeat`)

News, US, en. Home: <https://www.votebeat.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://www.votebeat.org/pages/republishing/>); "Unless otherwise noted, Votebeat stories are free to republish through a Creative Commons CC BY-NC-ND 4.0 license."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://www.civicnews.org/tos>)
- **Credit asked:** "Please include this line at the top of the story: “This article was originally published by Votebeat, a nonprofit news organization covering local election administration and voting access.”"
- **Third-party material:** Stories are CC 'unless otherwise noted'; the page does not say how partner or wire stories are noted
- **Status: pending.** Reason code `nc_or_nd`. Votebeat licenses its stories CC BY-NC-ND 4.0 'unless otherwise noted' and is silent on bulk or automatic republishing (no 'individually' clause, no pixel requirement); may an NC-ND source silent on bulk enter the corpus?
- **Notes:** Published by Civic News Company; its Terms of Service (civicnews.org/tos, read as a Chalkbeat page) defer to the republishing policy, are silent on automated access and say the Services are intended for US users only. Per-story republish pages were not read (they hold article text). Not pursued for version 1 (maintainer's decision, 2026-11-13).

### Wikinews (ar) (`wikinews_ar`)

News, INTL, ar. Home: <https://ar.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/deed.ar>); "المحتوى متاح وفق CC BY-SA 4.0 ما لم يرد خلاف ذلك."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 10,452,306 bytes compressed. Copyright page read: yes.

### Wikinews (bs) (`wikinews_bs`)

News, INTL, bs. Home: <https://bs.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Sadržaj je dostupan pod licencom Creative Commons Attribution 4.0 osim ako nije drugačije navedeno."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 635,167 bytes compressed. Copyright page read: not found.

### Wikinews (ca) (`wikinews_ca`)

News, INTL, ca. Home: <https://ca.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "El contingut està disponible sota la llicència Creative Commons Attribution 4.0 si no s'indica el contrari."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 4,563,174 bytes compressed. Copyright page read: yes.

### Wikinews (cs) (`wikinews_cs`)

News, INTL, cs. Home: <https://cs.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Text je dostupný pod Creative Commons Attribution 4.0, pokud není uvedeno jinak."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 5,195,102 bytes compressed. Copyright page read: yes.

### Wikinews (de) (`wikinews_de`)

News, INTL, de. Home: <https://de.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 2.5 (<https://creativecommons.org/licenses/by/2.5/>); "Der Inhalt ist verfügbar unter CC BY 2.5, sofern nicht anders angegeben."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 19,079,364 bytes compressed. Copyright page read: yes.

### Wikinews (el) (`wikinews_el`)

News, INTL, el. Home: <https://el.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Το περιεχόμενο είναι διαθέσιμο υπό Creative Commons Attribution 4.0 εκτός αν αναφέρεται διαφορετικά."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,551,286 bytes compressed. Copyright page read: yes.

### Wikinews (eo) (`wikinews_eo`)

News, INTL, eo. Home: <https://eo.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "La enhavo estas disponebla laŭ Creative Commons Attribution 4.0, se ne estas alia indiko."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,996,421 bytes compressed. Copyright page read: yes.

### Wikinews (es) (`wikinews_es`)

News, INTL, es. Home: <https://es.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "El contenido está disponible bajo la licencia Creative Commons Attribution 4.0, salvo que se indique lo contrario."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 16,753,692 bytes compressed. Copyright page read: yes.

### Wikinews (fa) (`wikinews_fa`)

News, INTL, fa. Home: <https://fa.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/deed.fa>); "محتوا تحت CC BY-SA 4.0 در دسترس است، مگر اینکه خلافش ذکر شده باشد."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,627,858 bytes compressed. Copyright page read: yes.

### Wikinews (fi) (`wikinews_fi`)

News, INTL, fi. Home: <https://fi.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Sisältö on käytettävissä lisenssillä Creative Commons Attribution 4.0, ellei toisin mainita."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,163,297 bytes compressed. Copyright page read: yes.

### Wikinews (fr) (`wikinews_fr`)

News, INTL, fr. Home: <https://fr.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/deed.fr>); "Le contenu est disponible sous licence CC BY-SA 4.0 sauf mention contraire."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 25,346,880 bytes compressed. Copyright page read: yes.

### Wikinews (guw) (`wikinews_guw`)

News, INTL, guw. Home: <https://guw.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Nuhe tin tofi lẹpo tin to Creative Commons Attribution 4.0 glọ adavo eyin mí dọdọ e ma yinmọ."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 490,554 bytes compressed. Copyright page read: not found.

### Wikinews (he) (`wikinews_he`)

News, INTL, he. Home: <https://he.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "התוכן זמין לפי תנאי Creative Commons Attribution 4.0 אלא אם כן נאמר אחרת."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,088,852 bytes compressed. Copyright page read: yes.

### Wikinews (hu) (`wikinews_hu`)

News, INTL, hu. Home: <https://hu.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>); "A lap szövege CC BY 3.0 alatt érhető el, ha nincs külön jelölve."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,286,251 bytes compressed. Copyright page read: not found.

### Wikinews (it) (`wikinews_it`)

News, INTL, it. Home: <https://it.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Il contenuto è disponibile in base alla licenza Creative Commons Attribution 4.0, se non diversamente specificato."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 15,211,477 bytes compressed. Copyright page read: yes.

### Wikinews (ja) (`wikinews_ja`)

News, INTL, ja. Home: <https://ja.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "コンテンツは、特に記載されていない限り、Creative Commons Attribution 4.0のもとで利用可能です。"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 10,082,447 bytes compressed. Copyright page read: yes.

### Wikinews (ko) (`wikinews_ko`)

News, INTL, ko. Home: <https://ko.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "별도로 명시하지 않은 경우, 내용은 Creative Commons Attribution 4.0에 따라 사용할 수 있습니다."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,346,418 bytes compressed. Copyright page read: yes.

### Wikinews (li) (`wikinews_li`)

News, INTL, li. Home: <https://li.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "De inhawd is besjikbaar ónger de Creative Commons Attribution 4.0 behauve is angers aangegeve."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,783,033 bytes compressed. Copyright page read: not found.

### Wikinews (nl) (`wikinews_nl`)

News, INTL, nl. Home: <https://nl.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "De inhoud is beschikbaar onder de licentie Creative Commons Attribution 4.0 tenzij anders aangegeven."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 7,118,433 bytes compressed. Copyright page read: yes.

### Wikinews (no) (`wikinews_no`)

News, INTL, no. Home: <https://no.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Innholdet er tilgjengelig under Creative Commons Attribution 4.0 hvis ikke annet er angitt."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 871,166 bytes compressed. Copyright page read: yes.

### Wikinews (pl) (`wikinews_pl`)

News, INTL, pl. Home: <https://pl.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Treść udostępniana na licencji Creative Commons Attribution 4.0, o ile nie podano inaczej."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 21,981,516 bytes compressed. Copyright page read: yes.

### Wikinews (pt) (`wikinews_pt`)

News, INTL, pt. Home: <https://pt.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Conteúdo disponibilizado nos termos da Creative Commons Attribution 4.0, salvo indicação em contrário."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 33,765,093 bytes compressed. Copyright page read: yes.

### Wikinews (ro) (`wikinews_ro`)

News, INTL, ro. Home: <https://ro.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Conținutul este disponibil sub Creative Commons Attribution 4.0, exceptând cazurile în care se specifică altfel."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,880,019 bytes compressed. Copyright page read: yes.

### Wikinews (ru) (`wikinews_ru`)

News, INTL, ru. Home: <https://ru.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Если не указано иное, содержание доступно по лицензии Creative Commons Attribution 4.0."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,129,517,443 bytes compressed. Copyright page read: yes.

### Wikinews (shn) (`wikinews_shn`)

News, INTL, shn. Home: <https://shn.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "ၸိူဝ်းၶဝ်ႈပႃးဝႆႉၼႆႉ မၼ်းတေၸၢင်ႈၸႂ်ႉလႆႈ ၵႃႈတီႈ မ်ႂ Creative Commons Attribution 4.0"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,087,465 bytes compressed. Copyright page read: yes.

### Wikinews (sq) (`wikinews_sq`)

News, INTL, sq. Home: <https://sq.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Përmbajtja ofrohet nën Creative Commons Attribution 4.0 përveç nëse shënohet ndryshe."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 789,986 bytes compressed. Copyright page read: not found.

### Wikinews (sr) (`wikinews_sr`)

News, INTL, sr. Home: <https://sr.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Садржај је доступан под лиценцом Creative Commons Attribution 4.0 осим ако је другачије наведено."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 26,228,074 bytes compressed. Copyright page read: not found.

### Wikinews (sv) (`wikinews_sv`)

News, INTL, sv. Home: <https://sv.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/deed.sv>); "Innehållet är tillgängligt under CC BY-SA 4.0 om ingenting annat anges."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 2,299,927 bytes compressed. Copyright page read: yes.

### Wikinews (ta) (`wikinews_ta`)

News, INTL, ta. Home: <https://ta.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "வேறுவகையாகக் குறிப்பிடப்பட்டிருந்தாலன்றி இவ்வுள்ளடக்கம் Creative Commons Attribution 4.0 இல் கீழ் கிடைக்கும்."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 3,452,817 bytes compressed. Copyright page read: yes.

### Wikinews (tr) (`wikinews_tr`)

News, INTL, tr. Home: <https://tr.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Aksi belirtilmedikçe içerik Creative Commons Attribution 4.0 lisansı altında kullanılabilir."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 1,838,514 bytes compressed. Copyright page read: yes.

### Wikinews (uk) (`wikinews_uk`)

News, INTL, uk. Home: <https://uk.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "Вміст доступний на умовах Creative Commons Attribution 4.0, якщо не вказано інше."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 3,383,767 bytes compressed. Copyright page read: not found.

### Wikinews (zh) (`wikinews_zh`)

News, INTL, zh. Home: <https://zh.wikinews.org/>. Checked on 2026-11-17.

- **License:** CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>); "除非另有声明,本网站内容采用Creative Commons Attribution 4.0授权。"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `partial_license`. Its footer names today's license (quoted); this edition's copyright page (read where it was found) dates its licenses, and older articles carry other licenses (or none: public domain). Which license applies to each date in this edition?
- **Notes:** An edition of Wikinews, closed: 'The Wikimedia Foundation's Board of Trustees has decided to close all Wikinews projects. From 4 May, Wikinews sites will become read-only' (the English site notice, read 2026-11-17). Its articles come from its dump: latest pages-articles 33,815,460 bytes compressed. Copyright page read: yes.

### ZimFact (`zimfact`)

Fact-check, ZW, en. Home: <https://zimfact.org/>. Checked on 2026-11-16.

- **License:** no license named
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt none; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: pending.** Reason code `site_unavailable`. zimfact.org still shows only a hosting 'Suspended' page on 2026-11-16, so there is no license or terms to read: keep it pending until the site returns, or drop it?
- **Notes:** the home page (226 bytes) says the account is suspended by the host; robots.txt 404; the outlet appears to have stopped publishing at this address Not pursued for version 1 (maintainer's decision, 2026-11-13).

## Excluded

### CalMatters (`calmatters`)

News, US, en, es. Home: <https://calmatters.org/>. Checked on 2026-11-13.

- **License:** no license named (<https://calmatters.org/about/republish/>); "All of the articles at CalMatters are available to republish for free, under the following conditions:"
- **Bulk or automatic reuse:** silent; "If you’d like to regularly republish our stories, we have some other options available."
- **Automated collection:** robots.txt allows; terms forbids (<https://calmatters.org/about/policies-and-standards/>); "You specifically agree not to access (or attempt to access) any of our Resources through any automated, unethical or unconventional means."
- **Credit asked:** "include this copy: “This story was originally published by CalMatters. Sign up for their newsletters.”"
- **Third-party material:** Guest commentary is bylined 'Special for CalMatters'; wire photos (AP, Reuters, iStock) are not free to republish
- **Status: exclude.** Reason code `terms_forbid_automation`. Point 3 fails: CalMatters' terms forbid accessing its resources 'through any automated' means.
- **Notes:** No license is named on the republish page; regular republishing is routed to republish@calmatters.org. The terms also say reproduction or distribution is prohibited unless authorized.

### Common Dreams (`commondreams`)

News, US, en. Home: <https://www.commondreams.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 3.0 (<https://www.commondreams.org/opinion/midterms-democracy-in-action>); "Our work is licensed under Creative Commons (CC BY-NC-ND 3.0). Feel free to republish and share widely."
- **Bulk or automatic reuse:** forbids; "You cannot automatically republish all articles; select stories individually."
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "Include the full name of the writer in the byline."
- **Third-party material:** Articles 're-published from other sources' are not licensed; organizations' press releases sit under /newswire/
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: Common Dreams forbids automatically republishing all articles; stories must be selected individually.
- **Notes:** The Republish Our Work page says 'Creative Commons 3.0 license' with no commercial use; the article footer names CC BY-NC-ND 3.0. No terms of use page was found.

### EduCeleb (`educeleb`)

News, NG, en. Home: <https://educeleb.com/>. Checked on 2026-11-16.

- **License:** all rights reserved; "This website and its content are copyrights of EduCeleb.com. All rights reserved."
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (<https://educeleb.com/terms/>)
- **Credit asked:** "Please, link back to the site if you ever need to use any of its content."
- **Third-party material:** not stated
- **Status: exclude.** Reason code `rights_reserved`. The terms reserve all rights and grant only personal, non-commercial use of the site, so no license allows redistributing the full text (point 1).
- **Notes:** the terms say 'You may access the material on the Site only for your own personal, non-commercial use'; no Creative Commons link on any saved page Re-read on 2026-11-16: the quoted words are unchanged.

### Grist (`grist`)

News, US, en. Home: <https://grist.org/>. Checked on 2026-11-13.

- **License:** no license named (<https://grist.org/about/promote/>); "If you’re interested in republishing our stories online or in print, we just have a few requirements."
- **Bulk or automatic reuse:** silent; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "That’s because we ask republishing partners to include a pixel to help us measure the reach of our stories."
- **Third-party material:** not stated
- **Status: exclude.** Reason code `tracker_required`. Point 2 fails: Grist requires republishers to copy the HTML from its republish page, which carries a tracking pixel.
- **Notes:** No license is named; the footer reads 'All rights reserved'. Terms of use at https://grist.org/terms/ were not fetched (the pixel already settles it).

### Inside Climate News (`insideclimatenews`)

News, US, en. Home: <https://insideclimatenews.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 3.0 (<https://insideclimatenews.org/republishing-guidelines/>); "Creative Common License (CC BY-NC-ND 3.0)"
- **Bulk or automatic reuse:** forbids; "Bots. Do not republish our material wholesale, or automatically. You must select stories to be republished individually."; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms silent (<https://insideclimatenews.org/about/privacy-policy/>)
- **Credit asked:** "Allow tracking. A pixel tracker is included in the HTML provided for each article to measure the reach of our stories. Please make sure it’s included when republishing online. Do not remove it."
- **Third-party material:** Material licensed from third parties may not be republished (user agreement); its marking is not described
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: Inside Climate News forbids wholesale or automatic republishing (stories must be selected individually) and requires its tracking pixel.
- **Notes:** Its user agreement (in the privacy policy page) says copyright is owned by ICN and republishing is granted 'upon request on a case by case basis', which differs from the CC BY-NC-ND 3.0 guidelines page.

### Institute for Nonprofit News (`inn`)

Portal, US, en. Home: <https://inn.org/>. Checked on 2026-11-13.

- **License:** all rights reserved
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt blocked; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: exclude.** Reason code `third_party_portal`. Point 1 fails: INN is a portal whose stories belong to its member newsrooms, so it holds no license to their text; the members are assessed one by one, later (ruling of 2026-11-13).
- **Notes:** robots.csv: robots_status 403, state blocked, home and feeds not allowed; the home page was refused before any request (disallowed). A portal, not a newsroom.

### Mehr News Agency (`mehrnews`)

State-agency, IR, en. Home: <https://en.mehrnews.com/>. Checked on 2026-11-16.

- **License:** all rights reserved; "© 2017 Mehr News Agency. All rights reserved"
- **Bulk or automatic reuse:** silent
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Third-party material:** not stated
- **Status: exclude.** Reason code `rights_reserved`. Point 1 fails: the home page and an article page read on 2026-11-16 carry only the footer '© 2017 Mehr News Agency. All rights reserved' and no license; the Creative Commons line Open Newswire quotes is on neither (a page that says so would make it pending).
- **Notes:** Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) list it as CC BY and mark its feed inactive. The kind (a state news agency) is from public descriptions of it, not from a page read.

### Milwaukee Neighborhood News Service (`milwaukeenns`)

News, US, en. Home: <https://milwaukeenns.org/>. Checked on 2026-11-16.

- **License:** CC BY-ND 4.0 (<https://milwaukeenns.org/2026/11/12/5-things-to-know-and-do-the-weekend-of-nov-13/>); "This work is licensed under a Creative Commons Attribution-NoDerivatives 4.0 International License."
- **Bulk or automatic reuse:** forbids; "Don’t extract, store or resell Milwaukee Neighborhood News Service content as a database."
- **Automated collection:** robots.txt allows; terms silent (<https://milwaukeenns.org/user-agreement-and-privacy-policy/>)
- **Credit asked:** "Credit should be given, in this format: “By Ron Smith, Wisconsin Watch”"
- **Third-party material:** not stated
- **Status: exclude.** Reason code `bulk_clause`. The republishing rules on article pages say 'Don't extract, store or resell Milwaukee Neighborhood News Service content as a database', which forbids bulk reuse (point 2).
- **Notes:** the license and rules sit in the 'Republish This Story' box of each article; the box's code carries a republication tracking pixel (no rule says to keep it); the credit example names Wisconsin Watch; the user agreement is silent Re-read on 2026-11-16: the quoted words are unchanged.

### openDemocracy (`opendemocracy`)

News, GB, en, es. Home: <https://www.opendemocracy.net/en/>. Checked on 2026-11-13.

- **License:** CC BY-NC 4.0 (<https://www.opendemocracy.net/en/creative-commons/>); "This article is published under a Creative Commons Attribution-NonCommercial 4.0 International licence."
- **Bulk or automatic reuse:** forbids; "Our general rule is that if you want to republish more than two pieces per month on a regular basis we ask that you contact us."
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "You must, however, give credit to openDemocracy by displaying or printing “This article was originally published on opendemocracy.net” and follow the other terms of the licence."
- **Third-party material:** A licensing note at the bottom of each article page says which terms apply; some articles are under other terms
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: free republishing covers 'any single item', and regular use of more than two pieces a month needs openDemocracy's agreement.
- **Notes:** The license is per article (CC BY-NC 4.0 on most), not site-wide; profit-making republishers must negotiate a fee; the Creative Commons page asks for exact copies; no terms of use page found

### ProPublica (`propublica`)

News, US, en, es. Home: <https://www.propublica.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 3.0 US (<https://www.propublica.org/steal-our-stories>); "Unless otherwise noted, you can republish our articles for free under a Creative Commons license."
- **Bulk or automatic reuse:** forbids; "You can’t republish our material wholesale, or automatically; you need to select stories to be republished individually."; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms silent (no terms of use page found)
- **Credit asked:** "If you’re republishing online, you must link to the URL of this story on propublica.org, include all of the links from our story, including our newsletter sign up language and link, and use our PixelPing tag."
- **Third-party material:** Co-reporting partners are named in the byline; 'unless otherwise noted' marks stories under other terms
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: no wholesale or automatic republishing (stories must be selected individually) and the PixelPing tracking tag is required.
- **Notes:** The guidelines page links CC BY-NC-ND 3.0 US; article republish boxes say 'CC BY-NC-ND 3.0'; propublica.org/legal redirects to the privacy policy, no terms of use read; syndication to third-party platforms is also barred

### SINC (`sinc`)

State-agency, ES, es, en. Home: <https://www.agenciasinc.es/en>. Checked on 2026-11-16.

- **License:** CC BY 4.0 (<https://www.agenciasinc.es/en/About-SINC/CC-License>); "Most of the content of agenciasinc.es is published under the Creative Commons BY 4.0 licence"
- **Bulk or automatic reuse:** forbids; "Use of the content under the Creative Commons BY 4.0 licence, does not, under any circumstances, authorize the exploitation, whether for commercial purposes or otherwise, of SINC content to create publications, in any medium, when they are chiefly made up of content from agenciasinc.es."
- **Automated collection:** robots.txt allows; terms silent (<https://www.agenciasinc.es/Sobre-SINC/Aviso-legal-y-Politica-de-privacidad>)
- **Credit asked:** "Citing SINC as the source in the case of content licensed by SINC."
- **Third-party material:** photographic, graphic or audiovisual material from other sources keeps its own license (CC License page)
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: the license page says CC BY 4.0 does not authorize using SINC content 'to create publications, in any medium, when they are chiefly made up of content from agenciasinc.es'. A filter on this corpus to SINC's rows would make such a publication, and the corpus cannot pass that condition on to its users, so the row stays exclude; the license also covers only 'most' content.
- **Notes:** SINC is run by FECYT, the Spanish Foundation for Science and Technology (its legal notice), so its kind is state-agency; the legal notice names CC BY 3.0 where the license page names 4.0. Open Newswire's English feeds (feeds.csv at commit c4e1d10, 2025-11-11) tag its English feed CC BY.

### The Conversation (US) (`theconversation`)

News, US, en. Home: <https://theconversation.com/us>. Checked on 2026-11-13.

- **License:** CC BY-ND 4.0 (<https://theconversation.com/us/republishing-guidelines>); "We believe in the free flow of information and publish all our work under a Creative Commons — Attribution/No Derivatives license."
- **Bulk or automatic reuse:** forbids; "You can't systematically republish all of our articles."; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms silent (<https://theconversation.com/us/terms-and-conditions>)
- **Credit asked:** "You must use our page view counter when republishing online."
- **Third-party material:** Articles are written by named academic authors; images under commercial licenses are flagged in captions
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: systematic republishing of all articles is forbidden and the 1x1 page view counter is required.
- **Notes:** robots.txt shuts out AI crawlers (CCBot; GPTBot; ClaudeBot; anthropic-ai; Google-Extended; Bytespider); commercial, non-journalism use may carry license fees; the terms and conditions are silent on automated access

### The Solutions Journalism Exchange (`sojoexchange`)

Portal, US, en. Home: <https://sojoexchange.solutionsjournalism.org/>. Checked on 2026-11-16.

- **License:** no license named (<https://sojoexchange.solutionsjournalism.org/the-rules>); "Looking for solutions journalism to republish in your news outlet under a Creative Commons license?"
- **Bulk or automatic reuse:** forbids; "Republication, systematic reproduction, posting in electronic form on servers, or other uses of the Content, except to the extent permissible under fair use principles, requires permission or license from SJN or the third-party copyright holder, as applicable."
- **Automated collection:** robots.txt allows; terms silent (<https://www.solutionsjournalism.org/terms>)
- **Credit asked:** "Republishers must credit the original journalist and news outlet at the top."
- **Third-party material:** every story belongs to another newsroom, credited to its journalist and outlet; the offering newsroom's own rules apply
- **Status: exclude.** Reason code `bulk_clause`. SJN's terms of use, which name sojoexchange.solutionsjournalism.org, require permission for 'systematic reproduction' of site content (point 2), and every Exchange story is another newsroom's work, which is third-party material.
- **Notes:** a portal: no license is named, only 'a Creative Commons license' set by each offering newsroom; the terms' CC BY-NC 4.0 covers only the Learning Lab, The Whole Story and Collections; search results show a story page asking republishers to keep a tracking pixel (not read) Re-read on 2026-11-16: the quoted words are unchanged.

### The Texas Tribune (`texastribune`)

News, US, en. Home: <https://www.texastribune.org/>. Checked on 2026-11-13.

- **License:** no license named (<https://www.texastribune.org/republishing-guidelines/>); "That’s why you’re welcome to republish our articles and graphics for free using the following ground rules."
- **Bulk or automatic reuse:** silent; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms forbids (<https://www.texastribune.org/terms-of-service/>); "any automated use of the system, such as using scripts to add friends or send comments or messages"
- **Credit asked:** "11. Articles include a pixel to help us measure the reach and understand the impact of our stories."
- **Third-party material:** Stories by third-party partner newsrooms are not available for republishing; their marking is not described
- **Status: exclude.** Reason code `tracker_required`. Point 2 fails: republished Texas Tribune articles include its tracking pixel; point 3 also fails: its terms prohibit 'any automated use of the system'.
- **Notes:** No license is named; the terms grant only a revocable, non-sublicensable license to reproduce and display. The automation clause's examples are about social features, but its wording is general.

### Truthout (`truthout`)

News, US, en. Home: <https://truthout.org/>. Checked on 2026-11-13.

- **License:** CC BY-NC-ND 4.0 (<https://truthout.org/republish-our-work/>); "This article is licensed under Creative Commons (CC BY-NC-ND 4.0), and you are free to share and republish under the terms of the license."
- **Bulk or automatic reuse:** forbids; "You can’t republish all of our content automatically; you must select stories to be republished individually."
- **Automated collection:** robots.txt allows; terms forbids (<https://truthout.org/republish-our-work/>); "Do not scrape our site or repurpose our stories for SEO, ad revenue, or AI training."
- **Credit asked:** "Stories must credit Truthout and any co-reporting partners."
- **Third-party material:** Only 'select original articles' carry the CC BY-NC-ND 4.0 notice at the end
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: Truthout forbids republishing all its content automatically; point 3 fails: it forbids scraping its site.
- **Notes:** robots.txt sets crawl-delay 10. No separate terms of use page was found; the scraping ban is on the Republish Our Work page, which also forbids AI training use.

### Undark (`undark`)

News, US, en. Home: <https://undark.org/>. Checked on 2026-11-13.

- **License:** no license named (<https://undark.org/republishing-guidelines/>); "If you are interested in republishing an original story, photograph, or other material that first appeared at Undark within the last 90 days, feel free to do so, assuming your usage meets the rest of our criteria below."
- **Bulk or automatic reuse:** forbids; "You are not permitted to republish all of our articles; you need to select stories to be republished individually."; a tracking pixel or counter is required
- **Automated collection:** robots.txt allows; terms silent (<https://undark.org/terms/>)
- **Credit asked:** "If you are republishing online, we ask that you include our page view counter — a single pixel and short snippet of HTML that lets us know how much traffic our story has received."
- **Third-party material:** Only stories with a 'Republish' link are original to Undark and available
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: Undark forbids republishing all its articles (stories must be selected individually) and asks for its page view counter pixel.
- **Notes:** Free republishing covers only material first published within the last 90 days; older pieces need the author's permission. No license is named.

### Voice of America (`voa`)

State-agency, US, en. Home: <https://www.voanews.com/>. Checked on 2026-11-16.

- **License:** Public domain (<https://www.voanews.com/p/5338.html>); "All text, audio and video material produced exclusively by the Voice of America is in the public domain."
- **Bulk or automatic reuse:** forbids; "VOA does not grant U.S. domestic media permission for the blanket, standing or recurring use of original VOA content."
- **Automated collection:** robots.txt allows; terms silent (<https://www.voanews.com/p/5338.html>)
- **Credit asked:** "Credit for any use of VOA material should be given to voanews.com, Voice of America, or VOA."
- **Third-party material:** AFP, AP and Reuters copy (named in the copyright statement as licensed, not public domain) is identified by agency byline or credit and left out
- **Status: exclude.** Reason code `bulk_clause`. Point 2 fails: VOA's usage-requests page refuses U.S. domestic media blanket, standing or recurring use and asks for a request for each piece.
- **Notes:** An official US government (USAGM) source whose own text is public domain; the refusal sits on insidevoa.com/p/5719.html, ties itself to the ban on propagandizing in the US, and addresses 'U.S. domestic media', so the maintainer may judge whether it binds a research corpus; the saved home page shows only a short 'Top Stories' list from a few language services (Kurdish, Ukrainian, Russian, Korean, Mandarin, Pashto), no English news sections and no visible dates (page metadata: last modified 2026-11-13), so English publishing looks sharply reduced Re-read on 2026-11-16: the quoted words are unchanged.

## Pages that refused scripted requests

These pages answered 401 or 403, showed a bot check, or are closed to the CommonsWire
user agent by robots.txt. They were not fetched any other way; they need to be read
by a person.

| Source | Page | Answer |
|---|---|---|
| theconversation | <https://cdn.theconversation.com/static_files/files/4357/Global_Editorial_Guidelines.pdf> | robots.txt disallows the CommonsWire user agent |
| dodnews | <https://www.defense.gov/News/> | robots.txt answered HTTP 403 |
| stategov | <https://www.state.gov/> | robots.txt answered HTTP 403 |
| stategov | <https://www.state.gov/copyright-information/> | robots.txt answered HTTP 403 |
| the19th | <https://19thnews.org/> | a bot check page |
| mississippitoday | <https://mississippitoday.org/topic/mississippi-midterms/> | HTTP 403 |
| mississippitoday | <https://mississippitoday.org/terms-of-service/> | HTTP 403 |
| marshallproject | <https://www.themarshallproject.org/> | HTTP 403 |
| inn | <https://inn.org/> | robots.txt answered HTTP 403 |
| mekongeye | <https://www.mekongeye.com/> | HTTP 403 |
| newcanadianmedia | <https://www.newcanadianmedia.ca/> | robots.txt answered HTTP 403 |
| tasnim | <https://www.tasnimnews.com/en> | robots.txt could not be reached |
| mekongeye | <https://www.mekongeye.com/about> | HTTP 403 |
| the19th | <https://19thnews.org/republishing-guidelines/> | a bot check page |
| mississippitoday | <https://mississippitoday.org/about/republication/> | HTTP 403 |
| marshallproject | <https://www.themarshallproject.org/2026/10/16/911-book-policing-mental-health/republication> | HTTP 403 |
| dodnews | <https://www.defense.gov/News/> | robots.txt answered HTTP 403 |
| stategov | <https://www.state.gov/> | robots.txt answered HTTP 403 |
| stategov | <https://www.state.gov/copyright-information/> | robots.txt answered HTTP 403 |
| mekongeye | <https://www.mekongeye.com/> | HTTP 403 |
| newcanadianmedia | <https://www.newcanadianmedia.ca/> | robots.txt answered HTTP 403 |
| tasnim | <https://www.tasnimnews.com/en> | robots.txt could not be reached |
| aljumhuriya | <https://www.aljumhuriya.net/en/> | HTTP 403 |
| projectmultatuli | <https://projectmultatuli.org/en/> | HTTP 403 |
| projectmultatuli | <https://projectmultatuli.org/en/about/> | HTTP 403 |
