# A blind Kiddushin boundary set: the 60% was never a fact about Kiddushin — 2026-08-31

**Capability: 4 Boundaries.** **Status of every number below: measured.** No API calls;
every run scored here was already on disk.

Kiddushin's boundary gate was **15 targets, all of them corrections, with a ±7-point
noise band** — one target worth 6.7 points. Applying Ketubot's 2026-08-30 method to
Jeff's newly parsed Kiddushin list gives **176 blind targets**, and the noise floor
collapses to one target worth **0.77 points**.

**Kiddushin scores 85% HIT / 91% HIT+NEAR, not 60% / 73%.** It clears the ≥75% gate, and
it scores *above* Ketubot's 80% / 84%. The old figure was not a measurement of Kiddushin;
it was a measurement of a biased 15-question exam.

---

## 1. The set

```bash
python3 scripts/build_boundary_testset_2005.py \
  --expert-json results/expert_lists/kiddushin_2005.json --expert-filter blind \
  --tractate Kiddushin --out tests/expert_boundary_targets_2005_kiddushin.json
```

| | Ketubot | Kiddushin |
|---|---|---|
| stories in | 149 | **89** (`blind`) |
| aligned | 147 (98.7%) | **88 (98.9%)** |
| targets | 294 | **176** |
| `align_fraction` median | 0.995 | **0.993** |
| `align_fraction` p10 / min | 0.973 / 0.912 | 0.972 / 0.887 |
| `bracket_ratio` median / p90 | 1.009 / 1.071 | 1.006 / 1.055 |
| rejected | 2 (`weak_alignment`) | **1** (`kiddushin_036`, 33a, `weak_alignment`) |

The alignment quality is indistinguishable from Ketubot's on every statistic, including
the tails. Jeff's Kiddushin transcription is his own edition in the same way his Ketubot
one is, and the same difflib alignment handles it.

**The filter is `blind` (89), not the `recall` filter (90) used for recall.** They differ
on 81b. Recall keeps it because we never proposed it, so counting it can only *lower*
our number. A boundary target has the opposite requirement: it must be an extent **Jeff**
chose. All five appendix entries are our own spans that he annotated, so a target built
from one would grade us against a boundary we picked. Excluding all five costs one story.

## 2. The score, and the noise floor that makes it readable

Both target sets scored today, separately, never pooled (Lesson 24).

**A — the new blind set (176 targets, 130 scorable):**

| run | scored | HIT | NEAR | MISS | N/A | hit | hit+near |
|---|---|---|---|---|---|---|---|
| no trimming (shipped) | 130 | 100 | 10 | 20 | 46 | **77%** | **85%** |
| Wave 5 clause spans | 130 | 110 | 8 | 12 | 46 | **85%** | **91%** |
| Wave 5, **same code, repeat** | 130 | 111 | 7 | 12 | 46 | **85%** | **91%** |

**B — the old corrections set (`expert_boundary_targets_v2.json`, 15 scorable on Kiddushin):**

| run | scored | HIT | NEAR | MISS | hit | hit+near |
|---|---|---|---|---|---|---|
| no trimming | 15 | 2 | 5 | 8 | 13% | 47% |
| Wave 5 clause spans | 15 | 9 | 2 | 4 | **60%** | **73%** |
| Wave 5, **same code, repeat** | 15 | 10 | 1 | 4 | **67%** | **73%** |

**The ±7 points is reproduced exactly, and so is its cause.** Across the two identical
runs **exactly one target changes verdict** — Kiddushin 66b seg 0 start, NEAR → HIT, from
model nondeterminism alone. On 15 targets that one flip is 6.7 points and reads as a
result. On 130 it is 0.77 points on HIT and **0 points on HIT+NEAR**. Same noise, same
single target; the denominator is the whole difference.

This is what the brief asked for and it is the deliverable: **a Kiddushin boundary score
that can adjudicate a change.** Before today, any change worth less than ~7 points was
invisible on this tractate.

## 3. What the score actually says

**Kiddushin clears the ≥75% hit+near gate on the shipped, untrimmed output alone (85%),
and reaches 91% with Wave 5 clause spans.** Scored today for a like-for-like comparison
(Lesson 11); Ketubot reproduces its published 80% / 84% and 75% / 83% exactly.

