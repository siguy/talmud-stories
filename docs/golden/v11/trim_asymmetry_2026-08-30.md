# Trim asymmetry: start-trims work, deep end-trims destroy — 2026-08-30

The neutral ruler (`tests/expert_boundary_targets_2005.json`, 229 scorable Ketubot
boundaries) can do something the corrections ruler never could: name the boundaries
we had **right** and broke. That list turned out to have a single, sharp pattern.

## What Wave 5's trimming actually does

Per boundary, no-trim vs Wave 5:

| | fixes | regressions |
|---|---|---|
| **start** trims | 15 | 2 |
| **end** trims | 7 | 12 |

Start-trimming is a clear win. End-trimming is a net loss — **and it fails in one
direction only.** Every end regression cuts too EARLY; none cuts too late. The
drifts on Ketubot 61-112: `-6, -6, -6, -6, -4, -3, -2, -2, -2, -1`. The model is
lopping the resolution off the end of stories.

## The fix

| variant | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|
| no trimming at all | 172 | 18 | 39 | 75% | 83% |
| trim both ends (shipped) | 183 | 10 | 36 | 80% | 84% |
| start-trim only | 183 | 13 | 33 | 80% | 86% |
| **start + end-trim capped at 3 clauses** | **185** | **11** | **33** | **81%** | **86%** |

`MAX_END_TRIM_CLAUSES = 3` in `src/story_detector_v11.py`. Caps of 1, 2 and 3 score
identically — the 14 end-trims that remove 2-3 clauses are score-neutral, while the
9 that remove 4-6 are pure damage. 3 is the conservative choice: it removes only the
trims we have evidence against.

**This is a pure post-filter on the model's answer, so the numbers above are exact,
not estimates** — they come from re-filtering the existing run artifacts, not from a
re-run. No API calls were needed to establish it.

## Why nobody could see this before

On the corrections ruler the same comparison reads **33% → 67%, a doubling**, because
every question in it is a case where the plain boundary was already wrong, so any trim
can only help. It has no way to represent "you broke one that was fine". Lesson 23.

## Caveat

Ketubot only — Kiddushin has no neutral ruler, so this cap is unvalidated there. It is
conservative in the safe direction (less trimming, matching the project's stated
preference for under-trimming), so shipping it corpus-wide is defensible, but it should
be re-measured on any tractate that gets a neutral ruler.
