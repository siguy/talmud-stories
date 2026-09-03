#!/usr/bin/env python3
"""
Run the full v11 pipeline on a tractate we have fetched but never detected on.

Stage 1 (event triage) -> Stage 2 (constrained detection) -> Stage 4 (merge,
stitch, Mishnah filter, snap, trim, Wave 5 clause spans).

Reads `results/sefaria/<tractate>.json` (fetched 2026-08-30, never re-fetched),
caches triage to `results/triage/<tractate>.json` and Stage 2 to
`results/stage2/<tractate>.json`, writes the run to
`results/v11/<tractate>/<tractate>_v11.json`.

Both caches checkpoint every CHECKPOINT pages, so a crash resumes instead of
restarting. A Stage 2 page is reused only if the prompt that produced it is
unchanged, and a page the model FAILED on is never cached — see
tests/test_stage2_checkpoint.py.

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [new_tractate] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

MODEL = 'gemini-3-flash-preview'
CHECKPOINT = 10  # pages between cache writes, Stage 1 and Stage 2 alike
DELAY = 0.5
KNOWN = ('gittin', 'yevamot', 'eruvin')

STAGE2_SCHEMA = 'stage2-cache-1'


def stage2_header(tractate, name, model, thinking, detector_module):
    """The identity of the run a Stage 2 cache belongs to.

    Every field here can change what the model is asked or which model answers, so a
    cache whose header disagrees with the run is refused rather than blended. The
    per-page digest (`stage2_cache_digest`) is the fine-grained check; this is the
    coarse one, and it is the one a human can read.
    """
    return {'schema_version': STAGE2_SCHEMA, 'tractate': tractate, 'name': name,
            'model': model, 'thinking_level': thinking, 'detector': detector_module}


def load_stage2_cache(path, header):
    """Return `ref -> {digest, stories, span_repairs}`, or raise on a header mismatch.

    Refuses rather than falls back: a cache from another model or another detector
    silently blended into this run would put two detectors' output in one file with
    nothing on its face to say so. Nothing under results/ is ever deleted here — the
    message tells the operator to move the file aside or pass --stage2-cache.
    """
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    got = {k: doc.get(k) for k in header}
    if got != header:
        differ = {k: (header[k], got[k]) for k in header if header[k] != got[k]}
        raise SystemExit(
            f'Stage 2 cache {path} does not belong to this run: '
            + '; '.join(f'{k}: run has {r!r}, cache has {c!r}' for k, (r, c) in differ.items())
            + f'. Move it aside or pass --stage2-cache <other path>; '
              f'--fresh-stage2 ignores it. Nothing is deleted automatically.')
    pages = doc.get('pages', {})
    if not isinstance(pages, dict):
        raise SystemExit(f'Stage 2 cache {path}: "pages" is {type(pages).__name__}, '
                         f'expected an object keyed by ref')
    return pages


def write_stage2_cache(path, header, pages):
    """Atomic write: a partial file must never be readable as a complete one.

    The cache is rewritten whole to a sibling temp file, flushed and fsynced, then
    `os.replace`d — which is atomic on POSIX, so a reader sees either the previous
    complete cache or the new complete one, never a truncated JSON document. A crash
    mid-write therefore costs at most the pages since the last checkpoint, which is the
    same thing a crash mid-run costs.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({**header, 'pages': pages}, indent=2, ensure_ascii=False)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


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
    ap.add_argument('--thinking', default=None, help='low|medium|high (Gemini 3.x)')
    ap.add_argument('--delay', type=float, default=DELAY)
    ap.add_argument('--retriage', action='store_true',
                    help='re-run Stage 1 even if a cache exists (costs money)')
    ap.add_argument('--stage2-cache',
                    help='default: results/stage2/<tractate>.json')
    ap.add_argument('--fresh-stage2', action='store_true',
                    help='ignore any Stage 2 cache and re-detect every page '
                         '(costs money; the cache is still written, never deleted)')
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

    # ---- Stage 2 checkpoint ---------------------------------------------
    # Stage 2 held every page in memory until the tractate finished, so one raise
    # discarded the whole spend -- twice on Yevamot, 2026-09-03, the second time at
    # page 35 of 106. Same shape of fix as Stage 1's above: write every CHECKPOINT
    # pages, and write once more on the way out of a failure.
    s2_path = Path(args.stage2_cache) if args.stage2_cache else (
        PROJECT_ROOT / 'results' / 'stage2' / f'{args.tractate}.json')
    s2_header = stage2_header(args.tractate, name, args.model, args.thinking,
                              V7StoryDetector.__module__.rsplit('.', 1)[-1])
    s2_pages = {} if args.fresh_stage2 else load_stage2_cache(s2_path, s2_header)
    if s2_pages:
        log.info('Stage 2 cache: %d page(s) from %s — a page is only reused if the '
                 'prompt it was produced from is unchanged', len(s2_pages), s2_path.name)
    resume = dict(s2_pages)
    since_write = [0]

    def checkpoint(ref, digest, stories, span_repairs):
        s2_pages[ref] = {'digest': digest, 'stories': stories,
                         'span_repairs': span_repairs}
        since_write[0] += 1
        if since_write[0] >= CHECKPOINT:
            write_stage2_cache(s2_path, s2_header, s2_pages)
            since_write[0] = 0
            log.info('Stage 2 cache: %d page(s) written to %s',
                     len(s2_pages), s2_path.name)

    t0 = time.time()
    try:
        results = detector.run_pipeline(pages, triage_results=triage,
                                        delay=args.delay, tractate=name,
                                        resume_stories=resume,
                                        on_page_detected=checkpoint)
    except Exception:
        write_stage2_cache(s2_path, s2_header, s2_pages)
        log.error('run failed with %d Stage 2 page(s) cached — re-run to resume '
                  'from %s', len(s2_pages), s2_path.name)
        raise
    write_stage2_cache(s2_path, s2_header, s2_pages)
    elapsed = time.time() - t0

    results['version'] = 'v11'
    results['run_meta'] = {'model': args.model, 'thinking_level': args.thinking,
                           'elapsed_seconds': round(elapsed, 1),
                           'pages': len(pages), 'source': src.name,
                           'ground_truth': 'ketubot-only (cross-tractate)',
                           # On its face, so a run assembled partly from a cache is
                           # never mistaken for a fresh sample of a nondeterministic
                           # model.
                           'stage2_cache': str(s2_path.relative_to(PROJECT_ROOT))
                           if s2_path.is_relative_to(PROJECT_ROOT) else str(s2_path),
                           'stage2_resumed_pages':
                               results.get('stage2_summary', {}).get(
                                   'resumed_from_cache', 0)}
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
