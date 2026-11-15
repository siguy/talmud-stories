# The narrate test (2026-11-14)

Work item: [`work/done/2026-11-14-narrate-test.md`](../../work/done/2026-11-14-narrate-test.md). Script `scripts/narrate_test.py`,
prompt `src/prompts/narrate_v1.md`, data `results/shas_run/narrate_test/` (`score.json` has every number below).

**Headline (measured).** Neither claim holds as a way to ship stories or move borders.
1. *Classification:* `can_narrate == yes` recovers far more of Jeff's yes than the rule grader (80/141 and 84/141 vs 32/141)
   but at precision 0.81 / 0.80, not 0.95. The pre-registered second-judge rule (`grader story OR (narrate yes AND grader
   borderline)`) lands at precision 0.83-0.84, Wilson lower bound 0.74-0.76. **Misses both bars** (precision >= 0.90, LB >= 0.80).
2. *Boundaries:* the narrator's min/max `needed_segments` equals the detector's span in 168/190 (pass 1) and 169/191 (pass 2)
   units, and moves **at most 2 targets in either direction per tractate**. It does not beat the detector on Ketubot ends.

Nothing ships from this item.

## What ran

- **Narrator:** Claude Code subagents on **Sonnet** (`claude-sonnet-5-5`), 20-passage batches, two independent passes (different
  subagents, different shuffle seeds 1 and 2), 493 units each, all 493 answers valid in both passes. It never saw
  `STORY_RULES.md`, span ids, keys or the manifest. Window = passage +-3 segments, PASSAGE segments marked.
- **Classification set (CLS, 300 spans):** the calibration manifest. C1 (158 spans) is **CIRCULAR** (Jeff's
  verdicts on what the detector showed him, and the golden LOW stories on his list); C2 (142 spans, Eruvin/Yevamot) is **BLIND**.
  Jeff `borderline` = not a story. Precision is over spans whose truth is known; `unknown` (on no list) is counted apart.
- **Boundary set (BND, 193 units = 121 Ketubot + 72 Kiddushin detector stories):** every detector story (`results/v10/wave4_notrim`)
  covering a scorable target of the **BLIND** 2005 lists (Ketubot 294 targets, Kiddushin 176). Scored by
  `score_boundary_targets.score()` unchanged; the narrator's span is written in the detector's own run shape (start/end segment, no
  text span), so both runs get the same segment-level clause defaults and are scored on the **same targets**. All targets lie
  inside the +-3 window, so the window is not what limits the narrator.

## Caveat that governs every comparison to the grader

The rule grader's numbers (`results/shas_run/low_pool/calibration/pass*/claude.json`, precision 32/33, recall 32/141) came from
**Opus with the rule register and a +-1 segment window**; the narrator is **Sonnet without rules and a +-3 window**. Model, prompt
and context all differ. Differences below are **not attributable** to "narrating" as such; the test shows what *this* Sonnet
narrator does, not what narrating does in general. (The Opus-vs-Sonnet gap alone could account for part of the precision gap.)

## 1. Classification (measured)

| arm | scope | precision (known) | Wilson 95% | recall of Jeff yes |
|---|---|---|---|---|
| grader story (both passes) | all | 32/33 = 0.97 | .85-.995 | 32/141 = 0.23 |
| narrate yes, pass 1 | all | 80/99 = 0.81 | .72-.87 | 80/141 = 0.57 |
| narrate yes, pass 2 | all | 84/105 = 0.80 | .71-.87 | 84/141 = 0.60 |
| narrate yes, both passes | all | 73/89 = 0.82 | .73-.89 | 73/141 = 0.52 |
| narrate yes or partial, pass 1 / 2 | all | 0.78 / 0.76 | .71-.83 / .69-.82 | 125/141 / 129/141 = 0.89 / 0.91 |
| COMBINED (grader story OR narrate yes & grader borderline), pass 1 / 2 / both | all | 0.83 / 0.84 / 0.84 | LB .74 / .76 / .75 | 0.56 / 0.57 / 0.52 |

