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
    with no entry is UNKNOWN, not DELIBERATION.
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
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_config import default_model, default_thinking_level  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [new_tractate] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

CHECKPOINT = 10  # pages between triage-cache writes
DELAY = 0.5
KNOWN = ('gittin', 'yevamot', 'eruvin', 'kiddushin')

# Where each tractate's text and cached Stage 1 labels live. The three new tractates were
# fetched to results/sefaria/ on 2026-08-30; Kiddushin predates that layout and keeps its
# v7-era files. Same shape either way: pages[] of {ref, segments[]}, and a triage cache
# with a `triage_results` map. Added 2026-09-15 so the twin pass could be measured on a
# tractate with cross-tractate few-shots (Ketubot's are Ketubot's own -- Critical Rule 2).
SOURCES = {
    'kiddushin': {
        'pages': 'results/v7/kiddushin_pages.json',
        'triage': 'results/v7/event_triage_kiddushin.json',
    },
}


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


def version_of(module):
    """'src.story_detector_v11' -> 'v11'. The run says which detector it ran, not which
    one this file hoped it would."""
    return module.__name__.rsplit('_', 1)[-1]


def _git_rev():
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, text=True,
                              capture_output=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def build_run_meta(args, detector, module, elapsed, pages, src_name, triage_summary):
    """Everything a later reader needs to attribute this run's numbers to a configuration.
    Counters the detector already keeps (and nothing wrote down) are recorded too: a twin
    pass whose calls all failed must not look like one that found nothing (Lesson 38)."""
    return {
        'model': args.model, 'thinking_level': args.thinking,
        'elapsed_seconds': round(elapsed, 1),
        'pages': len(pages), 'source': src_name,
        'ground_truth': 'ketubot-only (cross-tractate)',
        'detector_module': module.__name__,
        'twin_pass': os.getenv('TWIN_PASS', module.TWIN_PASS_DEFAULT),
        'twin_trigger': os.getenv('TWIN_TRIGGER', module.TWIN_TRIGGER_DEFAULT),
        'twin_reach': os.getenv('TWIN_REACH', '1'),
        'series_rule': os.getenv('SERIES_RULE', '0'),
        'stage2_fingerprint': detector._stage2_fingerprint(),
        'git_rev': _git_rev(),
        'refs': args.refs, 'retriage': args.retriage,
        'triage_failed': {'count': triage_summary['failed'],
                          'refs': triage_summary['failed_refs']},
        'resumed_pages': getattr(detector, 'resumed_pages', 0),
        'stage2_errors': getattr(detector, 'stage2_errors', []),
        'truncated_responses': len(getattr(detector, 'truncated_responses', [])),
        'empty_responses': len(getattr(detector, 'empty_responses', [])),
        'twin_verdicts': len(getattr(detector, 'twin_verdicts', [])),
        'twin_failures': [list(f) for f in getattr(detector, 'twin_failures', [])],
        'pass2_failures': list(getattr(detector, 'pass2_failures', [])),
    }


def load_triage_cache(cache):
    """The existing Stage 1 cache as {ref: [EventType]}; empty if there is none.
    Always loaded -- even under --retriage -- because write_cache() dumps this dict
    wholesale, and starting it empty overwrote a whole tractate with a few pages."""
    from src.ground_truth import EventType
    if not cache.exists():
        return {}
    raw = json.loads(cache.read_text()).get('triage_results', {})
    return {ref: [EventType(v) for v in evs] for ref, evs in raw.items()}


def plan_triage(pages, cached, retriage):
    """Pages that need Stage 1. Under --retriage, drop ONLY these pages' labels from
    `cached` (in place) so every other page's label survives the cache rewrite."""
    if retriage:
        for p in pages:
            cached.pop(p['ref'], None)
    # A cached page whose labels are ALL TRIAGE_FAILED holds no judgment at all (the page
    # fails open into Stage 2); retry it on the next run rather than trust it forever.
    from src.ground_truth import EventType
    return [p for p in pages if p['ref'] not in cached
            or (cached[p['ref']]
                and all(e == EventType.TRIAGE_FAILED for e in cached[p['ref']]))]


def log_triage_summary(triage, pages=None):
    """Send Stage 1's counts to project.log -- failed pages by name.

    With `pages`, "skipped" uses the predicate run_pipeline uses: should_skip_page AND no
    canonical story introducer on the page (the lexical override forces Stage 2 anyway)."""
    from src.event_triage import EventTriager
    from src.story_detector_v11 import _page_has_story_introducer
    s = EventTriager.summarize_triage(triage)
    if pages is not None:
        by_ref = {p['ref']: p for p in pages}
        s['skipped'] = sum(1 for ref, evs in triage.items()
                           if EventTriager.should_skip_page(evs)
                           and not (ref in by_ref and _page_has_story_introducer(by_ref[ref])))
        s['kept'] = s['total_pages'] - s['skipped']
        s['skip_rate'] = f"{100 * s['skipped'] / max(s['total_pages'], 1):.0f}%"
    log.info('Stage 1 summary: %d pages, %d skipped, %d kept (%s skip rate), %d failed',
             s['total_pages'], s['skipped'], s['kept'], s['skip_rate'], s['failed'])
    if s['failed_refs']:
        log.warning('Stage 1 FAILED on %d page(s), kept open for Stage 2: %s',
                    s['failed'], s['failed_refs'])
    return s


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


