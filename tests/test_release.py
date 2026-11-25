"""The release build, with invented sources and articles. No network."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone

import pytest

from commonswire import release as rel
from commonswire import release_pack as rel_pack
from commonswire.cli import main
from commonswire.release import ReleaseError, collect, series_sources, verify, write_release
from commonswire.release_pack import (
    KAGGLE_SUBTITLE,
    KAGGLE_TITLE,
    card_body,
    kaggle_folder,
    zenodo_folder,
)
from commonswire.release_text import card, licenses_md
from commonswire.schema import article_id, make_article, text_hash
from commonswire.sources import load_sources, render_credit
from test_sources import row, write_csv

T0 = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
SENTENCE = (
    "The invented council met on an invented Tuesday to discuss an invented budget for the "
    "invented river bridge, and residents asked invented questions about the invented plan. "
)
TEMPLATES = {
    "alpha": (
        "Alpha News",
        "news",
        "CC-BY-4.0",
        "{title}, by {authors}, {source} ({url}), {license}",
    ),
    "beta": (
        "Beta Record",
        "news",
        "CC-BY-SA-4.0",
        "{title}, by {authors}, {source} ({url}), {license}",
    ),
    "gamma": (
        "Gamma Checks",
        "fact-check",
        "public-domain",
        "{title}, {source} ({url}), {license}",
    ),
}


def registry_csv(tmp_path):
    rows = [
        row(
            source_id=s,
            name=n,
            kind=k,
            license=lic,
            credit_line=c,
            homepage=f"https://{s}.example/",
        )
        for s, (n, k, lic, c) in TEMPLATES.items()
    ]
    rows.append(
        row(
            source_id="delta",
            name="Delta",
            status="pending",
            reason_code="extra_conditions",
            reason="Does it allow bulk use?",
        )
    )
    return write_csv(tmp_path, rows)


def article(source, n, text, *, days=0, authors=("Ana Invented",), lic=None, **kw):
    name, _, default, template = TEMPLATES[source]
    url = f"https://{source}.example/story-{n}"
    lic = lic or default
    title = f"Invented story {n}"
    credit = render_credit(
        template,
        title=title,
        authors=authors,
        source=name,
        url=url,
        license=lic,
        translators=kw.get("translators", ()),
    )
    a = make_article(
        source_id=source,
        url=url,
        title=title,
        text=text,
        published_at=T0 + timedelta(days=days),
        retrieved_at=T0 + timedelta(days=70),
        language="en",
        license=lic,
        credit_line=credit,
        authors=authors,
        **kw,
    )
    return json.loads(a.model_dump_json())


def corpus(tmp_path):
    long = SENTENCE * 12
    alpha = [
        article("alpha", 1, long),
        article("alpha", 2, "A short invented note about an invented fair.", days=1),
        article(
            "alpha",
            3,
            "An invented held story.",
            days=2,
            authors=(),
            releasable=False,
            hold_reason="no byline: Alpha News asks for the author's name",
        ),
        article("alpha", 4, "An invented story later removed.", days=3),
        article("alpha", 5, long.replace("Tuesday", "Wednesday"), days=60),
    ]
    alpha[3] = {**alpha[3], "text": "", "content_hash": text_hash(""), "status": "removed"}
    beta = [
        article("beta", 1, long.replace("bridge", "tunnel"), days=5),
        article("beta", 2, "A short invented note about an invented fair.", days=6),  # same text
        article("beta", 3, "An invented changed story.", days=7),
    ]
    beta[2] = {**beta[2], "status": "changed"}
    gamma = [article("gamma", 1, "An invented public record.", days=-3000, authors=())]
    rows_dir = tmp_path / "data" / "interim" / "rows"
    rows_dir.mkdir(parents=True)
    for name, rows in (("alpha", alpha), ("beta", beta), ("gamma", gamma)):
        (rows_dir / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows_dir


@pytest.fixture
def series(monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 9), ("alpha", "beta", "gamma"))


def test_series_sources_by_version():
    assert series_sources("0.1.0") == series_sources("0.1.7")
    assert "globalvoices" not in series_sources("0.1.0")
    assert len(series_sources("0.1.0")) == 6
    with pytest.raises(ReleaseError, match=r"of the form 0\.1\.0"):
        series_sources("0.1")
    with pytest.raises(ReleaseError, match=r"series 0\.9, which has no source list"):
        series_sources("0.9.0")


def test_series_0_2_adds_global_voices_and_the_translators_column():
    assert series_sources("0.2.0") == (*series_sources("0.1.0"), "globalvoices")
    assert len(rel.columns("0.1.3")) == 18 and "translators" not in rel.columns("0.1.3")
    cols = rel.columns("0.2.0")
    assert len(cols) == 19 and cols[cols.index("authors") + 1] == "translators"
    with pytest.raises(ReleaseError, match="of the form"):
        rel.columns("2")


def test_translators_are_released_in_their_column_credited_and_checked(
    tmp_path, series, monkeypatch
):
    rows_dir = corpus(tmp_path)
    tr = article("alpha", 9, "An invented translated note.", days=4, translators=("Tia Invented",))
    with (rows_dir / "alpha.jsonl").open("a") as fh:
        fh.write(json.dumps(tr) + "\n")
    r, out, _ = build(tmp_path)
    got = next(x for x in r.rows["by"] if x["id"] == tr["id"])
    assert got["translators"] == ["Tia Invented"]
    assert "by Ana Invented, translated by Tia Invented, Alpha News" in got["credit_line"]
    assert all(x["translators"] == [] for x in r.rows["by"] if x["id"] != tr["id"])
    assert verify(out) == []
    k = kaggle_folder(out, tmp_path / "k")
    by = {x["path"]: x for x in json.loads((k / "dataset-metadata.json").read_text())["resources"]}
    assert "translators" in [f["name"] for f in by["commonswire-by.parquet"]["schema"]["fields"]]
    # A series without the column refuses a row that names translators, and writes the old
    # 18 columns; verify notices files whose columns are not the version's.
    monkeypatch.setitem(rel.SERIES, (0, 1), ("alpha", "beta", "gamma"))
    registry = load_sources(registry_csv(tmp_path))
    old = collect(tmp_path, "0.1.9", registry)
    assert any("names translators" in x for x in old.checks.invalid)
    (rows_dir / "alpha.jsonl").write_text(
        "".join(line for line in (rows_dir / "alpha.jsonl").open() if tr["id"] not in line)
    )
    old = collect(tmp_path, "0.1.9", registry)
    assert old.checks.ok
    out01 = tmp_path / "v01"
    write_release(old, out01, registry_csv(tmp_path), registry, card="", licenses_md="")
    import pyarrow.parquet as pq

    assert "translators" not in pq.read_schema(out01 / "data/by/train-00000-of-00001.parquet").names
    assert verify(out01) == []
    k01 = kaggle_folder(out01, tmp_path / "k01")
    res = json.loads((k01 / "dataset-metadata.json").read_text())["resources"]
    fields = next(x for x in res if x["path"] == "commonswire-by.parquet")["schema"]["fields"]
    assert len(fields) == 18
    manifest = json.loads((out01 / "manifest.json").read_text())
    manifest["version"] = "9.9.0"
    (out01 / "manifest.json").write_text(json.dumps(manifest))
    assert any("columns are not those of version 9.9.0" in p for p in verify(out01))


def test_collect_dedups_checks_and_groups(tmp_path, series):
    corpus(tmp_path)
    registry = load_sources(registry_csv(tmp_path))
    r = collect(tmp_path, "9.9.0", registry)
    assert r.checks.ok and r.checks.rows_in == 9
    assert dict(r.checks.held) == {"alpha": 1} and dict(r.checks.removed) == {"alpha": 1}
    assert dict(r.checks.exact_duplicates) == {"same_text:beta": 1}  # the later copy goes
    counts = r.counts()
    assert counts["rows_by_configuration"] == {"by": 3, "by-sa": 2, "pd": 1}
    assert counts["rows_by_source"] == {
        "alpha": {"by": 3},
        "beta": {"by-sa": 2},
        "gamma": {"pd": 1},
    }
    by = {x["id"]: x for x in r.rows["by"]}
    near = [x for x in r.rows["by"] + r.rows["by-sa"] if x["near_duplicates"]]
    assert r.near_duplicate_pairs >= 1 and near  # alpha 1 and beta 1 differ by one word
    assert all(x["license_url"].startswith("https://creativecommons.org/") for x in by.values())
    assert r.rows["pd"][0]["license_url"].endswith("/publicdomain/mark/1.0/")
    assert [x["published_at"] for x in r.rows["by"]] == sorted(
        x["published_at"] for x in r.rows["by"]
    )
    assert {x["status"] for x in r.rows["by-sa"]} == {"live", "changed"}


def test_a_copy_of_another_sources_row_is_left_out_and_counted(tmp_path, series, monkeypatch):
    """Series 0.3 on: a row of a source that republished another's (REPUBLISHED_COPIES) whose
    near-duplicate is that other source's row is third-party material: left out, counted, and
    no longer named in its twin's near_duplicates."""
    corpus(tmp_path)
    registry = load_sources(registry_csv(tmp_path))
    before = collect(tmp_path, "9.9.0", registry)
    assert before.near_duplicate_pairs >= 1 and not before.checks.copies
    monkeypatch.setattr(rel, "REPUBLISHED_COPIES", {"beta": "alpha"})
    r = collect(tmp_path, "9.9.0", registry)
    copy_id = article_id("https://beta.example/story-1")
    assert r.checks.ok and dict(r.checks.copies) == {"beta": 1}
    assert r.checks.copy_ids == [copy_id]
    released = {x["id"]: x for c in r.rows.values() for x in c}
    assert copy_id not in released
    assert all(copy_id not in x["near_duplicates"] for x in released.values())
    assert r.near_duplicate_pairs == 0
    out = tmp_path / "out"
    m = write_release(
        r,
        out,
        tmp_path / "sources.csv",
        registry,
        card=card(r, registry, len(r.checks.copy_ids)),
        licenses_md=licenses_md(r, registry),
    )
    assert m["copies_left_out"] == {"beta": 1}
    # An older series keeps its rules and its manifest's keys.
    monkeypatch.setitem(rel.SERIES, (0, 2), ("alpha", "beta", "gamma"))
    old = collect(tmp_path, "0.2.9", registry)
    assert not old.checks.copies and old.near_duplicate_pairs >= 1
    m_old = write_release(
        old,
        tmp_path / "old",
        tmp_path / "sources.csv",
        registry,
        card="x",
        licenses_md="x",
    )
    assert "copies_left_out" not in m_old


