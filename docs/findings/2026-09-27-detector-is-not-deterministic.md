# The detector is not deterministic: two identical full Yevamot runs disagree on 3 of Jeff's stories

**2026-09-27.** Status: **measured** — one same-code repeat, full tractate, same day.
Corrects the determinism claim in
[`2026-09-09-broken-prompt-explains-everything`](2026-09-09-broken-prompt-explains-everything.md)
(*"spread 0.0… a single run is comparable to another single run"*).

## What was run

`scripts/run_new_tractate.py --tractate yevamot`, identical code (`8db3c1d`), identical
config (`gemini-3-flash-preview`, thinking off, temperature 0.1, twin pass on), cached
triage, twice, about 30 minutes apart:
`results/v11/twin_pass/yevamot_full_twin2.json` and `…_twin2_r2.json`.

## What differed

| | run 1 | run 2 |
|---|---|---|
| Detection recall vs his 2005 list (BLIND) | **95/102 = 93.1%** | **94/102 = 92.2%** |
| Jeff's stories found in one run only | 45a (`yevamot_014`), 59b (`yevamot_023`) | 78a (`yevamot_050`) |
| page-level Stage 2 proposals only in this run | 8 | 5 |
| same span, different classification | 12 (e.g. 78b 13-20: `NOT_A_STORY` ↔ `HIGH_CONFIDENCE`) | |
| twin-pass additions only in this run | 101b:14, 45a:17 | 101b:13 |

**Run-to-run, 3 of 102 list stories flip.** Recall moves by a story either way from
noise alone, with no code change.

## Why the 2026-09-09 measurement said 0.0

It was three repeats on a **20-page slice** (36 list stories). A flip rate of 3 in 102
stories over 106 examined pages is ~1 flip per 35 pages; on 20 pages, a run of zero flips
across a few repeats is the expected outcome, not evidence of determinism. The slice was
too small to see this rate. Temperature is 0.1, not 0.

## What this changes

- **Single-run comparisons on a full tractate carry a ±1–2 story floor on Yevamot.**
  Every recall delta of one story, in either direction, is inside it.
- **Twin pass, off → on: 89.2% → 92.2–94.1% across three runs** (old wording 94.1; new
  wording 93.1, 92.2). **+3 to +5 stories, still clear of the floor.** The pass works.
- **Old wording vs new wording (94.1 vs 93.1/92.2): not distinguishable.** Retracted:
  the 2026-09-27 claim that *"the one story lost is the one the re-ask predicted."* In run
  1, `yevamot_050` was lost because the twin addition 78a:13 was dropped **and** the
  page-level proposal 78a:17 did not appear; in run 2, 78a:17 appeared and the story was
  found. The re-ask's prediction about the twin addition was right; its effect on recall
  was not isolated.
- **The 2026-09-25 re-ask stands**: 21/21 old-wording verdicts reproduced — a short,
  narrow call is far more stable than a page-level detection call, which is consistent.
- **Past single-run findings on full tractates** (twin-pass Kiddushin 88.9 → 90.0, one
  story) are inside the floor and should be read as indicated, not measured.

## How to compare runs from here

Lesson 22 applies without the 2026-09-09 exemption: **a same-code repeat per arm**, and
report a delta against the spread. The cheapest honest unit is two runs per arm on a full
tractate (~25 min each on Yevamot).