| | Ketubot (n=229) | Kiddushin (n=130) |
|---|---|---|
| no trimming — **what ships today** | 75% / 83% | **77% / 85%** |
| Wave 5 clause spans — best mechanism | 80% / 84% | **85% / 91%** |
| same-code noise floor | 0 pts | 0.8 pts (1 target) |
| N/A (no story covers the segment) | 65 / 294 (22%) | 46 / 176 (26%) |

**Kiddushin is the better tractate for boundaries, not the worse one.** Every document in
this repo says the opposite, and every one of them was quoting the 15-target exam. The
ordering reverses on both the shipped output and the Wave 5 mechanism.

By direction, Wave 5 on Kiddushin: starts 86% / 93% (n=69), ends 84% / 89% (n=61).

## 4. The clause-edge ceiling generalizes

**88% of Jeff's Kiddushin boundaries fall exactly on a clause edge** — 154 of 176 —
against Ketubot's 87% (257 of 294). Split by direction the agreement is closer still:

| | Ketubot | Kiddushin |
|---|---|---|
| start on a clause edge | 79% (116/147) | **80%** (70/88) |
| end on a clause edge | 96% (141/147) | **95%** (84/88) |

So the ~87% ceiling that justified Wave 5's clause anchoring is **not a Ketubot artifact**.
It is stable across two tractates, twenty-year-old transcriptions, and 470 boundaries —
and the start/end asymmetry is stable too: ends are nearly always clause-aligned, starts
are where the residual 20% lives. That is the first evidence that the finer-splitter
question is a *start* problem.

Measured with the letter test, per the guardrail: a clause range runs past its closing
full stop while Jeff's text ends on a letter, so the honest question is whether any Hebrew
**letter** is left outside his boundary. `clause_of()` already does this.

## 5. Cross-check against the corrections set

14 boundaries appear in both sources (same ref, segment and direction) — against Ketubot's
32.

| | Ketubot | Kiddushin |
|---|---|---|
| starts agreeing | 7/7 | **2/3** |
| ends agreeing | 16/19 | **8/11** |
| overall | 84% (27/32) | **71% (10/14)** |

**Ketubot's clean "agree on starts, split on ends" pattern does not reproduce, and the
Kiddushin overlap is too small to say much.** Three start boundaries is not a sample. Of
the three end disagreements, two have the 2005 boundary *later* than the 2026 correction,
which is the direction Lesson 24 predicts — but that is a count of three and it is
recorded as a count of three, not as evidence. One of the four (25a seg 4) is a
`needs_human` / `polarity: unclear` target the scorer skips anyway.

## 6. Ends, under the standard Simon settled — reported, not tuned

The brief's guardrail says do not tune ends against this set until Jeff answers. This is
measurement only: scoring the 2005 end as an **upper bound** (ending earlier than Jeff-2005
is expected under the Jeff-2026 standard; ending later is wrong under both).

| | exact | earlier (expected) | **LATER (wrong either way)** |
|---|---|---|---|
| Kiddushin, no trimming (n=61) | 48 | 0 | **13** |
| Kiddushin, Wave 5 (n=61) | **51** | 4 | **6** |
| Ketubot 61-112, no trimming (n=76) | 60 | 0 | **16** |
| Ketubot 61-112, Wave 5 (n=76) | 57 | 10 | **9** |

End-trimming halves the definite overshoots on both tractates. **On Kiddushin it does so
while also raising exact matches (48 → 51)**, where on Ketubot it trades 3 exacts for 7
fewer overshoots. Kiddushin is the cleaner case for end-trimming, and nothing here depends
on Jeff's answer, because *later than his 2005 boundary* is wrong under either standard.

## 7. What changed in the code

- **`scripts/build_boundary_testset_2005.py`** takes `--expert-json` / `--expert-filter`
  and stamps `source_round` per tractate. Verified inert first: the Ketubot build is
  **byte-identical** to the committed 294-target file.
- **`scripts/score_boundary_targets.py`** classified blind-vs-corrections by the literal
  filename `expert_boundary_targets_2005.json`, so the new Kiddushin set would have been
  **reported as a corrections set** — exactly the pooling Lesson 24 forbids, arriving
  through a string comparison. It now classifies on `source_round`.

## 8. Retire the old number

**The 60% / 73% is superseded, not averaged.** It answers "did we fix the boundaries Jeff
flagged as wrong", which the corrections set is still the right instrument for and which
is still worth reporting — separately, and with its ±7 noise stated. It never answered
"are our Kiddushin boundaries right", and it is the second number in this project to have
been quoted for months as though it did (Lesson 23).
