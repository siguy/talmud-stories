"""
The miss-cause split must be a partition of the misses, by construction.

`measure_recall_vs_expert_list.py` prints:

    CAUSE of the N misses: A triage discarded the page, B page examined and
    nothing proposed in range

which asserts A + B == N. It used to compute N from the run's proposals and A from
`triage_lost` — *every* story on an unexamined page, found or not. Normally a story on an
unexamined page cannot be found, so the two coincided and the bug was invisible. They
diverge the moment a detected file's proposals disagree with its own `skipped_by_triage`
flags, which is exactly what the `results/v11/triage_recall/*_plus_*.json` measurement
artifacts deliberately do. Observed 2026-08-31:

    CAUSE of the 3 misses: 4 triage discarded the page, 2 page examined and ...

4 + 2 != 3, printed with a straight face. This is the only line in the pipeline that
attributes a miss to Triage rather than Detection, and Lesson 35 exists because charging
one capability's losses to another sends the fix to the wrong place.

The fix is structural, not defensive: derive both buckets from the misses. Then they
partition by construction and the assertion can only fire if the code is edited wrongly.

→ docs/findings/2026-08-31-cause-bucket-partition.md
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.measure_recall_vs_expert_list import cause_buckets   # noqa: E402


def row(found, survived):
    return {'in_detector': found, 'survived_triage': survived, 'ref': 'X'}


def test_the_buckets_partition_the_misses():
    rows = [row(True, True), row(False, True), row(False, False)]
    missed, triage_lost, kept_missed = cause_buckets(rows)
    assert len(missed) == 2
    assert len(triage_lost) == 1
    assert len(kept_missed) == 1
    assert len(triage_lost) + len(kept_missed) == len(missed)


def test_a_found_story_on_an_unexamined_page_is_not_a_miss():
    """
    The exact shape that produced 4 + 2 != 3. A merged run carries pages still flagged
    `skipped_by_triage` that nonetheless have proposals; such a story is FOUND and must
    not be counted as a triage-discarded miss.
    """
    rows = [row(True, False), row(True, False), row(False, False)]
    missed, triage_lost, kept_missed = cause_buckets(rows)
    assert len(missed) == 1, "two of these three were found"
    assert len(triage_lost) == 1, "only the missed one is a triage-discarded MISS"
    assert len(kept_missed) == 0
    assert len(triage_lost) + len(kept_missed) == len(missed)


@pytest.mark.parametrize('rows', [
    [],
    [row(True, True)],
    [row(False, False)],
    [row(True, False), row(False, True), row(False, False), row(True, True)],
])
def test_the_partition_holds_for_every_combination(rows):
    missed, triage_lost, kept_missed = cause_buckets(rows)
    assert len(triage_lost) + len(kept_missed) == len(missed)
    assert not (set(map(id, triage_lost)) & set(map(id, kept_missed))), "buckets overlap"


def test_flags_disagreeing_with_proposals_are_surfaced_not_swallowed():
    """
    A found story on a page flagged unexamined means the detected file's
    `skipped_by_triage` flags disagree with its proposals. That is legitimate for the
    merged measurement artifacts, so it must WARN rather than crash — but it must not
    pass silently, or the triage/detection attribution is quietly wrong (Lesson 38:
    absence is quiet).
    """
    from scripts.measure_recall_vs_expert_list import flags_disagreeing_with_proposals
    assert flags_disagreeing_with_proposals([row(True, True), row(False, False)]) == []
    assert len(flags_disagreeing_with_proposals([row(True, False)])) == 1
