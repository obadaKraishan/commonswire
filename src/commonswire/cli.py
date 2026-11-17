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
    from commonswire.http import Blocked, FetchError, make_client
    from commonswire.probe import VOLUME_FIELDS, Volume, probe_sitemap, probe_wordpress

    root = Path(args.root)
    client = make_client(root, byte_budget=20 * 1024 * 1024)
    try:
        if args.wordpress:
            vol = probe_wordpress(client, args.source_id, args.wordpress)
        else:
            vol = probe_sitemap(client, args.source_id, args.sitemap)
    except Blocked as exc:
        method = "wordpress" if args.wordpress else "sitemap"
        vol = Volume(args.source_id, method, requests=1, note=f"refused: HTTP {exc.status}")
    except FetchError as exc:
        method = "wordpress" if args.wordpress else "sitemap"
        vol = Volume(args.source_id, method, note=f"not fetched: {exc}"[:120])
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
    raw_dir = root / "data" / "raw" / "sample" / args.source_id / args.date
    summary_path = (
        root / "data" / "evidence" / "sample" / f"{args.source_id}-{args.date}.summary.json"
    )
    earlier_totals: dict[str, object] = {}
    if args.replay:
        import json as _json

        from commonswire.fetchers.base import ReplayStore, ReplayTransport
        from commonswire.http import Pacer, PoliteClient, UsageLog

        files = sorted(raw_dir.glob("*.json"))
        if not files:
            print(f"no saved raw answers in {raw_dir}", file=sys.stderr)
            return 2
        interim = root / "data" / "interim"
        client = PoliteClient(
            usage_log=UsageLog(interim / "replay_log.csv"),
            pacer=Pacer(interim / "replay-locks", 0.0),
            transport=ReplayTransport(files),
        )
        raw = ReplayStore(raw_dir)
        if summary_path.exists():
            earlier_totals = _json.loads(summary_path.read_text()).get("api_totals", {})
    else:
        client = make_client(root, byte_budget=args.max_mb * 1024 * 1024)
        raw = RawStore(raw_dir)
    fetcher = FETCHERS[args.source_id](client, source, raw)
    result = run_sample(fetcher, limit=args.max)
    if hasattr(fetcher, "archive_start"):
        fetcher.archive_start()
        result.api_totals = dict(fetcher.api_totals)
        result.raw_files = list(raw.files)
    for key, value in earlier_totals.items():
        if result.api_totals.get(key) is None:
            result.api_totals[key] = value
    if args.replay:
        result.raw_bytes = sum(f.stat().st_size for f in sorted(raw_dir.glob("*.json")))
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
        f"{sum(result.dropped.values())} {dict(result.dropped)}; "
        f"{'no requests (replayed)' if args.replay else f'{client.bytes_used:,} bytes'}; "
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


def blocked_pages(root: Path) -> list[dict[str, str]]:
    """Pages that refused scripted requests, with a plain answer for each."""
    from commonswire.evidence import read_rows

    robots = {r["source_id"]: r for r in read_rows(root / "data" / "evidence" / "robots.csv")}
    out = []
    for row in read_rows(root / "data" / "evidence" / "pages.csv"):
        if row["outcome"] not in ("blocked", "disallowed"):
            continue
        state = robots.get(row["source_id"], {}).get("state")
        if row["outcome"] == "blocked":
            if row["status"] and row["status"] != "200":
                answer = f"HTTP {row['status']}"
            else:
                answer = "a bot check page"
        elif state == "blocked":
            answer = f"robots.txt answered HTTP {robots[row['source_id']]['robots_status']}"
        elif state == "unreachable":
            answer = "robots.txt could not be reached"
        else:
            answer = "robots.txt disallows the CommonsWire user agent"
        out.append({**row, "answer": answer})
    return out


def cmd_sources_render(args: argparse.Namespace) -> int:
    from commonswire.render import render_sources_md
    from commonswire.sources import load_sources

    root = Path(args.root)
    sources = load_sources(Path(args.sources))
    text = render_sources_md(sources.values(), blocked_pages(root))
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({len(sources)} sources)")
    return 0


def _wordpress_fetcher(root: Path, source_id: str, sources_path: str):  # type: ignore[no-untyped-def]
    from commonswire.fetchers import WORDPRESS
    from commonswire.fetchers.base import ReplayStore
    from commonswire.http import make_client
    from commonswire.sources import load_sources

    if source_id not in WORDPRESS:
        raise SystemExit(
            f"no WordPress backfill for {source_id}; there are: {', '.join(WORDPRESS)}"
        )
    registry = load_sources(Path(sources_path))
    if source_id not in registry:
        raise SystemExit(f"{source_id} is not in the registry")
    client = make_client(root)
    folder = root / "data" / "raw" / "backfill" / source_id
    fetcher = WORDPRESS[source_id](client, registry[source_id], ReplayStore(folder))
    _load_bylines(root, fetcher)
    return fetcher, client


