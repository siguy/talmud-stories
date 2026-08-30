"""Wave 5b runner: a failed call must never be recorded as a judgment.

This is the regression guard for Lesson 21. Wave 5b's runner shipped a failure
path that `continue`d an inner loop and then fell through to an unconditional
success write, so a total API outage produced stories stamped
`clause_kept_full` ("the model read this and judged all of it in-story"),
fabricated `speech_profile` rows in the dataset meant to answer Jeff's
speech-act question, and counters that summed to 12 for 5 stories.

Everything here is pure: the model is stubbed, no API key is needed, and the
runner's outputs are redirected into a tmp dir. Milliseconds.

Fixture is a real slice of `results/v10/wave4_notrim/kiddushin_v10_notrim.json`
(Lesson 9 — fixture != production), chosen to cover every outcome bucket:
6 eligible stories, one of which is the corpus's only both-sides single-clause
story (Kiddushin 8b 14-14 -> `no_clause_split`) and one the only mixed story
(Kiddushin 79b, start splits into 5 clauses, end into 1).

Run directly:  python3 -m tests.test_wave5b_runner_outcomes
Or via pytest: pytest tests/test_wave5b_runner_outcomes.py -v
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / 'tests' / 'fixtures' / 'wave5b_runner_pages.json'

# scripts/ is not a package; load the runner by path.
_spec = importlib.util.spec_from_file_location(
    'run_clause_labeling', ROOT / 'scripts' / 'run_clause_labeling.py')
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

SUCCESS_SOURCES = {'clause_roles', 'clause_kept_full'}


# --------------------------------------------------------------------------
# stubs
# --------------------------------------------------------------------------

class _StubDetector:
    """Stands in for V7StoryDetector. `behaviour` decides what every call does."""

    def __init__(self, behaviour, **_kwargs):
        self.behaviour = behaviour
        self.client = object()      # truthy: main() checks this before running
        self.calls = 0

    def _call_google(self, prompt, max_tokens=8192, json_mode=True):
        self.calls += 1
        if self.behaviour == 'raise':
            raise RuntimeError('injected API failure')
        if self.behaviour == 'garbage':
            return 'I am sorry, I cannot do that.'
        # 'ok': label clause 0 as framing and the rest narrative, so a real
        # trim is emitted on the start side and the end side is kept full.
        n_heb = prompt.count('\n  [')
        n_eng = prompt.count('\n  (')
        return json.dumps({
            'hebrew': [{'i': i, 'role': 'framing' if i == 0 else 'narrative',
                        'speech': i % 2 == 1} for i in range(n_heb)],
            'english': [{'i': i, 'role': 'framing' if i == 0 else 'narrative',
                         'speech': False, 'covers': [i] if i < n_heb else []}
                        for i in range(n_eng)],
        })

    def _parse_json_response(self, content):
        try:
            return json.loads(content)
        except ValueError:
            return None


def _run(tmp_path, behaviour, name='t', extra_argv=()):
    """Run the runner end to end with a stubbed model. Returns (spans, labels)."""
    real_root, real_detector = runner.PROJECT_ROOT, runner.V7StoryDetector
    runner.PROJECT_ROOT = Path(tmp_path)
    runner.V7StoryDetector = lambda **kw: _StubDetector(behaviour, **kw)
    argv = sys.argv
    sys.argv = ['run_clause_labeling.py', '--in', str(FIXTURE),
                '--name', name, *extra_argv]
    try:
        rc = runner.main()
    finally:
        runner.PROJECT_ROOT, runner.V7StoryDetector = real_root, real_detector
        sys.argv = argv
    assert rc == 0, f'runner exited {rc}'
    spans = json.loads((Path(tmp_path) / 'results/v11/wave5b' / f'{name}.json').read_text())
    labels_path = Path(tmp_path) / 'results/clause_labels' / f'{name}.json'
    # reassembly produces no labels of its own — it consumes them.
    labels = json.loads(labels_path.read_text()) if labels_path.exists() else None
    return spans, labels


def _stories(spans):
    return [s for p in spans['pages'] for s in p.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY']


def _processed(spans):
    """Stories the runner actually reached (it stamps every one it processes)."""
    return [s for s in _stories(spans) if 'text_span_source' in s]


# --------------------------------------------------------------------------
# the P0 guard: total outage
# --------------------------------------------------------------------------

def test_total_api_failure_is_never_a_judgment(tmp_path):
    spans, labels = _run(tmp_path, 'raise')
    stats = spans['wave5b_stats']
    processed = _processed(spans)

    assert processed, 'fixture produced no processed stories'

    # 1. No story may carry a provenance that means "the model judged this".
    sources = {s['text_span_source'] for s in processed}
    assert not (sources & SUCCESS_SOURCES), (
        f'failed run stamped success provenance: {sources}')
    assert sources <= {'skipped', 'no_clause_split'}, sources

    # 2. No derived data computed from absent inputs.
    fabricated = [s for s in processed
                  if s['text_span_source'] == 'skipped' and 'speech_profile' in s]
    assert not fabricated, f'{len(fabricated)} skipped stories carry a speech_profile'
    assert not labels['speech_profiles'], 'speech rows written for a dead run'
    # The labels file is an account of the run, so a record per story is correct
    # — but none may carry a label block, and every side must say it failed.
    for rec in labels['stories']:
        assert 'start' not in rec and 'end' not in rec, f'label block on {rec["ref"]}'
        assert set(rec['status'].values()) <= {'skipped', 'no_clause_split'}, rec['status']

    # 3. Buckets are a partition of the work.
    assert sum(stats['counts'].values()) == stats['stories_labelled'], stats['counts']
    assert len(processed) == stats['stories_labelled']

    # 4. A failed story is flagged, and carries no span.
    for s in processed:
        if s['text_span_source'] == 'skipped':
            assert s.get('needs_review') is True, 'failed story not flagged'
            assert 'text_span_start' not in s and 'text_span_end' not in s


def test_unparseable_response_is_never_a_judgment(tmp_path):
    """A model that answers but not in JSON is a failure too, not a kept-full."""
    spans, labels = _run(tmp_path, 'garbage')
    stats = spans['wave5b_stats']
    sources = {s['text_span_source'] for s in _processed(spans)}
    assert not (sources & SUCCESS_SOURCES), sources
    assert sum(stats['counts'].values()) == stats['stories_labelled'], stats['counts']
    assert not labels['speech_profiles']


# --------------------------------------------------------------------------
# the success path must partition too
# --------------------------------------------------------------------------

def test_success_run_counts_each_story_exactly_once(tmp_path):
    spans, labels = _run(tmp_path, 'ok')
    stats = spans['wave5b_stats']
    processed = _processed(spans)

    assert sum(stats['counts'].values()) == stats['stories_labelled'] == len(processed)
    assert stats['counts']['skipped'] == 0

    # Kiddushin 8b 14-14 is one clause on both sides: a named outcome that must
    # survive to the artifact, not be overwritten by the post-loop write.
    by_ref = {(p['ref'], f"{s['start_segment']}-{s['end_segment']}"): s
              for p in spans['pages'] for s in p.get('stories', [])
              if s.get('classification') != 'NOT_A_STORY'}
    no_split = by_ref[('Kiddushin 8b', '14-14')]
    assert no_split['text_span_source'] == 'no_clause_split'
    assert stats['counts']['no_clause_split'] == 1
    assert 'speech_profile' not in no_split, 'profile written with no labels'

    # Every labelled story gets a real trim (clause 0 was framing) and a profile.
    labelled = [s for s in processed if s['text_span_source'] in SUCCESS_SOURCES]
    assert labelled
    for s in labelled:
        assert 'speech_profile' in s
        assert s['speech_profile']['in_story_clauses'] > 0
    # One record per processed story; label blocks only where labels exist.
    assert len(labels['stories']) == len(processed)
    assert sum(1 for r in labels['stories'] if 'start' in r or 'end' in r) == len(labelled)
    assert len(labels['speech_profiles']) == len(labelled)


# --------------------------------------------------------------------------
# item 4: one shared emit_span -> the two paths cannot diverge
# --------------------------------------------------------------------------

def test_reassemble_matches_fresh_run(tmp_path):
    fresh, _ = _run(tmp_path, 'ok', name='fresh')
    labels_path = Path(tmp_path) / 'results/clause_labels/fresh.json'
    # reassembly must not call the model at all
    again, _ = _run(tmp_path, 'raise', name='again',
                    extra_argv=('--from-labels', str(labels_path)))

    keys = ('text_span_source', 'text_span_start', 'text_span_end',
            'needs_review', 'speech_profile')
    a = [{k: s.get(k) for k in keys} for s in _stories(fresh)]
    b = [{k: s.get(k) for k in keys} for s in _stories(again)]
    assert a == b, 'reassembled artifact differs from the fresh run'
    assert fresh['version'] == again['version']
    assert fresh['wave5b_stats']['counts'] == again['wave5b_stats']['counts']


if __name__ == '__main__':
    import tempfile
    failures = 0
    for fn in (test_total_api_failure_is_never_a_judgment,
               test_unparseable_response_is_never_a_judgment,
               test_success_run_counts_each_story_exactly_once,
               test_reassemble_matches_fresh_run):
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(td)
                print(f'PASS {fn.__name__}')
            except AssertionError as exc:
                failures += 1
                print(f'FAIL {fn.__name__}: {exc}')
            except Exception as exc:                      # noqa: BLE001
                failures += 1
                print(f'ERROR {fn.__name__}: {type(exc).__name__}: {exc}')
    sys.exit(1 if failures else 0)
