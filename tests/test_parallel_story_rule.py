#!/usr/bin/env python3
"""
Guards for the parallel-practice rule in the Wave 5 clause-span prompt.

See docs/findings/2026-09-01-parallel-story-rule.md and
work/2026-09-01-parallel-story-rule.md.

Two things are pinned here, for two different reasons.

1. THE DEFECT ITSELF, on frozen data. Ketubot 62a and 105b each discard a whole
   second story off the end of a segment. Those two trims are in the shipped v11
   outputs and will stay there — the files are frozen. The test asserts the screen
   still finds them, so the case that motivated the change cannot quietly stop being
   reproducible.

2. THE WORDING THAT SURVIVED A BY-EYE PASS. The rule's first draft said a parallel
   is a second story when it has "its own characters and its own events or dialogue".
   Screening all 50 end-trims showed four of the 13 deep ones are amoraic legal
   debate — `אָמַר אַבָּיֵי ... אֲמַר לֵיהּ רַב אַדָּא בַּר מַתְנָא` — which has exactly that
   surface form and is trimmed correctly today. The rule therefore has to key on
   EVENTS and say so about names and speech. That distinction cost a measurement to
   find and is one careless edit from being lost, so it is pinned in the same spirit
   as the test recording why `V>=4` was rejected on triage.

Pinning prompt text is a blunt instrument and it is deliberate here: the assertions
below are about the DISTINCTION being present, not about phrasing. Reword freely —
if you remove the events-not-speech clause, this test should fail, and that is the
point.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from src.story_detector_v11 import V7StoryDetector  # noqa: E402

PROMPT = V7StoryDetector._TEXT_SPAN_PROMPT_TEMPLATE

# ref -> (end segment, clauses discarded) as measured 2026-09-01 on the frozen runs.
KNOWN_SECOND_STORIES = {
    ('Ketubot 62a', 7): 6,    # R. Yochanan on the stair, with dialogue and a punchline
    ('Ketubot 105b', 9): 6,   # Mar Ukva, the spittle, and פסילנא לך לדינא
}
FROZEN_RUN = 'results/v11/wave5_summaryfix/ketubot_61-112_v11_g37high.json'


def test_the_rule_still_distinguishes_a_bare_mention_from_a_full_incident():
    """A bare 'and so-and-so did the same' is trimmed; a full incident is kept."""
    assert 'SECOND STORY' in PROMPT, (
        'the parallel rule no longer names a second story as a distinct case — '
        'this is the conflation that deleted Ketubot 62a and 105b')
    assert 'FULL INCIDENT' in PROMPT


def test_the_rule_keys_on_events_and_not_on_names_or_speech():
    """The clause that four amoraic-debate cases depend on. See the module docstring.

    Without it the rule reads onto `אמר אביי ... אמר ליה רב אדא בר מתנא`, which is
    legal argument the prompt trims correctly today, and Jeff's Wave 3 verdict —
    'crude criteria, such as ... a rabbi's name automatically signalling the story's
    end' — applies in mirror image."""
    assert 'EVENTS, never on names or speech' in PROMPT, (
        'the events-not-speech distinction is gone; the rule will now keep amoraic '
        'debate. See docs/findings/2026-09-01-parallel-story-rule.md §2')
    assert 'Amoraic debate' in PROMPT


@pytest.mark.parametrize('ref,seg,depth', [(r, s, d) for (r, s), d in KNOWN_SECOND_STORIES.items()])
def test_the_frozen_runs_still_reproduce_the_deletion(ref, seg, depth):
    """The two motivating cases, on data that cannot change."""
    from screen_end_trim_depth import trims

    found = {(t['ref'], t['segment']): t for t in trims(ROOT / FROZEN_RUN)}
    assert (ref, seg) in found, f'{ref} seg {seg} no longer shows an end-trim in {FROZEN_RUN}'
    t = found[(ref, seg)]
    assert t['depth'] == depth, f'{ref} seg {seg}: expected {depth} clauses discarded, got {t["depth"]}'
    assert t['dropped_hebrew'].strip(), 'the discarded region is empty — the screen is not reading text'


def test_the_screen_reports_indicated_not_measured():
    """Depth over-selects ~6x (13 candidates, 2 real). The script must not present
    its candidate list as a count of second stories — Lesson 18."""
    src = (ROOT / 'scripts' / 'screen_end_trim_depth.py').read_text()
    assert 'INDICATED, NOT MEASURED' in src
    for marker in ('כי הא', 'similarly'):
        assert marker in src, 'markers dropped from the screen'
    assert 'never as a filter' in src.lower() or 'never a filter' in src.lower(), (
        'the screen must state that parallel markers are evidence, not a filter (Lesson 15)')


def test_the_experiment_runner_cannot_quietly_drop_what_makes_it_trustworthy():
    """The runner exists so the method is not re-derived (or skipped) by whoever has
    the key. Three things are load-bearing and each has been skipped in this project
    before: the same-code repeat (Lesson 22), keeping the blind and corrections rulers
    apart (Lesson 24), and splitting by direction (the pooled number hid that Ketubot's
    whole deficit is ends). Pinned by name, not by phrasing."""
    src = (ROOT / 'scripts' / 'run_parallel_rule_experiment.py').read_text()
    assert '_repeat' in src, 'the same-code repeat arm is gone (Lesson 22)'
    assert '--by-direction' in src, 'the direction split is gone'
    assert 'expert_boundary_targets_2005.json' in src and \
           'expert_boundary_targets_2005_kiddushin.json' in src, 'a blind ruler is gone'
    assert 'expert_boundary_targets_v2.json' in src, 'the corrections ruler is gone'
    assert 'CIRCULAR' in src, 'the corrections ruler is no longer labelled biased (Lesson 24)'
    assert 'GOOGLE_API_KEY' in src, 'the runner no longer refuses without a key'
