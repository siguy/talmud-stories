# FRAMEWORK — how this project is measured

**Companion to [`STATUS.md`](STATUS.md).** This file says *how we measure and what
counts as good enough*. STATUS says *where we are*. This one changes rarely; that one is
rewritten every session.

---

## 1. The six capabilities

"Phases" implies a sequence you finish. These six run at once, and each can be improved
after we have moved past it. Story text flows through them in order, so a loss early is
a loss everywhere.

```
Triage  →  Detection  →  Classification  →  Boundaries  →  Review  →  Publication
```

**What makes something a capability here:** it can fail *independently* and be measured
*independently*. Two things that always fail together are one capability. Two things
that share a prompt but fail differently are two — Detection and Classification live in
the same Stage 2 call today, and that is an implementation detail, not a reason to
measure them together.

---

### 1. Triage
**Does:** given a page of Talmud, decide whether it is worth examining at all. In: page
text. Out: one yes/no per page. It never sees a story and never produces one.

**Why it is its own capability:** it is the only step that discards material *before
anything looks at it*, and the only one whose errors leave no trace downstream. A page
never examined produces no record of what was lost. Fusing it into detection hides its
cost — which is exactly what happened here until 2026-08-30, when it turned out to be
discarding 56% of Ketubot.

**Fails by:** dropping a page that held a story (invisible, permanent) · keeping an
empty page (costs money only).

**Measured by:** of the blind list's stories, the fraction sitting on pages we kept.
**Now: 98.0%** — 3 of Jeff's 149 lost, while examining 44% of pages.

**Gate: ≥98% — PROVISIONAL.** *Set to our current value, which is circular reasoning
in a principle's clothing. The defensible part is the shape, not the number; the number
falls out of §2b once the end-to-end target is set.* Losses here are invisible and
permanent, so the bar is the strictest of the six. But the capability exists *to save
money* — a bar quoted without its cost saving is meaningless, and 2% of recall for a
56% cost cut may well be a good trade. That is a decision to take deliberately, not a
defect to fix reflexively.

### 2. Detection
**Does:** given a page we chose to examine, propose every span that might be a story.
In: page segments. Out: candidate spans. It proposes; it does not judge.

**Why it is its own capability:** a story never proposed cannot be recovered by any
later step. A bad proposal costs one reviewer click. Those are different enough costs to
need different bars — and different measurements: recall requires a blind dataset,
precision does not.

**Fails by:** never proposing a real story (invisible) · proposing noise (visible, cheap).

**Measured by:** recall against the blind 2005 list. **Now: Ketubot 96.0%** (143/149),
**Kiddushin 93.3%** (83/89).

Quote the test with the number. The published figure credits a proposal anywhere in the
aligner's search window, which runs to 14 segments and straddles daf boundaries. Under a
**strict** test — a proposal must overlap a segment the story actually occupies — it is
**87.9% / 84.3%**. The gap is almost entirely cross-page stories whose text sits on a
continuation daf we proposed nothing on.

**Gate: ≥95% — PROVISIONAL.** *Half-derived: Jeff's lists missing stories genuinely
proves 100% is not the standard, but it does not prove 95.* Jeff's own 2005 lists
missed stories he later accepted from us — his
words: *"the AI has found some stories we missed."* So 100% is not the human standard.
Matching a careful scholar working deliberately is the honest ceiling.

### 3. Classification
**Does:** given a proposed span, decide whether it is really a story, by Jeff's criteria
— actual not hypothetical, speech alone insufficient, emotional reactions count,
halakhic stories included. Out: a verdict plus a `borderline` flag.

**Why it is its own capability:** it is the only one whose ground truth is *contested
among scholars* — Jeff said so directly. Its errors are therefore partly definitional
rather than technical, and it is the only capability where *"mark it borderline and let
database users decide"* is a legitimate answer rather than an evasion.

**Fails by:** admitting a non-story (costs reviewer time) · rejecting a real one
(invisible, and as costly as a detection miss).

**Measured by:** two different things, and this file used to pool them.

*Harness precision* — classification precision from `scripts/evaluate_golden.py` against
the canonical golden (CIRCULAR — correct for precision, never for recall).
**Now, current detector, measured 2026-08-30: Ketubot 89.2%** (TP 149 / FP 18 / FN 15
after the golden grew to 187 — precision is unchanged; the 5 additions are all FN),
**Kiddushin 85.3%** (TP 81 / FP 14 / FN 4). *Both are AT or ABOVE the gate.*

