"""Deduplication across the corpus.

Three steps, in order:

1. **Canonical URL.** Rows with the same ``id`` (the hash of the canonical URL) are the same
   article: the first one (earliest publication, then registry order) is kept, the rest are
   dropped and counted.
2. **Text hash.** Rows with the same ``content_hash`` under different URLs are the same text:
   the earliest is kept, the rest are dropped and counted.
3. **Near-duplicates.** Never dropped, only flagged. Character 5-gram shingles (lowercased text,
   whitespace collapsed) are hashed with a deterministic rolling hash, MinHash signatures go
   through LSH banding to find candidate pairs, and each candidate's exact Jaccard similarity
   is computed. The flag threshold is chosen from the measured distribution.

Needs the ``corpus`` extra (numpy, pyarrow).
"""

from __future__ import annotations

import itertools
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SHINGLE = 5
PERMUTATIONS = 64
BANDS = 16
ROWS = PERMUTATIONS // BANDS
MAX_BUCKET = 200
_BASE = np.uint64(1_000_003)
_SPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _SPACE.sub(" ", text.lower()).strip()


def shingles(text: str, n: int = SHINGLE) -> np.ndarray:
    """The distinct hashed character n-grams of a text (deterministic across runs)."""
    t = normalize(text)
    if len(t) < n:
        t = t.ljust(n)
    codes = np.frombuffer(t.encode("utf-32-le"), dtype=np.uint32).astype(np.uint64)
    width = len(codes) - n + 1
    h = np.zeros(width, dtype=np.uint64)
    with np.errstate(over="ignore"):
        for j in range(n):
            h = h * _BASE + codes[j : j + width]
    return np.unique(h)


def _seeds(k: int = PERMUTATIONS) -> np.ndarray:
    rng = np.random.default_rng(20261113)
    return rng.integers(1, 2**63 - 1, size=k, dtype=np.uint64)


SEEDS = _seeds()


def minhash(sh: np.ndarray, seeds: np.ndarray = SEEDS) -> np.ndarray:
    """A MinHash signature: the minimum of a splitmix64 mix of each shingle, per seed."""
    with np.errstate(over="ignore"):
        z = sh[None, :] + seeds[:, None]
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return z.min(axis=1)


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    if not len(a) and not len(b):
        return 1.0
    inter = np.intersect1d(a, b, assume_unique=True).size
    return inter / (a.size + b.size - inter)


@dataclass
class Row:
    id: str
    source_id: str
    published_at: str
    content_hash: str
    text: str
    title: str = ""


@dataclass
class DedupResult:
    rows_in: int = 0
    kept_ids: list[str] = field(default_factory=list)
    dropped: dict[str, str] = field(default_factory=dict)  # id -> reason
    dropped_by: Counter[str] = field(default_factory=Counter)
    pairs: list[tuple[str, str, str, str, float, float]] = field(default_factory=list)
    oversized_buckets: int = 0


def exact_duplicates(rows: Iterable[Row], source_order: list[str]) -> DedupResult:
    """Steps 1 and 2: drop repeated canonical URLs, then repeated texts."""
    order = {s: i for i, s in enumerate(source_order)}
    ranked = sorted(rows, key=lambda r: (r.published_at, order.get(r.source_id, 99), r.id))
    result = DedupResult(rows_in=len(ranked))
    seen_ids: set[str] = set()
    seen_text: dict[str, str] = {}
    for r in ranked:
        if r.id in seen_ids:
            result.dropped_by[f"same_url:{r.source_id}"] += 1
            continue  # the same row id: nothing to keep twice
        seen_ids.add(r.id)
        if r.content_hash in seen_text:
            first = seen_text[r.content_hash]
            result.dropped[r.id] = f"same_text_as:{first}"
            result.dropped_by[f"same_text:{r.source_id}"] += 1
            continue
        seen_text[r.content_hash] = r.id
        result.kept_ids.append(r.id)
    return result


def candidate_pairs(signatures: dict[str, np.ndarray]) -> tuple[set[tuple[str, str]], int]:
    """LSH banding: ids sharing any band of their signature. Buckets over MAX_BUCKET ids
    (shared boilerplate) are skipped and counted."""
    pairs: set[tuple[str, str]] = set()
    oversized = 0
    for band in range(BANDS):
        buckets: dict[bytes, list[str]] = defaultdict(list)
        lo, hi = band * ROWS, (band + 1) * ROWS
        for rid, sig in signatures.items():
            buckets[sig[lo:hi].tobytes()].append(rid)
        for ids in buckets.values():
            if len(ids) < 2:
                continue
            if len(ids) > MAX_BUCKET:
                oversized += 1
                continue
            ids.sort()
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pairs.add((ids[i], ids[j]))
    return pairs, oversized


def _title_words(title: str) -> set[str]:
    return {w for w in re.findall(r"\w+", title.lower()) if len(w) > 3}


def near_duplicates(rows: dict[str, Row], kept_ids: Iterable[str]) -> tuple[list, int]:
    """Step 3: candidate pairs among the kept rows, with exact Jaccard and title overlap."""
    kept = list(kept_ids)
    # Signatures (512 bytes each) for every row; shingles only again for candidates, so memory
    # stays small.
    sigs = {rid: minhash(shingles(rows[rid].text)) for rid in kept}
    pairs, oversized = candidate_pairs(sigs)
    needed = sorted({x for pair in pairs for x in pair})
    sh = {rid: shingles(rows[rid].text) for rid in needed}
    out = []
    for a, b in sorted(pairs):
        j = jaccard(sh[a], sh[b])
        ta, tb = _title_words(rows[a].title), _title_words(rows[b].title)
        tj = len(ta & tb) / len(ta | tb) if (ta or tb) else 0.0
        out.append((a, b, rows[a].source_id, rows[b].source_id, round(j, 4), round(tj, 4)))
    return out, oversized


def histogram(pairs: list, cross_source: bool) -> list[dict[str, object]]:
    """Counts of candidate pairs by Jaccard bin, with the mean title overlap per bin."""
    edges = [round(0.05 * i, 2) for i in range(21)]
    out = []
    for lo, hi in itertools.pairwise(edges):
        sel = [
            p
            for p in pairs
            if (p[2] != p[3]) == cross_source and lo <= p[4] < (hi if hi < 1 else 1.01)
        ]
        if not sel:
            continue
        out.append(
            {
                "from": lo,
                "to": hi,
                "pairs": len(sel),
                "mean_title_overlap": round(sum(p[5] for p in sel) / len(sel), 3),
            }
        )
    return out


def read_rows(paths: Iterable[Path]) -> Iterator[Row]:
    for path in paths:
        with Path(path).open(encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                yield Row(
                    id=d["id"],
                    source_id=d["source_id"],
                    published_at=d["published_at"],
                    content_hash=d["content_hash"],
                    text=d["text"],
                    title=d.get("title", ""),
                )
