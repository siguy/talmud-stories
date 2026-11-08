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