def test_two_removed_rows_are_both_counted_as_removed_not_as_duplicates(tmp_path, series):
    rows_dir = corpus(tmp_path)
    gone = article("alpha", 8, "Another invented story later removed.", days=9)
    gone = {**gone, "text": "", "content_hash": text_hash(""), "status": "removed"}
    with (rows_dir / "alpha.jsonl").open("a") as fh:
        fh.write(json.dumps(gone) + "\n")
    (tmp_path / "data" / "takedowns.csv").write_text(
        f"id,requested_on,basis\n{gone['id']},2026-11-16,x\n"
    )
    r = collect(tmp_path, "9.9.0", load_sources(registry_csv(tmp_path)))
    # Both have the empty text's hash; neither is taken for a copy of the other.
    assert dict(r.checks.exact_duplicates) == {"same_text:beta": 1}
    assert dict(r.checks.removed) == {"alpha": 1} and dict(r.checks.taken_down) == {"alpha": 1}
    (tmp_path / "data" / "takedowns.csv").write_text("id,requested_on,basis\n")
    r = collect(tmp_path, "9.9.0", load_sources(registry_csv(tmp_path)))
    assert dict(r.checks.removed) == {"alpha": 2}
    assert dict(r.checks.exact_duplicates) == {"same_text:beta": 1}


