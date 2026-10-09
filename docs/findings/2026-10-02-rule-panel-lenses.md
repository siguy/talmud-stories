# Rule panel ("lenses"): a worse classifier, a sharp diagnostic

**2026-10-02.** Status: **indicated, same-data**. The register's precedents and these labels
overlap. Item: [`rule-panel-lenses`](../../work/done/2026-10-02-rule-panel-lenses.md).
Run as a **diagnostic**, at Simon's direction: one run per arm, no repeat.

## 1. What ran

The same 997 units, passage text and full rule register as consensus phase 1b
([`consensus-phase1` §10](2026-09-28-consensus-phase1.md)). The only change is the
question. Instead of *"is it a story?"*, the model answers nine feature questions
(`src/prompts/judges/panel_v1.md`, sha `907dcc38901d`), and `src/consensus/decide.py`
computes the verdict. Two of the table's rows encode **our** proposals, not his words:
*"an incident only alluded to is not a story"* and *"a custom with no one-time event stays a
custom"*.

| arm | how | ok / invalid |
|---|---|---|
| Gemini (`gemini-3-flash-preview`) | API, one call per span | 997 / 0 |
| Claude (Opus 5.5) | 40 Claude Code subagents × 25 spans; transcripts audited: every passage seen in full, no forbidden reads | 997 / 0 |

Six agents wrote their JSON through a scratch Python script instead of one Write. The audit
shows none read anything but the prompt and its own batch. Cost: Gemini only, a few dollars.

## 2. As a classifier: worse than the single question

| plan §4 criterion | single question (1b run 1) | panel |
|---|---|---|
| models agree (review spans) | 291/363 = 80% | 283/364 = **78% [73–82]** |
| agreed `story` on his `no` | 4 | **8** |
| list stories both call `not` | 9 of 444 | **17 of 448** |
| list stories Gemini / Claude alone call `not` | 10 / 39 | 20 / **77** |

The item's first test, *errors no higher than the single question*, **fails**. Splitting the
question did not make the models agree with him more. It made Claude reject twice as many of
his list stories.

## 3. As a diagnostic: every disagreement points at one feature

The item's second test, *≥ 80% of disagreements trace to one judge*, **passes**: of the 207
spans where the two arms reach different verdicts, **205 differ on exactly one deciding
feature**.

**Where the arms split** (deciding feature): speech with/without conflict **79**, alluded-only
**76**, response or consequence **32**, commentary 8, custom then event 7, actual 7.
**Three features cover 187 of 207 (90%).**

**Where a model calls his `yes` a `not`**, the row that decided it:

| deciding row | Gemini | Claude |
|---|---|---|
| alluded only (**ours**) | 2 | **47** |
| speech without conflict (R-C2) | 1 | 25 |
| nothing follows (R-C5) | 7 | 25 |
| custom, no event (**ours**) | 10 | 7 |
| commentary (R-B4) | 5 | 4 |
| not an actual event (R-C0) | 4 | 4 |

**Our two rows cause 54 of Claude's 112 and 12 of Gemini's 29.** The biggest single source of
disagreement with Jeff is wording we wrote, not his rules. On his 2005 lists, Claude reads 32
stories as "only alluded to"; he lists every one.

**Where a model calls his `no` a `story`**: in all 26 (Gemini) and 9 (Claude), **every feature
reads as a story**, i.e. actual, an event beyond speech, a response. The nine questions do not contain
the reason he said no. His notes say what it is: *"a legal problem and answer"*, *"a legal
discussion with legal reasoning"*, *"a legal ruling"*. **A tenth feature is missing**: is the
incident the point, or only the vehicle for a ruling? That is the report-vs-incident line seen
from the other side (`jeff:report-vs-incident`).

## 4. What it means

- **Do not use the panel to classify.** The single question stays the judge for phase 2.
- **Use it to choose Jeff's questions.** Four, in order of how many passages each answer reaches:
  1. **Alluded incidents:** his lists keep them; our line rejects them (Claude: 47). Likely our
     line is wrong. Ask him, with Kiddushin 80b and Yevamot 107b (Pishon).
  2. **Speech and conflict:** the arms split on 79 spans. Where does a sharp exchange become
     conflict? His R-C2 has his words but too few cases.
  3. **Incident as vehicle for a ruling:** the missing tenth feature. Ketubot 50b vs Gittin 88a
     / 80b.
  4. **A custom with no one-time event:** his list keeps four (Ketubot 61a ×2, 67b ×2); our note
     rejects them.
- These go to `jeff-feature-questions` as contrast pairs, which is now unblocked.

## 5. Limits

One run per arm: the panel's spread is unmeasured. The single question's Claude spread was
6–8%, so a difference of a few spans is noise; the doubling of list rejections (39 → 77) and
of agreed `story` on his `no`s (4 → 8) is larger than that. Same-data: the register quotes
some of these pages.
