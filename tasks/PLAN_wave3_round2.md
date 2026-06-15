# Wave 3 Round 2 Plan — Jeff's 2026-06-03 Reply

**Source:** Jeff's email + `validation/feedback/kiddushin_review_2026-05-26 (1).json` (received 2026-06-03)
**State on entry:** Wave 3 shipped (v9, tag `v9-wave3`). Kiddushin composite 0.8859 (gate fail per Lesson 14, shipped per Lesson 13). Ketubot 0.9170. Item 4 (text-internal boundary regex) was the experimental piece.

---

## What Jeff said (one-line each)

**Kiddushin Item 4 verdict — MIXED:**
- Works: 17, 18, 19, 20, 34 (the canonical ההוא/ההיא openers)
- Fails: 8a_9-10 (under-trim), 8b_2-2, 9a_1-1 (only explicit "incorrect"), 9a_2-2, 13a_3-3, 31b_4-4, 33a_15-15 (all over-trim — chopped story content), 12b_4-4 (needs more trim)
- Confirmed correct: 12a_13-13
- Diagnosis (verbatim): *"crude criteria, such as the word אלא or a rabbi's name automatically signalling the story's end"* — confirms the regex's failure mode.
- Did NOT verdict the 7 new candidates (the gate-relevant ones).

**Ketubot golden corrections (bonus):**
- 7a seg 1: NOT_A_STORY → **LOW_CONFIDENCE** (re-add as LOW)
- 26a seg 9: confirms current NOT_A_STORY (no change)
- 102a seg 6: not in golden, confirms (no change)
- 106a seg 1-2: story should be **segs 2-3**, currently 3-3 (extend start back one seg)

---

## Step 1 — Apply 4 Ketubot golden corrections + rescore (THIS SESSION)

- [ ] 1a. Update `results/canonical/ketubot_canonical.json`:
  - 7a: re-add story seg 1-1 as LOW_CONFIDENCE
  - 106a: extend existing 3-3 story to 2-3
  - Log entries in `canonical_review_applied_log` with date 2026-06-03 + source = Jeff email
- [ ] 1b. Re-run `scripts/evaluate_golden.py` on Wave 3 Ketubot results
- [ ] 1c. Compare new composite vs prior 0.9170 — expect small positive movement (one new LOW + one boundary correction; both should agree with v9 detector)
- [ ] 1d. Write `docs/golden/v9/wave3_round2_ketubot_rescore.md` with before/after numbers

## Step 2 — Draft reply to Jeff (THIS SESSION)

- [ ] 2a. Thank him for the boundary-fix diagnostics
- [ ] 2b. Acknowledge the regex approach hits a ceiling on exactly the cases he flagged — explain Wave 4 will replace the regex with LLM-side semantic boundary selection
- [ ] 2c. Ask him to **complete the remaining ~85 Kiddushin verdicts** when he can (he offered)
- [ ] 2d. Specifically ask him to verdict the **7 new candidates** (still unverdicted) — they're what move the composite
- [ ] 2e. Confirm we'll apply his 4 Ketubot corrections immediately
- [ ] 2f. Save draft to `docs/golden/v9/email_draft_jeff_wave3_round2.md`

## Step 3 — `/update-docs` (THIS SESSION)

- [ ] 3a. `CLAUDE.md`: bump current state to 2026-06-03, note new Ketubot composite, note Item 4 verdict-mixed
- [ ] 3b. `tasks/todo.md`: mark Wave 3 follow-up items checked where applicable
- [ ] 3c. `docs/technical/VERSION_HISTORY.md`: add Round 2 golden update entry
- [ ] 3d. Add **Lesson 15** to `tasks/lessons.md`: regex-based text-internal boundary editing cannot generalize — pattern markers (אלא, rabbi names) are sometimes story content and sometimes framing; only semantic judgment can tell. Document the empirical evidence (Jeff's 7 over-trim cases on stories where ההוא/ההיא wasn't the actual story opener).

## Step 4 — Wave 4 plan kickoff (NEXT SESSION, blocking on user approval)

Triage of the 4 Wave 4 tracks in `todo.md` in light of new evidence:

- **Track 3 (text-internal boundary, LLM-side text-span emission)** → PROMOTED to top priority. Jeff just labeled fail cases for us. Likely path:
  - Fork v9 → v10
  - Add `text_span_start` / `text_span_end` to Stage 2 prompt schema; instruct Gemini to mark the exact slice of the start/end segment that is story (semantic judgment, not regex)
  - Keep regex as fallback ONLY for the 10 ההוא/ההיא cases Jeff confirmed
  - Test fixtures: all 7 Jeff over-trim cases must keep their full text; all 5 confirmed cases must keep their slice
  - Gate: Kiddushin composite ≥ Wave 3 + Ketubot composite ≥ Wave 3 Round 2
- **Track 1 (post-detection FP classifier)** → blocked until Jeff verdicts the remaining 85 Kiddushin stories. The labeled negatives we need are exactly the ones he hasn't filled in yet.
- **Track 2 (second baraita-embedded few-shot for 81b)** → still valid but low-leverage (1 known FN).
- **Track 4 (Bava Metzia)** → still valid but a different scope (new tractate, fresh golden) — defer until v10 ships.

**Recommendation:** Track 3 next, single-feature Wave 4. Plan doc at `tasks/PLAN_wave4.md` after Step 1-3 done and user has approved this plan.

---

## Verification checklist

- [ ] Step 1: ketubot canonical updated, evaluator re-run, composite written down
- [ ] Step 2: email draft saved, reviewed by user, sent
- [ ] Step 3: 4 doc files updated, Lesson 15 added
- [ ] Step 4: PLAN_wave4.md scaffolded for next-session approval