def test_collect_refuses_missing_rows_and_unknown_sources(tmp_path, series, monkeypatch):
    registry = load_sources(registry_csv(tmp_path))
    with pytest.raises(ReleaseError, match="no rows for alpha, beta, gamma"):
        collect(tmp_path, "9.9.0", registry)
    corpus(tmp_path)
    monkeypatch.setitem(rel.SERIES, (9, 8), ("alpha", "omega"))
    (tmp_path / "data" / "interim" / "rows" / "omega.jsonl").write_text("")
    with pytest.raises(ReleaseError, match="omega not in the registry"):
        collect(tmp_path, "9.8.0", registry)


def test_checks_catch_bad_credit_third_party_nc_and_invalid_rows(tmp_path, series):
    rows_dir = corpus(tmp_path)
    registry = load_sources(registry_csv(tmp_path))
    good = [json.loads(x) for x in (rows_dir / "alpha.jsonl").read_text().splitlines()]
    good[0]["credit_line"] = "Somebody else"
    good[1]["third_party"] = True
    good[4] = article("alpha", 5, "An invented NC story.", lic="CC-BY-NC-4.0")
    bad_source = dict(good[2], source_id="beta")
    broken = dict(article("alpha", 9, "An invented broken row.", days=9), content_hash="0" * 64)
    lines = [*good, bad_source, broken]
    (rows_dir / "alpha.jsonl").write_text("".join(json.dumps(r) + "\n" for r in lines))
    r = collect(tmp_path, "9.9.0", registry)
    assert not r.checks.ok
    problems = " | ".join(r.checks.problems())
    for word in ("credit mismatch", "third party", "unreleasable class", "invalid"):
        assert word in problems
    with pytest.raises(ReleaseError, match="the checks failed"):
        write_release(
            r, tmp_path / "out", registry_csv(tmp_path), registry, card="", licenses_md=""
        )


def build(tmp_path, out_name="out", version="9.9.0"):
    registry_path = registry_csv(tmp_path)
    registry = load_sources(registry_path)
    r = collect(tmp_path, version, registry)
    out = tmp_path / out_name
    m = write_release(
        r,
        out,
        registry_path,
        registry,
        card=card(r, registry, 4),
        licenses_md=licenses_md(r, registry),
    )
    return r, out, m


def test_the_same_input_gives_the_same_files_and_verify_passes(tmp_path, series):
    corpus(tmp_path)
    _, a, ma = build(tmp_path, "a")
    _, b, mb = build(tmp_path, "b")
    names = sorted(str(p.relative_to(a)) for p in a.rglob("*") if p.is_file())
    assert names == sorted(str(p.relative_to(b)) for p in b.rglob("*") if p.is_file())
    for n in names:
        assert (a / n).read_bytes() == (b / n).read_bytes(), n
    assert ma == mb
    assert "data/by/train-00000-of-00001.parquet" in names and "index.csv" in names
    assert ma["rows"] == 6 and ma["as_of"] == "2026-11-10T08:00:00Z"
    assert ma["held_rows_not_released"] == {"alpha": 1}
    assert ma["removed_rows_not_released"] == {"alpha": 1}
    assert verify(a) == []
    index = (a / "index.csv").read_text().splitlines()
    assert index[0] == "id,source_id,configuration,url,license,content_hash,published_at"
    assert len(index) == 7 and "text" not in index[0]
    assert (a / "sources.csv").read_bytes() == registry_csv(tmp_path).read_bytes()