def _load_bylines(root: Path, fetcher) -> None:  # type: ignore[no-untyped-def]
    """Author names kept from a users endpoint, a story listing and article pages, if any,
    with the listing's translators and why a page or listing names no person."""
    import json

    from commonswire.listingbylines import translators_by_url
    from commonswire.pagebylines import load_page_bylines, names_by_url, source_credited

    folder = root / "data" / "interim" / "bylines"
    users = folder / f"{fetcher.source_id}.json"
    if users.exists():
        data = json.loads(users.read_text())
        fetcher.byline_map = {int(k): tuple(v) for k, v in data.items() if v}
    pages = folder / f"{fetcher.source_id}.pages.json"
    listing = folder / f"{fetcher.source_id}.listing.json"
    fetcher.page_bylines = {**names_by_url(listing), **names_by_url(pages)}
    fetcher.source_credited = source_credited(listing) | source_credited(pages)
    fetcher.page_translators = translators_by_url(listing)
    fetcher.byline_why_none = {
        u: v["why_none"]
        for path in (listing, pages)
        for u, v in load_page_bylines(path).items()
        if v.get("why_none")
    }


def cmd_backfill(args: argparse.Namespace) -> int:
    from commonswire.backfill import backfill_wordpress, check_backfill

    root = Path(args.root)
    if not (root / "data" / "raw").exists():
        print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
        return 2
    if args.check:
        folder = root / "data" / "raw" / "backfill" / args.source_id / args.run
        if not folder.is_dir():
            print(f"no saved run at {folder}", file=sys.stderr)
            return 2
        r = check_backfill(folder)
        missing = ", ".join(str(n) for n in r["missing_pages"][:20]) or "none"  # type: ignore[index]
        bad = ", ".join(str(n) for n in r["empty_or_invalid"]) or "none"  # type: ignore[union-attr]
        print(
            f"{args.source_id} {args.run}: {r['pages_present']} of {r['pages_expected']} pages, "
            f"{r['posts']} posts (the site counted {r['total_posts'] or '?'}); missing pages: "
            f"{missing}; empty or invalid: {bad}; "
            + ("complete" if r["complete"] else "NOT complete")
        )
        return 0 if r["complete"] else 1
    fetcher, client = _wordpress_fetcher(root, args.source_id, args.sources)
    client.byte_budget = args.max_mb * 1024 * 1024
    folder = root / "data" / "raw" / "backfill" / args.source_id / args.run
    progress = backfill_wordpress(
        fetcher,
        client,
        folder,
        run=args.run,
        max_pages=args.max_pages,
        say=lambda m: print(m, flush=True),
    )
    print(
        f"{args.source_id}: {progress.pages_saved} of {progress.total_pages or '?'} pages saved "
        f"({progress.total_posts or '?'} posts); {progress.requests_this_run} requests and "
        f"{progress.bytes_this_run:,} bytes this run; "
        + ("finished" if progress.finished else f"not finished: {progress.stopped or 'stopped'}")
    )
    return 0 if progress.finished or progress.stopped.startswith("stopped after") else 1


def cmd_build(args: argparse.Namespace) -> int:
    import json

    from commonswire.backfill import build_rows
    from commonswire.daily import load_rows, replay_daily
    from commonswire.sources import load_sources
    from commonswire.validate import validate_file

    root = Path(args.root)
    fetcher, _ = _wordpress_fetcher(root, args.source_id, args.sources)
    folder = root / "data" / "raw" / "backfill" / args.source_id / args.run
    out = root / "data" / "interim" / "rows" / f"{args.source_id}.jsonl"
    result = build_rows(fetcher, folder, out)
    daily = replay_daily(fetcher, out, root / "data" / "raw" / "daily" / args.source_id)
    check = validate_file(out, load_sources(Path(args.sources)))
    rows = load_rows(out)
    info = result.summary()
    info.update(
        run=args.run,
        validate_errors=len(check.errors),
        validate_warnings=len(check.warnings),
        daily_replayed={
            "days": daily.days,
            "files": daily.files,
            "new": daily.new,
            "changed": daily.changed,
            "removed": daily.removed,
            "unchanged_modified": daily.unchanged_modified,
            "dropped": dict(sorted(daily.dropped.items())),
        },
        rows_after_daily=len(rows),
        releasable_after_daily=sum(1 for r in rows.values() if r["releasable"]),
    )
    path = root / "data" / "evidence" / "backfill" / f"{args.source_id}.build.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{args.source_id}: seen {result.seen}, kept {result.kept} ({result.releasable} "
        f"releasable, {result.credited_to_source} credited to the source itself), dropped "
        f"{sum(result.dropped.values())}; daily answers replayed: {daily.files} files over "
        f"{daily.days} days, {daily.new} new, {daily.changed} changed, {daily.removed} removed; "
        f"{len(rows)} rows now; validate: {len(check.errors)} errors, "
        f"{len(check.warnings)} warnings"
    )
    for msg in check.errors[:5]:
        print(f"  error: {msg}")
    return 0 if check.ok else 1


