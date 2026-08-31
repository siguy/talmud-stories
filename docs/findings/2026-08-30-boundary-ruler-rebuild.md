# Rebuilding the boundary ruler — 2026-08-30

**Why:** the boundary exam was 52 questions, 35 gradeable, every one of them a case
Jeff had flagged as *wrong*. Two runs of identical code scored 50% and 56% on it, so
it could not tell a real improvement from the model's own randomness. Simon's push:
use everything Jeff has given us, not just his corrections.

**Result:** 35 gradeable targets → **249 on Ketubot**, the two independent sources
agree with each other 84% of the time, and the noise floor went from **7 points to
zero**.

---

## 1. Two sources, and they measure different things

| | targets | covers | bias |
|---|---|---|---|
| `tests/expert_boundary_targets_v2.json` | 70 (was 52) | both tractates | **corrections only** — cases we already know we got wrong |
| `tests/expert_boundary_targets_2005.json` | 294 | Ketubot | **none** — Jeff's list predates the detector by ~20 years |

The first answers *"did we fix the known failures?"*. Only the second can answer
*"are we right in general?"* or catch a **regression** — a boundary we had right and
broke. Nothing we had before could see those at all.

### 1a. The corrections harvest was leaking (52 → 70)

The builder gated on an English phrase list. Across all rounds: **303 notes, 102 with
a Hebrew quote, 57 matched, 45 skipped.** Jeff simply writes it other ways:

- *"The story ends וַאֲתָא אִיהוּ וְקָא מְעַרְעַר"* — missed; the pattern needed "ends **with**".
- *"The following lines should be quoted too: יָתֵיב רַב אָשֵׁי..."*
- *"The legal discussions that follow the story need not be quoted."*
- *"...only the text of the stories should be included. The first is: ..."* — and then
  he writes each story **in full**, which anchors *both* edges from one note.

New: `harvest_rule` on every target (`v1_start` / `v1_end` / `widened_end` /
`full_story_quote`). The original 52 reproduce exactly — no regression, only additions.

### 1b. `quote_polarity` — a real defect, found by the cross-check

Review §3.4 flagged that 24 of 52 targets might be anchored one clause off because
nothing modelled whether the quoted Hebrew is text to **keep** or text to **cut**. The
cross-check against the 2005 list proved it. Ketubot 23a:

> *"The last few words are not part of the story but are the Gemara's comment: (טַעְמָא דְּלָא אֲתוֹ עֵדִים...)"*

The harvester anchored the target **on** the Gemara's comment (clause 6) — the exact
text Jeff said to remove. The boundary is clause 5.

Now modelled: `exclude` polarity anchors the *opposite* end of the quote and shifts one
clause; `mixed`/`unclear` notes are flagged `needs_human` and **skipped by the scorer
by default** rather than silently miscounted. 43 include / 11 exclude / 11 mixed /
5 unclear; 16 quarantined.

### 1c. The 2005 aligner

Jeff's text is his own edition — unvocalised, abbreviated (א"ל for אמר ליה) — so exact
matching fails and sequence alignment does not. **147 of 149 stories align** with a
median 99% of his letters matched in order. Each target carries `align_fraction` and
`bracket_ratio` so consumers can filter on alignment quality.

## 2. Do Jeff-2005 and Jeff-2026 agree?

32 boundaries are covered by both sources:

```
identical clause : 26  (81%)
within 1 clause  :  1  ( 3%)
differ by >1     :  5  (16%)
```

**84% agreement between two sources twenty years apart.** Of the 5 that differ, 3 are
`mixed`-polarity notes already quarantined for human review. The two sources
substantially validate each other, which is the licence to use the big one.

## 3. Does Wave 5's premise hold?

**87% of Jeff's boundaries fall exactly on a clause edge** (257 of 294); 13% fall
inside a clause. So clause-anchored spans can reach seven-eighths of his boundaries,
and the last 13% is a **ceiling no prompt can lift** — it would need a finer splitter.
That is the first direct evidence for or against Wave 5's core design choice.

*(Measuring this required care: a first pass said 61% land mid-clause, which was an
artifact — clause ranges run past the closing `.` while Jeff's text ends on a letter.
The honest test is whether any Hebrew **letter** is left outside his boundary.)*

## 4. The noise floor — fixed

Same code, two runs, scored on each ruler:

| ruler | run A | run B | swing |
|---|---|---|---|
| old (Kiddushin corrections, 15–16 targets) | 60% | 67% | **7 points** |
| new (Ketubot 2005 list, 168 targets) | 79% | 79% | **0 points** |

The two Ketubot runs genuinely differ — 2 of 111 boundaries moved — and the score does
not budge. **The ruler is now stable enough to adjudicate a code change.**

## 5. What the neutral ruler says that the old one could not

Ketubot, no-trim vs Wave 5 clause spans:

| | corrections ruler | 2005 neutral ruler |
|---|---|---|
| **Ketubot 2-60** no-trim | 50% hit | 64% hit / 77% hit+near |
| **Ketubot 2-60** Wave 5 | 71% hit | 80% hit / 85% hit+near |
| **Ketubot 61-112** no-trim | 33% hit | **79% hit / 85% hit+near** |
| **Ketubot 61-112** Wave 5 | 67% hit | 80% hit / **84%** hit+near |

Read the bottom two rows. On the corrections ruler Wave 5 doubles the score
(33% → 67%) — because that ruler is made *entirely* of cases where the plain boundary
was wrong, so trimming can only help. On the neutral sample the plain segment boundary
was **already 79% right**, Wave 5 adds ~1 point of HIT, and hit+near goes slightly
*down* (85% → 84%).

**Wave 5's benefit is real but far smaller than the old exam implied, and concentrated
in Ketubot 2-60.** The old exam was structurally incapable of showing this, and it is
exactly the regression signal its own header warned it could not provide.

## 6. What this changes

- **The 52-target exam is no longer the primary measure.** Simon's planned hour on its
  2 contradictions and 3 duplicates is now a small cleanup, not a blocker.
- **Wave 5b's precondition needs re-asking.** "Revive it if a properly-fed one-shot
  stalls near 50%" was written against the corrections ruler. On the neutral ruler the
  number is 80%, and the honest question is different: *is the remaining 20% reachable
  at all, given 13% of boundaries are not on clause edges?*
- **Ask Jeff for his lists on other tractates.** This is now the highest-value item in
  the ledger, not a nice-to-have: it is how a neutral ruler gets built for Kiddushin
  and everything after. Kiddushin still rests on 15 corrections targets with a 7-point
  noise floor.

## Artifacts

```
tests/expert_boundary_targets_v2.json       70 correction targets (+ polarity, harvest_rule)
tests/expert_boundary_targets_2005.json    294 detector-blind targets from the 2005 list
scripts/build_boundary_testset_2005.py     the aligner
scripts/build_boundary_testset.py          widened vocabulary + polarity
scripts/score_boundary_targets.py          --targets (pool files), --by-source, needs_human skip
results/v11/wave5_summaryfix/*_repeat.json  the same-code repeats behind §4
```
