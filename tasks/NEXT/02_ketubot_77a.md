# NEXT 02 — Why does the classifier reject Ketubot 77a?

**Self-contained.** Read `STATUS.md` first. **Depends on Jeff: no.** **Cost: reading time.**

## Why this one passage matters more than it looks

Two independent sources say there is a story on Ketubot 77a, segments 8-14:
**Jeff's 2005 list** (58 words, 97% text alignment) and **our own expert-validated
golden dataset**. They agree with each other.

Stage 2 processed the page and returned **zero stories for the entire page**.

That makes it unique among our six recall misses. For the other five someone could
argue "perhaps that is not really a story" — they were never in our labels either. Here
no argument is available: we already agreed it is a story, after expert validation. The
classifier contradicts its own ground truth.

**A story that both an expert and our own labellers accept, which the prompt rejects, is
the sharpest available signal about what the prompt gets wrong.** That is worth more
than another tuning round.

## Method

1. Read the passage — Hebrew and English — from `results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json`, `Ketubot 77a` segments 8-14.
2. Read it against the Stage 2 criteria block in `src/story_detector_v11.py`, criterion
   by criterion. Which one rejects it, and is that criterion wrong or mis-stated?
3. Check it against Jeff's own rubric in
   `docs/golden/workflow/jeff_story_definition_criteria.md` — hypothetical vs actual,
   speech-acts, emotional reactions.
4. Re-run Stage 2 on that single page a few times. If it sometimes finds the story, this
   is variance, not a criterion problem — that is a different bug and worth knowing.

## How you know it worked

A one-sentence statement of which criterion rejects the passage and why that is wrong.
Not a fix — a diagnosis. The fix belongs to Wave 6.

## Guardrails

- Do not tune the prompt here. Diagnose, write it down, hand it to Wave 6.
- Never few-shot on the tractate being evaluated (Lesson 2).
- If you re-run, run the same code twice before attributing anything (Lesson 22).

## When done

Add the finding to `tasks/PLAN_wave6.md` as a seed case, and to the criteria
conformance set. Update `STATUS.md` axis 2.
