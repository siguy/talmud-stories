# L-042 — A verdict with no column to go in gets rounded, and the rounding looks like his

**Date:** 2026-09-25
**Found in:** `results/canonical/ketubot_canonical.json` — ten entries labelled
`LOW_CONFIDENCE` whose own `corrections` quote Jeff saying *"borderline"*
→ [`2026-09-25-jeff-verdicts-scope-commentary-reports.md`](../docs/findings/2026-09-25-jeff-verdicts-scope-commentary-reports.md)

## The rule

**When an expert answers in a category the dataset has no slot for, record the answer
verbatim in its own field before mapping it to the nearest slot — and name the mapping as
ours.** A rounded label reads as his label to every later reader, and nobody goes looking
for a distinction the schema cannot hold.

## What happened

In the February and March 2026 rounds Jeff wrote *"This should be marked a borderline
story"* ten times. The golden had four classes and no BORDERLINE, so the auto-applier put
each one in `LOW_CONFIDENCE` under a prefix of our own — *"Jeff noted borderline/low
confidence:"* — which reads like his words. For six months the golden said he had judged
those ten *low confidence*. When he confirmed on 2026-09-23 that speech-with-conflict is
*borderline* (R-C2), the column existed at last (Gittin had it since 2026-09-02), and the
ten were found by searching our own notes for his word.

Two things kept this recoverable: the applier kept his sentence in `corrections`, and the
prefix was fixed text we could strip. Without the first, the distinction would be gone.

## How to apply

- A new answer category in feedback is a **schema question first**, not a mapping.
- Never prefix our words onto a quote of his; put our mapping in its own field.
- Relabel from **his words only**. The other 65 `LOW_CONFIDENCE` entries may well be
  borderline too — that is his call, not an inference from ours.
