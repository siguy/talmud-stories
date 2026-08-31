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
discarding more than half of Ketubot.

**Fails by:** dropping a page that held a story (invisible, permanent) · keeping an
empty page (costs money only).

**Measured by:** of the blind list's stories, the fraction sitting on pages we kept —
and always beside the fraction of pages examined, since the bar is meaningless without
its cost saving. **Current value: [`STATE.md`](STATE.md).**

**Gate: ≥98% — PROVISIONAL.** *Set to our current value, which is circular reasoning
in a principle's clothing. The defensible part is the shape, not the number; the number
falls out of §2b once the end-to-end target is set.* Losses here are invisible and
permanent, so the bar is the strictest of the six. But the capability exists *to save
money* — a bar quoted without its cost saving is meaningless, and a couple of points of
recall for a large cost cut may well be a good trade. That is a decision to take deliberately, not a
defect to fix reflexively.

### 2. Detection
**Does:** given a page we chose to examine, propose every span that might be a story.
In: page segments. Out: candidate spans. It proposes; it does not judge.

**Why it is its own capability:** a story never proposed cannot be recovered by any
later step. A bad proposal costs one reviewer click. Those are different enough costs to
need different bars — and different measurements: recall requires a blind dataset,
precision does not.

**Fails by:** never proposing a real story (invisible) · proposing noise (visible, cheap).

**Measured by:** recall against the blind 2005 lists. **Current values:**
[`STATE.md`](STATE.md).

**Quote the test with the number, always.** The published figure credits a proposal
anywhere in the aligner's search window, which runs to 14 segments and straddles daf
boundaries; a **strict** test requires the proposal to overlap a segment the story
actually occupies. The two differ by several points, and the gap is almost entirely
cross-page stories whose text sits on a continuation daf we proposed nothing on. The
loose test is **provably** over-credited in at least one case, so treat it as an upper
bound (`tests/test_build_ruler.py::test_the_loose_window_credits_a_story_we_never_proposed`).

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
the canonical golden (CIRCULAR — correct for precision, never for recall). This is the one
we have as a point estimate. **Current value: [`STATE.md`](STATE.md).**

*Review-round precision* — **counting only rejections that dispute whether the passage is
a story.** A rejection objecting to the boundary, the merge, or our confidence level
belongs to another capability; pooling them is how this project mistook a boundary problem
for a classification one (Lesson 30). `adjust` counts as **accepted**: it says the story is
real and the extent is wrong. It is reported as a **range, never a point** — the lower
bound counts every rejection, the upper bound only the classification ones, and the width
is the notes too ambiguous to sort. Narrowing it needs the review UI to capture *which*
thing is wrong (`work/2026-08-30-review-verdict-axes.md`), not more inference over free
text. Review-round figures are also per detector version, so they are **not** comparable
with the harness number and must never be quoted as though they were.

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

