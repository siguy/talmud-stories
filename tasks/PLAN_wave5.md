# Wave 5 Plan — Sefaria-anchored Hebrew text boundaries (replaces LLM char offsets)

**Status:** Mechanism built and A/B'd on Kiddushin (2026-08-29). **Paused before
full execution at Simon's instruction** — the model A/B is set up; the wave itself
is not yet run across tractates. This is still the FIRST wave when it resumes.
**Why first:** Simon's requirement — the Hebrew text-selection problem must be fixed
*before* Jeff sees anything again. Everything Jeff reviews is Hebrew text; if the
text he is shown is wrong, no other improvement registers with him.
**Predecessor:** Wave 4 / v10 ([PLAN_wave4.md](PLAN_wave4.md)) shipped LLM
character-offset spans. Audited 2026-08-28: **104 of 189 cuts (55%) sever a Hebrew
word**; 9 of 9 reviewed trims judged wrong. Reverted the same day.
→ [`docs/golden/v10/wave4_span_failure_audit_2026-08-28.md`](../docs/golden/v10/wave4_span_failure_audit_2026-08-28.md)

**Current baseline (what Wave 5 must beat):** `results/v10/wave4_notrim/` —
segment-level boundaries, no sub-segment trimming, Ketubot composite 0.9171.

---

## The idea: never emit a number; select a real text unit

Sefaria's Davidson Hebrew is fully punctuated and aligned clause-for-clause with a
correct English translation. Jeff repeatedly noted "the English highlight is correct
but the Hebrew is cut off" (9a_2, 8b_14) — the model *understands* the boundary; it
cannot express it as a character count.

So: split the boundary segment into **punctuation-delimited clauses**, have the model
**choose a clause**, and snap to it. Mid-word cuts become structurally impossible.

### Validated against all 8 of Jeff's stated intents

| Ref | Jeff's intent | Clause-representable? |
|---|---|---|
| 9a_2 | through `לָאו כְּלוּם הוּא` | yes, clauses 0–8 |
| 12b_4 | include `וּפְרַשׁוּ רַבָּנַן מִינַּהּ` | **yes — those words are *inside* clause 0, after a comma. v10 cut at that comma; clause granularity makes the error impossible.** |
| 12b_8 | `הָהוּא חַתְנָא … רַב שֵׁשֶׁת!` | yes, clause 2 — overshoots by one word (`וְהָא`) |
| 12b_10 | through `שְׁקַלְתַּהּ וְאִישְׁתִּיקָא.` | yes, clauses 0–4 |
| 13a_3 | through `שְׁקַלְתֵּיהּ וְאִישְׁתִּיקָה` | yes, clauses 0–4 |
| 22b_18 | **no trim** | yes — *if the default is no-trim* |
| 25a_3 | include `מַתְנִיתָא בְּעוֹ מִינָּךְ. דִּתְנַן…` | yes, clauses 0–3 (or 0–4) — **his ellipsis is ambiguous; ASK HIM** |
| 30a_7 | through `לְיָנוֹקָא וּמוֹסְפֵיהּ` | yes, clauses 0–7 (clause 8 is a parallel he excludes) |

**8/8.** The plan's original worry — that clause granularity is too coarse — is
backwards: on 12b_4 the coarseness *is* the fix.

## Hard constraints, measured from the corpus

Over all 2,405 Kiddushin segments:

- **Split on `. : ? !` ONLY. Never on commas.** The comma is the corpus's most
  frequent mark (4,855 vs 3,959 periods) and 12b_4 is precisely a story continuing
  past one. Resulting granularity: median 5 words/clause, p90 14, max 43.
- **97 segments (4%) contain HTML** (`<big>`, `<strong>`). Strip before splitting;
  ensure recorded offsets refer to the same string the review UI renders.
- **20 segments (0.8%) have no terminal punctuation.** Clause selection degenerates
  to whole-segment. That must be a *named, logged* outcome
  (`text_span_source: 'no_clause_split'`), never a silent accident.
- **Default is NO TRIM.** 22b_18 shows Jeff keeping a trailing `אִיכָּא דְּאָמְרִי…`
  that the v10 prompt was told to cut. Flip the bias from "cut framing" to "keep
  unless clearly not story."

## Option B, scoped narrowly

Option B (verbatim quote + string match) is **not** a general fallback for "clause
too coarse" — that is a vague LLM judgment. Its one real job is a **sub-clause
framing prefix** (`וְהָא`, `וְתוּ`, `תָּא שְׁמַע`) at the head of an otherwise-correct
clause, i.e. the 12b_8 shape. Apply it only when the selected start clause begins
with such a prefix, and only if the result lands on a verified word boundary.

## Phases

- **Phase 0 — DONE (2026-08-28).** Spans reverted; score-neutrality proven both ways
  (0.9171 → 0.9171); structural baseline recorded in
  [`scripts/audit_text_spans.py`](../scripts/audit_text_spans.py).
