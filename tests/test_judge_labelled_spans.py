"""The consensus judge: a failed or invalid answer is COUNTED, never scored (Lesson 21).

Written before the judge itself (work/2026-09-28-consensus-1-test-the-bet.md, step 2),
and watched fail. Every backend here is a stub -- no API key, no network, milliseconds.

What is pinned:
  * a backend that raises, refuses, returns garbage, returns a verdict outside the
    vocabulary, or cites a segment outside the passage yields an outcome that is NOT
    `ok` and carries no verdict;
  * the scorer never reads a verdict off a non-`ok` row: failures shrink the
    denominator and are reported as failures, they do not become `not` or `unsure`;
  * the label builder refuses a review file it has not been told about (Lesson 38).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    'judge_labelled_spans', ROOT / 'scripts' / 'judge_labelled_spans.py')
judge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judge)


SPAN = {
    'id': 'test:Gittin 19a_16-16', 'tractate': 'Gittin',
    'cells': [['Gittin 19a', 16]],
}
# Passage numbering: context before = 1, passage = 2, context after = 3.
PASSAGE_NUMBERS = {2}


def _ok(verdict='story', segments=(2,), rules=('R-C5',)):
    return json.dumps({'verdict': verdict, 'segments': list(segments),
                       'rules': list(rules), 'reason': 'stub'})


@pytest.mark.parametrize('behaviour, expected', [
    (RuntimeError('injected API failure'), 'failed'),
    (judge.Refusal('refusal'), 'refused'),
    ('I am sorry, I cannot do that.', 'invalid'),
    ('', 'invalid'),
    (_ok(verdict='maybe'), 'invalid'),                 # outside the vocabulary
    (_ok(segments=(2, 7)), 'invalid'),                 # a segment outside the passage
    (_ok(segments=(1,)), 'invalid'),                   # a CONTEXT segment is not the passage
    (_ok(verdict='story', segments=()), 'invalid'),    # a story must say where it is
    (json.dumps({'verdict': 'story'}), 'invalid'),     # fields missing
])
def test_a_bad_answer_is_counted_and_carries_no_verdict(behaviour, expected):
    def backend(_system, _user):
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour

    out = judge.ask(backend, 'SYSTEM', 'USER', PASSAGE_NUMBERS)
    assert out['outcome'] == expected
    assert out['verdict'] is None, 'a failed call must never carry a verdict'


def test_a_good_answer_is_ok():
    out = judge.ask(lambda s, u: _ok(), 'SYSTEM', 'USER', PASSAGE_NUMBERS)
    assert out['outcome'] == 'ok'
    assert out['verdict'] == 'story'
    assert out['segments'] == [2]


def test_not_may_name_no_segments():
    out = judge.ask(lambda s, u: _ok(verdict='not', segments=()), 'S', 'U', PASSAGE_NUMBERS)
    assert out['outcome'] == 'ok' and out['verdict'] == 'not'


def _row(label, g, c, g_outcome='ok', c_outcome='ok', tractate='Gittin', kind='review'):
    return {'id': f'{label}-{g}-{c}-{g_outcome}-{c_outcome}', 'tractate': tractate,
            'kind': kind, 'label': label,
            'answers': {
                'gemini': {'outcome': g_outcome, 'verdict': g if g_outcome == 'ok' else None},
                'claude': {'outcome': c_outcome, 'verdict': c if c_outcome == 'ok' else None}}}


def test_failures_shrink_the_denominator_and_never_count_as_agreement_or_error():
    rows = [
        _row('no', 'not', 'not'),                       # agree, right
        _row('no', 'story', 'story'),                   # agree, WRONG on his no
        _row('no', None, 'story', g_outcome='failed'),  # must not count anywhere
        _row('no', None, None, g_outcome='invalid', c_outcome='refused'),
        _row('yes', 'story', 'not'),                    # split
    ]
    s = judge.summarise(rows, ('gemini', 'claude'))
    pooled = s['pooled']
    assert pooled['both_answered'] == 3
    assert pooled['models_agree'] == 2
    assert pooled['agreed_on_his_no'] == 2
    assert pooled['agreed_story_on_his_no'] == 1
    assert pooled['failures'] == {'gemini': {'failed': 1, 'invalid': 1},
                                  'claude': {'refused': 1}}


def test_unsure_is_never_agreement():
    s = judge.summarise([_row('no', 'unsure', 'unsure')], ('gemini', 'claude'))
    assert s['pooled']['both_answered'] == 1
    assert s['pooled']['models_agree'] == 0


def test_the_label_builder_refuses_an_unknown_review_file(tmp_path, monkeypatch):
    (tmp_path / 'validation' / 'feedback').mkdir(parents=True)
    (tmp_path / 'validation' / 'feedback' / 'surprise_round.json').write_text('{}')
    with pytest.raises(judge.UnaccountedFile):
        judge.account_for_review_files(tmp_path)


def test_eruvin_is_never_a_source():
    assert 'Eruvin' not in judge.TRACTATES
    for paths in judge.TEXT_SOURCES.values():
        assert not any('eruvin' in p.lower() for p in paths)
