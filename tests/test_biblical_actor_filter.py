"""4j, the biblical-actor scope filter, matches whole names and labels what it demotes.

2026-11-07 review, finding 13. `'eli'` matched inside Eliezer and Elijah as a bare
substring, and `'samuel'` alone (prophet or amora -- ambiguous) demoted a story.
R-S1 says a passage dropped for scope carries a scope label, so a demotion now adds
`out_of_scope` / `scope_reason` beside the unchanged NOT_A_STORY classification.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.story_detector_v11 import (  # noqa: E402
    _actors_are_biblical_only, filter_biblical_actor_stories)


@pytest.mark.parametrize('evidence', [
    'R. Eliezer',
    'Eliezer',
    'Elijah appeared to Rav Kahana',
    'Samuel',
])
def test_not_demoted(evidence):
    assert _actors_are_biblical_only(evidence) is False


@pytest.mark.parametrize('evidence', [
    'Nebuchadnezzar',
    'Moses and Aaron',
    'Nebuchadnezzar, Pelatiah son of Benaiah',   # the Kiddushin 72b evidence
])
def test_demoted(evidence):
    assert _actors_are_biblical_only(evidence) is True


def _page(evidence):
    return {'ref': 'X 2a', 'stories': [{
        'start_segment': 0, 'end_segment': 0, 'classification': 'YES',
        'criteria': {'identifiable_characters': {'evidence': evidence}}}]}


def test_demotion_keeps_the_classification_vocabulary_and_adds_scope_label():
    page = _page('Moses and Aaron')
    assert filter_biblical_actor_stories([page]) == 1
    s = page['stories'][0]
    assert s['classification'] == 'NOT_A_STORY'      # readers know only the four values
    assert s['classification_pre_biblical_filter'] == 'YES'
    assert s['out_of_scope'] is True
    assert s['scope_reason'] == 'biblical_actors'


def test_not_demoted_story_gets_no_scope_label():
    page = _page('R. Eliezer')
    assert filter_biblical_actor_stories([page]) == 0
    s = page['stories'][0]
    assert s['classification'] == 'YES'
    assert 'out_of_scope' not in s


def test_the_one_shipped_firing_still_fires():
    # Kiddushin 72b is the only story any shipped v11 run demoted (correctly).
    run = json.loads((ROOT / 'results/v11/kiddushin/kiddushin_v11.json').read_text())
    fired = [s for p in run['pages'] for s in p['stories'] if s.get('filtered_as_biblical')]
    assert len(fired) == 1
    ev = fired[0]['criteria']['identifiable_characters']['evidence']
    assert _actors_are_biblical_only(ev) is True