def cmd_wikinews_dump(args: argparse.Namespace) -> int:
    import json
    from collections import Counter
    from datetime import datetime, timezone

    from commonswire.backfill import save_once
    from commonswire.http import make_client
    from commonswire.licensing import license_on
    from commonswire.schema import make_article
    from commonswire.sources import load_sources, render_credit
    from commonswire.validate import validate_file
    from commonswire.wikidump import (
        DUMP_NAME,
        DUMP_URL,
        MD5_URL,
        expected_md5,
        md5_of,
        open_dump,
        read_dump,
    )

    root = Path(args.root)
    folder = root / "data" / "raw" / "backfill" / "wikinews_en" / args.run
    dump = folder / DUMP_NAME
    if args.download and not dump.exists():
        if not (root / "data" / "raw").exists():
            print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
            return 2
        client = make_client(root, byte_budget=80 * 1024 * 1024)
        sums = client.get(MD5_URL, accept="text/plain", note="backfill:wikinews_en")
        save_once(folder / "md5sums.txt", sums.body)
        resp = client.get(
            DUMP_URL, accept="*/*", max_bytes=80 * 1024 * 1024, note="backfill:wikinews_en"
        )
        if resp.status != 200 or resp.truncated:
            print(f"the dump answered HTTP {resp.status} (truncated: {resp.truncated})")
            return 1
        save_once(dump, resp.body)
    if not dump.exists():
        print(f"no dump at {dump}; run with --download first", file=sys.stderr)
        return 2
    sums_path = folder / "md5sums.txt"
    want = expected_md5(sums_path.read_text()) if sums_path.exists() else None
    got = md5_of(dump)
    if want and want != got:
        print(f"the dump's md5 {got} differs from the published {want}", file=sys.stderr)
        return 1
    registry = load_sources(Path(args.sources))
    src = registry["wikinews_en"]
    retrieved = datetime.fromtimestamp(dump.stat().st_mtime, timezone.utc).replace(microsecond=0)
    skipped: Counter[str] = Counter()
    out = root / "data" / "interim" / "rows" / "wikinews_en.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    seen: set[str] = set()
    first = last = ""
    with open_dump(dump) as stream, out.open("w", encoding="utf-8") as fh:
        for art in read_dump(stream, skipped):
            if art.url in seen:
                skipped["duplicate_url"] += 1
                continue
            seen.add(art.url)
            lic = license_on("wikinews_en", art.published_at, src.license)
            credit = render_credit(
                src.credit_line,
                title=art.title,
                authors=(),
                source=src.name,
                url=art.url,
                license=lic,
            )
            try:
                row = make_article(
                    source_id="wikinews_en",
                    url=art.url,
                    title=art.title,
                    text=art.text,
                    published_at=art.published_at,
                    updated_at=art.last_edit,
                    retrieved_at=max(retrieved, art.published_at),
                    language="en",
                    license=lic,
                    credit_line=credit,
                )
            except ValueError:
                skipped["invalid"] += 1
                continue
            fh.write(row.model_dump_json() + "\n")
            kept += 1
            day = art.published_at.date().isoformat()
            first, last = min(first or day, day), max(last or day, day)
    check = validate_file(out, registry)
    info = {
        "source_id": "wikinews_en",
        "run": args.run,
        "dump_md5": got,
        "md5_checked": bool(want),
        "dump_bytes": dump.stat().st_size,
        "kept": kept,
        "skipped": dict(sorted(skipped.items())),
        "first": first,
        "last": last,
        "rows_bytes": out.stat().st_size,
        "validate_errors": len(check.errors),
        "validate_warnings": len(check.warnings),
    }
    path = root / "data" / "evidence" / "backfill" / "wikinews_en.build.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"wikinews_en: kept {kept}; skipped {dict(skipped)}; validate: {len(check.errors)} errors"
    )
    return 0 if check.ok else 1


def cmd_dedup(args: argparse.Namespace) -> int:
    import json
    from collections import Counter

    import pyarrow as pa
    import pyarrow.parquet as pq

    from commonswire.dedup import exact_duplicates, histogram, near_duplicates, read_rows

    root = Path(args.root)
    paths = sorted((root / "data" / "interim" / "rows").glob("*.jsonl"))
    rows = list(read_rows(paths))
    order = [p.stem for p in paths]
    exact = exact_duplicates(rows, order)
    by_id = {r.id: r for r in rows}
    pairs, oversized = near_duplicates(by_id, exact.kept_ids)
    threshold = args.threshold
    cross = [p for p in pairs if p[2] != p[3]]
    flagged = [p for p in cross if p[4] >= threshold]
    out = root / "data" / "interim" / "dedup"
    out.mkdir(parents=True, exist_ok=True)
    (out / "dropped.json").write_text(json.dumps(exact.dropped, indent=1) + "\n")
    table = pa.table(
        {
            "id_a": [p[0] for p in pairs],
            "id_b": [p[1] for p in pairs],
            "source_a": [p[2] for p in pairs],
            "source_b": [p[3] for p in pairs],
            "jaccard": [p[4] for p in pairs],
            "title_overlap": [p[5] for p in pairs],
        }
    )
    pq.write_table(table, out / "near_duplicates.parquet")
    summary = {
        "rows_in": exact.rows_in,
        "kept_after_exact": len(exact.kept_ids),
        "dropped_exact": dict(sorted(exact.dropped_by.items())),
        "candidate_pairs": len(pairs),
        "candidate_pairs_cross_source": len(cross),
        "oversized_buckets_skipped": oversized,
        "threshold": threshold,
        "flagged_pairs_cross_source": len(flagged),
        "flagged_rows_cross_source": len({x for p in flagged for x in p[:2]}),
        "flagged_by_source_pair": dict(Counter(f"{p[2]}|{p[3]}" for p in flagged)),
        "histogram_cross_source": histogram(pairs, cross_source=True),
        "histogram_same_source": histogram(pairs, cross_source=False),
    }
    ev = root / "data" / "evidence" / "dedup"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        f"{exact.rows_in} rows; {len(exact.kept_ids)} after exact duplicates "
        f"({dict(exact.dropped_by)}); {len(pairs)} candidate pairs, {len(cross)} across "
        f"sources; {len(flagged)} flagged at Jaccard >= {threshold}"
    )
    return 0


