from __future__ import annotations

import pytest

import commonswire
from commonswire.cli import main


def test_version_is_a_dev_version():
    assert commonswire.__version__.startswith("0.1.0")


def test_cli_without_a_command_prints_help(capsys):
    assert main([]) == 0
    assert "commonswire" in capsys.readouterr().out


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "commonswire 0.1.0" in capsys.readouterr().out


def test_data_file_finds_a_checkout_file_and_names_both_places_when_missing():
    from commonswire._paths import data_file, repo_root

    assert (repo_root() / "src" / "commonswire").is_dir()
    with pytest.raises(FileNotFoundError, match="CommonsWire checkout"):
        data_file("no-such-table.csv")
    assert data_file("evidence").is_dir()
