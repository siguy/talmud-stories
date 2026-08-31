# Lesson 22 — Measure the noise floor before believing a one-run comparison

**2026-08-30**

Wave 5 Step 2 fixed a real defect: the boundary prompt read
`story['summary']`, present on **0 of 262** stories, so 100% of stories
fell through to a joined event list that stops before the story's
resolution — while 35 of the 52 expert targets are END boundaries. The
fix changed 14 of 262 boundaries (5%) and **zero** of the 35 scored
targets.

Before calling that a null result we ran the same code twice:

```
Kiddushin, 95 stories
  baseline vs fixed      (different code) :   6 (6%)
  fixed  vs fixed-repeat (SAME code)      :   3 (3%)   <- noise floor
```

And the two identical-code runs disagreed on the scoreboard: 50% vs 56%
HIT, because one target flipped NEAR→HIT from nondeterminism alone. On
16 scorable Kiddushin targets, one target is 6.25 points — and noise
moves about one target per run.

**Rule:** before attributing a score change to a code change, run the
SAME code twice and report that spread alongside the result. If the
effect is not larger than the spread, say so; do not report it as an
improvement.

**Why:** every prompt-tuning number this project has quoted came from
one run each side. A 6-point "gain" on a 16-target gate is one target,
which is exactly what the model moves on its own. Without the noise
floor you cannot tell a fix from a coin flip — and the write-up will
claim a fix, because that is the story you set out to tell.

**How to apply:** (a) One extra run of the unchanged side costs the same
as the run you already did — always spend it. (b) Report `n` targets and
"one target = X points" next to any percentage. (c) When the effect is
inside the noise, keep a change only on its own merits (this one is a
strict information improvement) and say plainly that the gate is silent.
(d) If a decision depends on the difference, fix the gate first — see
`docs/findings/2026-08-30-wave5-summary-fix.md` §5.
