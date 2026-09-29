"""An old verdict means what it meant for the call he was SHOWN (2026-09-29).

Before the axes UI every round asked "is the detector's call correct?". A `correct` on a
NOT_A_STORY call is his NO. build_ruler.py and map_verdict_vocabularies.py read every
`correct` as "a story" until 2026-09-29 (finding 2026-09-28-consensus-phase1 sec. 8);
scripts/verdict_reading.py is now the one reading all of them share.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VR = _load('verdict_reading')
_never = lambda notes: 'unclassified'  # noqa: E731


def test_correct_on_a_not_a_story_call_is_his_no():
    assert VR.label_old('correct', 'NOT_A_STORY', '', None, _never)[0] == 'no'


def test_correct_on_a_story_call_is_his_yes():
    assert VR.label_old('correct', 'HIGH_CONFIDENCE', '', None, _never)[0] == 'yes'


def test_a_boundary_complaint_on_a_story_is_still_a_story():
    """`incorrect` + a boundary objection = it IS a story, mis-drawn (Lesson 30)."""
    label = VR.label_old('incorrect', 'YES', 'the story starts one line earlier', None,
                         lambda notes: 'boundary')[0]
    assert label == 'yes'


def test_a_bare_incorrect_is_unknown_not_no():
    assert VR.label_old('incorrect', 'YES', '', None, _never)[0] == 'unknown'


def test_the_ruler_reports_story_precision_beside_the_published_figures():
    r = json.loads((ROOT / 'results/rulers/kiddushin_ruler.json').read_text())
    rnd = r['metrics']['classification']['per_round']['kiddushin_review_2026-04-23.json']
    assert 0.66 <= rnd['precision_all_causes'] <= 0.69, 'the published 68% must stay reproducible'
    assert rnd['story_precision']['precision'] > rnd['precision_all_causes'], (
        'read against the call he was shown, boundary complaints and confirmed NOT_A_STORY '
        'calls stop counting as precision failures')


def test_simons_rounds_are_never_scored_as_the_experts():
    for t in ('ketubot', 'kiddushin', 'gittin'):
        c = json.loads((ROOT / f'results/rulers/{t}_ruler.json').read_text())['metrics']['classification']
        assert not any('prescreen' in k or 'Simon' in k for k in c['per_round']), t
        assert any('prescreen' in k for k in c['excluded_rounds']), f'{t}: excluded but not counted'


def test_the_vocabulary_map_reads_against_the_call_shown():
    m = json.loads((ROOT / 'results/rulers/verdict_vocabulary_map.json').read_text())
    assert m['reread_against_shown_call'].get('yes->no', 0) >= 87, (
        '87 of the 2026-02-05 verdicts alone are `correct` on a NOT_A_STORY call')
    feb = [r for r in m['rows'] if r['round'].startswith('v5_1_feedback_anonymous_2026-02-05')
           and r['old_verdict'] == 'correct' and r['shown'] == 'NOT_A_STORY']
    assert feb and all(r['is_story'] == 'no' for r in feb)
