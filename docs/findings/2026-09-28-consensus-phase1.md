# Consensus phase 1: two models agreeing does not mean Jeff agrees — no-go (indicated)

**2026-09-28.** Status: **indicated**, as the plan fixed in advance
([`consensus-at-scale` §4](../history/2026-09-28-PLAN-consensus-at-scale.md)).
Item: [`consensus-1-test-the-bet`](../../work/done/2026-09-28-consensus-1-test-the-bet.md).
**The Claude arm is incomplete**: the Anthropic account ran out of credit after 403 of
997 calls (§5). The decision below does not depend on the missing calls, and §4 says why.

**Update 2026-10-01 — §10, phase 1b on the corrected register: no-go again (same-data /
indicated).** Agreement 80%, but 4 agreed `story` on his `no`s and 9 list stories called
`not` by both (limits 2 and 2); a same-prompt repeat gives 5 and 8. The R-C0 fix overshot:
Gemini's list `not`s fell 47 → 10 while its `story` on his `no`s rose 10 → 32. The Claude
arm ran as Claude Code subagents, not the API (§10a).

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
  [`verdicts-read-against-the-call-shown`](../../work/done/2026-09-28-verdicts-read-against-the-call-shown.md).

## 9. What happens next

1. **Re-run phase 1 on the corrected register** —
   [`consensus-1b-corrected-register`](../../work/done/2026-09-28-consensus-1b-corrected-register.md).
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

---

## 10. Phase 1b — the same test on the corrected register (2026-10-01): **no-go again (same-data / indicated)**

Item: [`consensus-1b-corrected-register`](../../work/done/2026-09-28-consensus-1b-corrected-register.md).
Same labels (`labels.json`), same prompt file, register as corrected on 2026-09-28 (R-C0
added, R-C5 gloss removed): prompt sha `f13af144f32d`, rules sha `88c035b7e7b1`.
**Same-data:** the register was corrected after seeing §1–§7's failures on these very
spans, so whatever this shows is *indicated*. The phase 2 audit would be the real test,
and it does not start (§4 of the plan).

### 10a. What ran — and the one change to the method

| arm | model | how | ok / invalid / failed |
|---|---|---|---|
| Gemini, full | `gemini-3-flash-preview`, thinking off, T 0.1 | API, one call per span (resumed the 997 rows stopped by the 429 cap) | 992 / 5 / 0 |
| Gemini, repeat | same | same | 994 / 3 / 0 |
| Claude, full | **Opus 5.5 as a Claude Code subagent**, not `claude-opus-5` via the API | 40 subagents × 25 spans | 997 / 0 / 0 |
| Claude, repeat | same | 40 subagents, **re-shuffled** (seed 2 vs 1) | 997 / 0 / 0 |

- **Why the Claude arm changed:** on 2026-10-01 the Anthropic account still refused every
  call (*"credit balance is too low"*, 997/997 failed, $0), and Simon declined to fund API
  calls. He chose subagents over a second Gemini model (same family, correlated errors) or
  no go/no-go. `scripts/judge_via_subagents.py` exports each span's **exact** user prompt
  (from `judge_labelled_spans.user_prompt`) and the exact system prompt; each subagent
  `cat`s the prompt file, then its 25 passage files, and writes one JSON object; `import`
  runs every answer through the same `ask()` validation the API arms use.
- **What differs from the API arm, and could matter:** (1) the model is Opus 5.5, not Opus
  5; (2) 25 spans share one context, not one call each — the batches are seeded shuffles,
  so batch-mates are unrelated, and the repeat re-shuffles them, so **the Claude spread
  below includes batch-mate effects**; (3) the judge prompt arrives as a file, not as the
  system prompt; (4) no structured-output constraint (every answer still parsed, 0 invalid).
