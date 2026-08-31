"""A review round must yield boundary targets the scorer reads, with provenance intact.

Phase B of `work/2026-08-30-review-verdict-axes.md`, boundary half. The review page
captures a boundary as a (segment, clause) pair -- the unit
`scripts/score_boundary_targets.py` scores -- and records whether our span was on screen
when the expert marked it.

That last bit is the whole point and the whole risk. Two kinds of target come out of one
round and they answer different questions (Lesson 24):

    corrections   our span was on screen. CIRCULAR. "Did we fix known failures", and it
                  cannot catch a regression (Lesson 23).
    blind         he marked the extent before our span was shown. Neutral, and the only
                  kind that can catch a regression.

Pooling them, or mislabelling one as the other, is how a circular number gets quoted as
accuracy -- the mistake FRAMEWORK sec.3 says cost this project months. So: two files,
never one, and the scorer decides which is which from the TARGET rather than from the
filename it happens to sit in.

Run:  pytest tests/test_boundary_targets_from_review.py -v
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


btargets = _load('build_boundary_targets_from_review',
                 'scripts/build_boundary_targets_from_review.py')
scorer = _load('score_boundary_targets', 'scripts/score_boundary_targets.py')

ROUND = {
    'schema': 'verdict_axes_v1',
    'tractate': 'Kiddushin',
    'reviews': {
        'Kiddushin 22b_18-18': {
            'page_ref': 'Kiddushin 22b', 'start_segment': 18, 'end_segment': 18,
            'classification_shown': 'YES', 'is_story': 'yes', 'extent': 'right',
            'boundary_marks': [
                {'direction': 'start', 'segment': 18, 'clause': 0, 'n_clauses': 5,
                 'blind': True, 'blind_basis': 'marked before our span was shown'},
                {'direction': 'end', 'segment': 18, 'clause': 4, 'n_clauses': 5,
                 'blind': True, 'blind_basis': 'marked before our span was shown'},
            ],
        },
        'Kiddushin 7b_9-10': {
            'page_ref': 'Kiddushin 7b', 'start_segment': 9, 'end_segment': 10,
            'classification_shown': 'LOW_CONFIDENCE', 'is_story': 'yes',
            'extent': 'ends_wrong',
            'boundary_marks': [
                {'direction': 'end', 'segment': 11, 'clause': 2, 'n_clauses': 3,
                 'blind': False, 'blind_basis': 'correction: our span was on screen'},
            ],
        },
    },
}


class BoundaryTargetsFromReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kinds = btargets.targets_from(ROUND)

    def test_the_two_kinds_are_separated_not_pooled(self):
        self.assertEqual(2, len(self.kinds['blind']))
        self.assertEqual(1, len(self.kinds['corrections']))
        self.assertTrue(all(t['boundary_blind'] for t in self.kinds['blind']))
        self.assertTrue(all(not t['boundary_blind'] for t in self.kinds['corrections']))

    def test_every_target_carries_the_fields_the_scorer_reads(self):
        """score() reads located_on/ref, segment, clause, direction. Nothing else is
        required, and a target missing one is silently N/A rather than an error."""
        for t in self.kinds['blind'] + self.kinds['corrections']:
            self.assertTrue(t.get('located_on') or t.get('ref'))
            self.assertIsInstance(t['segment'], int)
            self.assertIsInstance(t['clause'], int)
            self.assertIn(t['direction'], ('start', 'end'))
            self.assertLess(t['clause'], t['n_clauses'], 'target points past the segment')

    def test_every_target_states_why_it_is_blind_or_not(self):
        """Provenance travels with the target, so nobody reconstructs it from a commit."""
        for t in self.kinds['blind'] + self.kinds['corrections']:
            self.assertTrue(t['blind_basis'], f'{t["review_key"]}: no stated basis')

    def test_the_scorer_reads_blindness_from_the_target_not_the_filename(self):
        """It used to compare `target_file` against one hardcoded name, so any new blind
        source was reported as a correction -- understating the score against it and
        mislabelling its kind, which is exactly what FRAMEWORK sec.3 forbids."""
        for t in self.kinds['blind']:
            self.assertTrue(scorer.target_is_blind({**t, 'target_file': 'anything.json'}))
        for t in self.kinds['corrections']:
            self.assertFalse(scorer.target_is_blind({**t, 'target_file': 'anything.json'}))

    def test_the_2005_lists_are_still_read_as_blind(self):
        """The flag is new; those targets predate it and must not silently flip kind."""
        self.assertTrue(scorer.target_is_blind({'source_round': 'jeff_2005_ketubot_list'}))
        self.assertTrue(scorer.target_is_blind(
            {'target_file': 'expert_boundary_targets_2005.json'}))
        self.assertFalse(scorer.target_is_blind(
            {'source_round': 'canonical_review_anonymous_2026-03-17.json',
             'target_file': 'expert_boundary_targets_v2.json'}))

    def test_a_round_in_the_wrong_schema_is_refused(self):
        with self.assertRaises(SystemExit):
            btargets.targets_from({'schema': 'something_else', 'reviews': {}})

    def test_real_target_files_still_classify_as_they_did(self):
        """Pin the two counts the scorer prints, so the fix cannot drift them."""
        import json
        blind = json.loads((ROOT / 'tests/expert_boundary_targets_2005.json').read_text())
        corr = json.loads((ROOT / 'tests/expert_boundary_targets_v2.json').read_text())
        n_blind = sum(1 for t in blind['targets']
                      if scorer.target_is_blind({**t, 'target_file':
                                                 'expert_boundary_targets_2005.json'}))
        n_corr = sum(1 for t in corr['targets']
                     if scorer.target_is_blind({**t, 'target_file':
                                                'expert_boundary_targets_v2.json'}))
        self.assertEqual(294, n_blind, 'the 2005 set stopped reading as blind')
        self.assertEqual(0, n_corr, 'the corrections set started reading as blind')


if __name__ == '__main__':
    unittest.main(verbosity=2)