def test_verify_finds_changed_missing_and_extra_files_and_count_mismatches(tmp_path, series):
    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    report = {
        "sources": {
            "alpha": {"releasable_rows": 4},
            "beta": {"releasable_rows": 2},
            "gamma": {"releasable_rows": 1},
        }
    }
    assert verify(out, report) == []  # alpha: 4 releasable minus 1 removed
    report["sources"]["gamma"]["releasable_rows"] = 5
    assert any("gamma: 1 rows released" in p for p in verify(out, report))
    (out / "LICENSES.md").write_text("changed")
    (out / "stray.txt").write_text("x")
    (out / "index.csv").unlink()
    problems = verify(out)
    assert "LICENSES.md differs from the manifest" in problems
    assert "stray.txt is not in the manifest" in problems
    assert "index.csv is missing" in problems
    reg = (out / "sources.csv").read_text().replace("{title}, {source}", "{title}: {source}")
    (out / "sources.csv").write_text(reg)
    assert any("the credit line is not its source's template" in p for p in verify(out))
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["rows_by_configuration"]["pd"] = 2
    (out / "manifest.json").write_text(json.dumps(manifest))
    assert any(p.startswith("pd: 1 rows in the files, 2") for p in verify(out))


def test_card_and_licenses_say_what_the_release_holds(tmp_path, series, monkeypatch):
    """Series 0.2's card, which its weekly versions keep word for word."""
    monkeypatch.setitem(rel.SERIES, (0, 2), ("alpha", "beta", "gamma"))
    corpus(tmp_path)
    _, out, _ = build(tmp_path, version="0.2.9")
    text = (out / "README.md").read_text()
    assert text.startswith("---\npretty_name: CommonsWire\n")
    assert (
        "license: other\nlicense_name: per-row-open-licenses\nlicense_link: "
        "https://huggingface.co/datasets/obadakr/commonswire/blob/main/LICENSES.md"
    ) in text
    by_config = '- config_name: by\n  data_files:\n  - split: train\n    path: "data/by/*.parquet"'
    assert by_config + "\n  default: true" in text
    assert "# CommonsWire 0.2.9" in text and "6 articles" in text
    assert "| Alpha News | news | CC BY 4.0 | 3 |" in text
    assert "not affiliated with" in text and "issues/new?template=takedown.yml" in text
    assert "1 more rows are held back" in text
    assert "type: ignore" not in text
    for leftover in ("{_n(", "{f[", "{release", "{HF_", "{REPO", "{ISSUE", "{size", "{chr("):
        assert leftover not in text, leftover
    assert "`{title}, by {authors}, {source} ({url}), {license}`" in text
    assert "<https://doi.org/10.5281/zenodo.24231835> (all versions)" in text
    body = card_body(text)
    assert body.startswith("# CommonsWire 0.2.9") and "config_name" not in body
    lic = (out / "LICENSES.md").read_text()
    assert "| `by-sa` | CC BY-SA 4.0 (2) | 2 |" in lic and "not legal advice" in lic


def test_the_card_of_a_later_series_says_what_changed(tmp_path, series, monkeypatch):
    from commonswire import release_text

    rows_dir = corpus(tmp_path)
    tr = article("alpha", 9, "An invented translated note.", days=4, translators=("Tia Invented",))
    with (rows_dir / "alpha.jsonl").open("a") as fh:
        fh.write(json.dumps(tr) + "\n")
    monkeypatch.setitem(rel.SERIES, (0, 1), ("alpha", "beta"))
    monkeypatch.setitem(rel.SERIES, (0, 2), ("alpha", "beta", "gamma"))
    monkeypatch.setitem(release_text.CHANGES_SINCE, (0, 2), "0.1.0")
    monkeypatch.setitem(release_text.SHORT_REASONS, "alpha", "invented short notes")
    _, out, _ = build(tmp_path, version="0.2.9")
    text = (out / "README.md").read_text()
    assert "## Changes since 0.1.0" in text
    assert (
        "- **A new source: Gamma Checks** (1 row, Public domain, 2018 to 2018), fact-check." in text
    )
    assert "- **A new field, `translators`:**" in text and "(1 rows)" not in text
    assert "| `translators` | the translators the source names" in text
    assert "When the source names translators (Alpha News, for 1 row)" in text
    assert "**Near-duplicates across sources:** 2 pairs in this version." in text
    assert "- **Alpha News is most of it** (4 of 7 rows, 57%): results over the whole" in text
    assert "`authors` (1 row); the credit line" in text and "Wikinews text" not in text
    assert "have fewer than 200 characters of text: invented short notes" in text
    assert "Alpha News (news), Beta Record (news), and Gamma Checks\n  (fact-check)" in text
    assert "Fact-checks are" in text and "{" + "fact_words}" not in text
    prose = [x for x in text.splitlines() if not x.startswith("|") and "https://" not in x]
    assert max(len(x) for x in prose) <= 100


