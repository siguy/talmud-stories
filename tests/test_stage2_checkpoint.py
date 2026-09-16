"""Stage 2 checkpoints, resumes, and never turns a failed call into "no stories".

Before 2026-09-16 a Google 503 at page 32 of 66 discarded the whole arm; the third run
lost that way. These tests inject the failure and check three properties:
  - a resumed run is byte-identical to an uninterrupted one;
  - the resume is recorded, never silent;
  - a checkpoint from a different prompt/flags/model is refused;
  - a page that fails after retries is kept, marked, and counted.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.event_triage import EventType  # noqa: E402
from src.story_detector_v11 import V7StoryDetector  # noqa: E402

N, D = EventType.NARRATIVE_EVENT, EventType.DELIBERATION
PAGES = [{'ref': f'X {i}a', 'segments': [{'index': 0, 'hebrew': 'א', 'english': 'a'}]}
         for i in range(8)]
TRIAGE = {p['ref']: [N] for p in PAGES}


class Boom(Exception):
    code = 503


class Crash(Exception):
    """An unhandled shape -- not a server error, not retryable, kills the run."""


def _detector(monkeypatch, fail_on=None, fail_forever=False):
    """A detector whose detect_stories is deterministic and can be made to fail."""
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.client = object(); d.model_name = 'test-model'; d.thinking_level = None
    d.ground_truth = None; d.ground_truth_db = None
    d.calls = []

    def detect(ref, segments, events, prev_ctx, next_ctx):
        d.calls.append(ref)
        if ref == fail_on and (fail_forever or d.calls.count(ref) == 1):
            raise Boom('503 UNAVAILABLE')
        return [{'start_segment': 0, 'end_segment': 0, 'classification': 'YES'}]
    d.detect_stories = detect
    monkeypatch.setattr('time.sleep', lambda *_: None)
    # Stage 4 is not under test; the pipeline's post-processing needs a client only for
    # calls we do not make with one-segment pages.
    return d


def _run(d, tmp_path, checkpoint=True):
    return d.run_pipeline(PAGES, triage_results=TRIAGE, delay=0,
                          checkpoint_path=str(tmp_path / 'run.partial.json') if checkpoint else None)


def _stories(result):
    return {p['ref']: p.get('stories') for p in result['pages']}


def test_resume_is_byte_identical_and_recorded(monkeypatch, tmp_path):
    clean = _run(_detector(monkeypatch), tmp_path, checkpoint=False)

    # First run: a hard crash at page 6 (after checkpoint 5 was written).
    crashing = _detector(monkeypatch)
    inner = crashing.detect_stories
    def crash(ref, *a):
        if ref == 'X 6a':
            raise Crash('unhandled response shape')
        return inner(ref, *a)
    crashing.detect_stories = crash
    with pytest.raises(Crash):
        _run(crashing, tmp_path)
    assert (tmp_path / 'run.partial.json').exists()

    # Second run, same everything: resumes, finishes, matches the clean run.
    resumed_d = _detector(monkeypatch)
    resumed = _run(resumed_d, tmp_path)
    assert _stories(resumed) == _stories(clean)
    assert resumed_d.resumed_pages == 5, 'the five checkpointed pages were not resumed'
    assert resumed_d.calls == ['X 5a', 'X 6a', 'X 7a'], 'resumed pages were re-detected'


def test_checkpoint_from_a_different_prompt_is_refused(monkeypatch, tmp_path):
    d = _detector(monkeypatch)
    _run(d, tmp_path)           # writes a checkpoint with today's fingerprint
    ck = tmp_path / 'run.partial.json'
    blob = json.loads(ck.read_text()); blob['fingerprint'] = 'somebody-else'
    ck.write_text(json.dumps(blob))
    d2 = _detector(monkeypatch)
    _run(d2, tmp_path)
    assert d2.resumed_pages == 0
    assert len(d2.calls) == len(PAGES)


def test_transient_failure_is_retried_and_succeeds(monkeypatch, tmp_path):
    d = _detector(monkeypatch, fail_on='X 3a')      # fails once, then works
    out = _run(d, tmp_path)
    assert d.calls.count('X 3a') == 2
    assert not getattr(d, 'stage2_errors', [])
    assert _stories(out)['X 3a'][0]['classification'] == 'YES'


def test_persistent_failure_is_kept_marked_and_counted(monkeypatch, tmp_path):
    d = _detector(monkeypatch, fail_on='X 3a', fail_forever=True)
    out = _run(d, tmp_path)
    page = next(p for p in out['pages'] if p['ref'] == 'X 3a')
    assert page['stories'] == []
    assert 'failed after 3 attempts' in page['stage2_error']
    assert d.stage2_errors == ['X 3a']
    # every other page is unaffected -- the run continued
    assert sum(1 for p in out['pages'] if p.get('stories')) == len(PAGES) - 1


def test_client_error_is_not_retried(monkeypatch, tmp_path):
    class Bad(Exception):
        code = 400
    d = _detector(monkeypatch)
    def detect(ref, *a):
        raise Bad('our fault')
    d.detect_stories = detect
    with pytest.raises(Bad):
        _run(d, tmp_path)
