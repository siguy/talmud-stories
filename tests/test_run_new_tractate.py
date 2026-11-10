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


# ---- 2026-11-09: any fetched tractate runs; every call's tokens are counted ----
def test_any_tractate_resolves_to_its_sefaria_file():
    pages, cache = runner.source_paths('berakhot')
    assert pages == ROOT / 'results' / 'sefaria' / 'berakhot.json'
    assert cache == ROOT / 'results' / 'triage' / 'berakhot.json'
    assert runner.source_paths('kiddushin')[0] == ROOT / 'results' / 'v7' / 'kiddushin_pages.json'


def test_parser_accepts_a_tractate_outside_the_old_list():
    args = runner.build_parser().parse_args(['--tractate', 'Berakhot'])
    assert args.tractate == 'berakhot'


class _Usage:
    def __init__(self, i, o, t):
        self.prompt_token_count, self.candidates_token_count, self.thoughts_token_count = i, o, t


class _Resp:
    def __init__(self, usage):
        self.usage_metadata = usage


class _Models:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate_content(self, **kw):
        return self.responses.pop(0)


class _Client:
    def __init__(self, responses):
        self.models = _Models(responses)


def test_meter_counts_tokens_and_never_reads_a_missing_count_as_zero():
    m = runner.TokenMeter()
    c = m.attach(_Client([_Resp(_Usage(100, 20, 5)), _Resp(None), _Resp(_Usage(50, 10, None))]), 'stage2_and_4')
    for _ in range(3):
        c.models.generate_content(model='x', contents='y')
    assert m.tally['stage2_and_4'] == {'calls': 3, 'unmetered': 1, 'input': 150, 'output': 30, 'thinking': 5,
                                             'retries': 0, 'retries_exhausted': 0}


def test_meter_ignores_a_missing_client():
    assert runner.TokenMeter().attach(None, 'stage1') is None


# ---- Shas pre-flight item 1: retry every Gemini call; write the triage cache atomically ----
import os  # noqa: E402


class _Err(Exception):
    def __init__(self, code, msg='boom'):
        super().__init__(msg)
        self.code = code


def _tally():
    return {'calls': 0, 'unmetered': 0, 'input': 0, 'output': 0, 'thinking': 0,
            'retries': 0, 'retries_exhausted': 0}


def test_retry_recovers_from_429_then_503_and_counts_each_retry():
    seq = [_Err(429), _Err(503), 'ok']
    waited = []

    def fn():
        v = seq.pop(0)
        if isinstance(v, Exception):
            raise v
        return v
    t = _tally()
    assert runner.call_with_retry(fn, t, sleep=waited.append) == 'ok'
    assert t['retries'] == 2 and t['retries_exhausted'] == 0
    assert waited == [30, 60]


def test_retry_gives_up_after_five_tries_and_raises_the_real_error():
    n = []

    def fn():
        n.append(1)
        raise _Err(503, 'still busy')
    t = _tally()
    try:
        runner.call_with_retry(fn, t, sleep=lambda s: None)
        assert False, 'must raise: a dead call is not an empty answer (Lesson 21)'
    except _Err as e:
        assert e.code == 503
    assert len(n) == 5 and t['retries'] == 4 and t['retries_exhausted'] == 1


def test_non_retryable_error_is_raised_at_once():
    n = []

    def fn():
        n.append(1)
        raise _Err(400, 'bad request')
    t = _tally()
    try:
        runner.call_with_retry(fn, t, sleep=lambda s: None)
        assert False
    except _Err:
        pass
    assert len(n) == 1 and t['retries'] == 0


def test_meter_wraps_every_call_with_retry(monkeypatch):
    """The wrapper installed on a client retries, and counts the retry under that stage."""
    seq = [_Err(429), type('R', (), {'usage_metadata': None})()]

    class Models:
        def generate_content(self, *a, **kw):
            v = seq.pop(0)
            if isinstance(v, Exception):
                raise v
            return v
    client = type('C', (), {'models': Models()})()
    monkeypatch.setattr(runner.time, 'sleep', lambda s: None)
    m = runner.TokenMeter()
    m.attach(client, 'stage1')
    client.models.generate_content(model='x')
    assert m.tally['stage1']['retries'] == 1 and m.tally['stage1']['calls'] == 1
    assert m.tally['stage1']['unmetered'] == 1


def test_triage_cache_write_is_atomic(tmp_path, monkeypatch):
    cache = tmp_path / 't.json'
    runner.write_triage_cache(cache, 'X', 'm', {'X 1a': [D]})
    before = cache.read_text()
    # a crash while writing the new version must leave the old file whole
    real = os.replace
    monkeypatch.setattr(runner.os, 'replace', lambda a, b: (_ for _ in ()).throw(OSError('crash')))
    try:
        runner.write_triage_cache(cache, 'X', 'm', {'X 1a': [D], 'X 1b': [N]})
    except OSError:
        pass
    monkeypatch.setattr(runner.os, 'replace', real)
    assert cache.read_text() == before
    assert json.loads(before)['triage_results'] == {'X 1a': [D.value]}
    runner.write_triage_cache(cache, 'X', 'm', {'X 1a': [D], 'X 1b': [N]})
    assert set(json.loads(cache.read_text())['triage_results']) == {'X 1a', 'X 1b'}
    assert not list(tmp_path.glob('*.tmp'))