*Review-round precision* — **counting only rejections that dispute whether the passage is
a story.** A rejection objecting to the boundary, the merge, or our confidence level
belongs to another capability; pooling them is how this project mistook a boundary problem
for a classification one (Lesson 31). `adjust` counts as **accepted**: it says the story is
real and the extent is wrong. On the review rounds this gives Ketubot 87.9–94.8% (Mar 2026)
and Kiddushin 67.4–92.1% (Apr 2026, v7) — a range, not a point: the lower bound counts every
rejection, the upper bound only the classification ones, and the width is the notes too
ambiguous to sort. Narrowing it needs the review UI to capture *which* thing is wrong
(`NEXT/04`), not more inference over free text.

*Those March/April percentages are review-round figures on 5-month-old detector versions,
not harness precision. An earlier claim in this file that we had "no current number"
confused the two: we do have a current harness number, and it needed one run.*

**Gate: ≥85% — PROVISIONAL, and the weakest of the six.** *Invented. "Below ~85% a
reviewer spends more time rejecting than confirming" is a plausible sentence with no
measurement behind it. Only Jeff can settle this — see §2b.* Set by reviewer patience,
not by truth. Below roughly 85% a reviewer
spends more time rejecting than confirming, and reviewing is this project's actual
bottleneck — so classification quality is really a *review throughput* lever.

### 4. Boundaries
**Does:** given a confirmed story, decide the exact extent of text to display — start
and end, to sub-paragraph precision.

**Why it is its own capability:** a story can be found and correctly judged and still
shown with the wrong extent. It is also the only capability whose errors the end reader
can see and compensate for.

**Fails by:** over-trimming, cutting story content (the serious direction) ·
under-trimming, showing extra context (mild).

**Measured by:** hit / near against the blind boundary set.
**Now: 80% / 84% Ketubot** (untrimmed 75%/83%), 60% / 73% ±7pt Kiddushin.

**Gate: ≥75% hit+near — PROVISIONAL.** *The ceiling (87%) is measured and the ordering
is principled; the 75 is not.* The loosest of the six, because the reader sees the
surrounding text and can correct silently. There is also a structural ceiling near 87%:
13% of Jeff's boundaries do not fall on a clause edge, so no prompt can reach them.
Currently blocked on a definitional question with Jeff.

### 5. Review
**Does:** get human scholars to confirm, reject and annotate entries fast enough that
the whole Talmud is reachable.

**Why it is its own capability:** it fails by throughput and disagreement, not accuracy.
It is a process, not a model — and it is the bottleneck Jeff himself named.

**Fails by:** taking too long (Shas becomes unreachable) · reviewers disagreeing with
each other (published errors, though the crowd-edit design absorbs these).

**Measured by:** days per tractate; inter-rater agreement against Jeff.
**Now: not started.**

**Gate: a scholar reviews a tractate in days, not weeks — DERIVED.** *The only gate in
this document with a real basis.* Jeff's own figure: six weeks
per tractate makes the Talmud years of one person's life. That number is why
crowd-sourcing exists in the plan at all.

### 6. Publication
**Does:** the resource itself — every story with its boundaries, classification and
stated accuracy, plus the columns Jeff asked for (notes, references to scholarship,
Yerushalmi parallels, borderline flags), editable by scholars.

**Why it is its own capability:** it is the goal, and its requirements set everyone
else's bars. What the page must *show* is what determines how right the boundaries need
to be.

**Measured by:** not yet defined. **Now: not started.**

## 2. The rule that sets the gates: **recoverability**

A uniform "95% everywhere" would be arbitrary. What actually differs is **what happens
when each one is wrong**, and that is what sets its bar.

| when it's wrong | who notices | can it be fixed later? | so the bar is |
|---|---|---|---|
| **Triage** drops a page | nobody, ever | no — the story never enters the pipeline | **highest** |
| **Detection** misses a story | nobody | only by re-running everything | **high** |
| **Classification** admits a non-story | the reviewer | yes, one click | medium — set by reviewer patience |
| **Classification** rejects a real story | nobody | no | high |
| **Boundaries** are wrong | the reader | yes, and the reader sees the surrounding text anyway | **lowest** |
| **Review** disagrees with itself | published errors | yes, it is crowd-edited by design | medium |

**Invisible, permanent errors get the highest bars. Visible, correctable ones get the
lowest.** That is the whole principle.

