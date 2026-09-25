"""The twin pass: asks about the segment next door, adds only, fails loudly.

Guards three things the 2026-09-07/09 attempt got wrong:
  - the detection prompt itself must be untouched by the gate (a splice into it once
    sent `{few_shot_section}` to the model as literal text);
  - a failed call must add nothing and be counted, never read as "no twin here";
  - the pass may ADD a story beside an existing one; it may never move or drop one.
"""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.story_detector_v11 as mod  # noqa: E402
from src.event_triage import EventType  # noqa: E402

N, V, D = EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.DELIBERATION


@pytest.fixture(autouse=True)
def _labelled_trigger(monkeypatch):
    """The mechanics below are written against the labelled trigger, so they can show
    a label being ignored. The shipped default is `all` -- pinned separately."""
    monkeypatch.setenv('TWIN_TRIGGER', 'labelled')


def test_the_pass_is_on_by_default_and_asks_every_neighbour(monkeypatch):
    """ON since 2026-09-25, trigger `all` (the labelled one cannot see Yevamot 121b).
    Turning either back is a detector change and needs its own measurement."""
    monkeypatch.delenv('TWIN_PASS', raising=False)
    monkeypatch.delenv('TWIN_TRIGGER', raising=False)
    assert (mod.TWIN_PASS_DEFAULT, mod.TWIN_TRIGGER_DEFAULT) == ('1', 'all')
    d = _detector()
    cands = d._twin_candidates([{'start_segment': 2, 'end_segment': 2}],
                               [D, D, N, D, D], n_segments=5)
    assert [c['segment'] for c in cands] == [1, 3]


def test_all_trigger_asks_a_neighbour_with_no_label(monkeypatch):
    """Found by the default flip, 2026-09-25: under `all`, a caller with fewer labels than
    segments crashed the candidate builder instead of asking."""
    monkeypatch.setenv('TWIN_TRIGGER', 'all')
    cands = _detector()._twin_candidates([{'start_segment': 1, 'end_segment': 1}],
                                         [D, N], n_segments=3)
    assert [(c['segment'], c['label']) for c in cands] == [(0, D.value), (2, None)]


def test_the_question_carries_jeffs_2026_09_23_rejections():
    """Every twin-pass addition Jeff rejected on 2026-09-23 was one of these shapes
    (docs/STORY_RULES.md R-B4, R-C5, R-S1). Dropping one from the question should be a
    decision, not an edit that slips through."""
    segs = [{'hebrew': 'א', 'english': 'a'}] * 3
    prompt = _detector()._twin_prompt('X 1a', segs, 1, 1, 2)
    for phrase in ("the Gemara's commentary ON story A",
                   'a bare report of what someone did',
                   'a description of who sat where',
                   'actors are biblical figures'):
        assert phrase in prompt, phrase


def _detector():
    d = mod.V7StoryDetector.__new__(mod.V7StoryDetector)
    d.ground_truth = None
    d.ground_truth_db = None
    return d


def test_candidates_are_adjacent_uncovered_and_triggered():
    d = _detector()
    stories = [{'start_segment': 5, 'end_segment': 6}]
    labels = [D, D, D, D, N, N, N, V, D, D]
    #                       ^4 ^5 ^6 ^7
    cands = d._twin_candidates(stories, labels, n_segments=10)
    assert [c['segment'] for c in cands] == [4, 7]
    assert all(c['beside'] == (5, 6) for c in cands)


def test_candidate_inside_another_story_is_not_asked():
    d = _detector()
    stories = [{'start_segment': 5, 'end_segment': 6}, {'start_segment': 7, 'end_segment': 7}]
    labels = [D] * 4 + [N, N, N, N, N, D]
    cands = d._twin_candidates(stories, labels, n_segments=10)
    # 7 is covered by the second story; 4 and 8 are the free neighbours
    assert sorted(c['segment'] for c in cands) == [4, 8]


def test_deliberation_neighbour_is_not_asked():
    d = _detector()
    cands = d._twin_candidates([{'start_segment': 2, 'end_segment': 2}],
                               [D, D, N, D, D], n_segments=5)
    assert cands == []


def test_page_edges_are_respected():
    d = _detector()
    cands = d._twin_candidates([{'start_segment': 0, 'end_segment': 0}], [N, N], n_segments=2)
    assert [c['segment'] for c in cands] == [1]


def test_failed_call_adds_nothing_and_is_counted(monkeypatch):
    d = _detector()
    d._call_google = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom'))
    segs = [{'hebrew': 'א', 'english': 'a'}] * 4
    out = d._find_adjacent_twins('X 1a', segs, [D, N, N, D],
                                 [{'start_segment': 1, 'end_segment': 1}])
    assert out == []
    assert d.twin_failures == [('X 1a', 2)]


def test_unreadable_verdict_adds_nothing_and_is_counted():
    d = _detector()
    d._call_google = lambda *a, **k: '{"verdict": "maybe"}'
    segs = [{'hebrew': 'א', 'english': 'a'}] * 4
    out = d._find_adjacent_twins('X 1a', segs, [D, N, N, D],
                                 [{'start_segment': 1, 'end_segment': 1}])
    assert out == []
    assert d.twin_failures == [('X 1a', 2)]


def test_separate_incident_is_added_beside_and_only_there():
    d = _detector()
    d._call_google = lambda *a, **k: (
        '{"verdict": "separate_incident", "classification": "YES", "reason": "r"}')
    segs = [{'hebrew': 'א', 'english': 'a'}] * 4
    out = d._find_adjacent_twins('X 1a', segs, [D, N, N, D],
                                 [{'start_segment': 1, 'end_segment': 1}])
    assert out == [{'start_segment': 2, 'end_segment': 2, 'classification': 'YES',
                    'source': 'twin_pass', 'twin_of': [1, 1], 'reasoning': 'r',
                    'one_sentence_summary': 'r'}]
    assert d.twin_verdicts[0]['verdict'] == 'separate_incident'


def test_same_story_or_not_a_story_adds_nothing():
    for verdict in ('same_story', 'not_a_story'):
        d = _detector()
        d._call_google = lambda *a, **k: '{"verdict": "%s"}' % verdict
        segs = [{'hebrew': 'א', 'english': 'a'}] * 4
        assert d._find_adjacent_twins('X 1a', segs, [D, N, N, D],
                                      [{'start_segment': 1, 'end_segment': 1}]) == []
        assert not getattr(d, 'twin_failures', [])


def test_gate_does_not_touch_the_detection_prompt(monkeypatch):
    """TWIN_PASS must not change a single byte of the page-level prompt."""
    import json
    pages = json.loads(Path('results/sefaria/yevamot.json').read_text())
    pages = pages['pages'] if isinstance(pages, dict) else pages
    page = next(p for p in pages if p['ref'] == 'Yevamot 121b')
    tri = json.loads(Path('results/triage/yevamot.json').read_text())
    labels = [EventType(l) for l in tri.get('triage_results', tri)['Yevamot 121b']]

    def build(flag):
        monkeypatch.setenv('TWIN_PASS', flag)
        importlib.reload(mod)
        d = mod.V7StoryDetector.__new__(mod.V7StoryDetector)
        d.ground_truth = None
        d.ground_truth_db = None
        return mod.V7StoryDetector.build_detection_prompt(
            d, 'Yevamot 121b', page['segments'], labels, None, None)

    assert build('0') == build('1')