def test_the_series_0_3_card_covers_languages_licenses_rules_and_how_to_cite(tmp_path, series):
    """The card of series 0.3 on (commonswire.card03): sections, numbers from the rows, the
    citation first in "How to cite", and no raw HTML."""
    from commonswire import citation
    from commonswire.release import raw_html

    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    text = (out / "README.md").read_text()
    flat = " ".join(text.split())
    heads = [x for x in text.splitlines() if x.startswith("## ")]
    assert heads == [
        "## What it is, and what it is not",
        "## The publishers",
        "## Languages",
        "## Configurations and licenses",
        "## The rights rules of this version",
        "## Fields",
        "## How it was collected",
        "## Removals and corrections",
        "## Limitations",
        "## Contact",
        "## How to cite",
    ]
    assert "in 1 languages" not in flat and "It is English only" not in text
    assert "| `en` | English | 6 |" in text
    assert (
        "| CC BY 4.0 | `CC-BY-4.0` | 3 |" in text and "| Public domain | `public-domain` |" in text
    )
    assert "- **Mirror:** the same files on Kaggle, " + citation.KAGGLE_URL in text
    assert "need a free GitHub account" in flat and "Community tab" in flat
    cite = text[text.index("## How to cite") :]
    order = [
        cite.index(x)
        for x in ("*CommonsWire: A full-text", "@misc{", "10.5281/zenodo", "credit_line")
    ]
    assert order == sorted(order)
    assert citation.apa("9.9.0") in " ".join(cite.split())
    assert raw_html(text) == []
    for leftover in ("{_n(", "{f[", "{release", "{HF_", "{citation", "{chr(", "type: ignore"):
        assert leftover not in text, leftover
    prose = [x for x in text.splitlines() if not x.startswith("|") and "https://" not in x]
    assert max(len(x) for x in prose) <= 100
    lic = (out / "LICENSES.md").read_text()
    assert "**CC BY 4.0** (`by`)" in lic and "CC BY 2.5, 3.0 and 4.0" not in lic
    assert "| `by-sa` | CC BY-SA 4.0 (2) | 2 |" in lic


def test_verify_finds_raw_html_in_a_card(tmp_path, series):
    from commonswire.release import raw_html

    assert raw_html("x <https://a.example> `<b>` y") == []
    assert raw_html("x <br> y <!-- z -->") == ["<br>", "<!--"]
    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    card_file = out / "README.md"
    card_file.write_text(card_file.read_text() + "\n<details>x</details>\n")
    problems = verify(out)
    assert any("raw HTML outside code ('<details>')" in p for p in problems)


def test_kaggle_and_zenodo_folders(tmp_path, series):
    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    k = kaggle_folder(out, tmp_path / "k")
    meta = json.loads((k / "dataset-metadata.json").read_text())
    assert meta["licenses"] == [{"name": "other"}] and meta["id"] == "KAGGLE_USERNAME/commonswire"
    assert 6 <= len(KAGGLE_TITLE) <= 50 and 20 <= len(KAGGLE_SUBTITLE) <= 80
    assert meta["description"].startswith("# CommonsWire")
    names = sorted(p.name for p in k.iterdir())
    assert "commonswire-by.parquet" in names and "manifest.json" in names
    assert {r["path"] for r in meta["resources"]} == set(names) - {
        "dataset-metadata.json",
        "dataset-cover-image.png",
    }
    assert (k / "commonswire-pd.parquet").read_bytes() == (
        out / "data/pd/train-00000-of-00001.parquet"
    ).read_bytes()
    with pytest.raises(FileExistsError, match="not empty"):
        kaggle_folder(out, k)
    assert kaggle_folder(out, k, overwrite=True) == k
    z = zenodo_folder(out, tmp_path / "z", tmp_path)  # tmp_path is no git checkout
    zm = json.loads((z / "zenodo-metadata.json").read_text())["metadata"]
    assert zm["upload_type"] == "dataset" and zm["license"] == "apache-2.0"
    assert "no article text" in zm["title"] and "to be added at deposit" in zm["notes"]
    assert not list(z.glob("*.parquet"))
    assert sorted(p.name for p in z.iterdir()) == [
        "LICENSES.md",
        "README.md",
        "manifest.json",
        "sources.csv",
        "zenodo-metadata.json",
    ]  # no index.csv: a permanent record lists no article


def test_zenodo_folder_archives_the_code_of_a_git_checkout(tmp_path, series):
    import subprocess

    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("print('invented')\n")
    for cmd in (
        ["init", "-q"],
        ["add", "a.py"],
        ["-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-qm", "x"],
    ):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True)
    first = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (repo / "b.py").write_text("print('later')\n")
    for cmd in (
        ["add", "b.py"],
        ["-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-qm", "y"],
    ):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True)
    z = zenodo_folder(out, tmp_path / "z", repo, commit=first[:7])
    import tarfile

    with tarfile.open(z / "commonswire-code-9.9.0.tar.gz") as tar:
        names = tar.getnames()
    assert "commonswire-9.9.0/a.py" in names and "commonswire-9.9.0/b.py" not in names
    meta = json.loads((z / "zenodo-metadata.json").read_text())["metadata"]
    assert meta["notes"].startswith(f"Code commit: {first}.")
    assert meta["related_identifiers"][1]["identifier"].endswith(f"/tree/{first}")
    assert "no list of articles" in meta["description"]
    z2 = zenodo_folder(out, tmp_path / "z2", repo, commit="no-such-commit")
    assert not (z2 / "commonswire-code-9.9.0.tar.gz").exists()
    assert (
        len(
            json.loads((z2 / "zenodo-metadata.json").read_text())["metadata"]["related_identifiers"]
        )
        == 1
    )


