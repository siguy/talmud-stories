"""
A single NARRATIVE_EVENT is enough to examine a page.

The shipped rule required a narrative event to be *corroborated* — either by a
second narrative event, or by two verbal acts — and discarded the page otherwise.
Measured against both blind lists on 2026-08-31, the pages it discarded on that
basis are the single richest seam of missed stories in the corpus: 8 such pages
across Ketubot and Kiddushin, **6 of which carry a real story** (~75%, against
14.3% for discarded pages as a whole).

One of the 8 is **Ketubot 51a**, the false skip found by hand on 2026-02-13 and
recorded in `docs/capabilities/1_triage.md` ever since. The rule was never changed
to catch it.

These tests pin the new boundary and, critically, pin the cases that must NOT
change — a looser rule that also keeps storyless pages would spend the reviewer's
attention, which is the project's binding constraint.

→ docs/findings/2026-08-31-triage-single-narrative.md
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.event_triage import EventTriager                    # noqa: E402
from src.ground_truth import EventType                       # noqa: E402

N = EventType.NARRATIVE_EVENT
V = EventType.VERBAL_ACT
D = EventType.DELIBERATION
H = EventType.HABITUAL


def skip(*events):
    return EventTriager.should_skip_page(list(events))


# --- the change itself -------------------------------------------------------

@pytest.mark.parametrize('page,label', [
    ([N, V, D, D, D, D, D, D, D, D, D, D, D, D], 'Ketubot 51a shape (N=1, V=1)'),
    ([N, V, D, D, D, D, D, D, D, D, D], 'Ketubot 22b shape (N=1, V=1)'),
    ([N, D, D, D, D, D, D, D, D, D, D, D, D, D, D, D], 'Kiddushin 69a shape (N=1, V=0)'),
    ([N], 'a one-segment page whose only segment is narrative'),
])
def test_one_narrative_event_is_enough(page, label):
    """A single NARRATIVE_EVENT keeps the page, with or without dialogue."""
    assert skip(*page) is False, f"{label} must be examined"


def test_this_is_the_case_the_old_rule_dropped():
    """Guards the exact boundary that moved: N=1 with fewer than 2 verbal acts."""
    old_rule_would_skip = [N, V] + [D] * 12          # N=1, V=1
    assert skip(*old_rule_would_skip) is False


# --- what must NOT change ----------------------------------------------------

def test_no_narrative_event_still_skips():
    """The rule is looser about corroboration, not about narrative evidence."""
    assert skip(*([V] * 8 + [D] * 12)) is True
    assert skip(*([D] * 20)) is True
    assert skip(*([H] * 5 + [D] * 10)) is True
    assert skip() is True


def test_verbal_acts_alone_never_keep_a_page():
    """
    Kiddushin 10b (N=0, V=5) carries a real story and stays skipped. Keeping it
    needs a `V >= 4` clause, which the sweep showed costs 70 extra Ketubot calls
    for zero extra Ketubot stories — a threshold fitted to one story. Deliberately
    NOT adopted; this test pins that decision so it is revisited on purpose.
    """
    assert skip(*([V] * 5 + [D] * 10)) is True
    assert skip(*([V] * 20)) is True


def test_triage_failure_still_fails_open():
    """The 2026-08-31 fail-open behaviour is untouched (Lesson 21)."""
    assert skip(*([EventType.TRIAGE_FAILED] + [D] * 10)) is False


def test_previously_kept_pages_are_still_kept():
    """A strictly-looser rule must never start skipping something it kept."""
    assert skip(*([N, N] + [D] * 10)) is False           # old: N>=2
    assert skip(*([N, V, V] + [D] * 10)) is False        # old: N>=1 and V>=2