- **Two leaks closed before any answer was scored.** Span ids say `list:` for a story on his
  list — the label itself — so files are numbered, never named; ids live in a `keys/` folder
  no agent is told about. And a subagent's tool output is cut off past ~30 KB: the
  transcripts were audited for each passage's last 150 characters, **5 of 997** run-1 spans
  had not been seen in full, and those 5 were re-judged one file at a time by a fresh agent
  (marked `rejudged` in the output). The repeat, told to `cat` at most 3 files at a time,
  saw 997/997 in full.
- **Cost:** Gemini not metered; Claude **$0 API**, ~81 subagents at ~150k tokens each on
  Simon's plan. A crash in the Claude budget tally (it tripped on `list_misses.json`, a
  list) was fixed first — the only edit to `judge_labelled_spans.py`.

### 10b. The answer — §4, fixed in advance, not moved

| §4 criterion | threshold | run 1 | repeat | |
|---|---|---|---|---|
| models agree with each other (review spans) | ≥ 80% | **291/363 = 80.2% [75.8–83.9]** | 295/364 = 81.0% [76.7–84.7] | met, by 0–4 spans |
| agreed verdicts contradict his `no` | ≤ 2 | **4** agreed `story` (+ 2 agreed `borderline`) | **5** | **fails** |
| his list stories called `not` (by both) | ≤ 2 | **9 of 444 [1.1–3.8%]** | **8 of 445** | **fails** |

**No-go, on both runs.** The repeat moves each failing count by one; both stay at more than
double the limit. Phase 2 stays blocked.

**What the correction did** (v1 = §3, old register; Claude v1 answered 403 rows):

| | v1 | 1b run 1 | 1b repeat |
|---|---|---|---|
| list stories Gemini alone calls `not` | **47** of 444 | **10** | 10 |
| list stories Claude alone calls `not` | (none reached) | **39** of 448 | 38 |
| list stories both call `not` | (≈43 projected) | **9** | 8 |
| his `no`s Gemini calls `story` | 10 of 130 | **32** of 130 | 32 |
| his `no`s Claude calls `story` | 2 of 108 | 6 of 130 | 6 |
| agreed `story` on his `no` | 1 | **4** | 5 |
| his reviewed `yes`es both call `not` | 10 of 76 | 1 (Ketubot 105a:13) | 1 |

The fix landed on the miss it was aimed at and **overshot on the other side**: Gemini
stopped dropping his list stories (47 → 10) and started accepting his rejections (10 → 32).
Claude moved much less in either direction.

### 10c. By stratum (run 1; `report --markdown`, never pooled only)

| review spans | both answered | models agree [95%] | agreed on his `no`: right · `story` · `borderline` | agreed on his `yes`: right · `not` | splits: Gemini / Claude / neither sides with him |
|---|---|---|---|---|---|
| pooled | 363 | 291 = 80% [76–84] | 84/90 · 4 · 2 | 165/173 · 7 | 23 / 33 / 16 |
| Ketubot (CIRCULAR) | 231 | 195 = 84% [79–88] | 73/77 · 3 · 1 | 95/96 · 1 | 7 / 15 / 14 |
| Kiddushin (CIRCULAR) | 101 | 82 = 81% [72–88] | 4/5 · 0 · 1 | 69/76 · 6 | 13 / 4 / 2 |
| Gittin (rule-informed) | 27 | **11 = 41% [24–59]** | 4/5 · 1 · 0 | 1/1 · 0 | 2 / **14** / 0 |
| Yevamot (rule-informed) | 4 | 3 = 75% [30–95] | 3/3 · 0 · 0 | — | 1 / 0 / 0 |
| cited in STORY_RULES | 35 | 29 = 83% [67–92] | 12/12 · 0 · 0 | 11/12 · 1 | 1 / 4 / 1 |
| not cited | 328 | 262 = 80% [75–84] | 72/78 · 4 · 2 | 154/161 · 6 | 22 / 29 / 15 |
| **list** (BLIND lists, positives only) | 444 | 378 = 85% [82–88] | — | 363/378 · **9** | 60 / 2 / 4 |
| corrected (Ketubot, reported apart) | 185 | 151 = 82% [75–86] | 7/11 · 3 · 1 | 128/139 · 10 | 20 / 12 / 2 |