def cmd_daily(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone

    from commonswire.daily import daily_wordpress, load_state, save_state
    from commonswire.fetchers import WORDPRESS
    from commonswire.pagebylines import SITE_MARKUP, PageBylineReader

    root = Path(args.root)
    if not (root / "data" / "raw").exists():
        print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    state_path = root / "data" / "interim" / "daily" / "state.json"
    state = load_state(state_path)
    wanted = args.only.split(",") if args.only else None
    print("wikinews_en: skipped (closed since 2026-05-04; its archive comes from the dump)")
    for source_id in WORDPRESS:
        if wanted and source_id not in wanted:
            continue
        rows_path = root / "data" / "interim" / "rows" / f"{source_id}.jsonl"
        if not rows_path.exists():
            print(f"{source_id}: skipped (no rows yet; run its backfill and build first)")
            continue
        fetcher, client = _wordpress_fetcher(root, source_id, args.sources)
        client.byte_budget = args.max_mb * 1024 * 1024
        raw = root / "data" / "raw" / "daily" / source_id / now.date().isoformat()
        src_state = state.setdefault(source_id, {})
        reader = None
        if source_id in SITE_MARKUP and fetcher.requires_byline:
            reader = PageBylineReader(
                client,
                source_id,
                root / "data" / "raw" / "pages" / source_id,
                root / "data" / "interim" / "bylines" / f"{source_id}.pages.json",
                source_name=fetcher.source.name,
            )
        result = daily_wordpress(
            fetcher, client, rows_path, raw, src_state, now, page_bylines=reader
        )
        if reader is not None:
            reader.save()
        print(result.line(), flush=True)
    save_state(state_path, state)
    return 0


def _kinds(sources_path: str) -> dict[str, str]:
    from commonswire.sources import load_sources

    return {k: v.kind for k, v in load_sources(Path(sources_path)).items()}


def cmd_corpus_report(args: argparse.Namespace) -> int:
    import json

    from commonswire.corpus import corpus_report

    root = Path(args.root)
    report = corpus_report(root, _kinds(args.sources), args.threshold)
    path = root / "data" / "evidence" / "corpus" / "report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for source, v in report["sources"].items():
        print(
            f"{source}: {v['rows_kept']} rows ({v['releasable_rows']} releasable), "
            f"{v['first']} to {v['last']}, median {v['words_median']} words, "
            f"{v['per_day_last_90_days']} a day lately"
        )
    t = report["total"]
    print(
        f"total: {t['rows_kept']} rows, {t['releasable_rows']} releasable, "
        f"{t['per_day_last_90_days']} a day over the last 90 days"
    )
    return 0


def cmd_store(args: argparse.Namespace) -> int:
    import json

    from commonswire.corpus import write_parquet

    root = Path(args.root)
    counts = write_parquet(root, _kinds(args.sources), args.threshold)
    path = root / "data" / "evidence" / "corpus" / "parquet_counts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"wrote Parquet for {len(counts)} sources, "
        f"{sum(sum(v.values()) for v in counts.values())} rows"
    )
    return 0


def cmd_bylines(args: argparse.Namespace) -> int:
    """Author names from a WordPress users endpoint, when the site leaves it open."""
    import json
    from urllib.parse import urlencode

    from commonswire.backfill import save_once
    from commonswire.http import Blocked, Disallowed, FetchError

    root = Path(args.root)
    fetcher, client = _wordpress_fetcher(root, args.source_id, args.sources)
    client.byte_budget = 20 * 1024 * 1024
    raw = root / "data" / "raw" / "backfill" / args.source_id / args.run / "users"
    names: dict[str, list[str]] = {}
    for page in range(1, 51):
        path = raw / f"users-p{page:03d}.json"
        if not path.exists():
            q = urlencode({"per_page": "100", "page": str(page), "_fields": "id,name"})
            try:
                resp = client.get(
                    f"{fetcher.api_base}/wp-json/wp/v2/users?{q}",
                    accept="application/json",
                    note=f"bylines:{args.source_id}",
                )
            except (Blocked, Disallowed, FetchError) as exc:
                print(f"{args.source_id}: the users endpoint was refused or failed: {exc}")
                return 1
            if resp.status != 200:
                break
            save_once(path, resp.body)
        data = json.loads(path.read_bytes())
        for u in data:
            if u.get("name"):
                names[str(u["id"])] = [u["name"]]
        if len(data) < 100:
            break
    out = root / "data" / "interim" / "bylines" / f"{args.source_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(names, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.source_id}: {len(names)} author names from the users endpoint")
    return 0


