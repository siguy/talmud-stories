"""The new-tractate runner's Stage 1 cache rules, tested without any API call.

Each test pins one finding of docs/findings/2026-11-07-pre-eruvin-code-review.md.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.ground_truth import EventType  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    'run_new_tractate', ROOT / 'scripts' / 'run_new_tractate.py')
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

N, D, F = EventType.NARRATIVE_EVENT, EventType.DELIBERATION, EventType.TRIAGE_FAILED


def _pages(*refs):
    return [{'ref': r, 'segments': [{}]} for r in refs]


def _write_cache(path, labels):
    path.write_text(json.dumps({'triage_results': {r: [e.value for e in evs]
                                                   for r, evs in labels.items()}}))


# ---- Finding 5: --retriage must not destroy the cache -------------------
def test_retriage_with_refs_keeps_every_other_page(tmp_path):
    cache = tmp_path / 't.json'
    _write_cache(cache, {'X 1a': [D], 'X 1b': [N], 'X 2a': [D]})
    cached = runner.load_triage_cache(cache)
    todo = runner.plan_triage(_pages('X 1b'), cached, retriage=True)
    assert [p['ref'] for p in todo] == ['X 1b']
    assert set(cached) == {'X 1a', 'X 2a'}      # only the re-triaged ref was dropped


def test_retriage_without_refs_redoes_every_page(tmp_path):
    cache = tmp_path / 't.json'
    _write_cache(cache, {'X 1a': [D], 'X 1b': [N]})
    cached = runner.load_triage_cache(cache)
    todo = runner.plan_triage(_pages('X 1a', 'X 1b'), cached, retriage=True)
    assert len(todo) == 2


def test_no_retriage_only_does_pages_missing_from_cache(tmp_path):
    cache = tmp_path / 't.json'
    _write_cache(cache, {'X 1a': [D]})
    cached = runner.load_triage_cache(cache)
    todo = runner.plan_triage(_pages('X 1a', 'X 1b'), cached, retriage=False)
    assert [p['ref'] for p in todo] == ['X 1b']


def test_missing_cache_loads_empty(tmp_path):
    assert runner.load_triage_cache(tmp_path / 'nope.json') == {}


# ---- Finding 14: Stage 1 failures reach the log; failed pages get retried ----
import logging  # noqa: E402

from src.event_triage import EventTriager  # noqa: E402


def test_cached_all_failed_page_is_retriaged_without_flag(tmp_path):
    cache = tmp_path / 't.json'
    _write_cache(cache, {'X 1a': [F, F], 'X 1b': [D], 'X 2a': [F, D]})
    cached = runner.load_triage_cache(cache)
    todo = runner.plan_triage(_pages('X 1a', 'X 1b', 'X 2a'), cached, retriage=False)
    # 1a is all TRIAGE_FAILED -> retried; 2a has a real label too -> left alone
    assert [p['ref'] for p in todo] == ['X 1a']


def test_triage_failure_is_logged_not_printed(monkeypatch, caplog):
    t = EventTriager(api_key='x')
    t.client = object()
    monkeypatch.setattr(t, '_call_google', lambda prompt: 'not json at all')
    with caplog.at_level(logging.WARNING):
        out = t.triage_page('X 1a', [{'index': 0, 'english': 'a', 'hebrew': 'b'}])
    assert out == [F]                                    # still fails open
    assert any('TRIAGE FAILED on X 1a' in r.getMessage() for r in caplog.records)


def test_summary_logs_counts_and_warns_on_failed_refs(caplog):
    triage = {'X 1a': [F], 'X 1b': [D], 'X 2a': [N]}
    with caplog.at_level(logging.INFO):
        runner.log_triage_summary(triage)
    msgs = [(r.levelname, r.getMessage()) for r in caplog.records]
    assert any(l == 'WARNING' and 'X 1a' in m for l, m in msgs)
    assert any(l == 'INFO' and '3 pages' in m for l, m in msgs)


# ---- Finding 9: triage and detection share one thinking level ----
def test_triager_and_detector_get_the_same_thinking_level(monkeypatch):
    from src.story_detector_v13 import V7StoryDetector
    monkeypatch.delenv('GEMINI_THINKING_LEVEL', raising=False)
    args = runner.build_parser().parse_args(
        ['--tractate', 'gittin', '--thinking', 'low'])
    triager = runner.make_triager(EventTriager, args)
    detector = V7StoryDetector(api_key='x', model_name=args.model,
                               thinking_level=args.thinking)
    assert triager.thinking_level == detector.thinking_level == 'low'


def test_env_is_loaded_before_the_parser_defaults(monkeypatch):
    monkeypatch.delenv('GEMINI_THINKING_LEVEL', raising=False)
    calls = []
    monkeypatch.setattr(runner, 'load_env', lambda: calls.append('env'))
    monkeypatch.setattr(runner, 'default_thinking_level',
                        lambda: calls.append('default') or None)
    runner.build_parser()
    assert calls[:2] == ['env', 'default']


# ---- Finding 6: run_meta carries the run's configuration ----
class _FakeDetector:
    resumed_pages = 0
    stage2_errors = []
    truncated_responses = [900, 1200]
    empty_responses = ['NO_CANDIDATES']
    twin_failures = [('X 1a', 3)]
    twin_verdicts = [{}, {}, {}]
    pass2_failures = ['X 2b']

    def _stage2_fingerprint(self):
        return 'abc123'


def test_run_meta_carries_the_configuration(monkeypatch):
    from src import story_detector_v13 as mod
    monkeypatch.setenv('TWIN_PASS', '0')
    monkeypatch.delenv('TWIN_TRIGGER', raising=False)
    args = runner.build_parser().parse_args(
        ['--tractate', 'gittin', '--refs', 'X 1a', '--retriage'])
    meta = runner.build_run_meta(
        args, _FakeDetector(), mod, elapsed=12.34, pages=[{}], src_name='s.json',
        triage_summary={'failed': 1, 'failed_refs': ['X 1a']})
    for key in ('detector_module', 'twin_pass', 'twin_trigger', 'twin_reach',
                'series_rule', 'stage2_fingerprint', 'git_rev', 'refs', 'retriage',
                'triage_failed', 'truncated_responses', 'empty_responses',
                'twin_failures', 'twin_verdicts', 'pass2_failures',
                'model', 'thinking_level', 'stage2_errors', 'resumed_pages'):
        assert key in meta, key
    assert meta['detector_module'] == mod.__name__
    assert meta['twin_pass'] == '0'                       # env wins
    assert meta['twin_trigger'] == mod.TWIN_TRIGGER_DEFAULT  # module default otherwise
    assert meta['stage2_fingerprint'] == 'abc123'
    assert meta['refs'] == 'X 1a' and meta['retriage'] is True
    assert meta['triage_failed'] == {'count': 1, 'refs': ['X 1a']}
    assert meta['truncated_responses'] == 2 and meta['twin_verdicts'] == 3
    assert meta['twin_failures'] == [['X 1a', 3]] and meta['pass2_failures'] == ['X 2b']
    json.dumps(meta)                                      # must serialise


def test_version_comes_from_the_module_name():
    from src import story_detector_v13 as mod
    assert runner.version_of(mod) == 'v13'


# ---- P3: the logged skip rate counts what Stage 2 really skips ----
def test_summary_does_not_count_introducer_pages_as_skipped(caplog):
    triage = {'X 1a': [D], 'X 1b': [D]}            # Stage 1 would skip both
    pages = [{'ref': 'X 1a', 'segments': [{'hebrew': 'עובדא הוה'}]},
             {'ref': 'X 1b', 'segments': [{'hebrew': 'מעשה בחסיד אחד'}]}]  # introducer
    with caplog.at_level(logging.INFO):
        runner.log_triage_summary(triage, pages)
    assert any('1 skipped, 1 kept' in r.getMessage() for r in caplog.records)
