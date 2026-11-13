"""validate tests. Every article here is invented."""

from __future__ import annotations

import csv
import json

from commonswire.cli import main
from commonswire.schema import text_hash
from commonswire.sources import SOURCE_FIELDS, parse_row
from commonswire.validate import validate_file
from test_schema import art, as_dict
from test_sources import row

TEMPLATE = "{title}, by {authors} for {source}, {license}"


def registry(**over):
    src = parse_row(row(credit_line=TEMPLATE, **over))
    return {src.source_id: src}


def good(**over):
    base = dict(credit_line="An invented story, by Example News for Example News, CC BY 4.0")
    base.update(over)
    return art(**base)


def write_jsonl(tmp_path, items, name="a.jsonl"):
    path = tmp_path / name
    lines = []
    for item in items:
        lines.append(item if isinstance(item, str) else json.dumps(item))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_a_good_file_passes(tmp_path):
    path = write_jsonl(tmp_path, [as_dict(good())])
    result = validate_file(path, registry())
    assert result.ok and result.articles == 1
    assert result.warnings == ["line 1: text is short (84 characters)"]


def test_every_error_names_its_line(tmp_path):
    a = as_dict(good())
    items = [
        a,
        a,  # duplicate id and text
        "{not json",
        as_dict(good(), language="English"),
        as_dict(good(url="https://news.example.org/other"), third_party=True),
        "",
    ]
    result = validate_file(write_jsonl(tmp_path, items), registry())
    assert "line 2: id cw_588a8165f3de2ca6 is also on line 1" in result.errors
    assert any(e.startswith("line 3: not valid JSON") for e in result.errors)
    assert any(e.startswith("line 4: language:") for e in result.errors)
    assert any(e.startswith("line 5: third_party is true") for e in result.errors)
    assert "line 6: empty line" in result.warnings
    assert any("same text as line 1" in w for w in result.warnings)


def test_registry_checks(tmp_path):
    path = write_jsonl(tmp_path, [as_dict(good())])
    pending = registry(status="pending", reason="Is it ok?")
    assert any("is pending, not include" in e for e in validate_file(path, pending).errors)
    other = registry(source_id="someone_else")
    assert any("not in the source registry" in e for e in validate_file(path, other).errors)
    bad_license = write_jsonl(
        tmp_path,
        [
            as_dict(
                good(
                    license="CC-BY-SA-4.0",
                    credit_line="An invented story, by Example News for Example News, CC BY-SA 4.0",
                )
            )
        ],
        "b.jsonl",
    )
    assert any(
        "differs from the source's license" in e
        for e in validate_file(bad_license, registry()).errors
    )
    pd = write_jsonl(
        tmp_path,
        [
            as_dict(
                good(
                    license="public-domain",
                    credit_line=(
                        "An invented story, by Example News for Example News, Public domain"
                    ),
                )
            )
        ],
        "c.jsonl",
    )
    assert validate_file(pd, registry()).ok
    wrong_credit = write_jsonl(tmp_path, [as_dict(good(credit_line="Example News"))], "d.jsonl")
    assert any("credit_line should be" in e for e in validate_file(wrong_credit, registry()).errors)
    removed = as_dict(good(), status="removed", text="", content_hash=text_hash(""))
    assert validate_file(write_jsonl(tmp_path, [removed], "e.jsonl"), registry()).ok


def test_without_a_registry_there_is_a_warning(tmp_path):
    result = validate_file(write_jsonl(tmp_path, [as_dict(good())]), None)
    assert result.ok
    assert result.warnings[-1].startswith("no source registry given")


def write_registry(tmp_path, **over):
    path = tmp_path / "sources.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        writer.writeheader()
        writer.writerow(row(credit_line=TEMPLATE, **over))
    return path


def test_cli_validate_and_sources_check(tmp_path, capsys):
    reg = write_registry(tmp_path)
    good_file = write_jsonl(tmp_path, [as_dict(good())])
    assert main(["validate", str(good_file), "--sources", str(reg)]) == 0
    assert "1 articles, 0 errors" in capsys.readouterr().out
    bad_file = write_jsonl(tmp_path, ["{"], "bad.jsonl")
    assert main(["validate", str(bad_file), "--no-registry"]) == 1
    assert main(["validate", str(good_file), "--sources", str(tmp_path / "none.csv")]) == 2
    assert main(["--root", str(tmp_path), "sources", "check", "--sources", str(reg)]) == 0
    out = capsys.readouterr().out
    assert "quotes were not checked" in out and "1 sources (1 include, 0 pending, 0 exclude)" in out
    (tmp_path / "data" / "raw" / "evidence").mkdir(parents=True)
    assert main(["--root", str(tmp_path), "sources", "check", "--sources", str(reg)]) == 1
    assert "no saved pages" in capsys.readouterr().out
    assert main(["sources", "check", "--sources", str(reg), "--no-quotes"]) == 0
