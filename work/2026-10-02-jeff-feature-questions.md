---
title: Ask Jeff about classes, not passages — contrast pairs per feature, his own sureness on every answer, and a page ranked by what he would teach us
capability: [review, classification]
tractate: []
blocked_by: []
awaiting: []
writes: [validation/generators/generate_axis_review_ui.py, validation/generators/review_ui_core.py, tests/test_review_ui_symmetry.py, tests/test_axis_review_ui.py, scripts/build_contrast_pairs.py, results/consensus/contrast_pairs.json, comms/JEFF.md, scripts/verdict_reading.py]
finding:
superseded_by:
---

# Ask Jeff about classes, not passages

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), [`comms/JEFF.md`](../comms/JEFF.md),
[`docs/STORY_RULES.md`](../docs/STORY_RULES.md), and the rule-panel finding
(`docs/findings/2026-10-02-rule-panel-lenses.md`). Eruvin untouched.

## The problem

One verdict from Jeff labels one passage. His time is the bottleneck, and the corpus is
the whole Bavli. An answer about a **feature boundary** ("an incident brought to a rabbi
who rules: story; a question sent by letter and answered: not") decides every passage of
that shape in every tractate. Three gaps today:
- we ask him about passages one at a time;
- the review page records whether the *detector's* confidence is right, not **how sure he
  is** of his own answer, so his borderline calls and his firm calls look alike;
- the page order does not favour the items that would teach us most.

## Method

1. **Contrast pairs** (`scripts/build_contrast_pairs.py` → `results/consensus/contrast_pairs.json`).
   For each judge whose answers caused panel-vs-Jeff disagreements (the rule-panel per-feature
   table), pick pairs that differ on **that feature only**: one he called a story, one he
   did not, both with the other judges agreeing. Seed pair for `jeff:report-vs-incident`:
   Ketubot 50b:4 (orphans before Shmuel, a ruling) vs Gittin 80b:1–2 (a question sent by
   letter). Each pair is one question: *"Where is the line between these two?"*
2. **His own sureness, required** (`generate_axis_review_ui.py`): every answer to *is it a
   story?* also asks **"How sure are you? Sure / Leaning"**. Keep the existing optional
   axes, including the detector-confidence axis, which answers a different question. Export
   field `jeff_sure`; bump `schema_version`; add the field to `verdict_reading.py`'s
   reading (Lesson 38: a new field nobody reads is a silent loss). Symmetry test updated.
3. **Ranking**, written into the page builder and used by phase 2: items where the two
   models' panels disagree on **a single judge** first (one feature in doubt, so his answer
   settles it), then contrast pairs, then audit samples.
4. **The email section** in `comms/JEFF.md`: at most 3 contrast-pair questions per round,
   each with both passages linked, the feature named in plain words, and our current
   reading marked as ours.

## How you know it worked

- The page renders in the browser with Hebrew + English, story highlighted, the sureness
  question present and required, and an export carrying `jeff_sure` that
  `verdict_reading.py` reads (test).
- After his next round: each contrast-pair answer is turned into a decision-table row or a
  STORY_RULES entry in his words, and the number of passages that row re-labels across the
  four labelled tractates is counted (*how far one answer reaches*).

## Guardrails

- His answers are evidence; a pair answer never bulk-relabels a golden without counting
  what it touches (Lesson 27).
- ≤ 3 pair questions per round; the round's ≤ 35-item cap stands.
- Old review files stay readable: `jeff_sure` absent ⇒ unknown, never "sure".

## When done

Finding in `docs/findings/`, `## Outcome`,
`python3 scripts/board.py finish 2026-10-02-jeff-feature-questions`.