def test_cli_release_build_check_kaggle_zenodo(tmp_path, series, capsys):
    corpus(tmp_path)
    reg = str(registry_csv(tmp_path))
    base = ["--root", str(tmp_path), "release"]
    assert main([*base, "check", "--version", "9.9.0"]) == 2
    assert main([*base, "kaggle", "--version", "9.9.0"]) == 2
    assert main([*base, "zenodo", "--version", "9.9.0", "--website"]) == 2
    capsys.readouterr()
    assert main([*base, "build", "--version", "9.9.0", "--sources", reg]) == 0
    out = capsys.readouterr().out
    assert "release 9.9.0: 6 rows (by 3, by-sa 2, pd 1); held back 1, removed 1" in out
    assert "checks: all passed" in out
    assert main([*base, "build", "--version", "9.9.0", "--sources", reg]) == 2
    assert "already exists" in capsys.readouterr().err
    assert main([*base, "build", "--version", "9.9.0", "--sources", reg, "--overwrite"]) == 0
    assert main([*base, "check", "--version", "9.9.0"]) == 0
    assert main([*base, "kaggle", "--version", "9.9.0"]) == 0
    assert main([*base, "zenodo", "--version", "9.9.0", "--website"]) == 0
    out = capsys.readouterr().out
    assert "zenodo-metadata.json and" in out and "This is the fallback" in out
    assert main([*base, "kaggle", "--version", "9.9.0", "--overwrite"]) == 0
    assert main([*base, "zenodo", "--version", "9.9.0", "--website", "--overwrite"]) == 0
    # Without --website: the GitHub route, which needs .zenodo.json and a git checkout.
    capsys.readouterr()
    assert main([*base, "zenodo", "--version", "9.9.0"]) == 1
    out = capsys.readouterr().out
    assert ".zenodo.json is missing" in out and "no git archive of HEAD" in out
    assert main([*base, "build", "--version", "0.9.0", "--sources", reg]) == 2
    # A corpus report that disagrees makes the check fail.
    ev = tmp_path / "data" / "evidence" / "corpus"
    ev.mkdir(parents=True)
    (ev / "report.json").write_text(json.dumps({"sources": {"alpha": {"releasable_rows": 9}}}))
    assert main([*base, "check", "--version", "9.9.0"]) == 1
    # A report older than the rows is not compared (it predates the last daily run).
    import os

    os.utime(ev / "report.json", (1, 1))
    capsys.readouterr()
    assert main([*base, "check", "--version", "9.9.0"]) == 0
    assert "the corpus report is older than the rows" in capsys.readouterr().out
    # Rows that fail the checks stop the build.
    rows = tmp_path / "data" / "interim" / "rows" / "gamma.jsonl"
    rows.write_text(rows.read_text().replace('"credit_line": "', '"credit_line": "X'))
    capsys.readouterr()
    assert main([*base, "build", "--version", "9.9.1", "--sources", reg]) == 1
    assert "check failed: 1 rows credit mismatch" in capsys.readouterr().err


def test_release_check_skips_the_corpus_report_for_a_version_built_by_update(
    tmp_path, series, capsys
):
    corpus(tmp_path)
    reg = str(registry_csv(tmp_path))
    base = ["--root", str(tmp_path), "release"]
    assert main([*base, "build", "--version", "9.9.0", "--sources", reg]) == 0
    ev = tmp_path / "data" / "evidence" / "corpus"
    ev.mkdir(parents=True)
    (ev / "report.json").write_text(json.dumps({"sources": {"alpha": {"releasable_rows": 9}}}))
    # A locally built version (no update block) is compared with the report, and fails.
    capsys.readouterr()
    assert main([*base, "check", "--version", "9.9.0"]) == 1
    out = capsys.readouterr().out
    assert "rows released, but the corpus report has" in out
    assert "was built by commonswire update" not in out
    # The same files with an update block in the manifest: the comparison is skipped.
    manifest = tmp_path / "data" / "release" / "9.9.0" / "manifest.json"
    data = json.loads(manifest.read_text())
    data["update"] = {"from_version": "9.8.0", "new": 1}
    manifest.write_text(json.dumps(data))
    assert main([*base, "check", "--version", "9.9.0"]) == 0
    out = capsys.readouterr().out
    assert (
        "note: 9.9.0 was built by commonswire update from 9.8.0, so its rows were not "
        "compared with the local corpus report" in out
    )
    assert "release 9.9.0: all checks passed" in out


