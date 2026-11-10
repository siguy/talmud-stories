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
# Any tractate with fetched text runs (scripts/fetch_tractate_pages.py --tractates <Name>).
# Until 2026-11-09 this was a closed list of four; Shas needs all 37.


def source_paths(tractate):
    """(pages, triage cache) for a tractate: the SOURCES override, else results/sefaria/<t>.json."""
    o = SOURCES.get(tractate, {})
    return (PROJECT_ROOT / o.get('pages', f'results/sefaria/{tractate}.json'),
            PROJECT_ROOT / o.get('triage', f'results/triage/{tractate}.json'))


# ---- retry with backoff (added 2026-11-09 for the Shas run) ---------------------------
# Google answers 429 ("slow down") or 503 ("too busy") under load. Before this, only Stage 2's
# first pass retried; triage raised and stopped the tractate, and the twin, stitch, continuation
# and clause-span calls failed once and were skipped. Retrying here covers every call, because
# every call goes through TokenMeter.metered. The detector code is untouched.
RETRY_STATUS = (429, 503)
RETRY_TEXT = ('RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'overloaded', 'Too Many Requests')
RETRY_WAITS = (30, 60, 120, 120)     # seconds before try 2, 3, 4, 5 -> 5 tries in all


def is_retryable(exc):
    """True for a 429/503 -- read from the exception's status code, else from its text."""
    code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    return code in RETRY_STATUS or any(t in str(exc) for t in RETRY_TEXT)


def call_with_retry(fn, tally, args=(), kwargs=None, sleep=time.sleep, waits=RETRY_WAITS):
    """Call fn; on a retryable error wait and try again. Every retry is counted in `tally`
    ('retries'), and a call that still fails after the last try is counted in
    'retries_exhausted' and re-raised -- the caller sees the real error, never an empty result
    (Lesson 21). A non-retryable error is raised at once."""
    kwargs = kwargs or {}
    for n in range(len(waits) + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 - classify, then decide
            if not is_retryable(e):
                raise
            if n == len(waits):
                tally['retries_exhausted'] += 1
                log.error('Gemini call failed after %d tries: %s', n + 1, str(e)[:200])
                raise
            tally['retries'] += 1
            log.warning('Gemini %s, retry %d/%d in %ds', getattr(e, 'code', '?'), n + 1,
                        len(waits), waits[n])
            sleep(waits[n])


def write_triage_cache(cache, name, model, labels):
    """Write the Stage 1 cache atomically: temp file, then os.replace. Two runs of one tractate
    read this file at the same moment the triage run may be rewriting it, and a half-written
    file reads as 'no labels' (a re-triage of the tractate, or worse)."""
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(cache.name + '.tmp')
    tmp.write_text(json.dumps(
        {'tractate': name, 'model': model,
         'triage_results': {r: [e.value for e in evs] for r, evs in labels.items()}},
        indent=2, ensure_ascii=False))
    os.replace(tmp, cache)


class TokenMeter:
    """Counts what each stage's Gemini calls cost, from the response's own usage_metadata.

    Wraps `client.models.generate_content` on one client instance; the detector code is
    untouched. A response without usage_metadata is counted under `unmetered`, never as zero
    tokens, so a missing count cannot read as a free call (Lesson 38). Added 2026-11-09 so
    the Shas run is priced from a measurement, not an estimate (docs/technical/shas-finder-plan.md §3)."""
    FIELDS = (('prompt_token_count', 'input'), ('candidates_token_count', 'output'),
              ('thoughts_token_count', 'thinking'))

    def __init__(self):
        self.tally = {}

    def attach(self, client, stage):
        if client is None:
            return client
        models = client.models
        orig = models.generate_content
        t = self.tally.setdefault(stage, {'calls': 0, 'unmetered': 0, 'input': 0, 'output': 0, 'thinking': 0,
                                                   'retries': 0, 'retries_exhausted': 0, 'cached_input': 0,
                                                   'model_versions': {}, 'service_tiers': {}})

        def metered(*a, **kw):
            r = call_with_retry(orig, t, a, kw)
            t['calls'] += 1
            # What Google says it served: which model, and which tier. A field the installed
            # library does not carry is recorded as 'not_reported', never guessed.
            mv = getattr(r, 'model_version', None) or 'not_reported'
            t['model_versions'][mv] = t['model_versions'].get(mv, 0) + 1
            u = getattr(r, 'usage_metadata', None)
            tier = getattr(u, 'service_tier', None) or getattr(u, 'traffic_type', None) or 'not_reported'
            tier = getattr(tier, 'value', tier)
            t['service_tiers'][str(tier)] = t['service_tiers'].get(str(tier), 0) + 1
            if u is None:
                t['unmetered'] += 1
            else:
                for src, dst in self.FIELDS:
                    t[dst] += int(getattr(u, src, None) or 0)
                t['cached_input'] += int(getattr(u, 'cached_content_token_count', None) or 0)
            return r
        models.generate_content = metered
        return client

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


def sha1_of(path):
    import hashlib
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def served_by(tally):
    """One-line summary of what Google served, from the per-stage tally: the model_version(s),
    the tier(s), and the cached input tokens (implicit caching). Feeds run_meta and the cost."""
    def merged(key):
        out = {}
        for t in tally.values():
            for k, n in t.get(key, {}).items():
                out[k] = out.get(k, 0) + n
        return out
    return {'model_version': merged('model_versions'), 'service_tier': merged('service_tiers'),
            'cached_content_token_count': sum(t.get('cached_input', 0) for t in tally.values())}


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
        # v13 dropped the gate; recording the env var there would claim an arm it ignored.
        'series_rule': (os.getenv('SERIES_RULE', '0') if hasattr(module, '_SERIES_RULE')
                        else None),
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
    from src.story_detector_v14 import _page_has_story_introducer
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
    ap.add_argument('--tractate', required=True, type=str.lower,
                    help='any tractate with fetched text in results/sefaria/<tractate>.json')
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
    from src import story_detector_v14 as detector_module  # adopted 2026-11-08 (Simon): docs/findings/2026-11-08-v14-vs-v11-yevamot.md
    V7StoryDetector = detector_module.V7StoryDetector

    src, cache = source_paths(args.tractate)
    if not src.exists():
        log.error('no text for %s at %s -- fetch it first: '
                  'python3 scripts/fetch_tractate_pages.py --tractates %s',
                  args.tractate, src, args.tractate.title())
        return 1
    meter = TokenMeter()
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
    cached = load_triage_cache(cache)
    if cached:
        log.info('triage cache: %d pages from %s', len(cached), cache.name)
    todo = plan_triage(pages, cached, args.retriage)
    if todo:
        triager = make_triager(EventTriager, args)
        meter.attach(triager.client, 'stage1')
        if not triager.client:
            log.error('no Gemini client — set GOOGLE_API_KEY'); return 1
        log.info('Stage 1: triaging %d page(s) not in cache', len(todo))

        def write_cache():
            write_triage_cache(cache, name, args.model, cached)

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
    meter.attach(detector.client, 'stage2_and_4')

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
    # Stage 1 tokens are this invocation's only: cached pages cost nothing now.
    results['run_meta']['tokens'] = meter.tally
    results['run_meta'].update(served_by(meter.tally))
    # Fingerprints of the two inputs that must not move between run 1 and run 2 (G3, G4): the
    # triage cache this run read, and the detector file it ran. git_rev flips on any commit.
    results['run_meta']['triage_sha1'] = sha1_of(cache) if cache.exists() else None
    results['run_meta']['detector_sha1'] = sha1_of(detector_module.__file__)
    log.info('tokens: %s', json.dumps(meter.tally))
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
