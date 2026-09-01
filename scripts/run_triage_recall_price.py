#!/usr/bin/env python3
"""
Price the triage trade: run Stage 2 on the pages Stage 1 discarded.

Capability 1 (Triage). Answers the question the capability history calls the
single highest-value untried item: "96% recall" is really 96% of the fraction
of the corpus we look at, and nobody has ever measured the rest.

Method — the only variable is the *skip decision*:

  - Pages come from `results/v10/wave4_notrim/`, whose skipped pages carry
    `skipped_by_triage: true` together with their full segment text. No refetch.
  - Event-type labels come from the shipped triage caches (`results/v7/
    event_triage_*.json`), NOT from a re-run and NOT from the all-DELIBERATION
    default that `--skip-triage` substitutes. Stage 2 therefore sees exactly the
    prompt it would have seen had the page not been skipped.
  - Cross-page context is built from the FULL page list, so a discarded page
    still sees its real neighbours.

Every skipped page is verified against the cache before any API call: the cache
entry must exist, its length must match the segment count, and
`should_skip_page()` on those labels must reproduce the shipped skip decision.
A page that fails any check is reported, not silently processed (Lesson 21 —
the buckets are a partition and the partition is asserted).

Writes to `results/v11/triage_recall/`. Never touches `wave4_notrim`.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.event_triage import EventTriager, EventType      # noqa: E402
from src.story_detector_v11 import (                      # noqa: E402
    V7StoryDetector,
    _page_has_story_introducer,
)

REPO = Path(__file__).resolve().parent.parent

RUNS = {
    'ketubot': [
        'results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
        'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json',
    ],
    'kiddushin': [
        'results/v10/wave4_notrim/kiddushin_v10_notrim.json',
    ],
}

TRIAGE_CACHES = [
    'results/v7/event_triage_2-60.json',
    'results/v7/event_triage_61-112.json',
    'results/v7/event_triage_kiddushin.json',
]


def load_triage_cache():
    """Merge the shipped triage caches into one ref -> [label] map."""
    merged = {}
    for rel in TRIAGE_CACHES:
        data = json.loads((REPO / rel).read_text())
        merged.update(data['triage_results'])
    return merged


def load_pages(tractate):
    """Full ordered page list, plus which file each page came from."""
    pages = []
    for rel in RUNS[tractate]:
        data = json.loads((REPO / rel).read_text())
        for p in data['pages']:
            pages.append(p)
    return pages


def classify_pages(pages, triage):
    """
    Partition the skipped pages into 'runnable' and each failure bucket.

    Returns (runnable, buckets) where buckets is a dict of ref-lists. The caller
    asserts the partition covers every skipped page.
    """
    runnable = []
    buckets = {
        'missing_cache': [],
        'seglen_mismatch': [],
        'would_not_skip': [],
        'has_introducer': [],
    }
    for page in pages:
        if not page.get('skipped_by_triage'):
            continue
        ref = page.get('ref', '')
        segs = page.get('segments', [])
        labels = triage.get(ref)
        if labels is None:
            buckets['missing_cache'].append(ref)
            continue
        if len(labels) != len(segs):
            buckets['seglen_mismatch'].append(ref)
            continue
        events = [EventType(l) for l in labels]
        if not EventTriager.should_skip_page(events):
            buckets['would_not_skip'].append(ref)
            continue
        if _page_has_story_introducer(page):
            buckets['has_introducer'].append(ref)
            continue
        runnable.append((page, events))
    return runnable, buckets


def build_context(pages, page_idx, triage):
    """
    Replicate the pipeline's cross-page context exactly
    (src/story_detector_v11.py, Stage 2 loop).
    """
    def render(segs, events, label):
        lines = []
        for s in segs:
            eng = re.sub(r'<[^>]+>', '', s.get('english', ''))[:300]
            heb = s.get('hebrew', '')[:200]
            idx = s.get('index', 0)
            et = events[idx] if idx < len(events) else "UNKNOWN"
            lines.append(f"[{et}] {label} Seg {idx}:\n  English: {eng}\n  Hebrew: {heb}")
        return '\n'.join(lines) if lines else None

    prev_ctx = next_ctx = None
    if page_idx > 0:
        prev_page = pages[page_idx - 1]
        prev_segs = prev_page.get('segments', [])
        if prev_segs:
            prev_ctx = render(prev_segs[-5:],
                              triage.get(prev_page.get('ref', ''), []), 'Prev')
    if page_idx < len(pages) - 1:
        next_page = pages[page_idx + 1]
        next_segs = next_page.get('segments', [])
        if next_segs:
            next_ctx = render(next_segs[:5],
                              triage.get(next_page.get('ref', ''), []), 'Next')
    return prev_ctx, next_ctx


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, choices=sorted(RUNS))
    ap.add_argument('--out-dir', default='results/v11/triage_recall')
    ap.add_argument('--delay', type=float, default=0.5)
    ap.add_argument('--limit', type=int, default=None,
                    help='process only the first N runnable pages (smoke test)')
    ap.add_argument('--dry-run', action='store_true',
                    help='verify and report the partition; make no API calls')
    args = ap.parse_args()

    triage = load_triage_cache()
    pages = load_pages(args.tractate)
    idx_of = {p.get('ref'): i for i, p in enumerate(pages)}

    n_skipped = sum(1 for p in pages if p.get('skipped_by_triage'))
    runnable, buckets = classify_pages(pages, triage)

    accounted = len(runnable) + sum(len(v) for v in buckets.values())
    assert accounted == n_skipped, (
        f"buckets are not a partition: {accounted} != {n_skipped}")

    print(f"{args.tractate}: {len(pages)} pages, {n_skipped} skipped by triage")
    print(f"  runnable: {len(runnable)}")
    for name, refs in buckets.items():
        print(f"  {name}: {len(refs)}" + (f" -> {refs}" if refs else ""))
    print(f"  segments never examined: "
          f"{sum(len(p.get('segments', [])) for p, _ in runnable)}")

    if args.dry_run:
        print("\n--dry-run: no API calls made.")
        return 0

    if args.limit:
        runnable = runnable[:args.limit]
        print(f"  --limit: processing {len(runnable)} pages")

    detector = V7StoryDetector()
    results = []
    calls = 0
    t0 = time.time()

    for i, (page, events) in enumerate(runnable):
        ref = page['ref']
        segs = page['segments']
        prev_ctx, next_ctx = build_context(pages, idx_of[ref], triage)
        print(f"  [{i+1}/{len(runnable)}] {ref} ({len(segs)} segs)...", flush=True)
        try:
            stories = detector.detect_stories(ref, segs, events, prev_ctx, next_ctx)
            error = None
        except Exception as exc:                      # noqa: BLE001
            stories, error = [], f"{type(exc).__name__}: {exc}"
            print(f"      FAILED: {error}")
        calls += 1
        real = [s for s in stories
                if s.get('classification') not in ('NOT_A_STORY', None)]
        if real:
            print(f"      -> {len(stories)} candidates, {len(real)} stories")
        results.append({
            'ref': ref,
            'segments': segs,
            'stories': stories,
            'was_skipped_by_triage': True,
            'stage2_error': error,
        })
        if args.delay:
            time.sleep(args.delay)

    out_dir = REPO / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.tractate}_skipped_stage2.json"

    n_err = sum(1 for r in results if r['stage2_error'])
    n_real = sum(len([s for s in r['stories']
                      if s.get('classification') not in ('NOT_A_STORY', None)])
                 for r in results)

    payload = {
        'tractate': args.tractate,
        'source': RUNS[args.tractate],
        'triage_caches': TRIAGE_CACHES,
        'model': getattr(detector, 'model_name', None),
        'pages_total': len(pages),
        'pages_skipped_by_triage': n_skipped,
        'pages_run': len(results),
        'partition': {k: v for k, v in buckets.items()},
        'stage2_calls': calls,
        'stage2_errors': n_err,
        'stories_proposed': n_real,
        'elapsed_seconds': round(time.time() - t0, 1),
        'pages': results,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    print(f"\nWrote {out}")
    print(f"  Stage 2 calls: {calls}  errors: {n_err}")
    print(f"  stories proposed on previously-discarded pages: {n_real}")
    if n_err:
        print("  NOTE: errors are recorded per page; a failed call is NOT a "
              "'no stories here' verdict (Lesson 21).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
