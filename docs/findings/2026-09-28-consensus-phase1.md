# Consensus phase 1: two models agreeing does not mean Jeff agrees — no-go (indicated)

**2026-09-28.** Status: **indicated**, as the plan fixed in advance
([`consensus-at-scale` §4](../history/2026-09-28-PLAN-consensus-at-scale.md)).
Item: [`consensus-1-test-the-bet`](../../work/done/2026-09-28-consensus-1-test-the-bet.md).
**The Claude arm is incomplete**: the Anthropic account ran out of credit after 403 of
997 calls (§5). The decision below does not depend on the missing calls, and §4 says why.

## 1. The answer

| §4 criterion | threshold | result | |
|---|---|---|---|
| models agree with each other | ≥ 80% | **197/235 = 84% [79–88]** — Ketubot + Gittin only | met |
| agreed verdicts contradict his `no` | ≤ 2 | **1** agreed `story` (+ 5 agreed `borderline`) | met |
| list stories called `not` | ≤ 2 | **Gemini alone: 47 of 444 [8–14%]**; consensus projected **≈ 43** | **fails** |

**No-go.** The costly error the bet had to rule out on the *positive* side is not rare:
when both models read one of his stories they call it *not a story* one time in eight
(10 of 76 of his `yes` review spans, below), and on his 2005 lists Gemini alone says `not`
to 47. Nothing may be called consensus. The panel can still rank a review queue.

**Which rule the errors cite: R-C5**, overwhelmingly — 98 of the 229 rule citations on
answers that disagree with him (Gemini 55, Claude 43), then R-C2 (62). All 10 agreed
`not`s on his `yes`es cite R-C5. The models read *"a bare report of what someone did is
not a story"* far more broadly than he applies it: a short incident with a ruling
attached, which he keeps, they drop.

## 2. What was judged

The span he judged, exactly as he saw it (never a detector candidate), and every story on
his 2005 lists (positives only). Eruvin was not read. `labels.json` records every source
and every rule's effect; `scripts/judge_labelled_spans.py labels` rebuilds it.

**His verdicts, read against what he was SHOWN.** Before the axes UI every round asked
*is the detector's call correct?* A `correct` on a span the detector called
`NOT_A_STORY` is his **no** — 87 of the 128 verdicts in the 2026-02-05 round are exactly
that. So every old verdict was read against the classification on the page he reviewed,
recovered from the HTML he sent back, from `ketubot_61-112.html` at `0f1f3a4` (the
page was regenerated two days after his review), or from the round file. Where that
page carries segment text it was compared with ours: no drift.

