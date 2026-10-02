"""The decision table on the cases Jeff ruled on, as feature answers (STORY_RULES precedents),
and the panel answer validator. No model calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from src.consensus.decide import decide, blocking, FEATURES  # noqa: E402
import run_rule_panel as rp  # noqa: E402

STORY = dict(actual='yes', event_beyond_speech='yes', conflict='n_a', response_or_consequence='yes',
             custom='no', event_after_custom='n_a', alluded_only='no', commentary='no', biblical_actors='no')


def f(**kw):
    return {**STORY, **kw}


def test_cow_case_is_a_story():                      # R-C0, Jeff 2026-07-06
    assert decide(STORY)[0] == 'story'


def test_hypothetical_is_not():                      # R-C0
    assert decide(f(actual='no'))[:2] == ('not', 'actual')


def test_bare_report_is_not():                       # R-C5, Yevamot 15a etrog
    assert decide(f(response_or_consequence='no'))[:2] == ('not', 'response_or_consequence')


def test_speech_with_conflict_is_borderline():       # R-C2
    assert decide(f(event_beyond_speech='no', conflict='yes'))[0] == 'borderline'


def test_speech_without_conflict_is_not():           # R-C2
    assert decide(f(event_beyond_speech='no', conflict='no'))[:2] == ('not', 'conflict')


def test_custom_then_one_day_is_a_story():           # R-C3, Gittin 57a Beitar
    assert decide(f(custom='yes', event_after_custom='yes'))[0] == 'story'


def test_custom_alone_is_ours():                     # our note, flagged as ours
    v, judge, rule, ours = decide(f(custom='yes', event_after_custom='no'))
    assert (v, judge, ours) == ('not', 'event_after_custom', True)


def test_commentary_is_not():                        # R-B4
    assert decide(f(commentary='yes'))[0] == 'not'


def test_alluded_is_ours():
    assert decide(f(alluded_only='yes'))[3] is True


def test_biblical_story_is_out_of_scope():           # R-S1
    assert decide(f(biblical_actors='yes'))[0] == 'out_of_scope'


def test_unsure_on_the_path_is_unsure_not_a_guess():
    assert decide(f(actual='unsure'))[:2] == ('unsure', 'actual')
    assert decide(f(event_beyond_speech='unsure'))[0] == 'unsure'


def test_blocking_lists_every_reason():
    b = blocking(f(commentary='yes', response_or_consequence='no'))
    assert {x[0] for x in b} == {'commentary', 'response_or_consequence'}


def _answer(**over):
    feats = {k: {'answer': v, 'reason': 'r'} for k, v in STORY.items()}
    feats.update(over)
    return json.dumps({'features': feats, 'segments': [2]})


def test_validator_accepts_and_decides():
    out = rp.ask_panel(lambda s, u: _answer(), 'sys', 'prompt', {2})
    assert out['outcome'] == 'ok' and out['verdict'] == 'story'


def test_validator_counts_a_missing_feature_as_invalid():
    raw = json.loads(_answer()); del raw['features']['commentary']
    out = rp.ask_panel(lambda s, u: json.dumps(raw), 'sys', 'prompt', {2})
    assert out['outcome'] == 'invalid' and out['verdict'] is None


def test_validator_counts_a_failed_call_as_failed():
    def boom(s, u):
        raise RuntimeError('503')
    assert rp.ask_panel(boom, 'sys', 'prompt', {2})['outcome'] == 'failed'


def test_validator_rejects_context_segments():
    out = rp.ask_panel(lambda s, u: _answer().replace('[2]', '[1]'), 'sys', 'prompt', {2})
    assert out['outcome'] == 'invalid'


def test_every_feature_is_asked_in_the_prompt():
    text = rp.PROMPT_PATH.read_text()
    assert all(f'`{k}`' in text for k in FEATURES)
