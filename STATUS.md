# STATUS — where the project is today

**Last rewritten: 2026-08-30.** This file is REWRITTEN, never appended. It is the
entry point: read this first, in any session. One page, on purpose.

---

## The one-paragraph version

We built a detector that finds narrative stories in the Talmud. Ketubot and Kiddushin
are done to the point of expert-validated golden datasets. **In August 2026 the project
changed character: it stopped being about improving the detector and became about
learning to measure it** — because it turned out most of our numbers were measuring
our own selection. Today the measurement is honest for the first time. The next moves
are consequences of that.

## The three axes — all quality lives on one of these

| | question it answers | Ketubot | Kiddushin | what blocks it |
|---|---|---|---|---|
| **1. Detection** | do we find the stories? | **96%** recall vs Jeff's blind 2005 list — but Stage 1 examines only **44% of pages** | **unmeasured** — no independent list exists | nothing. `NEXT/01` |
| **2. Classification** | is it really a story? | composite **0.9171** vs our golden | composite **0.8859** | Jeff's criteria received 2026-07-06, still not encoded — Wave 6 |
| **3. Boundaries** | what text do we show? | **80% / 84%** on the neutral ruler (untrimmed: 75% / 83%; ceiling ~87%) | **60% / 73%** on 15 targets, ±7pt noise | Jeff's answer on where an entry ends |

Read the table as: detection is better than we thought but measured on half the corpus;
classification is stale; boundaries are near their ceiling on Ketubot and unmeasurable
on Kiddushin.

## What is true today that was not true a week ago

- **True recall exists.** 96% on Ketubot against Jeff's 2005 list — genuinely blind,
  written twenty years before the detector. Every earlier accuracy number was the
  system checked against stories it had itself proposed.
- **The boundary ruler is honest.** It was 52 questions, all of them cases Jeff had
  flagged as wrong, so it could never show a boundary we had right and broke. Rebuilt
  from his 2005 list: **35 gradeable targets → 249**, run-to-run noise **7 points → 0**.
- **Wave 5's benefit is much smaller than claimed.** The old ruler said trimming
  doubled us on Ketubot 61-112 (33% → 67%). The neutral ruler says the untrimmed
  boundary was already 79% right.
- **Stage 1 discards 56% of Ketubot pages** before anything looks for a story. Half our
  known misses are there. Never noticed because nothing measured it.
- **Wave 5b is shelved.** Its trigger was "revive if we stall near 50%" — measured on
  the biased ruler. The real number is 80% of an ~87% ceiling.

## Waiting on Jeff (email sent 2026-08-30)

One question: **when a ruling is what makes a passage a story at all, is that ruling
part of the story we display, or the discussion that follows it?** His 2005 list keeps
it; his review notes say cut it. Both were made for different purposes; neither answers
this. Blocks axis 3's end rule. Also asked whether his lists cover other tractates —
that is the only route to a neutral ruler for Kiddushin.

## In flight

Nothing is mid-execution. The tree is clean and all work is committed.

## Next — see `tasks/NEXT/`, each brief is self-contained

| | task | depends on Jeff? | why now |
|---|---|---|---|
| **01** | Stage 2 over the 124 triage-discarded pages | no | largest unmeasured thing in the project |
| **02** | Diagnose Ketubot 77a | no | sharpest signal about the classifier; feeds Wave 6 |
| **03** | Stop discarding a second story in one segment | no | wrong under every definition |
| **04** | Fix the review UI Hebrew/English asymmetry | no | on the critical path for the next review round |
| — | Wave 6 (encode Jeff's criteria) | no | axis 2 is the stalest axis |
| — | Encode the end rule, re-check Ketubot | **yes** | — |

## Where things live — one job each

| file | its one job |
|---|---|
| **`STATUS.md`** | where we are today. Rewritten each session. **Start here.** |
| `tasks/NEXT/*.md` | one self-contained brief per ready task. Delete when done. |
| `tasks/lessons.md` | durable rules learned the hard way. Append-only. 24 of them. |
| `docs/golden/**` | dated findings. Immutable once written. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has said, and its disposition. |
| `CLAUDE.md` | how to work in this repo. Not status. |
| `FOR_SIMON.md` | the plain-English narrative of how it was built. |
| `tasks/PLAN_*.md` | historical plans. Wave 6 is live; the rest are archive. |

**The rule that keeps this working:** status goes in STATUS.md and nowhere else.
Findings go in a dated doc under `docs/golden/`. Rules go in `lessons.md`. If you find
yourself writing project status into a plan or a findings doc, stop — that is how the
last version of this became unnavigable.

## The numbers, in one place

```
Ketubot   182 golden stories · 0.9171 composite · 96% recall (of 44% of pages examined)
          167 detected stories · 249 gradeable boundary targets · 80%/84% boundaries
Kiddushin  85 golden stories · 0.8859 composite · recall unmeasured
           95 detected stories ·  15 gradeable boundary targets · 60%/73% ±7pt
Jeff       149 Ketubot stories in his 2005 list · 70 boundary corrections across 8 rounds
```
