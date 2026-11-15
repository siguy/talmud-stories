"""Selection and scoring logic of scripts/narrate_test.py (no model is called)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import narrate_test as nt  # noqa: E402


class FakeText:
    def __init__(self, n=10):
        self.cells = [('Ketubot 2a', i) for i in range(n)]
        self.pos = {c: i for i, c in enumerate(self.cells)}
        self.seg = {c: {'hebrew': f'h{c[1]}', 'english': f'e{c[1]}'} for c in self.cells}


def test_window_has_three_each_side_and_marks_passage():
    shown, numbered, passage = nt.window(FakeText(), [('Ketubot 2a', 4), ('Ketubot 2a', 5)])
    assert [c[1] for c in shown] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert passage == {4, 5}
    assert numbered[4] == ('Ketubot 2a', 4)


def test_window_clips_at_the_ends_of_the_text():
    shown, _, passage = nt.window(FakeText(), [('Ketubot 2a', 0)])
    assert [c[1] for c in shown] == [0, 1, 2, 3] and passage == {1}


def test_prompt_never_shows_the_segment_index_or_any_id():
    prompt, passage, shown = nt.user_prompt(FakeText(), [('Ketubot 2a', 4)])
    assert 'PASSAGE -- Ketubot 2a' in prompt and passage == {4}
    assert 'STORY_RULES' not in prompt and 'C1:' not in prompt


def test_validate_accepts_and_sorts():
    ok, err = nt.validate({'can_narrate': 'yes', 'needed_segments': [5, 3, 3]}, [1, 2, 3, 4, 5])
    assert err is None and ok['needed_segments'] == [3, 5]


def test_validate_rejects_without_scoring():
    shown = [1, 2, 3]
    assert nt.validate({'can_narrate': 'maybe', 'needed_segments': [1]}, shown)[0] is None
    assert nt.validate({'can_narrate': 'yes', 'needed_segments': [9]}, shown)[0] is None   # outside the window
    assert nt.validate({'can_narrate': 'yes', 'needed_segments': []}, shown)[0] is None
    assert nt.validate({'can_narrate': 'partial', 'needed_segments': ['1']}, shown)[0] is None
    assert nt.validate('text', shown)[0] is None
    assert nt.validate({'can_narrate': 'no', 'needed_segments': []}, shown)[1] is None


def test_predicted_span_is_min_and_max():
    numbered = {n: ('Ketubot 2a', n) for n in range(1, 9)}
    assert nt.predicted_span(numbered, [6, 3, 4]) == (('Ketubot 2a', 3), ('Ketubot 2a', 6))


def test_verdict_class_treats_invalid_as_none():
    assert nt.verdict_class({'outcome': 'invalid', 'answer': None}) is None
    assert nt.verdict_class({'outcome': 'ok', 'answer': {'can_narrate': 'partial'}}) == 'partial'
    assert nt.verdict_class(None) is None


def test_grader_class_and_combined_rule():
    assert nt.grader_class('story', 'story') == 'story'
    assert nt.grader_class('story', 'borderline') == 'borderline'
    assert nt.grader_class('not', 'not') == 'not'
    assert nt.combined_rule('story', False)
    assert nt.combined_rule('borderline', True)
    assert not nt.combined_rule('borderline', False)
    assert not nt.combined_rule('not', True)      # narrating never rescues a grader `not`


def test_precision_recall_counts_unknown_apart():
    rows = [(True, 'yes'), (True, 'no'), (True, 'borderline'), (True, 'unknown'), (False, 'yes'), (False, 'no')]
    k, called, n_yes, unk = nt.precision_recall(rows)
    assert (k, called, n_yes, unk) == (1, 3, 2, 1)


def test_boundary_set_is_blind_2005_only():
    import json
    for slug, rel in nt.TARGETS.items():
        d = json.loads((ROOT / rel).read_text())
        assert all(str(t.get('source_round', '')).startswith('jeff_2005_') for t in d['targets'])
