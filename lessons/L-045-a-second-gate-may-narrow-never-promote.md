# L-045 — A second gate may narrow what ships, never promote what the first gate held back

**Date:** 2026-11-09
→ PR siguy/talmud-stories#84, `scripts/build_site_data.py` (`strong_yes_cells`)

## The rule

**When a new check is added on top of an existing publishing rule, it may only remove items.
If it would let through anything the existing rule blocks, that is a policy change — ask
Simon, do not decide it in code.** Pin it with a test that holds across every tractate.

## What happened

The Septimus site ships only definite stories: YES/HIGH_CONFIDENCE, never LOW_CONFIDENCE
(Simon, 2026-10-12). Adding Berakhot, the consensus judges were added as a second gate:
ship only what both judges call a story. 8 of the 74 strong-yes passages were LOW in v14,
and the export was written so that "both judges say story" *overrode* the detector's LOW —
the judges promoted 8 passages past a rule Simon had set. Reported to him as a feature
("8 extra passages"). His answer: only stories that are definitely stories reach the site.

Why it read as reasonable: the judges were the newer, stronger signal, and the goal was
"the 74". But the goal was the *intersection* of two signals of definiteness, and the
code computed something closer to their union.

## The guard

`tests/test_site_data.py::test_no_low_confidence_or_not_a_story_ships` — every shipped
story in every tractate is YES, HIGH_CONFIDENCE or BORDERLINE (tier `borderline`), never
LOW_CONFIDENCE or NOT_A_STORY.

## Same day, the same error one level down

The export then read **one** v14 run. v14 is not deterministic (two runs kept 189 and 187);
2 shipped stories were YES in run 1 and LOW in run 2 — not definite either. A story now
ships only if every listed run grades it YES/HIGH (`CORROBORATE` in `build_site_data.py`):
64 stories. **Definite means definite in every measurement we hold**, not in the one we
happened to pick.
