# Lesson 19 — Reverting to the safe default beats shipping a better version of a broken feature

**2026-08-28**

The Wave 5 plan went straight from "broken char-offset trimmer" to
"clause-anchored trimmer," leaving 153 stories with corrupt boundaries
live for however long v11 took to build and validate. The better first
move was to **delete the feature**: strip the spans, restore
segment-level boundaries, ship today. Cost: $0, no LLM calls, no new
detector. Score movement: none (0.9171 → 0.9171, verified by running
the harness both ways). On Jeff's own sample, untrimmed output would
have scored 4/6 instead of 4/15.

**Rule:** When a feature is measurably net-negative, revert it before
building its replacement. Ship the safe default, then treat the new
mechanism as an improvement over a clean baseline rather than a rescue
of a corrupt one.

**Why:** The risk is asymmetric. An over-inclusive segment boundary is
recoverable by a human reader — Jeff can see the extra text and tell us
to trim it. A mid-word cut destroys information and reads as
incompetence to the expert whose trust the project runs on. "We are
building a fix" does not help the reviewer looking at corrupt text
today. Reverting also removes all schedule pressure from the
replacement, which is how the replacement gets built properly.

**How to apply:** Ask "what does this system do if I delete the feature
entirely?" If the answer is *degraded but honest*, that is the correct
interim state. Prove neutrality by running the eval harness before and
after rather than reasoning about what it reads. Keep the reverted
version as a new file; never edit the frozen one
(`scripts/strip_text_spans.py` → `results/v10/wave4_notrim/`).
