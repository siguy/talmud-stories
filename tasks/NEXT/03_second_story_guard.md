# NEXT 03 — Stop discarding a second story that shares a segment

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first.
**Capability: 4 Boundaries.** **Depends on Jeff: no** — this is wrong
under every definition of where a story ends. **Cost: small, plus one measured run.**

## The bug, with the evidence

**Ketubot 105b segment 9** holds two parallel incidents. Ameimar, judging a case, has a
feather removed from his head by a passer-by and disqualifies himself; then Mar Ukva,
with spittle before him, has a man cover it and disqualifies himself. Sefaria prints
both in full.

We keep the first and **delete the second entirely** — six clauses of narrative and
dialogue. Same shape at **Ketubot 62a**: R. Yochanan on the collapsing stair, cut away.

This is not a boundary disagreement. It is a coverage failure: where two stories share a
segment, the second one vanishes from the output. Same family as the open multi-story
item on Kiddushin 12a (two `הָהוּא גַּבְרָא` stories in one detection).

## The fix, and why it is this one

A depth cap on trimming was tried on 2026-08-30 and reverted — it is a magic number that
cannot tell "we cut a second story" from "we disagree about legal framing", and it
optimised for the wrong expert standard. See `docs/findings/2026-08-30-trim-asymmetry.md`.

The principled rule is **never trim away a clause that is narrative in its own right.**
It targets exactly this failure and leaves the definitional question alone.

That needs one signal per clause — *is this narrative?* — which is the one salvageable
piece of the shelved Wave 5b: its labeller used as a **guard on the trim**, not as the
mechanism that computes the boundary. Roughly 40 lines against the original 433.
Salvage list in `tasks/RESUME_after_clear.md`; full review in
`docs/findings/2026-08-30-wave5b-review.md`.

## Method

1. Build the one-role labeller: per clause, `narrative` / `not_narrative` / `unclear`.
   Hebrew only. Reuse `_split_into_clauses` and `_assert_word_boundary`.
2. Veto any trim that would remove a clause labelled `narrative`.
3. Measure on the neutral ruler, both directions, and re-check 62a and 105b by eye.
4. Run the same code twice and report the spread before claiming a gain (Lesson 22).

## How you know it worked

- Ketubot 62a and 105b keep their second story.
- Neutral-ruler score does not fall. Baseline: **80% hit / 84% hit+near** on 229 Ketubot
  targets; overshoots past Jeff's 2005 outer limit currently **10 of 105**.
- A same-code repeat is reported alongside the result.

## Guardrails

- A failed model call must never carry a success provenance, and outcome buckets must
  sum to items processed — assert it (Lesson 21). `scripts/run_clause_labeling.py` and
  `tests/test_wave5b_runner_outcomes.py` show the pattern.
- Never ask the model for a character offset (Lesson 16).
- Report the corrections ruler and the neutral ruler separately (Lesson 24).