## 2b. The gates are PROVISIONAL — and here is how to settle them

**Four of the five gates above were invented.** Only Review's is derived. The *shapes*
are defensible — invisible-and-permanent gets the strictest bar, visible-and-correctable
the loosest — but the numbers were picked, then dressed as principles. Recording that
here rather than letting it calcify.

**Gates should not be picked one at a time, because they compose.** Recall multiplies
down the pipeline, which is checkable against what we already measured:

```
triage recall  ×  detection recall  =  end-to-end recall
   0.980       ×       0.980        =       0.960     ← matches the measured 96.0%
```

So the only number anyone has to defend is the **end-to-end** one; the rest are
allocated backwards from it. And the end-to-end number is not a technical question, it
is a claim about the product:

> **Open (Simon):** if we publish "every story in the Talmud," what miss rate makes that
> claim false? 1 in 20? 1 in 50? That single number sets Triage and Detection.

> **Open (Jeff — add to the next email):** at what error rate does reviewing our output
> become worse than working from scratch? That single number sets Classification, and he
> is the only person who can answer it.

Until both are answered, quote the gates as provisional and say so.

One further question is open with Jeff, on **scope** rather than on a gate:

> **Open (Jeff — scope):** do stories quoted inside a **Mishnah** belong in the database?
> He told us (Kiddushin 50b) they should be "catalogued with Mishnah stories, not Talmud
> stories"; he also marked **correct** all four Ketubot stories our Mishnah filter now
> deletes. We read him as asking for a separate catalogue, not exclusion. Until he
> answers, Ketubot's Classification numbers understate: the filter alone accounts for
> **4 of its 15 golden false negatives**.
> → measured in [`docs/golden/v11/mishnah_filter_delta_2026-08-30.md`](docs/golden/v11/mishnah_filter_delta_2026-08-30.md)

All three are drafted, in ask-order, in
[`docs/golden/v11/email_jeff_next_open_questions.md`](docs/golden/v11/email_jeff_next_open_questions.md).

## 3. Ground truth — say which one, and say if it is blind

Every number must name its dataset and its kind. This is not bookkeeping: quoting a
circular number as an accuracy claim is the mistake that cost this project months.

**Count golden datasets the same way, and say which way.** A canonical file holds every
entry Jeff ruled on, the rejected ones included: Ketubot is 187 entries / 164 accepted,
Kiddushin 96 / 85. This project has been quoting Ketubot's *entries* against Kiddushin's
*accepted-only* — for a long time as "182 and 85" — as though they were the same
measurement.

| dataset | n | kind | what it can measure |
|---|---|---|---|
| `jeff comms/b.ketubot (1).doc` | 149 Ketubot stories | **BLIND** — written 2005, 20 yrs pre-detector | recall, triage recall |
| `tests/expert_boundary_targets_2005.json` | 294 boundaries | **BLIND** — derived from the above | boundaries, regressions |
| `results/expert_lists/kiddushin_2005.json` | 89 Kiddushin stories | **BLIND** — of 95 parsed; excludes 1 he added and 5 appendix entries | recall, triage recall, boundaries |
| `results/canonical/ketubot_canonical.json` | 187 entries · 164 accepted | **CIRCULAR** — we proposed, Jeff corrected. v7 + v9, several rounds | precision, consistency |
| `results/canonical/kiddushin_canonical.json` | 96 entries · 85 accepted | **CIRCULAR** — v7 only, one round | precision, consistency |
| `results/rulers/{tractate}_ruler.json` | Ketubot 201, Kiddushin 122 entries | **JOINED** — each entry says whether it is expert-listed (blind) and/or proposed (circular) | recall *and* precision, from one file |
| `tests/expert_boundary_targets_v2.json` | 70 boundaries | **CIRCULAR + biased** — all are cases we got wrong | "did we fix known failures" only |
| review-round verdict files | 8 rounds | **CIRCULAR** — verdicts on what we proposed | precision |

**CIRCULAR means the system helped choose what it is graded on.** Such a set can measure
precision (of what we proposed, how much is good) but *never* recall (what did we never
propose).

**A blind list stops being blind the moment the expert merges our output into it.**
This is not hypothetical: five Kiddushin entries are cases from our own runs that Jeff
annotated and merged into his list. They look exactly like his other 90 — same column,
same hand, no marker — and the only reason we know is that the appendix he built them
from survived as a separate file. Nothing in the merged list would ever have shown it.

Two consequences:

