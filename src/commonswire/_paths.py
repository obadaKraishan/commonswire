"""Where the tracked reference tables live.

In a checkout they are in the repository's ``data/`` folder; in an installed wheel they are
copied into ``commonswire/data/``. The package copy is checked first.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGE = Path(__file__).resolve().parent


def data_file(name: str) -> Path:
    """The path of a tracked data file such as ``sources.csv``."""
    candidates = [_PACKAGE / "data" / name, _PACKAGE.parents[1] / "data" / name]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"can't find {name}: looked in {candidates[0].parent} and {candidates[1].parent}. "
        "Run the command from a CommonsWire checkout, or pass the file's path."
    )


def repo_root() -> Path:
    """The checkout's root folder (the parent of ``src/``)."""
    return _PACKAGE.parents[1]