By evidence (narrate yes, pass 1 / pass 2):

- **CIRCULAR (C1):** precision 60/77 = 0.78 / 62/79 = 0.78; recall 60/104 / 62/104 (0.58 / 0.60).
- **BLIND (C2, Eruvin/Yevamot):** precision 20/22 = 0.91 (.72-.98) / 22/26 = 0.85 (.67-.94); recall 20/37 / 22/37 (0.54 / 0.59);
  +17 / +14 called-yes spans that sit on no list (truth unknown, so excluded; a lower bound only). The blind precision is higher than
  circular but the intervals overlap and n is 22-26.

Where it helps: of the spans the grader called `borderline` and the narrator `yes`, Jeff said yes on 47/71 (pass 1) and 49/72
(pass 2) (known-truth precision 47/62 = 0.76, 49/63 = 0.78): the narrator does recover Jeff-yes stories the grader left out, but
at roughly a 20 point precision cost (0.76 vs 0.97). The combined rule gains 47 Jeff-yes over the grader alone (79 vs 32) and loses 14 points of precision (0.83 vs 0.97).
The `partial` bucket is mostly yes (Jeff yes on 25/29 and 23/29 of known-truth grader-borderline partials), so `yes|partial`
is almost all of Jeff's yes (recall 0.89-0.97) but is not selective.
The narrator says `no` on 86 / 75 spans; of those with known truth, Jeff's yes is 16 / 12 vs not-yes 25 / 21: `no` is a real
signal (it correctly catches non-stories) but not clean.

Stability across passes: same `can_narrate` 246/300, same yes-or-not 266/300 (89%). Two same-prompt passes disagree on 11% of
spans, so differences of a few spans between arms are inside noise.

**Against the pre-registered bar:** precision >= the grader's 0.95 **fails** (0.80-0.82); recall clearly above 32/141 **passes**;
combined-rule precision >= 0.90 with LB >= 0.80 **fails** (0.83-0.84, LB 0.74-0.76). As a stand-alone or second judge for shipping
cards to the family site this narrator is not good enough. As a *recall* signal for review (a ranked list of what the grader missed) it
is useful: 47-49 Jeff-yes recovered per pass among grader-borderline spans.

## 2. Boundaries (measured, BLIND)

Hit rates, segment-level scoring, narrator vs detector **on the same targets** (HIT / NEAR / MISS; N/A where the narrator said `no` or
the span covered nothing):

| tractate | direction | pass | detector hit (hit+near) | narrator hit (hit+near) | flips |
|---|---|---|---|---|---|
| Ketubot | start | 1 | 93/122 = .762 (.852) | 92/122 = .754 (.844) | -1 HIT |
| Ketubot | start | 2 | 92/119 = .773 (.874) | 90/117 = .769 (.872) | 2 HIT -> N/A |
| Ketubot | **end** | 1 | 77/104 = .740 (.798) | 78/102 = .765 (.824) | MISS->HIT +2, HIT->MISS -1 |
| Ketubot | **end** | 2 | 77/101 = .762 (.822) | 76/98 = .776 (.837) | MISS->HIT +2, HIT->MISS -1, HIT->N/A 2 |
| Kiddushin | start | 1 / 2 | .765 / .754 | .779 / .768 | MISS->HIT +1 each |
| Kiddushin | end | 1 / 2 | .800 / .787 | .814 / .783 | HIT->MISS -1 (pass 2) |

(Full rows incl. N/A in `score.json`; the all-covered detector baseline is Ketubot start .758 / end .743, Kiddushin start .754 / end
.787.)

The Ketubot end hit-rate rises 1.5-2.5 points in the narrator's favour, which is **two targets** (two MISS -> HIT) against one
HIT -> MISS, and the narrator's N/A (`no` on 2-7 stories) shrinks its denominator. Pass 1 and pass 2 differ from each other by about as much as either differs from the detector. **Ketubot's
end deficit is not recovered:** the detector has 21 end MISSes; the narrator turns 2 of them into HIT in each pass and leaves 12 as MISS (the rest are N/A or share a segment). The
start side is level. Both passes agree, so the claim "beats the detector on ends without losing starts" is **not supported**.

