# Can a Claude grader promote LOW-confidence stories to the site? Calibration (2026-11-13)

**Question:** the site ships definite stories only. About 1,259 detector proposals sit below that bar
(`2026-11-13-how-many-stories-we-miss.md`). Is a Claude grader on the current judge prompt
(`src/prompts/judge_register_v2.md`, sha `88e8fff62716`) precise enough to promote some of them?

**Method:** `scripts/calibrate_low_pool_grader.py`. 300 spans Jeff has ruled on, all LOW or split in the
detector, graded twice by Claude Code subagents (claude-opus-5-5, one subagent per batch of 20, different
subagents per pass, ids hidden). Truth: Jeff yes; **borderline counts as not a story** (the site rule).
C1 = 158 spans from review rounds (CIRCULAR, the register was written from these verdicts). C2 = 142
Eruvin/Yevamot spans scored against his 2005 lists as updated 2026-11-12 (BLIND; 95 have no list story,
so truth unknown). Ship bar: precision >= 0.90, Wilson 95% lower bound >= 0.80. Output: `results/shas_run/low_pool/calibration/score.json`.

## Result — measured

| rule | grader says story, Jeff yes | precision | Wilson 95% | recall of Jeff's yes |
|---|---|---|---|---|
| pass 1 | 36 / 38 | 0.947 | 0.83–0.99 | 36 / 141 |
| pass 2 | 38 / 40 | 0.950 | 0.84–0.99 | 38 / 141 |
| **both passes say story** | **32 / 33** | **0.970** | **0.85–1.00** | **32 / 141** |
| C2 blind only, both passes | 6 / 6 | 1.00 | 0.61–1.00 | 6 / 37 |

Stability: same story-or-not call on 287 / 300 spans; same exact verdict on 256 / 300.

**Precision clears the bar. Recall is low: the grader calls about a quarter of Jeff's real stories `story`.**
It is much stricter than Jeff. Of his yes stories it called most `borderline` (54–64) or `not` (39–51).
Widening the rule to story-or-borderline drops precision to about 0.83, below the bar.

Caveats: C1 is circular, and the blind slice is 6 spans, too small to carry the result alone (its lower bound is 0.61).
The `golden_low_on_list` subgroup is 13/14 under both passes, with too few spans to judge on its own.

## What it implies — indicated

Applying "both passes say story" to the 1,259-span pool would promote about a quarter of the real
stories in it: on the earlier estimate of 330–790 real, roughly **80–200 stories**, at ~95% precision.
That is below the ~300 hoped for, because the grader is conservative. It is still the only route found
that adds stories without lowering what "definite" means on the site.

Next, if approved: grade the pool twice (~63 batches per pass), take both-passes-story, then Simon reads a
random 60 of the would-be promotions; nothing ships unless at least 54 are real.

## Pool graded — measured (2026-11-13, same day)

`scripts/grade_low_pool.py`: all 1,259 pool spans graded twice (1,117 new per pass + 142 reused from calibration C2), 0 unscored.
**80 spans both passes call `story`** (P1 26, P3 51, P4 3) — the bottom of the 80–200 indicated above.
At the calibrated ~0.95 precision that is roughly 75 real stories. Nothing ships yet: Simon reviews a seeded random 60
(`review_sample.json`) on `validation/ui/low_pool_promotions_review.html` (all 80 shown, sample first); ship only if >= 54 of 60 are yes.