def cmd_page_bylines(args: argparse.Namespace) -> int:
    """Author names from article pages, for rows that have no byline (each page fetched once)."""
    import json

    from commonswire.pagebylines import SITE_MARKUP, PageBylineReader, collect_page_bylines

    root = Path(args.root)
    sid = args.source_id
    if sid not in SITE_MARKUP:
        print(
            f"no byline markup is known for {sid}; there is for: {', '.join(SITE_MARKUP)}",
            file=sys.stderr,
        )
        return 2
    if not (root / "data" / "raw").exists():
        print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
        return 2
    rows = root / "data" / "interim" / "rows" / f"{sid}.jsonl"
    if not rows.exists():
        print(f"{sid}: no rows yet; run its backfill and build first", file=sys.stderr)
        return 2
    fetcher, client = _wordpress_fetcher(root, sid, args.sources)
    client.byte_budget = args.max_mb * 1024 * 1024
    reader = PageBylineReader(
        None if args.replay else client,
        sid,
        root / "data" / "raw" / "pages" / sid,
        root / "data" / "interim" / "bylines" / f"{sid}.pages.json",
        source_name=fetcher.source.name,
        say=lambda m: print(m, flush=True),
    )
    st = collect_page_bylines(reader, rows, limit=args.limit)
    info = st.summary()
    path = root / "data" / "evidence" / "bylines" / f"{sid}.pages.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{sid}: {st.rows_without_byline} rows without a byline; {st.with_person} pages name a "
        f"person, {sum(st.no_person.values())} do not ({dict(st.no_person)}); "
        f"{st.pages_fetched} fetched ({st.bytes_fetched:,} bytes), "
        f"{st.pages_already_saved} already saved"
        + (f"; stopped: {st.stopped}" if st.stopped else "")
    )
    print(f"next: commonswire build {sid} --run RUN, to put the names into the rows")
    return 0 if not st.stopped else 1


def cmd_listing_bylines(args: argparse.Namespace) -> int:
    """Writers' names from a source's paged story listing (each listing page fetched once)."""
    import json

    from commonswire.http import make_client
    from commonswire.listingbylines import LISTING_MARKUP, collect_listing_bylines
    from commonswire.sources import load_sources

    root = Path(args.root)
    sid = args.source_id
    if sid not in LISTING_MARKUP:
        print(
            f"no listing markup is known for {sid}; there is for: {', '.join(LISTING_MARKUP)}",
            file=sys.stderr,
        )
        return 2
    if not (root / "data" / "raw").exists():
        print("data/raw is missing. Mount the data drive and try again.", file=sys.stderr)
        return 2
    client = None
    if not args.replay:
        client = make_client(root, byte_budget=args.max_mb * 1024 * 1024)
    st = collect_listing_bylines(
        client,
        sid,
        root / "data" / "raw" / "pages" / sid / "listing" / args.run,
        root / "data" / "interim" / "bylines" / f"{sid}.listing.json",
        source_name=load_sources(Path(args.sources))[sid].name,
        max_pages=args.max_pages,
        say=lambda m: print(m, flush=True),
    )
    info = st.summary()
    info["run"] = args.run
    path = root / "data" / "evidence" / "bylines" / f"{sid}.listing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{sid}: {st.last_page} listing pages ({st.pages_fetched} fetched, "
        f"{st.pages_already_saved} already saved, {st.bytes_fetched:,} bytes); {st.stories} "
        f"stories, {st.with_writer} with a writer's name, {st.without_writer} without"
        + (f"; ended: {st.end}" if st.end else "")
        + (f"; stopped: {st.stopped}" if st.stopped else "")
    )
    print(f"next: commonswire build {sid} --run RUN, to put the names into the rows")
    return 1 if st.stopped else 0


def _third_party_dropped(root: Path, sources: Sequence[str]) -> int:
    import json

    total = 0
    for s in sources:
        path = root / "data" / "evidence" / "backfill" / f"{s}.build.json"
        if path.exists():
            info = json.loads(path.read_text())
            drops = info.get("dropped") or info.get("skipped") or {}
            total += sum(v for k, v in drops.items() if k.startswith("third_party"))
    return total


def _corpus_report(root: Path) -> dict | None:
    """The corpus report, if it is newer than every rows file (else its counts are stale)."""
    import json

    path = root / "data" / "evidence" / "corpus" / "report.json"
    if not path.exists():
        return None
    rows = list((root / "data" / "interim" / "rows").glob("*.jsonl"))
    if rows and path.stat().st_mtime < max(r.stat().st_mtime for r in rows):
        print(
            "note: the corpus report is older than the rows, so the counts were not compared "
            "with it (run commonswire dedup and corpus-report first to compare them)"
        )
        return None
    return json.loads(path.read_text())