def test_the_takedown_list_keeps_articles_out_and_must_be_well_formed(tmp_path, series):
    from commonswire.release import load_takedowns

    corpus(tmp_path)
    registry = load_sources(registry_csv(tmp_path))
    first = collect(tmp_path, "9.9.0", registry)
    gone = first.rows["pd"][0]["id"]
    path = tmp_path / "data" / "takedowns.csv"
    path.write_text(f"id,requested_on,basis\n{gone},2026-11-14,publisher\n")
    assert load_takedowns(path) == {gone}
    r = collect(tmp_path, "9.9.0", registry)
    assert r.rows["pd"] == [] and dict(r.checks.taken_down) == {"gamma": 1}
    out = tmp_path / "out"
    m = write_release(
        r, out, registry_csv(tmp_path), registry, card=card(r, registry, 0), licenses_md=""
    )
    assert m["taken_down_rows_not_released"] == {"gamma": 1}
    report = {
        "sources": {
            "alpha": {"releasable_rows": 4},
            "beta": {"releasable_rows": 2},
            "gamma": {"releasable_rows": 1},
        }
    }
    assert verify(out, report) == []
    path.write_text("id,requested_on,basis\nhttps://gamma.example/story-1,2026-11-14,x\n")
    with pytest.raises(ReleaseError, match="give the id, never the URL"):
        load_takedowns(path)
    path.write_text("url,date\n")
    with pytest.raises(ReleaseError, match="the header must be id,requested_on,basis"):
        load_takedowns(path)
    assert load_takedowns(tmp_path / "none.csv") == set()


def test_kaggle_metadata_describes_files_columns_provenance_and_frequency(tmp_path, series):
    import struct
    import zlib

    from commonswire.release import columns
    from commonswire.release_pack import (
        INDEX_COLUMNS,
        ROW_COLUMNS,
        SOURCE_COLUMNS,
        cover_image,
    )
    from commonswire.sources import SOURCE_FIELDS

    assert [c[0] for c in ROW_COLUMNS] == list(columns("9.9.0"))  # every column, in order
    assert [c[0] for c in SOURCE_COLUMNS] == list(SOURCE_FIELDS)
    assert [c[0] for c in INDEX_COLUMNS][:2] == ["id", "source_id"]
    corpus(tmp_path)
    _, out, m = build(tmp_path)
    k = kaggle_folder(out, tmp_path / "k")
    meta = json.loads((k / "dataset-metadata.json").read_text())
    assert meta["expectedUpdateFrequency"] == "monthly" and meta["isPrivate"] is False
    assert "sources.csv" in meta["userSpecifiedSources"]
    assert (
        "Publishers in version 9.9.0: Alpha News, Beta Record, Gamma Checks."
        in (meta["userSpecifiedSources"])
    )
    assert meta["keywords"] == rel_pack.KAGGLE_TAGS and len(meta["keywords"]) <= 5
    desc = meta["description"]
    heads = [x for x in desc.splitlines() if x.startswith("## ")]
    assert heads[0] == "## How to cite" and "## What is inside" in heads
    cite = desc[desc.index("## How to cite") :].split("\n", 2)[2]
    assert cite.startswith("Kraishan, O. (2026). *CommonsWire: A full-text corpus")
    assert len(desc) <= rel_pack.DESCRIPTION_MAX and "config_name" not in desc
    assert "`commonswire-by.parquet`: Articles under CC BY 4.0, one row each" in desc
    by = {r["path"]: r for r in meta["resources"]}
    fields = by["commonswire-by.parquet"]["schema"]["fields"]
    assert [f["name"] for f in fields] == list(columns("9.9.0"))
    assert all(f["description"] and f["type"] for f in fields)
    assert by["index.csv"]["schema"]["fields"][2]["name"] == "configuration"
    assert len(by["sources.csv"]["schema"]["fields"]) == len(SOURCE_FIELDS)
    assert "schema" not in by["README.md"] and by["README.md"]["description"]
    png = (k / "dataset-cover-image.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (560, 280)  # Kaggle's own cover size
    assert png == cover_image(m["rows_by_configuration"])  # the same input, the same image
    idat = png[png.index(b"IDAT") + 4 : png.index(b"IEND") - 8]
    assert len(zlib.decompress(idat)) == height * (1 + width * 3)
    assert cover_image({"by": 1, "by-sa": 0, "pd": 0}, (40, 20))[:8] == png[:8]


def test_pack_folders_refuse_stale_files(tmp_path, series):
    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    z = tmp_path / "z"
    z.mkdir()
    (z / "index.csv").write_text("an older pack's article list")
    with pytest.raises(
        FileExistsError, match=r"holds files this pack does not write \(index.csv\)"
    ):
        zenodo_folder(out, z, tmp_path, overwrite=True)
    with pytest.raises(FileExistsError, match="not empty"):
        zenodo_folder(out, z, tmp_path)


GOOD_ZENODO = {
    "title": "Invented: code and source registry, no article text",
    "upload_type": "software",
    "description": "<p>Invented <strong>code</strong>, <code>no text</code>.</p>",
    "creators": [{"name": "Invented, Ana", "affiliation": "Invented University"}],
    "license": "Apache-2.0",
    "keywords": ["invented"],
    "related_identifiers": [
        {"identifier": rel_pack.HF_URL, "relation": "isSupplementTo", "scheme": "url"},
        {"identifier": rel_pack.KAGGLE_URL, "relation": "isSupplementTo", "scheme": "url"},
    ],
}
GOOD_CFF = """# a comment
cff-version: 1.2.0
title: "Invented: code and source registry, no article text"
authors:
  - family-names: Invented
    given-names: Ana
    affiliation: "Invented University"
license: Apache-2.0
preferred-citation:
  title: "Another title"
  authors:
    - family-names: Other
"""


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({}, None),
        ({"title": "Invented code"}, "no article text"),
        ({"upload_type": "programme"}, "upload_type"),
        ({"creators": [{"name": "Ana Invented"}]}, "'Family, Given'"),
        ({"description": "<p>a <script>x</script></p>"}, "does not allow: script"),
        ({"related_identifiers": []}, "the Kaggle mirror"),
        (
            {"related_identifiers": [{"identifier": "x", "relation": "isRelatedTo"}]},
            "relation Zenodo does not know",
        ),
        ({"license": "MIT"}, "the license ('mit') differs from CITATION.cff"),
        ({"license": ""}, "license is missing"),
        (
            {"creators": [{**GOOD_ZENODO["creators"][0], "orcid": "0000-0000-0000-0000"}]},
            "the ORCID iD ('0000-0000-0000-0000') differs from CITATION.cff",
        ),
    ],
)
def test_check_zenodo_json(tmp_path, change, message):
    (tmp_path / "CITATION.cff").write_text(GOOD_CFF)
    (tmp_path / ".zenodo.json").write_text(json.dumps({**GOOD_ZENODO, **change}))
    problems = rel_pack.check_zenodo_json(tmp_path)
    if message is None:
        assert problems == []
    else:
        assert any(message in p for p in problems), problems