def build_parser():
    """Env first: --model and --thinking defaults read GEMINI_MODEL / GEMINI_THINKING_LEVEL,
    which live in .env. Building the parser before load_env() read them too early."""
    env = load_env()
    log.info('env loaded from %s', env or 'the environment only')
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, choices=KNOWN)
    ap.add_argument('--refs', help='comma-separated refs; default is every fetched page')
    ap.add_argument('--output', help='default: results/v11/<tractate>/<tractate>_v11.json')
    ap.add_argument('--triage-only', action='store_true')
    ap.add_argument('--model', default=default_model())
    ap.add_argument('--thinking', default=default_thinking_level(),
                    help='low|medium|high (Gemini 3.x)')
    ap.add_argument('--delay', type=float, default=DELAY)
    ap.add_argument('--retriage', action='store_true',
                    help='re-run Stage 1 for the --refs pages (all pages if no --refs); '
                         'other pages keep their cached labels (costs money)')
    return ap



def make_triager(EventTriager, args):
    """Stage 1 must reason at the same depth as Stage 2 (finding 9)."""
    return EventTriager(model_name=args.model, thinking_level=args.thinking)


def main():
    args = build_parser().parse_args()

    from src.event_triage import EventTriager
    from src.ground_truth import GroundTruthDB, EventType
    from src import story_detector_v11 as detector_module
    V7StoryDetector = detector_module.V7StoryDetector

    override = SOURCES.get(args.tractate, {})
    src = PROJECT_ROOT / override.get('pages', f'results/sefaria/{args.tractate}.json')
    data = json.loads(src.read_text())
    pages = data['pages'] if isinstance(data, dict) else data
    name = (data.get('tractate') if isinstance(data, dict) else None) or args.tractate.title()
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
    cache = PROJECT_ROOT / override.get('triage', f'results/triage/{args.tractate}.json')
    cached = load_triage_cache(cache)
    if cached:
        log.info('triage cache: %d pages from %s', len(cached), cache.name)
    todo = plan_triage(pages, cached, args.retriage)
    if todo:
        triager = make_triager(EventTriager, args)
        if not triager.client:
            log.error('no Gemini client — set GOOGLE_API_KEY'); return 1
        log.info('Stage 1: triaging %d page(s) not in cache', len(todo))

        def write_cache():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(
                {'tractate': name, 'model': args.model,
                 'triage_results': {r: [e.value for e in evs] for r, evs in cached.items()}},
                indent=2, ensure_ascii=False))

        # Checkpoint every CHECKPOINT pages. Writing the cache only at the end
        # means one bad page throws away the whole tractate's Stage 1 spend --
        # which is what happened on Yevamot, at page 228 of 242. A re-run now
        # resumes from the cache instead of starting over.
        try:
            for i in range(0, len(todo), CHECKPOINT):
                cached.update(triager.triage_all_pages(todo[i:i + CHECKPOINT],
                                                       delay=args.delay))
                write_cache()
                log.info('triage cache: %d/%d page(s) done', len(cached), len(pages))
        except Exception:
            write_cache()
            log.error('Stage 1 failed after %d cached page(s) — re-run to resume '
                      'from %s', len(cached), cache.name)
            raise
        log.info('triage cache written: %s (%d pages)', cache, len(cached))

    triage = {p['ref']: cached[p['ref']] for p in pages if p['ref'] in cached}
    triage_summary = log_triage_summary(triage, pages)
    if args.triage_only:
        return 0

    # ---- Stages 2 + 4 ---------------------------------------------------
    detector = V7StoryDetector(ground_truth_db=load_ground_truth(GroundTruthDB),
                               model_name=args.model, thinking_level=args.thinking)
    if not detector.client:
        log.error('no Gemini client — set GOOGLE_API_KEY'); return 1

    t0 = time.time()
    out = Path(args.output) if args.output else (
        PROJECT_ROOT / 'results' / 'v11' / args.tractate / f'{args.tractate}_v11.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    # Stage 2 checkpoints beside the output and resumes from it on a re-run of the same
    # command; removed once the run has been written in full.
    checkpoint = str(out) + '.partial.json'
    results = detector.run_pipeline(pages, triage_results=triage,
                                    delay=args.delay, tractate=name,
                                    checkpoint_path=checkpoint)
    elapsed = time.time() - t0

    results['version'] = version_of(detector_module)
    results['run_meta'] = build_run_meta(args, detector, detector_module, elapsed, pages,
                                         src.name, triage_summary)
    if results['run_meta']['resumed_pages']:
        log.warning('RESUMED %d page(s) from %s', results['run_meta']['resumed_pages'], checkpoint)
    if results['run_meta']['stage2_errors']:
        log.warning('%d page(s) have a Stage 2 error and NO verdict: %s',
                    len(results['run_meta']['stage2_errors']), results['run_meta']['stage2_errors'])
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    if os.path.exists(checkpoint):
        os.remove(checkpoint)

    stories = sum(1 for p in results['pages'] for s in p.get('stories', [])
                  if s.get('classification') != 'NOT_A_STORY')
    withheld = sum(len(p.get('mishnah_stories') or []) for p in results['pages'])
    log.info('DONE in %.0f min -> %s', elapsed / 60, out)
    log.info('%d stories, %d withheld by the Mishnah filter, %d span repair(s)',
             stories, withheld, len(results.get('span_repairs', [])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
