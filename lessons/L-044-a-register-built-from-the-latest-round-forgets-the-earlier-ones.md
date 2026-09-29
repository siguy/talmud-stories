# L-044 — A rule register built from the latest round forgets the rules that bound it

**Date:** 2026-09-28
→ [`2026-09-28-consensus-phase1.md`](../docs/findings/2026-09-28-consensus-phase1.md) §7

## The rule

**Before adding a rule that narrows what counts, search the expert's earlier words for the
rule that limits it — and write both down, side by side. Never gloss his cases into a
general statement he did not make.**

## What happened

`docs/STORY_RULES.md` was started on 2026-09-01 from Jeff's Gittin answers and grew by
rounds. His foundational July criteria — *stories are events that happened; "A man stole a
cow… Rava ruled… you may have a story"; halakhic stories are in* — lived in a findings file
and a memory note, never in the register. On 2026-09-25, R-C5 was written from four new
cases, with our gloss *"one act, however it is introduced, is a precedent, not a story."*
It read as a faithful summary. It contradicted the cow case.

On 2026-09-28 a judge was given the register as its whole instruction. It applied R-C5
exactly as written and rejected 47 stories on his 2005 lists and 10 he had accepted — 21 of
the 47 being precisely the cow shape. The same gloss had gone into the shipped twin-pass
prompt three days earlier, where nobody would have seen it fail.

## How to apply

- A register entry quotes his words; anything we infer is labelled **ours** and becomes a
  question for him, not a rule.
- A new narrowing rule gets a line: *"bounded by: R-…"*. If nothing bounds it, look again.
- The fastest audit of a register is to hand it, alone, to a model and score the model
  against his labels: whatever it gets wrong in bulk is a rule missing or overstated.
