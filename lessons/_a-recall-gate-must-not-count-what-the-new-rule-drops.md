# A recall gate must not count, as a loss, what the new rule is meant to drop

**Date:** 2026-11-07
→ [`2026-11-07-detector-v13-slice.md`](../docs/findings/2026-11-07-detector-v13-slice.md) § Correction

## The rule

**Before a recall comparison decides between an old prompt and one carrying a newer expert
rule, read every list story the new arm loses against that rule. A loss the rule predicts
is not a loss: set it aside (and ask him about it) before applying the gate. Write the
gate so it says so.**

## What happened

v13/v14 put Jeff's October rulings into the prompt. The decision rule for adopting v14 was
"at least as many list stories as v11, and no R-S1/R-B4 error". The one list story v13/v14
lost, Yevamot 78b:9, is a question to R. Eliezer and his answer: by R-C2 and the
2026-10-07 wording, not a story. The gate counted it against them. The 2005 list is
provisional and predates the rule, so a recall gate scored against it penalises exactly
the change being tested. Simon caught it on review; the outcome survived only because the
other half of the gate (two named errors) failed on its own.

## How to apply

- For each list story the new arm loses, check `docs/STORY_RULES.md`: does a rule the new
  wording carries say it is not a story? If yes, exclude it from both arms' counts and
  add it to `comms/JEFF.md`.
- Pair with [a provisional list is not an opposing ruling](_a-provisional-list-is-not-an-opposing-ruling.md):
  the list is evidence, not the rule.
