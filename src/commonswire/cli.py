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


def cmd_probe(args: argparse.Namespace) -> int:
    from commonswire.evidence import _append
    from commonswire.http import make_client
    from commonswire.probe import VOLUME_FIELDS, probe_sitemap, probe_wordpress

    root = Path(args.root)
    client = make_client(root, byte_budget=20 * 1024 * 1024)
    if args.wordpress:
        vol = probe_wordpress(client, args.source_id, args.wordpress)
    else:
        vol = probe_sitemap(client, args.source_id, args.sitemap)
    _append(root / "data" / "evidence" / "volume.csv", VOLUME_FIELDS, [vol.row(args.date)])
    print(
        f"{args.source_id}: {vol.per_day if vol.per_day is not None else '?'} a day over "
        f"{vol.dates_seen} dates; total {vol.total if vol.total is not None else '?'}; "
        f"archive from {vol.archive_from or '?'}; {vol.requests} requests. {vol.note}"
    )
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    from commonswire.fetchers import FETCHERS
    from commonswire.fetchers.base import RawStore, dumps, run_sample, summary, write_sample
    from commonswire.http import make_client
    from commonswire.sources import load_sources
    from commonswire.validate import validate_file

    root = Path(args.root)
    if not (root / "data" / "raw").exists():
        print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
        return 2
    registry = load_sources(Path(args.sources))
    if args.source_id not in FETCHERS:
        print(f"no fetcher for {args.source_id}; there are: {', '.join(FETCHERS)}", file=sys.stderr)
        return 2
    source = registry.get(args.source_id)
    if source is None:
        print(f"{args.source_id} is not in the registry", file=sys.stderr)
        return 2
    client = make_client(root, byte_budget=args.max_mb * 1024 * 1024)
    raw = RawStore(root / "data" / "raw" / "sample" / args.source_id / args.date)
    fetcher = FETCHERS[args.source_id](client, source, raw)
    result = run_sample(fetcher, limit=args.max)
    if hasattr(fetcher, "archive_start"):
        fetcher.archive_start()
        result.api_totals = dict(fetcher.api_totals)
        result.raw_files = list(raw.files)
    out = root / "data" / "interim" / "sample" / f"{args.source_id}-{args.date}.jsonl"
    digest = write_sample(result, out)
    info = summary(result)
    info["jsonl_sha256"] = digest
    info["checked_on"] = args.date
    summary_path = (
        root / "data" / "evidence" / "sample" / f"{args.source_id}-{args.date}.summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(dumps(info), encoding="utf-8")
    check = validate_file(out, registry)
    print(
        f"{args.source_id}: saw {result.seen}, kept {len(result.kept)}, dropped "
        f"{sum(result.dropped.values())} {dict(result.dropped)}; {client.bytes_used:,} bytes; "
        f"validate: {len(check.errors)} errors, {len(check.warnings)} warnings"
    )
    return 0 if check.ok else 1


def cmd_sample_report(args: argparse.Namespace) -> int:
    import json

    from commonswire.evidence import read_rows
    from commonswire.report import load_articles, sample_report, write_report

    root = Path(args.root)
    arts = load_articles(
        root / "data" / "interim" / "sample" / f"{args.source_id}-{args.date}.jsonl"
    )
    folder = root / "data" / "evidence" / "sample"
    info = json.loads((folder / f"{args.source_id}-{args.date}.summary.json").read_text())
    totals = info.get("api_totals", {})
    total = totals.get("total_posts") or totals.get("total_articles")
    archive = totals.get("archive_from")
    for row in read_rows(root / "data" / "evidence" / "volume.csv"):
        if row["source_id"] == args.source_id:
            total = total or (int(row["total_articles"]) if row["total_articles"] else None)
            archive = archive or row["archive_from"] or None
    report = sample_report(arts, info, total_articles=total, archive_from=archive)
    write_report(report, folder / f"{args.source_id}-{args.date}.report.json")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


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

    probe = sub.add_parser("probe", help="count a source's articles a day (dates only, no text)")
    probe.add_argument("source_id")
    how = probe.add_mutually_exclusive_group(required=True)
    how.add_argument("--wordpress", metavar="BASE_URL", help="the site's address, for its API")
    how.add_argument("--sitemap", metavar="URL", help="a news or post sitemap")
    probe.add_argument("--date", default=_today())
    probe.set_defaults(func=cmd_probe)

    sample = sub.add_parser("sample", help="fetch a small live sample from an included source")
    sample.add_argument("source_id")
    sample.add_argument("--max", type=int, default=200, help="articles (at most 200)")
    sample.add_argument("--date", default=_today())
    sample.add_argument("--max-mb", type=int, default=300, help="stop after this many megabytes")
    sample.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    sample.set_defaults(func=cmd_sample)

    rep = sub.add_parser("sample-report", help="aggregate a sample (counts only, no text)")
    rep.add_argument("source_id")
    rep.add_argument("--date", default=_today())
    rep.set_defaults(func=cmd_sample_report)
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
