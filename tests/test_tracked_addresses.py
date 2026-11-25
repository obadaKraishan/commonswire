"""The tracked request log and evidence files name article pages by id, never by address.

The last test reads the repository's own tracked files (no network); the others use invented
files.
"""

from __future__ import annotations

import csv
from pathlib import Path

from commonswire.addresses import (
    LINKS,
    LOG,
    PAGES,
    find,
    is_article_address,
    kept_addresses,
    kind,
    snapshot_name,
)
from commonswire.cli import main
from commonswire.http import USAGE_FIELDS
from commonswire.schema import article_id

REPO = Path(__file__).resolve().parents[1]
SITE = "https://news.example"
WIKI = "https://xx.wikinews.org"


def test_what_counts_as_an_article_address():
    assert kind(f"{SITE}/2024/05/03/an-invented-headline/") == "dated"
    assert kind(f"{SITE}/2024/05/an-invented-headline") == "dated"
    assert kind(f"{SITE}/fr/2024/05/03/12345/") == "dated"
    assert kind(f"{SITE}/about/") == "" and kind(f"{SITE}/2024/") == ""
    assert kind(f"{WIKI}/wiki/Invented_headline") == "wiki"
    assert kind(f"{WIKI}/wiki/Wikinews:Copyright") == ""
    assert kind(f"{WIKI}/wiki/Cat%C3%A9gorie:Invented") == ""
    kept = {f"{WIKI}/wiki/Main_Page", f"{SITE}/2019/01/01/our-license"}
    assert not is_article_address(f"{WIKI}/wiki/Main_Page", kept)
    assert not is_article_address(f"{SITE}/2019/01/01/our-license", kept)
    assert is_article_address(f"{SITE}/2024/05/03/an-invented-headline/", kept)
    assert not is_article_address(article_id(f"{SITE}/2024/05/03/x/"), kept)
    assert snapshot_name("2026-11-17/src/03-a-headline.html", "cw_" + "ab" * 8) == (
        "2026-11-17/src/03-cw_abababababababab.html"
    )


def _csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def invented_root(tmp_path: Path) -> Path:
    from test_sources import row, write_csv

    root = tmp_path / "repo"
    (root / "data").mkdir(parents=True)
    reg = write_csv(
        tmp_path,
        [
            row(
                source_id="alpha",
                homepage=f"{SITE}/",
                license_url=f"{SITE}/2019/01/01/our-license/",
            )
        ],
    )
    (root / "data" / "sources.csv").write_bytes(reg.read_bytes())
    article = f"{SITE}/2024/05/03/an-invented-headline/"
    main_page = f"{WIKI}/wiki/Main_Page"
    wiki_article = f"{WIKI}/wiki/Invented_headline"
    log = [
        {"time": "t", "host": "news.example", "path": "/2024/05/03/an-invented-headline/",
         "query_keys": "a", "status": "200", "bytes": "10", "note": "evidence:alpha"},
        {"time": "t", "host": "news.example", "path": "/2019/01/01/our-license/",
         "query_keys": "", "status": "200", "bytes": "9", "note": "evidence:alpha"},
        {"time": "t", "host": "xx.wikinews.org", "path": "/wiki/Main_Page",
         "query_keys": "", "status": "200", "bytes": "8", "note": "evidence:wikinews_xx"},
        {"time": "t", "host": "xx.wikinews.org", "path": "/wiki/Invented_headline",
         "query_keys": "", "status": "200", "bytes": "7", "note": "evidence:wikinews_xx"},
    ]  # fmt: skip
    _csv(root / LOG, USAGE_FIELDS, log)
    pf = ["checked_on", "source_id", "role", "url", "final_url", "status", "bytes", "sha256",
          "outcome", "file"]  # fmt: skip
    pages = [
        {"checked_on": "2026-11-17", "source_id": "wikinews_xx", "role": "home",
         "url": f"{WIKI}/", "final_url": main_page, "status": "200", "bytes": "8",
         "sha256": "s1", "outcome": "ok", "file": "2026-11-17/wikinews_xx/01-wiki-main-page.html"},
        {"checked_on": "2026-11-17", "source_id": "alpha", "role": "extra", "url": article,
         "final_url": article, "status": "200", "bytes": "10", "sha256": "s2", "outcome": "ok",
         "file": "2026-11-17/alpha/02-2024-05-03-an-invented-headline.html"},
        {"checked_on": "2026-11-17", "source_id": "wikinews_xx", "role": "extra",
         "url": wiki_article, "final_url": wiki_article, "status": "200", "bytes": "7",
         "sha256": "s3", "outcome": "ok", "file": ""},
        {"checked_on": "2026-11-17", "source_id": "alpha", "role": "extra",
         "url": f"{SITE}/2020/02/02/a-page-that-refused/", "final_url":
         f"{SITE}/2020/02/02/a-page-that-refused/", "status": "403", "bytes": "0",
         "sha256": "", "outcome": "blocked", "file": ""},
    ]  # fmt: skip
    _csv(root / PAGES, pf, pages)
    links = [
        {"checked_on": "2026-11-17", "source_id": "alpha", "page_url": article,
         "license_url": "https://creativecommons.org/licenses/by/4.0/", "link_text": "CC BY"},
        {"checked_on": "2026-11-17", "source_id": "wikinews_xx", "page_url": main_page,
         "license_url": "https://creativecommons.org/licenses/by/2.5/", "link_text": "CC BY"},
    ]  # fmt: skip
    _csv(root / LINKS, ["checked_on", "source_id", "page_url", "license_url", "link_text"], links)
    snap = root / "data" / "raw" / "evidence" / "2026-11-17" / "alpha"
    snap.mkdir(parents=True)
    (snap / "02-2024-05-03-an-invented-headline.html").write_text("<html>invented</html>")
    return root