Gittin — his hard, unlisted extras — is where the 80% breaks: 41%, and on 14 of 16 splits
Claude is the one siding with him. Gemini calls `story` on **13 of his 18** Gittin `no`s.
Ketubot's 84% is still carried by spans the detector itself had called `NOT_A_STORY` (§8).

### 10d. Spread (Lesson 43)

| | review moved | list moved | corrected moved |
|---|---|---|---|
| Gemini, same prompt, same day | 0 of 363 | 0 of 444 | 1 of 185 |
| Claude subagents, same prompt, re-shuffled batches | **21 of 364 (5.8%)** | **34 of 448 (7.6%)** | 12 of 185 (6.5%) |

**Claude's run-to-run spread is measured now — about 6–8% of verdicts — and it is ~20× Gemini
the judge's.** It includes what batch-mates do, so it is an upper bound for one-call-per-span
Claude, but it is the spread of the arm actually used. Every Claude-side count above carries
it: of the 47, Claude says `not` to 22 in run 1 and 24 in the repeat, mostly different ones.

### 10e. The 47 list misses of phase 1, one by one

Gemini v1 called all 47 `not`. Shapes are §7b's hand sort. Cells read *run 1 / repeat*.

| list id | ref | shape (§7b) | Gemini | Claude |
|---|---|---|---|---|
| ketubot_013 | Ketubot 20a | incident + ruling | story / story | story / **not** |
| ketubot_022 | Ketubot 27a | a rule misapplied | story / story | story / story |
| ketubot_038 | Ketubot 54a | incident + ruling | story / story | story / story |
| ketubot_044 | Ketubot 60b | incident + ruling | story / story | **not** / **not** |
| ketubot_046 | Ketubot 61a | single act / first-person | story / story | **not** / story |
| ketubot_048 | Ketubot 61a | single act / first-person | story / story | story / **not** |
| ketubot_047 | Ketubot 61a | single act / first-person | story / story | story / **not** |
| ketubot_049 | Ketubot 61a | habitual practice | story / story | **not** / **not** |
| ketubot_050 | Ketubot 61a | habitual practice | **not** / **not** | **not** / **not** |
| ketubot_065 | Ketubot 65b | speech / dialogue | story / story | story / story |
| ketubot_071 | Ketubot 67b | habitual practice | story / story | **not** / **not** |
| ketubot_076 | Ketubot 67b | habitual practice | **not** / **not** | **not** / **not** |
| ketubot_101 | Ketubot 85b | incident + ruling | story / story | story / story |
| ketubot_112 | Ketubot 100b | single act / first-person | story / story | **not** / **not** |
| ketubot_137 | Ketubot 111b | eyewitness wonder | story / story | story / story |
| ketubot_141 | Ketubot 111b | eyewitness wonder | story / story | story / story |
| ketubot_142 | Ketubot 111b | eyewitness wonder | story / story | story / story |
| ketubot_143 | Ketubot 111b | eyewitness wonder | story / story | story / story |
| kiddushin_012 | Kiddushin 21b | speech / dialogue | **not** / **not** | **not** / **not** |
| kiddushin_022 | Kiddushin 30a | speech / dialogue | **not** / **not** | **not** / **not** |
| kiddushin_028 | Kiddushin 31b | speech / dialogue | **not** / **not** | **not** / **not** |
| kiddushin_051 | Kiddushin 45b | incident + ruling | story / story | story / story |
| kiddushin_055 | Kiddushin 50a | incident + ruling | story / story | story / story |
| kiddushin_078 | Kiddushin 72a | incident + ruling | story / story | **not** / **not** |
| kiddushin_085 | Kiddushin 80b | single act / first-person | **not** / **not** | **not** / **not** |
| gittin_031 | Gittin 34a | incident + ruling | story / story | story / **not** |
| gittin_053 | Gittin 46b | incident + ruling | story / story | story / story |
| gittin_057 | Gittin 52a | incident + ruling | story / story | **not** / **not** |
| gittin_092 | Gittin 63b | incident + ruling | story / story | story / story |
| gittin_098 | Gittin 69b | single act / first-person | story / story | story / story |
| gittin_099 | Gittin 69b | single act / first-person | story / story | **not** / **not** |
| gittin_100 | Gittin 69b | single act / first-person | story / story | **not** / **not** |
| gittin_110 | Gittin 89a | incident + ruling | story / story | story / story |
| gittin_111 | Gittin 89a | incident + ruling | story / story | **not** / story |
| gittin_112 | Gittin 89a | incident + ruling | story / story | **not** / **not** |
| yevamot_008 | Yevamot 31a | incident + ruling | story / story | story / story |
| yevamot_015 | Yevamot 45b | incident + ruling | story / story | story / story |
| yevamot_014 | Yevamot 45a | incident + ruling | story / story | **not** / **not** |
| yevamot_017 | Yevamot 45b | incident + ruling | story / story | story / bord. |
| yevamot_016 | Yevamot 45b | incident + ruling | story / story | story / story |
| yevamot_027 | Yevamot 61b | incident + ruling | story / story | **not** / **not** |
| yevamot_030 | Yevamot 63a | single act / first-person | story / story | **not** / **not** |
| yevamot_031 | Yevamot 63a | single act / first-person | story / story | **not** / **not** |
| yevamot_084 | Yevamot 116b | incident + ruling | story / story | story / story |
| yevamot_086 | Yevamot 120b | eyewitness wonder | story / story | story / story |
| yevamot_099 | Yevamot 122b | a rule misapplied | story / story | story / story |
| yevamot_100 | Yevamot 122b | a rule misapplied | **not** / **not** | **not** / **not** |
- **Moved to `story` under both models in both runs: 20 of 47** — 11 of the 21
  incident-plus-ruling (Toviya's bequest, Ketubot 85b; Ketubot 54a; Kiddushin 45b, 50a;
  Gittin 46b, 63b, 89a:110; Yevamot 31a, 45b ×2, 116b), all five eyewitness wonders
  (Ketubot 111b ×4, Yevamot 120b), one single act (Gittin 69b:098), one speech case
  (Ketubot 65b), and two of the three rules-misapplied cases (Ketubot 27a, Yevamot
  122b:099). This is R-C0 working as written.
