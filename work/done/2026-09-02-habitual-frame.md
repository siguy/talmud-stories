---
title: A custom that frames a one-time event is still a story (Gittin 57a, Beitar)
capability: [detection, classification]
tractate: [gittin]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py]
finding: docs/findings/2026-09-02-jeff-answers-gittin.md
superseded_by:
---

# A custom that frames a one-time event is still a story

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) then
[`2026-09-02-jeff-answers-gittin`](../../docs/findings/2026-09-02-jeff-answers-gittin.md).

## The defect, in his words

Gittin 57a, `אשקא דריספק חריב ביתר`. Stage 1 labelled the segment `HABITUAL`; Stage 2
rejected it; it is on his 2005 list and he confirmed on 2026-09-01: **"clearly a story.
After the custom you have the one time event — One day the emperor's daughter…"**

The passage opens with what Beitar *used to* do — plant a cedar for a boy, a cypress for a
girl — and then turns: one day the carriage shaft breaks, the attendants cut a tree, the
town falls on them, and the war follows. **We stop at the frame.** The same shape is why
38b was missed: R. Yoḥanan's two uprooted families sit inside Rabba's dictum.

## The claim to test

A passage whose opening is habitual is not thereby disqualified: what matters is whether a
**single event** follows. Today `HABITUAL` reads as an end state, in Stage 1's label and in
Stage 2's disqualifiers.

## Method

1. **Measure the corpus-wide rate first** (Lesson 18): how many pages carry a `HABITUAL`
   segment that we reject, and how many of those hold a story on a blind list? Do this
   before touching a prompt — the answer may be two passages in five tractates.
2. If the rate justifies it, the change is to Stage 2's instruction, not to Stage 1's
   label: a habitual frame followed by a datable, single occurrence is a story.
3. Re-run only the affected pages; price it the way the triage rule change was priced.

## Guardrails

- **Do not** relabel `HABITUAL` in Stage 1. It is a true description of the clause, and
  the ablation record shows what happens when a label is bent to mean something else.
- A prompt change means a same-code repeat run before attributing any score move
  (Lesson 22).

## Outcome

**Implemented, measured, and it did not work. Kept anyway, and marked as ineffective.**

The rate justified the attempt (Lesson 18): 18 `HABITUAL` segments on examined Gittin
pages, 16 covered by no proposal, **3 of those inside one of his stories — 19%** against
14.3% for discarded pages generally.

The prompt now says a custom is often the *frame* of a story and the story starts at the
custom, with his quote and date; R-C4 got the parallel change for a story quoted inside a
dictum. On the four pages carrying the known cases, **1 of 3 came back** (58a seg 4). On a
full re-run of the tractate: **strict recall 108/112 before and after, the same four
misses**, 147 → 145 proposals with 7 gained and 9 lost, most of them the same stories
re-bounded — churn the noise floor produces on identical code, and no same-code repeat was
run to separate them (Lesson 22).

**What the attempt did buy is the diagnosis.** Beitar is not proposed at all, not even as
`NOT_A_STORY` — so Stage 2 never generates the candidate, and no criteria wording can
reject-or-accept a passage it does not see. 62a has the same signature. That moves the
problem from Classification to **Detection's coverage of a page**, which is the iterative
"find more stories" pass, and it is a different piece of work.

The wording stays (it is his rule, faithfully written down) and is pinned by
`tests/test_prompt_carries_the_rules.py` so it cannot be silently dropped while it is
still ineffective. **The shipped Gittin artifact remains the pre-change run**, because
nothing measured better.