- **Phase 1 — Fix the review UI FIRST.**
  [`validation/generators/generate_wave4_review_ui.py`](../validation/generators/generate_wave4_review_ui.py)
  (`renderHebrew`, ~line 304) trims **Hebrew only**; English is shown at full
  segment width. Several of Jeff's "the Hebrew doesn't match" notes are this bug,
  not the detector. Shipping a perfect detector into this UI reproduces the
  complaint. Trim both, or show untrimmed Hebrew with a marker.
- **Phase 2 — Fork.** `cp src/story_detector_v10.py src/story_detector_v11.py`.
  Add `_split_into_clauses(hebrew)`. v10 stays frozen
  (memory `feedback_detector_versioning.md`).
- **Phase 3 — Implement clause selection**, replacing `extract_text_spans_via_llm`.
  Record clause spans that snap to real positions; keep `text_span_source`
  provenance (`clause_llm`, `clause_prefix_fix`, `no_clause_split`, `kept_full`).
- **Phase 4 — Verify (see gates below).**
- **Phase 5 — Ship.** Regenerate review UIs; update
  [`docs/technical/VERSION_HISTORY.md`](../docs/technical/VERSION_HISTORY.md),
  CLAUDE.md, and the ledger.

## Gates — three automatic, one human

| Gate | Threshold | Coverage |
|---|---|---|
| **Structural** — `audit_text_spans.py --strict` | **0% mid-word, 100% clause-edge** | 100% of stories, automatic |
| **Score neutrality** — `evaluate_golden.py`, regenerated today (Lesson 11) | Ketubot ≥ 0.9171, Kiddushin ≥ 0.8859, **both Ketubot ranges** (Lesson 6) | automatic |
| **Segment boundary** — vs Jeff's 2005 list | ≥ **69% exact** (current baseline; 25% under-extend, 6% over-extend) | 149 stories, automatic |
| **Sub-segment semantics** | Simon/Claude spot-check + the 8 stated intents above | sample, human |

**Honest limit, tested 2026-08-29:** Jeff's 2005 list **cannot** grade sub-segment
boundaries. Deriving clause targets from his text was only 13% derivable and the
results were wrong (on Ketubot 65a it placed the story start *after*
`מַעֲשֶׂה בְּכַלָּתוֹ שֶׁל נַקְדִּימוֹן`, plainly the opener). His text is too abbreviated
for 4-gram matching on short clauses. Do not build a gate on it. The residual
sub-segment risk is covered by the structural gate (which is total) plus human
spot-check — **not** by a fixture, per Lesson 9/18.

## Out of scope

Criteria/classification ([PLAN_wave6.md](PLAN_wave6.md)); introducer lexicon
([PLAN_wave7.md](PLAN_wave7.md)); Cause-B segment/cross-page fixes; multi-story dedup.

## Cost

One selection call per real story (~290 stories) ≈ **$0.10–0.20 per tractate**,
~$0.40 total including gate re-runs. Verified against actuals of ~$0.30–0.60 per
full tractate detection (Lesson 4); this is cheaper because no re-detection is
needed — spans ride existing segment boundaries.

---

## Model A/B — run 2026-08-29 on Kiddushin (95 stories, both arms complete)

Simon's request: split the model change out and measure it. Because clause spans
are score-neutral, this A/B is safe to run independently of everything else.

| | **A: gemini-2.5-flash** (no thinking) | **B: gemini-3.7-flash** (thinking HIGH) |
|---|---|---|
| Stories trimmed | 76 / 95 (80%) | **47 / 95 (49%)** |
| Cuts emitted | 93 | 54 |
| **Mid-word cuts** | **0** | **0** |
| **Clause-edge rate** | **100%** | **100%** |
| Expert cases passed | 4 / 8 | **5 / 8** |
| Wall clock | 51s | 341s (6.7x) |
| Agreement between arms | 63/106 stories identical (59%) | |

**Both arms pass the structural gate**, against 55% mid-word / 4% clause-edge for
Wave 4. The mechanism works regardless of model — that is the primary result.

### The decisive finding is the *direction* of the errors

Every failure in both arms is on the **end** boundary; all 8 starts are correct in
both. But the arms fail in opposite directions:

- **2.5-flash over-trims** — 9a ends at clause 6 (wants 8), 30a at 6 (wants 7),
  22b starts at 1 (wants 0) and ends at 3 (wants 4), 25a ends at 2 (wants 3–4).
- **3.7-flash under-trims** — 12b_10 ends at 6 (wants 4), 13a at 7 (wants 4).

For this project those are not equivalent. **Over-trimming destroys text Jeff needs
and cannot recover; under-trimming leaves extra text he can see and tell us to cut.**
Jeff's 22b_18 note was literally *"nothing should have been trimmed"* — the exact
error 2.5-flash still makes and 3.7-flash does not. And 30a seg 7, the mid-word
case that started all of this, is now **exactly right** under 3.7-flash.