- **Gemini moved 40 of 47; Claude moved 25 (run 1) / 22 (repeat).** Claude still says `not`
  to 7 of the 21 incident-plus-ruling stories in run 1 and to 7 of the 10 single-act ones,
  citing R-C5 — Claude reads *"the act has to lead somewhere"* more strictly than Gemini.
- **Still `not` under all four answers: 7** — Ketubot 61a:050 and 67b:076 (habitual
  practice), Kiddushin 21b, 30a, 31b (speech / dialogue), Kiddushin 80b:085 (incident only
  alluded to), Yevamot 122b:100 (Gemara commentary on the Mishnah's story). Gemini's 7
  remaining `not`s among the 47 are exactly these. Two list stories outside the 47 join
  them: Kiddushin 26a:016 (run 1 only) and Yevamot 107b:072 (Pishon's wife, alluded to).

**The 10 agreed `not`s on his reviewed `yes`es** (§1): **5 now agreed `story`** in both runs
(Ketubot 85b:5 Toviya, 109b:12, 111b:12 / :21 / :22 the Land's wonders); **4 are splits** —
Gemini `story`, Claude `not` (Ketubot 69a:12, 100b:16, 103b:24–25; Gittin 43b:4 split in
run 1, agreed `story` in the repeat); **1 is still agreed `not`** in both runs (Ketubot
105a:13, R-C5).

### 10f. Did any of his `no`s flip to `story`? Yes — that is the cost of the correction

**Agreed `story` on his `no`** (criterion 2), with his words:

| span | his note | run 1 | repeat | the models' reading |
|---|---|---|---|---|
| Gittin 88a:11 | *"A legal problem and answer"* | story | story | R-C0: a contract brought before R. Abbahu, R. Yirmeya objects — new: v1 agreed `borderline` |
| Ketubot 50b:4–5 | *"correct. It is a legal discussion with legal reasoning."* | story | story | R-C0: orphans come before Shmuel, who rules — new |
| Ketubot 50a:10 | (no note; a `correct` on `NOT_A_STORY`, 2026-02-05) | story | Claude `borderline` | R. Yitzḥak finds R. Abbahu at Usha and learns a halakha forty times — new |
| Ketubot 111a:23–25 | *"It is not even a story"* | story | story | R-C4: a man's love-sickness inside Ilfa's letter — unchanged from v1 |
| Gittin 80b:1–2 | | not (split) | **story** | repeat only |
| Ketubot 8b:11–12 | | not (split) | **story** | repeat only |

Beyond the agreed ones, **Gemini alone now calls `story` on 32 of his 130 `no`s** (v1: 10) —
13 of 18 on Gittin, 15 on Ketubot, 4 on Kiddushin — mostly citing nothing or R-C2, on
passages he called a legal problem, a legal discussion, or speech. Claude does it on 6.

### 10g. Why it failed — diagnosis, the way §7 did it (no new calls; no rule touched)

Read one by one, every remaining error sits on a line **the register does not settle** —
the models apply it as written.

1. **The R-C0 / R-C5 line, from the other side** (criterion 2). R-C0 says an incident
   followed by a ruling *can* be a story; it does not say when a case brought to a rabbi is
   instead *"a legal problem and answer"* (his Gittin 88a words) or *"a legal discussion with
   legal reasoning"* (Ketubot 50b). Without that line, Gemini reads R-C0 as covering every
   case-before-a-rabbi, and three of his `no`s become agreed `story`. This is exactly the
   open question `jeff:report-vs-incident` (`comms/JEFF.md`) — and his two notes here are
   cases to send with it, on the *not a story* side. **Indicated** (4–5 spans, same-data).
2. **The 2005 lists vs the 2026 rules** (criterion 3). Of the 9 list stories both call
   `not`: 4 are scholarly exchanges (Kiddushin 21b, 26a, 30a, 31b) — R-C2 says speech
   without conflict is not a story, his 2005 list keeps them; 2 are habitual practice with no
   one-time event (Ketubot 61a, 67b) — R-C3/R-C5 as written say that stays a custom; 2 are
   incidents only alluded to (Kiddushin 80b, Yevamot 107b) — R-C5's proposed line names
   *"an incident only alluded to"* as not a story; 1 is the Gemara's commentary on a Mishnah
   story (Yevamot 122b:100) — R-B4. The register's own principle is that his lists are
   evidence and a rule that contradicts one is an *annotation*, not an edit. Four of the nine
   contradict **our own** wording (R-C5's proposed line; the custom-stays-a-custom note);
   five contradict **his** rules (R-C2 ×4, R-B4 ×1).
   **Measured** on these 9; what it implies about the rules is a question for him.
3. **Claude's spread is as large as the margin.** 6–8% of Claude verdicts move between
   re-shuffled runs; criterion counts move by ±1. Both runs still fail by more than that,
   so the decision does not depend on it — but any future pass by one span would.

So nothing here argues for re-wording the prompt or moving a threshold. The next information
is his: where the case-before-a-rabbi line falls, and whether a 2005-list story that R-C2,
R-C3 or the alluded-incident line rejects is an exception or a sign the rule is too broad.
