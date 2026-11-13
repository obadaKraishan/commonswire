"""The ``commonswire`` command line."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from commonswire import __version__
from commonswire._paths import repo_root


def _today() -> str:
    return date.today().isoformat()


def cmd_evidence_fetch(args: argparse.Namespace) -> int:
    from commonswire.evidence import EvidencePaths, fetch_evidence, read_candidates
    from commonswire.http import make_client

    root = Path(args.root)
    if not (root / "data" / "raw").exists():
        print(
            "data/raw is missing. Mount the data drive (data/raw links to it) and try again.",
            file=sys.stderr,
        )
        return 2
    candidates = read_candidates(Path(args.candidates))
    if args.only:
        wanted = set(args.only.split(","))
        unknown = wanted - {c.source_id for c in candidates}
        if unknown:
            print(f"not in the candidate list: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        candidates = [c for c in candidates if c.source_id in wanted]
    extra: dict[str, list[str]] = {}
    for item in args.url or []:
        source_id, _, url = item.partition("=")
        if not url:
            print(f"--url needs SOURCE_ID=URL, got {item!r}", file=sys.stderr)
            return 2
        extra.setdefault(source_id, []).append(url)
    client = make_client(root, byte_budget=args.max_mb * 1024 * 1024)
    counts = fetch_evidence(
        client,
        candidates,
        EvidencePaths(root, args.date),
        max_policy_pages=args.max_pages,
        extra_urls=extra,
        progress=lambda msg: print(msg, flush=True),
    )
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "nothing new"
    print(f"pages: {summary}; {client.bytes_used:,} bytes this run")
    return 0


def cmd_evidence_extract(args: argparse.Namespace) -> int:
    from commonswire.evidence import extract_evidence

    ids = args.only.split(",") if args.only else None
    n = extract_evidence(Path(args.root), args.date, ids)
    print(f"read {n} saved pages into data/interim/evidence/{args.date}/")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from commonswire.sources import load_sources
    from commonswire.validate import validate_file

    registry = None
    if not args.no_registry:
        try:
            registry = load_sources(Path(args.sources))
        except (OSError, ValueError) as exc:
            print(f"can't use the source registry: {exc}", file=sys.stderr)
            return 2
    result = validate_file(Path(args.file), registry)
    for msg in result.errors:
        print(f"error: {msg}")
    for msg in result.warnings:
        print(f"warning: {msg}")
    print(
        f"{args.file}: {result.articles} articles, {len(result.errors)} errors, "
        f"{len(result.warnings)} warnings"
    )
    return 0 if result.ok else 1


def cmd_sources_check(args: argparse.Namespace) -> int:
    from collections import Counter

    from commonswire.evidence import page_texts
    from commonswire.sources import check_quotes, validate_sources

    root = Path(args.root)
    sources, problems = validate_sources(Path(args.sources))
    if not args.no_quotes:
        if (root / "data" / "raw" / "evidence").exists():
            problems += check_quotes(sources, lambda sid: page_texts(root, sid))
        else:
            print("note: no saved evidence pages here, so quotes were not checked")
    for msg in problems:
        print(f"problem: {msg}")
    counts = Counter(s.status for s in sources)
    summary = ", ".join(f"{counts[k]} {k}" for k in ("include", "pending", "exclude"))
    print(f"{args.sources}: {len(sources)} sources ({summary}), {len(problems)} problems")
    return 0 if not problems else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commonswire",
        description="Build and check CommonsWire, a corpus of news that may be redistributed.",
    )
    parser.add_argument("--version", action="version", version=f"commonswire {__version__}")
    parser.add_argument(
        "--root", default=str(repo_root()), help="the checkout's root folder (default: this one)"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    ev = sub.add_parser("evidence", help="collect and read the evidence for the source registry")
    ev_sub = ev.add_subparsers(dest="evidence_command", metavar="STEP", required=True)
    fetch = ev_sub.add_parser("fetch", help="save robots.txt, homepages and policy pages")
    fetch.add_argument("--candidates", default=str(repo_root() / "data" / "candidates.csv"))
    fetch.add_argument("--date", default=_today(), help="the check date (default: today)")
    fetch.add_argument("--only", help="comma-separated source ids")
    fetch.add_argument("--max-pages", type=int, default=5, help="policy pages found per source")
    fetch.add_argument("--url", action="append", help="SOURCE_ID=URL: also read this page")
    fetch.add_argument("--max-mb", type=int, default=200, help="stop after this many megabytes")
    fetch.set_defaults(func=cmd_evidence_fetch)
    extract = ev_sub.add_parser("extract", help="turn saved pages into text and keyword lines")
    extract.add_argument("--date", default=_today())
    extract.add_argument("--only", help="comma-separated source ids")
    extract.set_defaults(func=cmd_evidence_extract)

    src = sub.add_parser("sources", help="check the source registry")
    src_sub = src.add_subparsers(dest="sources_command", metavar="STEP", required=True)
    check = src_sub.add_parser("check", help="check every rule and every quote")
    check.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    check.add_argument(
        "--no-quotes", action="store_true", help="skip the check against saved pages"
    )
    check.set_defaults(func=cmd_sources_check)

    val = sub.add_parser("validate", help="check a JSON Lines file of articles")
    val.add_argument("file")
    val.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    val.add_argument(
        "--no-registry", action="store_true", help="check the schema only, not the sources"
    )
    val.set_defaults(func=cmd_validate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
