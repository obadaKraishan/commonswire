"""How to cite CommonsWire: one definition, followed by the citation files."""

from __future__ import annotations

import json
from pathlib import Path

from commonswire import citation

ROOT = Path(__file__).resolve().parents[1]


def test_the_apa_citation_and_the_bibtex_entry():
    assert citation.apa("0.3.0") == (
        "Kraishan, O. (2026). *CommonsWire: A full-text corpus of openly licensed news* "
        "(Version 0.3.0) [Data set]. Hugging Face. "
        "https://huggingface.co/datasets/obadakr/commonswire"
    )
    assert "*" not in citation.apa("0.3.0", markdown=False)
    bib = citation.bibtex("0.3.0")
    assert bib.startswith("@misc{kraishan2026commonswire,\n") and bib.endswith("\n}")
    assert "version   = {0.3.0}" in bib and "{CommonsWire}: A full-text" in bib
    assert citation.ZENODO_ALL_VERSIONS in citation.software_sentence()
    assert "no article text" in citation.software_sentence()
    assert "credit_line" in citation.credit_request()


def test_citation_cff_and_zenodo_json_carry_the_orcid_and_the_title():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert cff.count(f'orcid: "{citation.ORCID}"') == 2  # the software and the data set
    preferred = cff[cff.index("preferred-citation:") :]
    assert f'title: "{citation.TITLE}"' in preferred
    assert f"url: \"{citation.HF_URL}\"" in preferred
    zen = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert zen["creators"][0]["orcid"] == citation.ORCID.removeprefix("https://orcid.org/")
    assert f"doi: {citation.ZENODO_ALL_VERSIONS}" in cff