### Recommendation — REVISED 2026-08-30 on a bigger test set

The 5/8 vs 4/8 result came from 8 hand-picked cases and **did not survive** a
larger, less biased test set. On the 52-target expert boundary set
(`tests/expert_boundary_targets.json`), scoring the 16 currently-scorable
Kiddushin targets:

| run | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|
| no trimming at all (baseline) | 1 | 5 | 10 | **6%** | 38% |
| gemini-2.5-flash | 9 | 3 | 4 | **56%** | 75% |
| gemini-3.7-flash + HIGH | 8 | 3 | 5 | **50%** | 69% |

Two conclusions, and the first matters far more than the second:

1. **Clause selection works.** 6% -> ~50-56% exact agreement with Jeff's stated
   boundaries, on top of eliminating mid-word cuts entirely. That is the Wave 5
   result.
2. **The two models are indistinguishable on this task** — one case apart at
   n=16. The earlier "3.7-flash is better" claim was an artifact of an 8-case
   fixture (Lessons 9, 18 — again).

**Ship on `gemini-3.7-flash` + HIGH anyway, but on risk grounds, not accuracy
grounds:** 2.5-flash's errors are over-trims (unrecoverable — text Jeff needs is
gone), 3.7-flash's are under-trims (recoverable — Jeff sees extra text and says
cut it). Accuracy is a wash; the failure mode is not. State it that way — do not
claim an accuracy win the data does not support.

Both arms also ran on a **degraded prompt** (see below), so neither number is a
ceiling.

The remaining 3/8 are all "kept too much," which is the safe failure. Worth one
prompt iteration before shipping, but not worth trading for the over-trimming arm.

### Gotcha worth remembering (cost us a full run)

Thinking tokens are drawn from `max_output_tokens`. Setting `thinking_level=HIGH`
while leaving the 512-token budget meant the model spent 487 tokens thinking and
returned `MAX_TOKENS` with no JSON — **72 of 95 stories failed**. Fixed by raising
the budget to 8192 when a thinking level is set (the same fix the Pro-model branch
already applied). See Lesson 20.

### Prompt defects found 2026-08-30 (both arms ran with these)

- **Summary bug:** the prompt reads `story['summary']`, present on **0 of 106**
  stories; the detector writes `one_sentence_summary`. It fell back to a joined
  `criteria.multiple_events.events` list — usable but the weaker of two available
  descriptions. Inherited from v10.
- **English never sent.** Sefaria's Davidson English bolds literal Talmud text and
  leaves Steinsaltz interpolation unbolded. On Kiddushin 22b seg 18 — which BOTH
  arms got wrong — clause 4 is bolded (literal text, Jeff said keep it) while the
  framing `The Gemara comments:` is unbolded. Jeff's own words were *"the English
  highlight is correct but the Hebrew is cut off"*; we withheld the English.
- **No classification context** (`classification`, `classification_reasoning`,
  `criteria`) though all are in the record.

Tested and rejected as a *verification* signal: English bolding predicts Jeff's
end-trims 6/8 but his start-trims **0/8** (nearly every segment opens with an
unbolded connector, so the signal is uninformative). Send English to the model as
context; do not build a gate on it.

## How we verify the model is segmenting correctly

Three layers. Only the third yields an unbiased number.

| Layer | What it proves | Coverage | Cost |
|---|---|---|---|
| **Structural** (`audit_text_spans.py --strict`) | boundary is **well-formed** — clause edge, never mid-word. Says nothing about being the RIGHT edge. | 100% | free |
| **Expert targets** (`score_boundary_targets.py`) | agreement with 52 boundaries Jeff stated in Hebrew across 7 rounds, both tractates | 52 targets | free |
| **Random sample, human-adjudicated** | the actual error rate, including regressions | ~30 random | human |

**The expert-target set is biased** — every target is a case Jeff flagged as wrong,
so it measures fixing known failures, not avoiding new ones. The random sample
exists precisely to catch what it cannot see.

Also available free: **inter-arm disagreement** as a review router. The two arms
agree exactly on 52/95 and disagree on 43/95; of Jeff's 8 known-answer cases, the
2 in the agree bucket were both correct and the 6 in the disagree bucket contained
every error either arm made. Useful for routing human attention, not as proof.

### Still to do before Wave 5 ships

- **Fix the prompt first** (summary field, English + bold markup, classification
  context), then re-run the A/B — current numbers are from a degraded prompt.
- Run both arms on **Ketubot** as well — 29 of the 52 expert targets are Ketubot
  and are currently unscored (N/A).
- Re-check the model choice on the full 52 once Ketubot is scored.
- Gates: composites regenerated today, segment-boundary vs Jeff's 2005 list >= 69%.
- Phase 1 UI fix (not yet started).
