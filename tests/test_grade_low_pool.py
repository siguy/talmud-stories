"""grade_low_pool.py: what gets promoted, and how a grader's bracket numbers map back to cells.

A span is promoted only when BOTH passes validly say `story`; a missing or invalid answer is never a verdict
(Lesson 21). A span reused from calibration is looked up by its calibration id, in the matching pass.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import grade_low_pool as g  # noqa: E402
import judge_labelled_spans as j  # noqa: E402


def span(i, reuse=None):
    s = dict(id=i, tractate='Eruvin', slug='eruvin', ref='Eruvin 2a', cells=[['Eruvin 2a', 1]], pool='P3',
             run1='LOW_CONFIDENCE', run2='LOW_CONFIDENCE', summary='x')
    if reuse:
        s['reuse'] = reuse
    return s


def ok(v):
    return {'outcome': 'ok', 'verdict': v, 'rules': [], 'segments': [2], 'reason': 'r'}


def test_select_needs_both_passes_story_and_valid():
    spans = [span('a'), span('b'), span('c'), span('d'), span('e', reuse='C2:e')]
    A = {'pass1': {'a': ok('story'), 'b': ok('story'), 'c': {'outcome': 'invalid'}, 'C2:e': ok('story')},
         'pass2': {'a': ok('story'), 'b': ok('borderline'), 'c': ok('story'), 'd': ok('story'), 'C2:e': ok('story'),
                   'e': ok('not')}}
    promos, c = g.select_promotions(spans, A)
    assert [p['id'] for p in promos] == ['a', 'e']           # e read by its calibration id, not its own
    assert promos[1]['reused_from_calibration'] == 'C2:e'
    assert promos[0]['grader']['pass2']['segments'] == [2]
    assert c['unscored'] == 2 and c['scored'] == 3 and c['promoted'] == 2   # c invalid, d missing in pass1


def test_bracket_cells_match_the_prompt_numbering():
    j.TEXT_SOURCES['Eruvin'] = [str(g.T.Paths('eruvin', ROOT).text.relative_to(ROOT))]
    text = j.Text('Eruvin')
    for cells in ([list(text.cells[0])], [list(c) for c in text.cells[5:8]]):   # first cell: no leading context
        prompt, passage = j.user_prompt({'cells': cells}, text)
        numbered = g.bracket_cells(cells, text)
        for n, cell in enumerate(numbered, start=1):
            assert f'[{n}] ' in prompt and f'-- {cell[0]}\n' in prompt
        assert [list(numbered[n - 1]) for n in sorted(passage)] == cells
