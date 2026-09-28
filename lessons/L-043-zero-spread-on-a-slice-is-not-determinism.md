# L-043 — Zero spread on a small slice is not determinism

**Date:** 2026-09-27
→ [`2026-09-27-detector-is-not-deterministic.md`](../docs/findings/2026-09-27-detector-is-not-deterministic.md)

## The rule

**Before declaring a stochastic system deterministic, ask how rare a flip would have to be
to show zero flips at your sample size — and whether the real run is bigger than that.**
Re-measure the spread at the scale you will compare at.

## What happened

On 2026-09-09, three repeats on a 20-page slice returned identical story sets. We wrote
"the detector is deterministic; one run per arm" and stopped repeating. On 2026-09-27, two
identical full Yevamot runs disagreed on 3 of 102 expert stories — about one flip per 35
pages, which a 20-page slice will usually show as zero. For eighteen days, one-story
deltas were read as effects, and one was written up as a confirmed prediction.