def cmd_release_build(args: argparse.Namespace) -> int:
    """Write data/release/<version>/ from the built rows (no requests)."""
    from commonswire.release import ReleaseError, collect, verify, write_release
    from commonswire.release_text import card, licenses_md
    from commonswire.sources import load_sources

    root = Path(args.root)
    out = root / "data" / "release" / args.version
    if out.exists() and not args.overwrite:
        print(
            f"{out} already exists. A published version never changes: pick a new version, or "
            "give --overwrite to rewrite an unpublished one in place.",
            file=sys.stderr,
        )
        return 2
    registry = load_sources(Path(args.sources))
    try:
        rel = collect(root, args.version, registry)
    except ReleaseError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not rel.checks.ok:
        for problem in rel.checks.problems():
            print(f"check failed: {problem}", file=sys.stderr)
        return 1
    third = _third_party_dropped(root, rel.sources)
    manifest = write_release(
        rel,
        out,
        Path(args.sources),
        registry,
        card=card(rel, registry, third),
        licenses_md=licenses_md(rel, registry),
    )
    problems = verify(out, _corpus_report(root))
    per = manifest["rows_by_configuration"]
    size = sum(f["bytes"] for f in manifest["files"])
    print(
        f"release {args.version}: {manifest['rows']:,} rows ("
        + ", ".join(f"{c} {n:,}" for c, n in per.items())
        + f"); held back {sum(manifest['held_rows_not_released'].values())}, removed "
        f"{sum(manifest['removed_rows_not_released'].values())}, exact duplicates "
        f"{sum(manifest['exact_duplicates_dropped'].values())}; {len(manifest['files']) + 1} "
        f"files, {size / 1e6:.1f} MB, in {out}"
    )
    for problem in problems:
        print(f"check failed: {problem}", file=sys.stderr)
    print("checks: all passed" if not problems else f"checks: {len(problems)} problems")
    return 1 if problems else 0


def cmd_release_check(args: argparse.Namespace) -> int:
    from commonswire.release import verify

    root = Path(args.root)
    out = root / "data" / "release" / args.version
    if not (out / "manifest.json").exists():
        print(f"no release at {out}; run commonswire release build first", file=sys.stderr)
        return 2
    import json

    update = json.loads((out / "manifest.json").read_text()).get("update")
    if update:
        # A version built by `commonswire update` adds the week's rows to the published one;
        # the local corpus report describes the last local build, so the two never agree.
        print(
            f"note: {args.version} was built by commonswire update from "
            f"{update.get('from_version', 'the version before')}, so its rows were not compared "
            "with the local corpus report"
        )
        report = None
    else:
        report = _corpus_report(root)
    problems = verify(out, report)
    for problem in problems:
        print(f"check failed: {problem}")
    print(f"release {args.version}: " + ("all checks passed" if not problems else "problems found"))
    return 1 if problems else 0


def cmd_release_kaggle(args: argparse.Namespace) -> int:
    from commonswire.release_pack import kaggle_folder

    root = Path(args.root)
    out = root / "data" / "release" / args.version
    if not (out / "manifest.json").exists():
        print(f"no release at {out}; run commonswire release build first", file=sys.stderr)
        return 2
    folder = kaggle_folder(
        out, root / "data" / "release" / f"{args.version}-kaggle", overwrite=args.overwrite
    )
    print(f"wrote {folder} (dataset-metadata.json and {len(list(folder.iterdir())) - 1} files)")
    return 0