| what was done | rows |
|---|---|
| review files read / excluded by name (Simon's test, Simon's pre-screen, the per-daf January round, two empty files) | 9 / 5 |
| verdict rows read | 623 (8 of them Simon's pre-screen, excluded) |
| `incorrect` with no readable objection → **unknown** | 12 (+2 boundary/merge objections on a `NOT_A_STORY` call) |
| read by hand where the rules misread the note (`HAND_LABELS`, each quoted) | 5 |
| spans with two different labels — reported, not scored | 7 |
| list stories his later verdict called not-a-story — reported, not scored | 4 |

| scored units | Ketubot | Kiddushin | Gittin | Yevamot |
|---|---|---|---|---|
| review `yes` / `no` / `borderline` / `out_of_scope` | 100 / 98 / 34 / 0 | 89 / 11 / 0 / 1 | 3 / 18 / 4 / 2 | 1 / 3 / 0 / 0 |
| evidence | CIRCULAR | CIRCULAR | rule-informed | rule-informed |
| 2005 list stories (BLIND list) | 146 | 89 | 111 | 102 |
| `applies_to: corrected` (reported separately) | 185 | | | |

The plan expected ~24 Ketubot negatives; reading the verdicts against what he was shown
finds **98** — most are his confirmations of the detector's own `NOT_A_STORY` calls.

## 3. Results

Prompt `src/prompts/judge_register_v1.md` (sha `a7d4200c3333`, carrying STORY_RULES
§Scope–§Boundaries), code at `f93695c` plus this branch. `gemini-3-flash-preview`
(thinking off, temperature 0.1, the project client); `claude-opus-5` (adaptive thinking,
effort `medium`, structured output, no server-side fallback — a fallback model answering
would change which model the arm measures).

**Review spans, both models answered** (brackets: Wilson 95%):

| | both answered | models agree | agreed on his `no`: right · `story` · `borderline` | agreed on his `yes`: right · `not` | splits: Gemini / Claude / neither sides with him |
|---|---|---|---|---|---|
| pooled | 235 | 197/235 = 84% [79–88] | 87/93 [87–97] · **1** · 5 | 65/76 [76–92] · **10** | 13 / 20 / 5 |
| Ketubot | 208 | 180/208 = 87% [81–90] | 77/82 · 1 · 4 | 65/75 · 9 | 10 / 14 / 4 |
| Gittin | 27 | 17/27 = 63% [44–78] | 10/11 · 0 · 1 | 0/1 · 1 | 3 / 6 / 1 |
| Kiddushin, Yevamot | 0 | not reached before the credit ran out | | | |

- Pages STORY_RULES cites as cases: 18/23 agree (78%); 9/9 right on his `no`s. Not cited:
  179/212 (84%); 78/84 right on his `no`s. The cited pages are not visibly easier.
- **The one agreed `story` on his `no`**: Ketubot 111a 23-25 (*"It is not even a story"*),
  both citing R-C4 — a story embedded in a letter.
- **The five agreed `borderline`s on his `no`s** all cite R-C2 (speech with conflict).
  Four are Ketubot `no`s from February, before `borderline` existed as an answer; one is
  Gittin 88a (*"A legal problem and answer"*). Whether they are errors depends on whether
  a February `no` survives R-C2. Counted as agreement-with-him failures, not as the
  criterion-2 error.
- **His `borderline`s (37 answered):** agreed on 26, of which 13 agreed `not` and 10
  agreed `story` — the models do not use the category where he does.
- **Corrected rows** (Ketubot canonical round, reported separately): 138/167 agree (83%);
  on his `no`s the agreed verdict is right 10/17.

**The list criterion.** Claude reached no list story. Gemini, alone, calls 47 of 444
`not` (Ketubot 18, Kiddushin 7, Gittin 10, Yevamot 12), almost all citing R-C5. On the
review set, of his `yes`es Gemini called `not`, **Claude also called `not` 10 of 11** —
and Claude says `not` more often than Gemini overall (127 of 235 review spans vs 145 of
364). At that rate the consensus-`not` count on the lists is ~43; to pass, Claude would
have to break with Gemini on 45 of 47 where it broke on 1 of 11. The failure does not
wait on the missing calls.

## 4. Spread (Lesson 43)

The Gemini arm repeated in full, same code, same day: **0 of 359 review verdicts changed**,
5 of 440 list verdicts, 1 of 184 corrected. The Claude arm was not repeated. The smoke
test, run twice (a format fix between, §5), is the only Claude repeat: **3 of 20** Claude
verdicts moved (Gittin 19a:16 story→borderline, 70a:22 borderline→not, 74b:4 not→story).
Claude's spread is therefore not small; the agreement figures carry it.

## 5. Failures — counted, never scored

| | Gemini (full) | Gemini (repeat) | Claude (full) |
|---|---|---|---|
| ok | 992 | 986 | 403 |
| invalid (segments as strings ×4, a JSON array ×1) | 5 | 5 | 0 |
| failed (Gemini 503 ×6; Anthropic **"credit balance is too low"** ×594) | 0 | 6 | **594** |
| refused | 0 | 0 | 0 |

- **The Claude arm stopped at call 404 on a 400 "credit balance too low".** The Lesson 21
  guard did what it is for: 594 failed calls are 594 rows with no verdict, and every
  figure above is over answered rows only. `run` resumes only `failed` rows:
  `python3 scripts/judge_labelled_spans.py run --set full --backend claude --out results/consensus/phase1/full.json`
  (~594 × $0.030 ≈ $18 at the measured rate).
- **A format defect, caught at call 32:** each segment was shown with both a sequence
  number and its page index, and 2 of the first 32 Gemini answers used the page index.
  The run was stopped, the page index removed from the passage, and the smoke test re-run
  under the fixed prompt (`smoke_format1.json` keeps the first smoke).
- **Smoke test** (10 of his `yes`, 10 of his `no`, Gittin 2026-09-02 first): 0 agreed
  `story` on his `no`s, 1 agreed `borderline` (Gittin 19b:6) — under the stop rule of 2.
  Agreement was 11/20, which already pointed where the full run went.

**Cost:** Claude **$8.94** (smoke $0.59 + $0.57, full $7.78). Gemini not metered.

## 6. What this changes

- **Nothing is called consensus.** Phase 2 as written (a consensus tier published with an
  audit) does not start. The models can rank a queue; they cannot clear one.
- **R-C5 is where the judge and he part.** The plan's own rule applies: decompose only
  where a rule fails. A narrow R-C5 question — *does anything follow the act?* — with his
  keep-cases beside his drop-cases is the candidate, tested on these same labels.
- **An existing script reads old verdicts the wrong way.** `map_verdict_vocabularies.py`
  maps `base_binary correct → is_story=yes` regardless of what the reviewer was shown, so
  the 87 `correct`-on-`NOT_A_STORY` verdicts of 2026-02-05 read there as *yes*. Not fixed
  here (out of this item's `writes:`); it should be.

---

## 7. Why it failed — diagnosis (2026-09-28, same day, after the run)

**Measured on the outputs above; no new model calls.** Scripts and data:
`scripts/diagnose_phase1_list_misses.py` → `results/consensus/phase1/list_misses.json`;
the hand sort → `results/consensus/phase1/list_misses_categories.json`.

### 7a. The passage was right; the rule was wrong

The first suspect was the unit: the judge sees the segments the recall matcher located,
and a truncated passage would read as a "bare report". It is not that. Of the 47 list
stories Gemini called `not`, **31 had ≥ 90% of his story's text inside the passage, 16 had
60–90%, none had less.** His stories there are short — median 26 Hebrew words — and the
judge read all of them.

### 7b. What the 47 are, read one by one

| shape | n | example |
|---|---|---|
| **an incident, then a ruling** — something happens to someone, a rabbi or court responds | **21** | *"A certain man said: my property to Toviya. He died. Toviya came. R. Yoḥanan said…"* (Ketubot 85b) |
| a single act with an outcome, or a first-person incident | 10 | *"Rav Shimi bar Ashi treated a gentile for it, and he was healed"* (Gittin 69b) |
| an eyewitness wonder (*"I myself saw…"*) | 5 | the fertility of the Land, Ketubot 111b |
| a habitual practice | 4 | R. Abba tying coins in his scarf, Ketubot 67b |
| speech only | 4 | Kiddushin 31b |
| a rule applied to the wrong thing | 3 | R-C1 to a Mishnah *cited* in the Gemara (which R-C1 calls Talmudic); R-B4 to the Gemara's retelling |

Every one of the 47 cites R-C5. **All 10** of his reviewed `yes`es that both models called
`not` have the same shapes (Toviya's bequest; the court forcing a master to free a slave;
a palm tree left in a will; the Land's wonders) and all cite R-C5.

### 7c. The cause: the register was missing the rule that bounds R-C5 — and R-C5 carried our gloss

On 2026-07-06 Jeff gave the project's foundational criteria: *"Legal problems/cases are
hypothetical… Stories are about events that happened"*; and, explicitly, *"A man stole
another man's cow and sold it. Rava ruled…. In this case you may have a story."* Halakhic
stories are in scope. **None of that was in `docs/STORY_RULES.md`**, which was begun on
2026-09-01 from his Gittin answers and never back-filled from July. Then on 2026-09-25 R-C5
was written from four 2026-09-23 cases with a gloss of ours — *"one act, however it is
introduced — even מעשה ב… — is a precedent, not a story"* — which says the opposite of the
cow case. A judge given exactly the register, faithfully applied it.

**So the no-go measures our register, not the bet.** Fixed in `STORY_RULES.md` the same day:
R-C0 added in his July words; the R-C5 gloss removed and recorded as a correction; the line
between them written as **our proposal**, flagged for him (`jeff:report-vs-incident`).
The same gloss is in the shipped twin-pass question (`_twin_prompt`, 2026-09-25) — see §9.

### 7d. The rest of the disagreement

- **His `borderline`s** (Gemini alone, 38): 20 `story`, 15 `not`, 3 `borderline`. The register
  defines borderline only for speech-with-conflict (R-C2); his February borderlines are
  broader — *"one event"*, *"lacks specificity"*, *"no causality"*, *"lacks real change"*. The
  judge was never told that. Not a model failure; an unwritten rule.
- **His `no`s the models call `borderline`** (5 agreed): four Ketubot February `no`s given
  before `borderline` was an answer he could choose, one Gittin *"legal problem and answer"*.

## 8. Corrections to §1–§5 (2026-09-28, same day)

- **The 84% inter-model agreement is flattered by easy cases.** On Ketubot spans the
  detector had already called `NOT_A_STORY` and he confirmed, the models agree 76/82. On
  Gittin — the hard cases, unlisted extras he judged on the axis page — they agree 11/18 on
  his `no`s and 1/3 on his `yes`es. Agreement depends on what is in the set; quote it by
  stratum, never pooled.
- **"Claude's spread is not small (3 of 20)" is withdrawn as a measurement.** The two
  smoke runs used **different prompts** (the segment-numbering fix of §5 came between them),
  so the difference is a prompt change plus sampling, not sampling alone. Claude's run-to-run
  spread is **unmeasured**. (Claude Opus 5 takes no temperature parameter, so it should be
  assumed nonzero until a same-prompt repeat measures it.)
- **Gemini the judge is steady where Gemini the detector is not** — 0 of 359 review
  verdicts moved on a full repeat, against 3 of 102 stories flipping between identical
  detector runs (Lesson 43). Suspected, not measured: one short question per call vs a long
  page with chained calls (iterative pass, twin pass) that compound small differences.
- **`map_verdict_vocabularies.py` and `build_ruler.py` read an old `correct` as "accepted as a
  story" whatever the detector had shown.** Before 2026-09-02 the rounds asked *is the
  detector's call correct?*; a `correct` on a `NOT_A_STORY` call is his **no** (87 of the 128
  verdicts of 2026-02-05). This item's labels read them correctly; those two scripts do not,
  so the per-round "precision" in `results/rulers/*_ruler.json` is partly agreement with the
  detector's call. Size not measured. Item:
  [`verdicts-read-against-the-call-shown`](../../work/2026-09-28-verdicts-read-against-the-call-shown.md).

## 9. What happens next

1. **Re-run phase 1 on the corrected register** —
   [`consensus-1b-corrected-register`](../../work/2026-09-28-consensus-1b-corrected-register.md).
   Started 2026-09-28 and stopped at once: **the Gemini project hit its monthly spend cap**
   (all 997 calls `failed` with 429, counted, none scored; `full_v2_gemini.json` resumes
   them). Claude is also out of credit. **Both are Simon's to raise.** The §4 go/no-go is
   unchanged; the result is labelled *same-data* — the register was corrected after seeing
   these failures, so a pass here is indicated, and the Yevamot audit remains the real test.
2. **The twin-pass question carries the same gloss** —
   [`twin-pass-r-c5-wording`](../../work/2026-09-28-twin-pass-r-c5-wording.md). A detector
   change: measured with a repeat per arm, not edited blind.
3. **Ask him where the line falls** — `jeff:report-vs-incident` in `comms/JEFF.md`, with the
   cases above on both sides.
4. **Phase 2 stays blocked** until a go.
