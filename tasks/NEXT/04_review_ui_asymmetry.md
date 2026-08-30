# NEXT 04 — Fix the review UI before Jeff sees another round

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first.
**Capability: 5 Review.** **Depends on Jeff: no, but it is on the
critical path for the next thing we send him.**

## The problem

`validation/generators/generate_wave4_review_ui.py` **trims the Hebrew but shows the
full English.** So a reviewer sees a Hebrew passage that stops early beside an English
one that does not.

This is not cosmetic. It **caused** several of Jeff's "the Hebrew doesn't match" notes
in the 2026-07-06 round — we spent his attention on a bug in our own display. See the
open-items tracker in `validation/feedback/jeff_2026-07-06_feedback_ledger.md`.

If he replies to the pending email and we want to put another round in front of him, we
must not send a UI that manufactures its own errors.

## Method

1. Apply the same span to both languages, or show both untrimmed with the story
   highlighted rather than cut. Highlighting is safer than trimming: it shows our
   judgment without hiding the text a reviewer needs to judge it.
2. **Open it in a browser and look at it** with a real story, Hebrew and English side by
   side. This project's rule: validation UIs must display text and be checked in a
   browser before being called done. Screenshot it.
3. Re-check the cases Jeff flagged as mismatched — they should now read correctly.

## How you know it worked

A screenshot of a real story where Hebrew and English show the same extent. Not a code
diff.

## Guardrails

- Do not change what the detector produces. This is display only.
- Never claim done without opening it in a browser (project rule, and it is what caused
  this bug in the first place).
