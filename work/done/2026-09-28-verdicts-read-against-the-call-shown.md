---
title: Read an old `correct` against the call Jeff was shown — map_verdict_vocabularies and build_ruler
capability: [classification]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [scripts/map_verdict_vocabularies.py, scripts/build_ruler.py, results/rulers/, tests/test_verdict_vocabulary_map.py, tests/test_build_ruler.py]
finding: docs/findings/2026-09-29-verdicts-read-against-the-call-shown.md
superseded_by:
---

# Read an old `correct` against the call he was shown

**Self-contained.** Read `docs/findings/2026-09-28-consensus-phase1.md` §2 and §8.

## The problem

Before the axes UI (2026-09-02) every round asked *is the detector's call correct?*, not
*is this a story?*. A `correct` on a span the detector showed as `NOT_A_STORY` is his **no**
— 87 of the 128 verdicts of 2026-02-05. `scripts/map_verdict_vocabularies.py` maps every
`base_binary correct` to `is_story=yes`, and `scripts/build_ruler.py` puts `correct` in
ACCEPTED regardless of the classification shown. So the per-round "precision" in
`results/rulers/*_ruler.json` is partly agreement with the detector's own call.

`scripts/judge_labelled_spans.py` (consensus phase 1) already reads them correctly — it
recovers the classification shown from the page he reviewed (`shown_*` functions). **Reuse
that; do not write a third reading.**

Also known: the committed `results/rulers/*_ruler.json` are already stale against current
`main` (found 2026-09-28, PR #54) — regenerate after the fix, and say what moved.

## Method

1. Move the "what was he shown" recovery into one shared place both scripts import.
2. Map `correct` on a shown `NOT_A_STORY` → `is_story=no`; on a shown story → `yes`.
3. Test: a synthetic round with one of each. Regenerate the rulers; report every per-round
   figure before and after.

## When done

Finding, `## Outcome`, `python3 scripts/board.py finish 2026-09-28-verdicts-read-against-the-call-shown`.

## Outcome

**Done, 2026-09-29.** → [finding](../../docs/findings/2026-09-29-verdicts-read-against-the-call-shown.md)

- The reading moved to `scripts/verdict_reading.py`; `judge_labelled_spans.py`,
  `build_ruler.py` and `map_verdict_vocabularies.py` all use it (phase 1 labels unchanged
  except `cited_in_rules`, which follows the corrected register).
- Rulers: `story_precision` per round beside the unchanged published fields — ~0.92–0.95 on
  the story-by-story rounds; Kiddushin's "68%" is 0.928; wave 4's "11 of 15 incorrect" is
  1.0 as a classification. Simon's pre-screen no longer scored as Jeff's
  (`excluded_rounds`). Rulers regenerated (they were stale).
- Vocabulary map: 109 yes→no, 66 no→yes; lossy 129 → 57.
- Tests: `tests/test_verdict_reading.py`. Not checked: whether any golden builder shares
  the defect.
