"""Every banked verdict must map onto the new shape, exactly once, without guessing.

Gate from `work/2026-08-30-review-verdict-axes.md`: *"Mapping table covers all banked
rounds -- assert every existing verdict maps to exactly one new shape."*

A new verdict vocabulary that cannot read the old ones starts the ledger over, and this
project has already lost feedback that way twice (Lesson 1: rounds split into an "apply"
pile and a "later" pile, and the later pile never revisited). So the mapping is code with
a test rather than a paragraph in a plan.

Two properties matter more than coverage:

  * **Nothing is guessed.** Where a legacy verdict underdetermines an axis, the axis is
    None and its name is in `undetermined`. Filling it to make coverage look complete is
    the failure FRAMEWORK sec.7 names.
  * **Layers do not merge.** A `correct` on already-corrected data is not a `correct` on
    base data (Lesson 3). Merging them lets the 2026-03-17 round's "the correction was
    right" silently overturn the earlier round's "incorrect" that caused the correction.

Run:  pytest tests/test_verdict_migration.py -v
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mv = _load('migrate_verdicts', 'scripts/migrate_verdicts.py')


class VerdictMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rounds = mv.migrate_all()
        cls.records = [r for recs in cls.rounds.values() for r in recs]

    def test_every_verdict_file_on_disk_is_accounted_for(self):
        """A file nobody classified is a file nobody reads. That is Lesson 1's shape.

        Three of these were listed in STATE.md as 'expert verdicts on disk that no ruler
        reads' -- they are unread because their records live under a different container
        key and in a list rather than a dict, not because anyone decided to skip them.
        """
        on_disk = {p.name for p in sorted((ROOT / 'validation' / 'feedback').glob('*.json'))}
        on_disk |= {p.name for p in sorted((ROOT / 'jeff comms').glob('*.json'))}
        declared = {Path(path).name for path, *_ in mv.ROUNDS}
        missing = sorted(on_disk - declared)
        self.assertEqual([], missing,
                         f'verdict files not in ROUNDS: {missing} -- classify them (set '
                         f'expert=False if they are ours) rather than leaving them unread')

    def test_every_record_maps_to_exactly_one_shape(self):
        for name, recs in self.rounds.items():
            keys = [(r['key'], r['source_round']) for r in recs]
            self.assertEqual(len(keys), len(set(keys)), f'{name}: duplicate records')
        for r in self.records:
            for field in ('key', 'source_round', 'source_vocabulary', 'layer', 'undetermined'):
                self.assertIn(field, r, f'{r.get("key")}: missing {field}')

    def test_every_axis_value_is_declared_or_absent(self):
        for r in self.records:
            for axis, allowed in mv.AXES.items():
                v = r[axis]
                self.assertTrue(v is None or v in allowed,
                                f'{r["source_round"]}/{r["key"]}: {axis}={v!r} undeclared')

    def test_undetermined_names_exactly_the_axes_that_are_none(self):
        """The two must not drift: `undetermined` is what makes 'we do not know' auditable."""
        for r in self.records:
            blank = {a for a in ('is_story',) + mv.ALL_AXES if r[a] is None}
            self.assertEqual(blank, set(r['undetermined']),
                             f'{r["source_round"]}/{r["key"]}: undetermined={r["undetermined"]} '
                             f'but the blank axes are {sorted(blank)}')

    def test_nothing_unreadable_is_guessed_into_a_bucket(self):
        """A rejection whose objection nobody could read must stay undetermined."""
        for r in self.records:
            if r['legacy_verdict'] == 'incorrect' and \
               r['objection_axis'] in ('unclassified', 'unresolvable') and \
               r['classification_shown'] != 'NOT_A_STORY':
                self.assertIsNone(r['is_story'],
                                  f'{r["source_round"]}/{r["key"]}: an unreadable rejection '
                                  f'was resolved to {r["is_story"]!r}')

    def test_an_overturned_rejection_migrates_as_a_story(self):
        """`incorrect` on a NOT_A_STORY means "you wrongly rejected this" -- a false
        NEGATIVE. Pooling it with false positives is the defect Phase A measured."""
        overturned = [r for r in self.records
                      if r['legacy_verdict'] == 'incorrect'
                      and r['classification_shown'] == 'NOT_A_STORY']
        self.assertTrue(overturned, 'no overturned rejections found -- the label under '
                                    'review is probably not being recovered')
        for r in overturned:
            self.assertEqual('yes', r['is_story'], f'{r["key"]}: overturned but not a story')
            self.assertEqual('under_call', r['direction'], r['key'])

    def test_confirming_a_rejection_is_not_read_as_accepting_a_story(self):
        """`correct` endorses OUR judgment. On a NOT_A_STORY that means "right to reject"."""
        confirmed = [r for r in self.records
                     if r['legacy_verdict'] == 'correct'
                     and r['classification_shown'] == 'NOT_A_STORY']
        self.assertTrue(confirmed, 'the 2026-02-05 round showed 95 NOT_A_STORY spans')
        for r in confirmed:
            self.assertEqual('no', r['is_story'], f'{r["key"]}: a confirmed rejection read '
                                                  f'as an accepted story')

    def test_the_canonical_round_stays_on_its_own_layer(self):
        """Lesson 3. A correct on corrected data is not a correct on base data."""
        canon = [r for r in self.records
                 if r['source_round'] == 'canonical_review_anonymous_2026-03-17.json']
        self.assertTrue(canon)
        self.assertTrue(all(r['layer'] == 'correction' for r in canon))
        base_keys = {r['key'] for r in self.records if r['layer'] == 'base'}
        shared = {r['key'] for r in canon} & base_keys
        self.assertTrue(shared, 'expected overlap -- that overlap is exactly the trap')
        for r in canon:
            self.assertNotEqual('base', r['layer'],
                                f'{r["key"]}: a corrected-data verdict on the base layer')

    def test_adjust_migrates_to_a_boundary_complaint_not_a_rejection(self):
        adj = [r for r in self.records if r['legacy_verdict'] == 'adjust']
        self.assertTrue(adj, 'the 2026-03-17 round has adjust verdicts')
        for r in adj:
            self.assertEqual('yes', r['is_story'])
            self.assertEqual('wrong_unspecified', r['extent'])

    def test_the_first_rounds_boundary_corrections_are_recovered(self):
        """2026-01-08 had a `length_adjustment` axis and no harness ever read it.

        Ten of its 25 entries say `shrink`. They are boundary corrections from the
        project's first expert round, and they have been invisible for seven months
        because the file keys its records under a list rather than a dict.
        """
        first = self.rounds['ketubot_review_Jeffrey_Rubenstein_2026-01-08.json']
        self.assertEqual(25, len(first))
        shrink = [r for r in first if r.get('legacy_length_adjustment') == 'shrink']
        self.assertEqual(10, len(shrink), f'expected 10 boundary corrections, got {len(shrink)}')
        for r in shrink:
            self.assertEqual('wrong_unspecified', r['extent'],
                             'shrink says the extent is wrong but not which end; claiming '
                             'a specific end would be inventing the answer')

    def test_our_own_files_are_marked_not_expert(self):
        """A test export of Simon's and an automated self-check are on disk beside the
        real rounds. Counting them as expert verdicts would inflate every denominator."""
        ours = {r['source_round'] for r in self.records if not r['expert']}
        self.assertIn('ketubot_review_Simon_-_Test_2026-01-05.json', ours)
        self.assertIn('jeff_v4.1_validation.json', ours)


if __name__ == '__main__':
    unittest.main(verbosity=2)
