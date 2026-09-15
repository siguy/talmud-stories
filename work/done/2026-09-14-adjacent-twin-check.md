---
title: Ask about the segment next door — a targeted twin check after detection
capability: [detection]
tractate: [yevamot]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, tests/test_twin_pass.py, results/v11/twin_pass/]
finding: docs/findings/2026-09-14-twin-pass.md
superseded_by:
---

# Ask about the segment next door

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then
[`miss-anatomy`](../../docs/findings/2026-09-07-miss-anatomy.md) and
[`broken-prompt`](../../docs/findings/2026-09-09-broken-prompt-explains-everything.md).
**Capability: 2 Detection.** **Depends on Jeff: no.** **Cost: ~1-3 extra calls per daf
that has a story; one 20-page slice to measure.**

## The claim to test

18 of 38 Detection misses sit **one segment from a proposal**, and in 18 of 18 the
proposal is a *different* story — the missed one's twin. The broad instruction
("a run of parallel incidents is N stories") did not recover any of them: +1 unrelated
story on the slice, 0 of 4 twins. Asking the model to *find everything on a page* saturates.

**Claim:** a narrow, side-by-side question — *here is the story we found, here is the
segment beside it, is that a separate incident?* — recovers twins the broad pass cannot.

## Method

1. **After Stage 2, per page.** For each real story, collect segments at distance 1
   (extend to 2 only if 1 measures well) that are inside no story and that Stage 1
   labelled `NARRATIVE_EVENT` or `VERBAL_ACT`. Stage 1's labels are the trigger; no
   lexical rule (Lesson 15).
2. **One call per candidate**, JSON: `verdict ∈ {separate_incident, same_story,
   not_a_story}`; on `separate_incident`, `start`/`end` within the candidate's free
   window and a classification. Anything else is discarded and **counted**.
3. **Gate `TWIN_PASS`, default off.** Off = the function is not called. The detection
   prompt is not edited at all; a test pins that it is byte-identical either way.
4. **Measure on the fixed 20-page slice** (`results/v11/series_rule_slice/slice.txt`,
   36 stories, 4 twin cases). Runs are deterministic (spread 0.0 measured 2026-09-09),
   so one run per arm — but confirm the new pass is deterministic too.
5. **Score boundaries beside recall.** Over-splitting one story into two is the failure
   mode; the neutral ruler sees it and recall does not.
6. **Diff the rendered prompt against the control before running.** One command. It was
   skipped once and cost two nights.

## How you know it worked

- The four slice twins, **by name**: Yevamot 121b seg 14 (both criers), 63a seg 6
  (R. Elazar and the field), 34b seg 6 (Rava to bat Rav Ḥisda), 64b seg 6 (Rav Giddel /
  Rav Aḥa bar Yaakov). Each reported found / not found.
- Slice recall from **83.3% (30/36)** with the pass off.
- Proposals-not-on-his-list beside the recall change — every extra proposal is reviewer
  cost.
- Boundary ruler not worse.
- A failure-injection test: a call that fails adds nothing, removes nothing, and is
  counted (Lesson 21).

## Guardrails

- Never splice into the detection f-string. The pass is its own prompt, its own method.
- A candidate must lie **outside** every existing story; the pass may add, never move.
- Report the twin cases by name even if the aggregate moves — an aggregate gain that
  recovers no twin is the series-clause result again, and it is not this hypothesis.

## When done

Finding to `docs/findings/<date>-twin-pass.md`, `## Outcome` here, then
`python3 scripts/board.py finish 2026-09-14-adjacent-twin-check`.

## Outcome

**Measured on the slice, 2026-09-14 — every twin recovered.** Control 83.3% (30/36);
twin pass with the labelled trigger 88.9%; with `TWIN_TRIGGER=all` **94.4% (34/36)**.
Nothing lost, 0 span repairs, 3 of the pass's 4 additions on Jeff's list. By name: 63a
and 34b under both triggers; both 121b criers under `all` only — Stage 1 had labelled
that segment DELIBERATION, so the labelled trigger never asked. The two remaining misses
are the speech-act class (`jeff:speech-act-policy`), not twins.

**Full Yevamot, same day: 89.2% → 94.1% (96/102).** All six adjacent-class misses on
the tractate recovered by name; 12 proposals added, 9 of them not on his list — the
reviewer cost, in single digits. **Both flags still default off**: one tractate, and the
nine extras want a review page before the pass becomes the default.
→ [`twin-pass`](../../docs/findings/2026-09-14-twin-pass.md)
