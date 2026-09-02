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

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) then
[`2026-09-02-jeff-answers-gittin`](../docs/findings/2026-09-02-jeff-answers-gittin.md).

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
