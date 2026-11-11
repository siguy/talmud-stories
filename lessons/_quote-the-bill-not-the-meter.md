# Quote the bill, not the meter, and never call a partial meter "measured"

**Date:** 2026-11-10
→ [`2026-11-10-shas-run.md`](../docs/findings/2026-11-10-shas-run.md)

## The rule

**A cost is measured only when every call that cost money passed through the meter. Otherwise say which calls
the meter saw, and quote the provider's bill (AI Studio) as the total.** Before a run, list every component that
calls a paid model. Check that each one goes through the meter (`TokenMeter` in `run_new_tractate.py`), and test it.

## What happened

The Shas run report called "$69.82" measured. That figure covered the detector runs and triage only. The Gemini
scope judge called Gemini directly, outside the meter, so its ~3,000 calls were estimated separately at $7–16.
AI Studio billed $85. That falls inside the stated range, but a reader who saw "measured $69.82" next to an $85
bill reasonably concluded the numbers were wrong. Fixed: the judge now goes through the same wrapper, which also
gives it the detector's 429 retry. Missing that retry was the run's other judge failure (182 calls).
