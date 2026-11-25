"""How to cite CommonsWire: the one definition the card (series 0.3 on), the Kaggle page and
the citation files follow.

The data set's citation is APA 7, with the version used and the Hugging Face address. The
Zenodo DOI is the code's and the source registry's (no article text), every version, and is
given beside it, never in its place.
"""

from __future__ import annotations

AUTHOR_APA = "Kraishan, O."
FAMILY, GIVEN = "Kraishan", "Obada"
AFFILIATION = "College of Media and Communication, Texas Tech University"
ORCID = "https://orcid.org/0009-0007-7180-8620"
TITLE = "CommonsWire: A full-text corpus of openly licensed news"
PUBLISHER = "Hugging Face"
HF_URL = "https://huggingface.co/datasets/obadakr/commonswire"
KAGGLE_URL = "https://www.kaggle.com/datasets/obadakraishan/commonswire"
REPO = "https://github.com/obadaKraishan/commonswire"
#: The code and the source registry on Zenodo, all versions (it resolves to the latest).
ZENODO_ALL_VERSIONS = "10.5281/zenodo.24231835"
#: The year a version was published, when it is not the year of its data's last day.
YEAR = 2026


def apa(version: str, year: int = YEAR, markdown: bool = True) -> str:
    """The data set's citation (APA 7); the title in italics when ``markdown``."""
    title = f"*{TITLE}*" if markdown else TITLE
    return f"{AUTHOR_APA} ({year}). {title} (Version {version}) [Data set]. {PUBLISHER}. {HF_URL}"


def bibtex(version: str, year: int = YEAR) -> str:
    """The data set's BibTeX entry (``@misc``, which every BibTeX style reads)."""
    fields = [
        ("author", f"{FAMILY}, {GIVEN}"),
        ("title", "{CommonsWire}: A full-text corpus of openly licensed news"),
        ("year", str(year)),
        ("version", version),
        ("publisher", PUBLISHER),
        ("note", "Data set"),
        ("url", HF_URL),
    ]
    width = max(len(k) for k, _ in fields)
    body = ",\n".join(f"  {k.ljust(width)} = {{{v}}}" for k, v in fields)
    return f"@misc{{kraishan{year}commonswire,\n{body}\n}}"


def software_sentence() -> str:
    """The sentence on the code and the source registry on Zenodo (all versions)."""
    return (
        "The code and the source registry that build CommonsWire (no article text) are "
        f"archived on Zenodo: https://doi.org/{ZENODO_ALL_VERSIONS} (all versions; it resolves "
        "to the latest)."
    )


def credit_request() -> str:
    """What the newsrooms ask of anyone who uses their articles."""
    return (
        "Please also credit the newsrooms: keep each article's `credit_line` with any of its "
        "text you share, as its license asks."
    )
