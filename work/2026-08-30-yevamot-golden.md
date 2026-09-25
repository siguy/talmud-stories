---
title: Yevamot — golden
capability: [classification]
tractate: [yevamot]
blocked_by: [2026-08-30-yevamot-expert-round]
awaiting: []
writes: [results/canonical/yevamot_canonical.json, tests/test_bookkeeping.py]
finding:
superseded_by:
---

# Yevamot — golden

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../docs/technical/new_tractate_workflow.md),
which documents this sequence, then this.

## Method

See the workflow doc; this item is the handle and the ordering.

## Guardrails

- **Ask Jeff to keep his appendix separate BEFORE the first review round**, not
  after (Lesson 29). Once merged into his list it cannot be reconstructed, and the
  list stops being able to measure what we missed.
- Regenerate a same-day baseline before any comparison (Lesson 11).
- Report the corrections ruler and the neutral ruler separately (Lesson 24).

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.

## Banked before this item starts — Jeff's first Yevamot verdicts (2026-09-23)

Source: `validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json`. Build the
golden the way Gittin's is built (`scripts/build_gittin_golden.py`: verdicts first, then
the blind list, `label_source` on every entry) and read these in as `expert_verdict`.
They judge spans from `results/v11/twin_pass/yevamot_full_twinall.json`.

| span | verdict | note |
|---|---|---|
| 105a:13 | **yes** — a story **not on his 2005 list** | Starts mid-segment at *רבה ואביי מדבית עלי קאתו* and ends at *…חיה שיתין שנין* (his quote fields; the start quote was captured twice by the page — use it once) |
| 15a:14 | no | The Gemara's comment on R. Akiva's etrog (R-B4) |
| 15a:12 | no, **indicated** | Not on the page, but his 15a note marks this report's extent (12-13) and says *"it is not really a story"* (R-C5) |
| 17a:4 | no | Seating arrangement, then discussion (R-C5) |
| 106b:9 | no | Mar Zutra's practice, no continuation; the ruling is not narrative (R-C5) |

Simon's pre-screen `no`s on 43a:12, 45a:17, 78a:11, 101b:13 are **not** expert labels and
do not enter this golden.
