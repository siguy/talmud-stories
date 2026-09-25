# The whole 18: 13 recovered by the pass, 2 by base detection, 3 still missed

**2026-09-22.** Status: **measured, one run per arm, four tractates.**
Item: [`finish-the-18-twins`](../../work/done/2026-09-22-finish-the-18-twins.md).
Closes the population opened by [`miss-anatomy`](2026-09-07-miss-anatomy.md) and measured
piecemeal in [`twin-pass`](2026-09-14-twin-pass.md) and
[`ketubot-twin-pass`](2026-09-15-ketubot-twin-pass.md).

## The 18, finished

| tractate | cases | **pass recovered** | control already had | still missed | recall, control -> twin | pass proposals | not on his list |
|---|---|---|---|---|---|---|---|
| Ketubot | 7 | **6** | 0 | 1 | 88.6% -> **93.3%** | 23 | 16 |
| Yevamot | 7 | **6** | 0 | 1 (Mishnah-scope) | 89.2% -> **94.1%** | 12 | 9 |
| Kiddushin | 3 | **1** | 2 | 0 | 88.9% -> **90.0%** | 8 | 6 |
| **Gittin** | **1** | **0** | 0 | **1** | 97.3% -> **97.3%** | 13 | 10 |
| **total** | **18** | **13** | **2** | **3** | | **56** | **41** |

**15 of the 18 are now found.** Thirteen by the pass, two by v11's base detection without
it. Three remain: Ketubot 111a seg 12, Gittin 47a seg 0, and Yevamot 122b seg 0 (which
sits inside a Mishnah and belongs to `jeff:mishnah-scope`, answered — it is catalogued,
not lost).

## Gittin: the pass did nothing, twice over

**Gittin 47a seg 0 is missed by both arms**, and Gittin's recall does not move: 108/111
either way, not one story gained or lost. The pass still added **13 proposals, 10 of them
not on Jeff's list.**

This is the first tractate where the mechanism produced nothing, and it is the one with a
single case — so it is a negative result on a sample of one, not a refutation. But it is
the shape a tractate takes when the cost arrives and the benefit does not, and it is why
the cost column below matters more than the recall column.

## "On his list" is not the same as "recovered"

Gittin's pass put **3** proposals on stories that are on Jeff's list and gained **0**
recall: all three landed on stories the control had already found. Counting "additions
that are on his list" as the benefit therefore overstates it. **The honest benefit is the
recall delta**, and against it the price is:

| | stories newly found | proposals not on his list |
|---|---|---|
| Ketubot | +7 | 16 |
| Yevamot | +5 | 9 |
| Kiddushin | +1 | 6 |
| Gittin | **0** | 10 |
| **total** | **+13** | **41** |

**Roughly three unjudged proposals per story recovered, and the ratio is far worse at the
thin end.** Yevamot's "single digits was the bar" reads differently now that four
tractates are in: 41 items for Jeff to rule on, against a correspondence record of 187,
96, 1, 15 verdicts per round.

## Boundaries held everywhere

`--by-direction`, `--standard jeff-2026`, blind 2005 targets:

| tractate | arm | scored | hit | **MISS** |
|---|---|---|---|---|
| Ketubot | control / twin | 232 / 248 | 81% / 82% | **39 / 39** |
| Kiddushin | control / twin | 140 / 143 | 91% / 91% | **10 / 10** |
| Gittin | control / twin | 170 / 170 | 85% / 85% | **21 / 21** |

**The MISS count is identical in every arm on every tractate.** The pass adds scoreable
targets (recovering a story gives the ruler something to grade) and never a boundary
error. That is now measured on three tractates rather than argued from one.

## Determinism is per tractate, not a property of the detector

| tractate | base-detection spans differing between arms |
|---|---|
| Ketubot | 5 only in control, 4 only in twin |
| Gittin | 3 only in control, 2 only in twin |
| **Kiddushin** | **0 / 0 — identical** |

[`twin-pass`](2026-09-14-twin-pass.md) justified one run per arm on a spread of 0.0 from a
20-page Yevamot slice; [`ketubot-twin-pass`](2026-09-15-ketubot-twin-pass.md) corrected
that to "Ketubot is not deterministic". **Both are too broad.** Kiddushin reproduces
exactly; Ketubot and Gittin do not. Determinism has to be checked per tractate and cannot
be inherited from a slice — which means every single-run comparison on Ketubot or Gittin
carries an unmeasured noise term, and the Kiddushin +1 does not.

## Method correction, and why it belongs in this finding

The first per-case lookup matched an anatomy case to **any recall row whose located window
overlapped its segment**. On a daf holding several of Jeff's stories that credits a
*neighbouring* story — which is the exact defect this entire line of work exists to fix,
reproduced inside the instrument measuring it.

Redone by text. **Ketubot's seven are unchanged** under the strict match (6 / 0 / 1);
**Kiddushin's changed** from "3 recovered" to "1 recovered, 2 the control already had".
Nothing published was wrong, and it was one daf away from being wrong.

## What is not established

- **One run per arm**, on two tractates now known not to reproduce.
- **Yevamot's control is the shipped artifact**, not a same-code control arm — the other
  three have matched controls. Its 89.2% -> 94.1% is the weakest row in the table.
- **The 41 non-listed additions are proposals, not errors**, and stay unjudged until Jeff
  sees them. They are what `jeff:review-error-rate` prices.
- **Gittin 47a seg 0 and Ketubot 111a seg 12 are unexplained** — both survive triage, both
  sit one segment from a proposal, neither is proposed by either arm.
- **Reach is still 1.** The 11 NEAR misses (2-6 segments) are untouched.

`TWIN_PASS` and `TWIN_TRIGGER` **stay default off**, and the Gittin row is now a second
reason why, independent of the reviewer cost.
