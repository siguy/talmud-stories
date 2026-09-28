---
title: The shipped twin-pass question carries the R-C5 gloss — correct and measure it
capability: [detection]
tractate: [yevamot]
blocked_by: []
awaiting: [jeff:report-vs-incident]
writes: [src/story_detector_v11.py, tests/test_twin_pass.py, results/v11/twin_pass/]
finding:
superseded_by:
---

# The twin-pass question carries the R-C5 gloss

**Self-contained.** Read `docs/findings/2026-09-28-consensus-phase1.md` §7 and
`docs/STORY_RULES.md` R-C0 and R-C5.

## The problem

`_twin_prompt()` in `src/story_detector_v11.py` (on by default since 2026-09-25) tells the
model that *"a bare report of what someone did or used to do, where nothing follows from
the act… A single act cited as a precedent is not a story, however it is introduced"* is
`not_a_story`. That is the gloss removed from R-C5 on 2026-09-28: it contradicts R-C0
(*"A man stole a cow… Rava ruled… you may have a story"*). A judge given the same words
rejected 21 incident-plus-ruling stories on his lists. The twin pass may be rejecting the
same shape beside a found story.

## Method

1. Reword the bullet to R-C5 as corrected (what someone did or used to do, cited as
   evidence or practice, with no one responding) and add R-C0's cow case as a `separate
   incident` example. Keep `tests/test_twin_pass.py` pinning the phrases.
2. Measure with `scripts/rejudge_twin_additions.py` (old vs new wording, same day) — it sees
   only what the new wording drops — **and** a full Yevamot run, **two per arm** (Lesson 43:
   one full run moves ±1–2 stories by itself).
3. Check by name: Yevamot 78a:13 (`yevamot_050`), and the incident-plus-ruling twins.

## When done

Finding, `## Outcome`, `python3 scripts/board.py finish 2026-09-28-twin-pass-r-c5-wording`.