def test_check_zenodo_json_reads_the_file_and_the_citation(tmp_path):
    assert "is missing" in rel_pack.check_zenodo_json(tmp_path)[0]
    (tmp_path / ".zenodo.json").write_text("{\n  'title': 1\n}")
    assert "line 2: not valid JSON" in rel_pack.check_zenodo_json(tmp_path)[0]
    (tmp_path / ".zenodo.json").write_text("[]")
    assert "one JSON object" in rel_pack.check_zenodo_json(tmp_path)[0]
    (tmp_path / ".zenodo.json").write_text(json.dumps(GOOD_ZENODO))
    assert rel_pack.check_zenodo_json(tmp_path) == []  # no CITATION.cff: nothing to compare
    (tmp_path / "CITATION.cff").write_text(GOOD_CFF.replace("Invented University", "Elsewhere"))
    assert "affiliation" in rel_pack.check_zenodo_json(tmp_path)[0]


def test_the_repositorys_own_zenodo_json_and_citation_agree():
    from commonswire._paths import repo_root

    assert rel_pack.check_zenodo_json(repo_root()) == []


def test_archive_leaves_out_the_request_log_and_needs_zenodo_json(tmp_path):
    import subprocess

    repo = tmp_path / "repo"
    (repo / "data" / "interim").mkdir(parents=True)
    (repo / "a.py").write_text("print('invented')\n")
    (repo / "data" / "usage_log.csv").write_text("time,host\n")
    (repo / "data" / "sources.csv").write_text("source_id\n")
    (repo / ".gitattributes").write_text("data/usage_log.csv export-ignore\n")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.org"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "x"], check=True)
    names = rel_pack.archive_names(repo)
    assert "commonswire/data/sources.csv" in names
    assert "commonswire/data/usage_log.csv" not in names
    assert rel_pack.archive_problems(names) == [
        ".zenodo.json is not in the archive (commit it first)"
    ]
    bad = [
        *names,
        "commonswire/.zenodo.json",
        "commonswire/data/usage_log.csv",
        "commonswire/data/raw/x.json",
    ]
    assert rel_pack.archive_problems(bad) == [
        "commonswire/data/usage_log.csv is in the archive",
        "commonswire/data/raw/x.json is in the archive",
    ]
    (repo / ".zenodo.json").write_text(json.dumps(GOOD_ZENODO))
    subprocess.run([*git, "add", ".zenodo.json"], check=True)
    subprocess.run([*git, "commit", "-qm", "y"], check=True)
    assert main(["--root", str(repo), "release", "zenodo", "--version", "9.9.0"]) == 0


def test_kaggle_lists_the_registry_columns_a_version_has(tmp_path, series):
    from commonswire.release_pack import kaggle_folder
    from commonswire.sources import LEGACY_FIELDS

    corpus(tmp_path)
    _, out, _ = build(tmp_path)
    # A version of series 0.1 or 0.2 ships the registry without reason_code.
    with (out / "sources.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with (out / "sources.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LEGACY_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    meta = json.loads((kaggle_folder(out, tmp_path / "k") / "dataset-metadata.json").read_text())
    by = {r["path"]: r for r in meta["resources"]}
    names = [f["name"] for f in by["sources.csv"]["schema"]["fields"]]
    assert names == LEGACY_FIELDS and "reason_code" not in names