- **Ask before the first review round on a tractate**, not after. An appendix kept
  separate, or entries marked, costs the expert nothing and cannot be reconstructed
  afterwards. Gittin, Yevamot and Eruvin are clean precisely because we have never run
  there — a list can only be contaminated by output we have actually produced, which
  also makes them the only place a clean floor test is available.
- **Check every expert list against what we sent him** before quoting it as blind —
  `scripts/check_appendix_coverage.py`. Provenance is a property to be tested, not
  inferred from a file's name or its date.

## 4. The scoreboard

| capability | metric | ground truth | Ketubot | Kiddushin | gate to move on | why that gate |
|---|---|---|---|---|---|---|
| **Triage** | % of true stories surviving | blind 2005 list | **98.0%** (3 of 149 lost) at 44% of pages examined | unmeasured | **≥98%**, and state the exchange rate | losses here are invisible and permanent; but 2% for a 56% cost cut may be a good trade — that is a decision, not a bug |
| **Detection** | recall | blind 2005 list | **96.0%** (143/149) | unmeasured | **≥95%** | Jeff's own lists missed stories; matching a careful scholar is the honest ceiling |
| **Classification** | precision vs golden | canonical golden (CIRCULAR) | **89.2%** | **85.3%** | **≥85%** | below ~85% a reviewer wades through junk; this is set by reviewer patience, not by truth |
| **Boundaries** | at expert's clause / within one | blind 2005 list | **80% / 84%** (ceiling ~87%) | 60% / 73%, ±7pt | **≥75%** hit+near | the reader sees surrounding text, so errors are visible and self-correcting |
| **Review** | throughput; inter-rater agreement | — | not started | not started | a scholar reviews a tractate in **days, not weeks** | Jeff: 6 weeks/tractate makes Shas take years |
| **Publication** | — | — | not started | not started | — | — |

**Known gaps in this table, stated rather than hidden:** classification precision is
measured against a CIRCULAR set — correct for precision, but it cannot tell us about
stories we never proposed; that is Detection's job and it needs the blind list.
Kiddushin's three blind cells are unfilled but no longer unfillable — it has a blind
list as of 2026-08-30 (`results/expert_lists/kiddushin_2005.json`); `NEXT/06` and
`NEXT/07` fill them.

## 5. Answering the seven questions, for any capability

Use this shape every time, in `STATUS.md`:

1. **Where are we?** — the metric's current value, with its dataset named.
2. **What have we done?** — link the dated finding in `docs/golden/`, not a retelling.
3. **How are we measuring it?** — the row above. If the metric is not in this file, it
   is not a metric yet.
4. **Where do we measure up?** — current vs gate, and say if it is inside the noise.
5. **How right must we be?** — the gate, justified by recoverability (§2). Not a vibe.
6. **If we are not ready, how do we improve?** — a brief in `tasks/NEXT/`.
7. **Can we improve it after moving on?** — see below.

## 6. Can a capability improve after we move past it?

**Yes for all six — but the cost differs, and that is what the gate is really pricing.**

- **Triage, Detection** — improving means re-running the corpus. Cheap in money, but
  every downstream label built on the old output must be re-checked. Expensive in
  *human* time, which is the scarce resource.
- **Classification** — same re-run, and the crowd-sourced database is designed to absorb
  corrections continuously. This is the one that improves most gracefully.
- **Boundaries** — cheapest. Spans ride on top of detections, so they can be recomputed
  without disturbing anything else. This is why the boundary gate is the loosest.
- **Review, Publication** — improve by their nature; they are processes, not artifacts.

**The asymmetry to keep in mind:** re-running costs money, but re-validating costs Jeff.
Money is not the constraint. That is why the upstream gates are strict and the
downstream ones are loose.

## 7. Language — use these words, only these

- **blind** / **circular** — of a dataset. Never quote a circular number as accuracy.
- **recall** — of the true stories, how many did we find. Needs a blind set.
- **precision** — of what we proposed, how much is real. A circular set is fine.
- **hit / near / miss** — boundary at the expert's clause / within one / elsewhere.
- **gate** — the value at which we may move on. Justified by §2, never invented.
- **measured / indicated / suspected** — confidence in any finding. Say which. An
  indication presented as a measurement is how this project has misled itself before.
- **capability** — one of the six. Not "phase", not "wave", not "axis".
- **wave** — a historical batch of changes (Waves 1-7). Retired as a planning unit;
  work is now a capability plus a brief in `tasks/NEXT/`.