Why: the narrator echoes the card. Its min/max `needed_segments` equals the detector's span in 168/190 (pass 1) and 169/191 (pass 2)
units; it extends the end beyond the card in 7 / 9 and trims it in 9 / 6, starts earlier in 7 / 7. The PASSAGE marker anchors it: this
is a **boundary check of a given span**, not an independent search for where the story is. (A prompt that withheld the card's extent
and showed an unmarked window is the untried variant, and the only way to test the "independent judge of borders" claim; see below.)

## What this does and does not show

- *Measured:* all numbers above.
- *Indicated:* Sonnet-narrate-yes is a *recall* tool; narrating mostly agrees with the detector's extent when told the extent.
- *Suspected, not tested:* Opus as the narrator would raise precision (model confound above); an unmarked window would test borders;
  the 11% unstable spans are mostly the `partial` boundary of yes/partial.
- Single run of 300 + 193 per pass; classification CIs above are Wilson 95%.

## Untried / for Simon

1. If a recall aid for the review queue is wanted: use `narrate yes AND grader borderline` to order cards for Jeff (47/62
   known-truth hit rate), never to ship. 2. If the border claim matters, re-run with the PASSAGE marker removed (window only) and
   on Opus, so the narrator cannot echo. Neither is run here.

## Addendum: the fair run (Opus, the grader's view) (measured)

Asked for: remove the confounds. Same 300 classification spans, narrator = **Opus** (`claude-opus-5-5`, the grader's model),
**+-1 segment window**, passage marked (the grader's exact view), still **without** `STORY_RULES.md`. Two passes, 300 valid
answers each. Run with `python3 scripts/narrate_test.py --variant opus_ctx1 ...`; data in `results/shas_run/narrate_test/opus_ctx1/`.
Boundaries were not re-run (the grader never judged them, and a marked window can only echo the card; the unmarked-window variant is
still untried).

| arm | precision (known) | Wilson 95% | recall of Jeff yes |
|---|---|---|---|
| grader story (Opus, rules) | 32/33 = 0.97 | .85-.995 | 32/141 = 0.23 |
| narrate yes, Opus pass 1 | 91/113 = 0.805 | .72-.87 | 91/141 = 0.65 |
| narrate yes, Opus pass 2 | 86/108 = 0.796 | .71-.86 | 86/141 = 0.61 |
| narrate yes, both passes | 80/99 = 0.808 | .72-.87 | 80/141 = 0.57 |
| narrate yes or partial, pass 1 / 2 | 137/184 = 0.745 (both) | .68-.80 | 137/141 = 0.97 |
| COMBINED (grader story OR narrate yes & grader borderline), pass 1 / 2 / both | 0.84 / 0.84 / 0.84 | LB .76 / .75 / .75 | 0.60 / 0.59 / 0.56 |

BLIND (C2): narrate yes precision 25/29 = 0.86 (.69-.95) and 23/27 = 0.85 (.68-.94); recall 25/37 and 23/37. Of the spans the grader
called borderline and Opus-narrate called yes, Jeff said yes on 52/76 and 51/74 (known-truth 52/67 = 0.78, 51/66 = 0.77). Pass-to-pass:
same `can_narrate` 247/300, same yes-or-not 264/300.

**Read:** the model and context confounds were not what separated the arms. Opus-narrate reads the same as Sonnet-narrate
(precision 0.80 vs 0.80-0.81, recall 0.61-0.65 vs 0.57-0.60), and the combined rule is unchanged (0.84, LB 0.75-0.76; bar 0.90 / 0.80, still
missed). What is left is **the prompt**: the rule register makes the grader strict (precision 0.97, recall 0.23); a narration prompt without
it says yes to anything with a sequence of events, including the ~20% of those that Jeff calls borderline or no. That attribution is
now supported by an arm that holds model and view equal, which the first run could not say. It is still one prompt on one set; whether a
*narrate-then-apply-rules* prompt would keep recall and recover precision is untested.
