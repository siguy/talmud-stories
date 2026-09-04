#!/usr/bin/env python3
"""
Run the full v11 pipeline on a tractate we have fetched but never detected on.

Stage 1 (event triage) -> Stage 2 (constrained detection) -> Stage 4 (merge,
stitch, Mishnah filter, snap, trim, Wave 5 clause spans).

Reads `results/sefaria/<tractate>.json` (fetched 2026-08-30, never re-fetched),
caches triage to `results/triage/<tractate>.json`, writes the run to
`results/v11/<tractate>/<tractate>_v11.json`.

Two things it does NOT do, on purpose:

  - **It never invents triage labels.** Cached labels are reused as-is; a page
    with no entry is UNKNOWN, not DELIBERATION. The `--examine-all-pages` flag
    only ever ADDS pages to Stage 2 (see tests/test_examine_all_pages.py).
  - **It uses no few-shot example from the tractate it is running on.** Ground
    truth comes from Ketubot only — cross-tractate, so it cannot overfit the
    pages being scored (Lesson 2).

Usage:
  python3 scripts/run_new_tractate.py --tractate gittin --refs "Gittin 6b,Gittin 7a" \
      --output results/v11/gittin/smoke.json          # smoke test, 2 pages
  python3 scripts/run_new_tractate.py --tractate gittin                    # full run
  python3 scripts/run_new_tractate.py --tractate gittin --triage-only      # Stage 1 only
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_config import default_thinking_level  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [new_tractate] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

MODEL = 'gemini-3-flash-preview'
DELAY = 0.5
KNOWN = ('gittin', 'yevamot', 'eruvin')


def load_env():
    """Read .env from this worktree, falling back to the primary checkout —
    worktrees do not share untracked files."""
    for env in (PROJECT_ROOT / '.env', Path.home() / 'talmud-stories' / '.env'):
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip() and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return env
    return None


def load_ground_truth(GroundTruthDB):
    """Ketubot labels only. Running on Gittin/Yevamot/Eruvin, every example is
    cross-tractate, so no page being scored can appear in its own prompt."""
    db = GroundTruthDB()
    feedback = (PROJECT_ROOT / 'validation' / 'feedback' /
                'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5 = [str(PROJECT_ROOT / 'results' / 'v5' / n)
          for n in ('pages_2-39.json', 'pages_40-60.json')]
    if feedback.exists():
        db.load_from_feedback(str(feedback), v5)
        log.info('ground truth: %d entries (Ketubot, cross-tractate)', len(db.entries))
    else:
        log.warning('NO ground truth found — running without few-shot examples')
    return db


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, choices=KNOWN)
    ap.add_argument('--refs', help='comma-separated refs; default is every fetched page')
    ap.add_argument('--output', help='default: results/v11/<tractate>/<tractate>_v11.json')
    ap.add_argument('--triage-only', action='store_true')
    ap.add_argument('--model', default=MODEL)
    ap.add_argument('--thinking', default=default_thinking_level(),
                    help='low|medium|high (Gemini 3.x)')
    ap.add_argument('--delay', type=float, default=DELAY)
    ap.add_argument('--retriage', action='store_true',
                    help='re-run Stage 1 even if a cache exists (costs money)')
    args = ap.parse_args()

    env = load_env()
    log.info('env loaded from %s', env or 'the environment only')

    from src.event_triage import EventTriager
    from src.ground_truth import GroundTruthDB, EventType
    from src.story_detector_v11 import V7StoryDetector

    src = PROJECT_ROOT / 'results' / 'sefaria' / f'{args.tractate}.json'
    data = json.loads(src.read_text())
    pages = data['pages']
    name = data.get('tractate') or args.tractate.title()
    if args.refs:
        want = [r.strip() for r in args.refs.split(',')]
        pages = [p for p in pages if p['ref'] in want]
        missing = sorted(set(want) - {p['ref'] for p in pages})
        if missing:
            log.error('refs not in %s: %s', src.name, missing)
            return 1
    log.info('%s: %d pages, %d segments', name, len(pages),
             sum(len(p['segments']) for p in pages))

    # ---- Stage 1 --------------------------------------------------------
    cache = PROJECT_ROOT / 'results' / 'triage' / f'{args.tractate}.json'
    cached = {}
    if cache.exists() and not args.retriage:
        raw = json.loads(cache.read_text()).get('triage_results', {})
        cached = {ref: [EventType(v) for v in evs] for ref, evs in raw.items()}
        log.info('triage cache: %d pages from %s', len(cached), cache.name)

    todo = [p for p in pages if p['ref'] not in cached]
    if todo:
        triager = EventTriager(model_name=args.model)
        if not triager.client:
            log.error('no Gemini client — set GOOGLE_API_KEY'); return 1
        log.info('Stage 1: triaging %d page(s) not in cache', len(todo))
        fresh = triager.triage_all_pages(todo, delay=args.delay)
        cached.update(fresh)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(
            {'tractate': name, 'model': args.model,
             'triage_results': {r: [e.value for e in evs] for r, evs in cached.items()}},
            indent=2, ensure_ascii=False))
        log.info('triage cache written: %s (%d pages)', cache, len(cached))

    triage = {p['ref']: cached[p['ref']] for p in pages if p['ref'] in cached}
    skip = sum(1 for evs in triage.values() if EventTriager.should_skip_page(evs))
    log.info('Stage 1 summary: %d pages, %d skipped, %d kept (%.0f%% skip rate)',
             len(triage), skip, len(triage) - skip, 100 * skip / max(len(triage), 1))
    if args.triage_only:
        return 0

    # ---- Stages 2 + 4 ---------------------------------------------------
    detector = V7StoryDetector(ground_truth_db=load_ground_truth(GroundTruthDB),
                               model_name=args.model, thinking_level=args.thinking)
    if not detector.client:
        log.error('no Gemini client — set GOOGLE_API_KEY'); return 1

    t0 = time.time()
    results = detector.run_pipeline(pages, triage_results=triage,
                                    delay=args.delay, tractate=name)
    elapsed = time.time() - t0

    results['version'] = 'v11'
    results['run_meta'] = {'model': args.model, 'thinking_level': args.thinking,
                           'elapsed_seconds': round(elapsed, 1),
                           'pages': len(pages), 'source': src.name,
                           'ground_truth': 'ketubot-only (cross-tractate)'}
    out = Path(args.output) if args.output else (
        PROJECT_ROOT / 'results' / 'v11' / args.tractate / f'{args.tractate}_v11.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    stories = sum(1 for p in results['pages'] for s in p.get('stories', [])
                  if s.get('classification') != 'NOT_A_STORY')
    withheld = sum(len(p.get('mishnah_stories') or []) for p in results['pages'])
    log.info('DONE in %.0f min -> %s', elapsed / 60, out)
    log.info('%d stories, %d withheld by the Mishnah filter, %d span repair(s)',
             stories, withheld, len(results.get('span_repairs', [])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