def test_the_rewrite_puts_ids_in_place_and_keeps_the_rest(tmp_path, capsys):
    root = invented_root(tmp_path)
    kept = kept_addresses(root)
    assert f"{WIKI}/wiki/Main_Page" in kept
    found = find(root, kept)
    assert found.total == 7  # the log 2; pages' url and final_url 2 each; links 1
    assert main(["--root", str(root), "tracked-addresses"]) == 1
    save = tmp_path / "saved"
    assert (
        main(["--root", str(root), "tracked-addresses", "--rewrite", "--save-to", str(save)]) == 0
    )
    out = capsys.readouterr().out
    assert '"left": 0' in out and "an-invented" not in out
    article = f"{SITE}/2024/05/03/an-invented-headline/"
    rid = article_id(article)
    log = list(csv.DictReader((root / LOG).open()))
    assert [r["path"] for r in log] == [
        rid,
        "/2019/01/01/our-license/",  # the page the registry cites for the license
        "/wiki/Main_Page",  # a main page
        article_id(f"{WIKI}/wiki/Invented_headline"),
    ]
    assert log[0]["query_keys"] == "" and log[0]["bytes"] == "10" and log[0]["status"] == "200"
    pages = list(csv.DictReader((root / PAGES).open()))
    assert pages[0]["final_url"] == f"{WIKI}/wiki/Main_Page"
    assert pages[1]["url"] == pages[1]["final_url"] == rid
    assert pages[1]["file"] == f"2026-11-17/alpha/02-{rid}.html"
    # A page that refused is listed for the maintainer to read: it keeps its address.
    assert pages[3]["url"] == f"{SITE}/2020/02/02/a-page-that-refused/"
    assert (root / "data" / "raw" / "evidence" / pages[1]["file"]).exists()
    assert (
        root
        / "data"
        / "raw"
        / "evidence"
        / "2026-11-17/alpha/02-2024-05-03-an-invented-headline.html"
    ).exists()
    links = list(csv.DictReader((root / LINKS).open()))
    assert [r["page_url"] for r in links] == [rid, f"{WIKI}/wiki/Main_Page"]
    mapping = list(csv.DictReader((save / "address-ids.csv").open()))
    assert {m["id"] for m in mapping} >= {rid}
    assert (save / "usage_log.csv").read_text().count("an-invented-headline") == 1
    assert find(root).total == 0
    assert main(["--root", str(root), "tracked-addresses"]) == 0
    # The copies are never overwritten.
    assert (
        main(["--root", str(root), "tracked-addresses", "--rewrite", "--save-to", str(save)]) == 2
    )
    assert "never overwritten" in capsys.readouterr().err


def test_the_tracked_log_and_evidence_name_no_article_address():
    """The repository's own request log and evidence files: an article page is named by its
    id (counts only on failure, never the addresses)."""
    found = find(REPO)
    assert found.total == 0, found.lines()