def cmd_release_zenodo(args: argparse.Namespace) -> int:
    """The GitHub route by default: check .zenodo.json and the release archive, and print the
    maintainer's steps. With --website, the fallback: a folder for a deposit by hand."""
    import subprocess

    from commonswire.release_pack import (
        archive_names,
        archive_problems,
        check_zenodo_json,
        zenodo_folder,
    )

    root = Path(args.root)
    if not args.website:
        problems = check_zenodo_json(root)
        try:
            names = archive_names(root, args.commit)
        except (OSError, subprocess.CalledProcessError):
            names = []
            problems.append(f"no git archive of {args.commit} in {root} (not a git checkout?)")
        else:
            problems += archive_problems(names)
        for problem in problems:
            print(f"check failed: {problem}")
        if problems:
            print("Zenodo (GitHub route): fix the problems above before the GitHub release.")
            return 1
        print(
            f"Zenodo (GitHub route): .zenodo.json passes, and the archive of {args.commit} holds "
            f"{len(names)} files, .zenodo.json among them, and no request log or collected data."
            "\nNothing is uploaded. The maintainer's steps:"
            "\n  1. In Zenodo, switch the repository on (profile menu, GitHub, Sync now, then the"
            "\n     switch next to the repository), before the release: Zenodo archives new"
            "\n     releases only."
            f"\n  2. On GitHub, publish the release v{args.version} (a full release, not a draft)."
            "\n  3. The DOI appears on the new Zenodo record and next to the repository on"
            "\n     Zenodo's GitHub page; add it to CITATION.cff, the README and the card then."
            f"\nFallback, a deposit by hand: commonswire release zenodo --version {args.version} "
            "--website"
        )
        return 0
    out = root / "data" / "release" / args.version
    if not (out / "manifest.json").exists():
        print(f"no release at {out}; run commonswire release build first", file=sys.stderr)
        return 2
    folder = zenodo_folder(
        out,
        root / "data" / "release" / f"{args.version}-zenodo",
        root,
        overwrite=args.overwrite,
        commit=args.commit,
    )
    print(f"wrote {folder} (zenodo-metadata.json and {len(list(folder.iterdir())) - 1} files)")
    print("This is the fallback; the GitHub route (without --website) is the default.")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """The weekly update: the next version from a published one (see commonswire.update)."""
    import json
    from datetime import datetime

    from commonswire.release import ReleaseError
    from commonswire.update import redact, run_update

    root = Path(args.root)
    prev, out = Path(args.from_dir).resolve(), Path(args.out).resolve()
    if not (prev / "manifest.json").exists():
        print(f"no version at {prev} (no manifest.json)", file=sys.stderr)
        return 2
    if prev == out or prev in out.parents or out in prev.parents:
        print("--out must be a folder of its own, apart from --from", file=sys.stderr)
        return 2
    work = Path(args.work)
    try:
        result = run_update(
            root,
            prev,
            out,
            work,
            registry_path=Path(args.sources),
            takedowns_path=Path(args.takedowns),
            baseline_path=Path(args.baseline),
            version=args.version,
            answers=Path(args.answers) if args.answers else None,
            usage_log=Path(args.usage_log) if args.usage_log else None,
            lock_dir=Path(args.locks) if args.locks else None,
            now=datetime.fromisoformat(args.now) if args.now else None,
            window=args.window,
            max_mb=args.max_mb,
            max_mb_per_source=args.max_mb_per_source,
            max_shrink=args.max_shrink,
            open_takedowns=args.open_takedowns,
            open_dataset_prs=args.open_dataset_prs,
            allow_skipped=frozenset(filter(None, (args.allow_skipped or "").split(","))),
            max_count_requests=args.max_count_requests,
            dry_run=args.dry_run,
            offline=args.offline,
            say=lambda m: print(redact(m), flush=True),
        )
    except ReleaseError as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 2
    summary = Path(args.summary) if args.summary else work / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(result.summary(), indent=2, sort_keys=True) + "\n")
    summary.with_suffix(".md").write_text(result.markdown())
    for reason in result.stop_reasons:
        print(f"stop: {reason}")
    for note in result.notes:
        print(f"note: {note}")
    print(
        f"update {result.from_version} -> {result.version}: {result.status}"
        + (" (dry run: nothing can be delivered)" if result.dry_run else "")
        + f"; {result.rows_before:,} rows before, {result.rows_after:,} after; "
        f"{result.size_bytes / 1e6:.1f} MB; {result.seconds:.0f} s; summary in {summary}"
    )
    return {"ready": 0, "unchanged": 4}.get(result.status, 3)


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
    render = src_sub.add_parser("render", help="write docs/sources.md from the registry")
    render.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    render.add_argument("--out", default=str(repo_root() / "docs" / "sources.md"))
    render.set_defaults(func=cmd_sources_render)

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
    sample.add_argument(
        "--replay",
        action="store_true",
        help="rebuild the rows from the saved raw answers (no requests)",
    )
    sample.set_defaults(func=cmd_sample)

    bf = sub.add_parser("backfill", help="save a source's whole archive (resumable)")
    bf.add_argument("source_id")
    bf.add_argument("--run", default=_today(), help="the run's name (default: today)")
    bf.add_argument("--max-mb", type=int, default=300, help="stop after this many megabytes")
    bf.add_argument("--max-pages", type=int, help="stop after this many new pages")
    bf.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    bf.add_argument(
        "--check", action="store_true", help="check a saved run for missing pages (no requests)"
    )
    bf.set_defaults(func=cmd_backfill)

    bd = sub.add_parser("build", help="build rows from a saved backfill (no requests)")
    bd.add_argument("source_id")
    bd.add_argument("--run", default=_today())
    bd.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    bd.set_defaults(func=cmd_build)

    wd = sub.add_parser("wikinews-dump", help="read the Wikinews dump into rows")
    wd.add_argument("--run", default=_today())
    wd.add_argument("--download", action="store_true", help="download the dump once first")
    wd.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    wd.set_defaults(func=cmd_wikinews_dump)

    dd = sub.add_parser("dedup", help="drop exact duplicates and flag near-duplicates")
    dd.add_argument("--threshold", type=float, default=0.6, help="Jaccard for a flag")
    dd.set_defaults(func=cmd_dedup)

    dl = sub.add_parser("daily", help="new, changed and removed articles since the last run")
    dl.add_argument("--only", help="comma-separated source ids")
    dl.add_argument("--max-mb", type=int, default=50, help="stop a source after this many MB")
    dl.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    dl.set_defaults(func=cmd_daily)

    cr = sub.add_parser("corpus-report", help="aggregate the corpus (counts only, no text)")
    cr.add_argument("--threshold", type=float, default=0.6)
    cr.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    cr.set_defaults(func=cmd_corpus_report)
    st = sub.add_parser("store", help="write Parquet by source and year")
    st.add_argument("--threshold", type=float, default=0.6)
    st.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    st.set_defaults(func=cmd_store)

    pb = sub.add_parser(
        "page-bylines", help="author names from article pages, for rows with no byline"
    )
    pb.add_argument("source_id")
    pb.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    pb.add_argument("--limit", type=int, help="fetch at most this many pages in this run")
    pb.add_argument("--max-mb", type=int, default=1000, help="stop after this many megabytes")
    pb.add_argument("--replay", action="store_true", help="read saved pages only, no requests")
    pb.set_defaults(func=cmd_page_bylines)
    lb = sub.add_parser(
        "listing-bylines", help="writers' names from a source's paged story listing"
    )
    lb.add_argument("source_id")
    lb.add_argument("--run", default=_today())
    lb.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    lb.add_argument("--max-pages", type=int, default=6000, help="read at most this many pages")
    lb.add_argument("--max-mb", type=int, default=1200, help="stop after this many megabytes")
    lb.add_argument("--replay", action="store_true", help="read saved pages only, no requests")
    lb.set_defaults(func=cmd_listing_bylines)
    by = sub.add_parser("bylines", help="author names from a WordPress users endpoint")
    by.add_argument("source_id")
    by.add_argument("--run", default=_today())
    by.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    by.set_defaults(func=cmd_bylines)

    rel = sub.add_parser("release", help="build and check a dataset version (no requests)")
    rel_sub = rel.add_subparsers(dest="release_command", metavar="STEP", required=True)
    rb = rel_sub.add_parser("build", help="write data/release/VERSION/ from the built rows")
    rb.add_argument("--version", required=True, help="the dataset version, such as 0.1.0")
    rb.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    rb.add_argument("--overwrite", action="store_true", help="rewrite an unpublished version")
    rb.set_defaults(func=cmd_release_build)
    rc = rel_sub.add_parser("check", help="check a written version against its manifest")
    rc.add_argument("--version", required=True)
    rc.set_defaults(func=cmd_release_check)
    rk = rel_sub.add_parser("kaggle", help="prepare the Kaggle folder of a version (no upload)")
    rk.add_argument("--version", required=True)
    rk.add_argument("--overwrite", action="store_true", help="rewrite the folder's files")
    rk.set_defaults(func=cmd_release_kaggle)
    rz = rel_sub.add_parser(
        "zenodo",
        help="check .zenodo.json and the release archive for Zenodo's GitHub route (no upload)",
    )
    rz.add_argument("--version", required=True, help="the release, as in its tag vVERSION")
    rz.add_argument(
        "--website",
        action="store_true",
        help="the fallback: prepare a folder for a deposit by hand on Zenodo's website",
    )
    rz.add_argument("--overwrite", action="store_true", help="with --website: rewrite the files")
    rz.add_argument(
        "--commit", default="HEAD", help="the commit whose code the record holds (default: HEAD)"
    )
    rz.set_defaults(func=cmd_release_zenodo)

    up = sub.add_parser(
        "update", help="the weekly update: the next version from a published one (no upload)"
    )
    up.add_argument("--from", dest="from_dir", required=True, help="the published version")
    up.add_argument("--out", required=True, help="the new version's folder (new or empty)")
    up.add_argument("--version", help="the new version (default: the next patch number)")
    up.add_argument(
        "--work", default="update-work", help="the run's own folder: answers, log, summary"
    )
    up.add_argument("--answers", help="where answers are saved once (default: WORK/answers)")
    up.add_argument("--usage-log", help="the request log (default: WORK/usage_log.csv)")
    up.add_argument("--locks", help="the pacer's lock folder (default: WORK/locks)")
    up.add_argument("--summary", help="the summary file (default: WORK/summary.json, and .md)")
    up.add_argument("--sources", default=str(repo_root() / "data" / "sources.csv"))
    up.add_argument("--takedowns", default=str(repo_root() / "data" / "takedowns.csv"))
    up.add_argument("--baseline", default=str(repo_root() / "data" / "update-baseline.json"))
    up.add_argument("--window", type=int, default=30, help="days looked back (default: 30)")
    up.add_argument("--max-mb", type=float, default=300, help="the run's byte budget, in MB")
    up.add_argument("--max-mb-per-source", type=float, default=100, help="each source's, in MB")
    up.add_argument(
        "--max-shrink", type=float, default=0.01, help="stop if rows fall by more (0.01 = 1%%)"
    )
    up.add_argument("--open-takedowns", type=int, default=0, help="open takedown requests")
    up.add_argument(
        "--open-dataset-prs", type=int, default=0, help="open pull requests on the dataset"
    )
    up.add_argument("--allow-skipped", help="sources that may be skipped without a stop")
    up.add_argument(
        "--max-count-requests",
        type=int,
        default=150,
        help="requests the count check may spend on drops in one run (default: 150)",
    )
    up.add_argument("--now", help="the run's time (ISO 8601; default: now)")
    up.add_argument(
        "--dry-run", action="store_true", help="mark the build as never to be delivered"
    )
    up.add_argument(
        "--offline", action="store_true", help="replay the saved answers; send no request"
    )
    up.set_defaults(func=cmd_update)

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
