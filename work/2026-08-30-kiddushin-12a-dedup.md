---
title: Kiddushin 12a: one detection covering two stories
capability: [detection]
tractate: [kiddushin]
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Kiddushin 12a: one detection covering two stories

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first.
**Capability: 2 Detection.** **Independent.** Open in the ledger since 2026-07-06.

## The case

Jeff on `Kiddushin 12a seg 13-15`: the verdict is *correct*, **but** it repeats much of
`12a seg 13-13`, and the passage contains **two** stories, each beginning `הָהוּא גַּבְרָא`
(at segments 13 and 14). So one detection covers two stories, and a second detection
duplicates part of it.

This is the same family as the Ketubot cases in `NEXT/03` (62a, 105b), where a second
story sharing a segment is discarded entirely. Here it is not discarded — it is merged
into its neighbour and partly duplicated. Worth doing together if one session takes both.

## Why it is a Detection problem, not a Boundaries one

The text is present in the output; what is wrong is the *unit* — how many stories we say
are there. A reader given one merged entry cannot separate them, and a database keyed on
entries will hold a duplicate. Boundaries decide the extent of a story; Detection decides
how many there are.

## Method

1. Reproduce from `results/v10/wave4_notrim/kiddushin_v10_notrim.json`, `Kiddushin 12a`.
2. Establish the corpus-wide rate **before** designing a fix (Lesson 18): how often does
   one detection span two passages each opening with a story-initial formula, and how
   often do two detections overlap? Count it across both tractates. A fix planned from a
   single case is how this project has gone wrong before.
3. Only then propose a fix, and prefer the smallest one.

## How you know it worked

A corpus-wide rate for both shapes (merged-pair, overlapping-duplicate), and 12a
resolving into two entries without duplication. If the rate turns out to be one or two
cases, say so and consider leaving it — a named, logged, rare defect beats a general
mechanism nobody can measure.

## Guardrails

- Measure the rate before fixing (Lesson 18).
- `הָהוּא גַּבְרָא` is a lexical marker, and Lesson 15 says such markers on Aramaic fail
  roughly half the time. Use it to *find* candidates, never as the rule.
- Report against both rulers separately (Lesson 24).
