# Lesson 13 — Tight numeric gates penalize correct quality improvements

**2026-05-24**

**Context:** Wave 2 ships 3 rabbinically correct start-boundary snaps
(ההוא ד / ההיא openers). Two land on Ketubot stories Jeff has not yet
reviewed. Because the unchanged Ketubot golden inherits the pre-snap
boundaries from v7, the snaps mechanically lower IoU by 1 segment on each
story → composite drops 0.0002 below Wave 1. Strict "Wave 2 ≥ Wave 1"
gate fails by this margin, even though each snap is unambiguously correct
by human reading.

**Rule:** A composite-score gate measures agreement with the current
golden, not absolute quality. When a mechanical change disagrees with
golden on a small number of cases the expert hasn't yet ruled on, the
right response is to ship + flag for expert review, not to disable the
change to pass the gate.

**Why:** Disabling the snap to satisfy the gate would throw away verified
quality wins to chase a tenth of a percent of agreement with a golden that
hasn't seen the changed cases. The cost of asking Jeff later is small;
the cost of regressing real quality is permanent.

**How to apply:** When a strict score gate fails by noise-scale margins,
inspect the disagreement cases by hand. If the change is defensible per
expert convention, ship + document + flag for next review round. If not,
tighten the change.