**Measured by:** hit / near against the blind boundary set, reported separately from the
corrections set — they encode different tasks and must never be pooled (Lesson 24).
**Current values: [`STATE.md`](STATE.md).**

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
```

*Checked once, on Ketubot, 2026-08-30: the two allocated factors multiplied out to the
end-to-end figure then measured. Worked once is not a law — re-check it, from
[`STATE.md`](STATE.md), before leaning on it again.*

So the only number anyone has to defend is the **end-to-end** one; the rest are
allocated backwards from it. And the end-to-end number is not a technical question, it
is a claim about the product:

> **Open (Jeff — `jeff:miss-rate`):** if we publish this as "the stories in tractate X,"
> what miss rate would make that claim false? 1 in 20? 1 in 50? That single number sets
> Triage and Detection. *This file previously assigned the question to Simon. It is a
> claim about scholarly completeness, so it belongs to the scholar making it.*

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
> → measured in [`docs/findings/2026-08-30-mishnah-filter-delta.md`](docs/findings/2026-08-30-mishnah-filter-delta.md)

All three are drafted, in ask-order, in
[`comms/JEFF.md`](comms/JEFF.md).

## 3. Ground truth — say which one, and say if it is blind

Every number must name its dataset and its kind. This is not bookkeeping: quoting a
circular number as an accuracy claim is the mistake that cost this project months.

**Count golden datasets the same way, and say which way.** A canonical file holds every
entry Jeff ruled on, the rejected ones included, so *entries* and *accepted* are two
different numbers. This project quoted one tractate's entries against another's
accepted-only for a long time. Quote entries against entries, accepted against accepted,
never one of each — and take both from [`STATE.md`](STATE.md) rather than typing them.

| dataset | kind | what it can measure |
|---|---|---|
| `jeff comms/b.ketubot (1).doc` | **BLIND** — written 2005, 20 yrs pre-detector | recall, triage recall |
| `tests/expert_boundary_targets_2005.json` | **BLIND** — derived from the above | boundaries, regressions |
| `results/expert_lists/kiddushin_2005.json` | **BLIND**, per entry — carries `blind` and `counts_for_recall` flags, which are **not the same question** | recall, triage recall, boundaries |
| `results/canonical/{tractate}_canonical.json` | **CIRCULAR** — we proposed, Jeff corrected | precision, consistency |
| `results/rulers/{tractate}_ruler.json` | **JOINED** — each entry says whether it is expert-listed (blind) and/or proposed (circular) | recall *and* precision, from one file |
| `tests/expert_boundary_targets_v2.json` | **CIRCULAR + biased** — every target is a case we got wrong | "did we fix known failures" only |
| review-round verdict files | **CIRCULAR** — verdicts on what we proposed | precision |

Sizes, and which cells each one currently fills, are in [`STATE.md`](STATE.md).

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

## 4. The gates, and why each one is what it is

**This table carries no values.** They live in [`STATE.md`](STATE.md), which is generated,
and in [`STATUS.md`](STATUS.md), which is the hand-written narrative. A number typed here
is a second copy that drifts — this file said the golden was both 182 and 187 on two
different lines, which is how the rule got written.

| capability | metric | ground truth | gate to move on | why that gate |
|---|---|---|---|---|
| **Triage** | % of true stories surviving, beside % of pages examined | blind 2005 lists | **≥98%**, and state the exchange rate | losses here are invisible and permanent; but recall traded for a large cost cut may be a good deal — that is a decision, not a bug |
| **Detection** | recall, loose **and** strict | blind 2005 lists | **≥95%** | Jeff's own lists missed stories; matching a careful scholar is the honest ceiling |
| **Classification** | precision vs golden | canonical golden (CIRCULAR) | **≥85%** | below ~85% a reviewer wades through junk; set by reviewer patience, not by truth |
| **Boundaries** | at expert's clause / within one | blind 2005 lists | **≥75%** hit+near | the reader sees surrounding text, so errors are visible and self-correcting |
| **Review** | throughput; inter-rater agreement | — | a scholar reviews a tractate in **days, not weeks** | Jeff: 6 weeks/tractate makes Shas take years |
| **Publication** | not yet defined | — | — | set by what the published form must show (§3 of the reorg plan) |

**A gap that no value can close, so it belongs here and not in `STATE.md`:**
classification precision is measured against a CIRCULAR set — correct for precision, but
structurally unable to tell us about stories we never proposed. That is Detection's job
and it needs a blind list. Which tractates have one, and which cells are still empty,
is [`STATE.md`](STATE.md)'s coverage matrix.

## 5. Answering the seven questions, for any capability

Use this shape every time, in `STATUS.md`:

1. **Where are we?** — the metric's current value, with its dataset named.
2. **What have we done?** — link the dated finding in `docs/golden/`, not a retelling.
3. **How are we measuring it?** — the row above. If the metric is not in this file, it
   is not a metric yet.
4. **Where do we measure up?** — current vs gate, and say if it is inside the noise.
5. **How right must we be?** — the gate, justified by recoverability (§2). Not a vibe.
6. **If we are not ready, how do we improve?** — a brief in `work/`.
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
  work is now a capability plus a brief in `work/`.
