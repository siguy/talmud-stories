# Yevamot under the new default: 94.1% → 93.1% (92.2% on a repeat)

**2026-09-27.** Status: **measured** (one full run, BLIND vs Jeff's 2005 list, exact matcher).
Item: [`yevamot-rerun-new-default`](../../work/done/2026-09-27-yevamot-rerun-new-default.md).
Run: `results/v11/twin_pass/yevamot_full_twin2.json` (twin pass on, `TWIN_TRIGGER=all`,
2026-09-25 wording, `gemini-3-flash-preview`, thinking off, 26 min).
Recall: `results/recall/yevamot_jeff2005_matches_twin2.json`. **Not promoted** — the shipped
artifact and the board's unsuffixed recall file are unchanged.

## Recall — Triage 102/102 in all three arms, so these are Detection

| arm | Detection recall |
|---|---|
| control, twin pass off (`yevamot_v11.json`) | 91/102 = 89.2% |
| twin pass, old wording (`yevamot_full_twinall.json`) | 96/102 = 94.1% |
| **twin pass, new wording — the shipped default** | **95/102 = 93.1%** |

The only story that changed is **`yevamot_050`, Yevamot 78a:13** (*כי אתא רב דימי אמר רבי
יוחנן*) — the one the 2026-09-25 re-ask predicted the new wording would drop, as *"a legal
ruling… followed by the Gemara's analytical inference"*. Whether it is a story under his
2026 rules is a question for Jeff; against his 2005 list it is a miss, and it stays one.

## Twin additions: 12 → 9, and the known-false ones mostly go

| addition | label | old | new |
|---|---|---|---|
| 34b:6, 63a:6, 121b:14 | his list | added | added |
| 105a:13 | Jeff **yes** | added | added |
| 78a:13 | his list (2005) | added | **dropped** |
| 15a:14, 17a:4 | Jeff **no** | added | **dropped** |
| 106b:9 | Jeff **no** | added | added — still |
| 78a:11 | Simon no | added | **dropped** |
| 43a:12, 45a:17 | Simon no | added | added — still |
| 101b:13 | Simon no | added | not asked (neighbour changed) |
| 101b:14, 15a:16 | unjudged | — | **new** |

Extras not on his list: **8 → 6**, of which 1 is his yes, 3 are known no, 2 are new and
unjudged (101b:14 — Rav Ashi at Rav Kahana's house for the ḥalitza quorum; 15a:16 — the
Yehu water trough incident).

## Something the twin pass cannot explain: page-level Stage 2 moved

Seven Stage 2 proposals differ between the two twin runs, none on his list: gone — 115a:7,
78a:17; new — 102a:13, 21b:15, **77a:0** (Doeg and David, the biblical episode R-S1 names,
now `HIGH_CONFIDENCE`); re-bounded by one segment — 121b 5-6 → 5-7, 79a 0-12 → 1-12.
The twin pass only adds after Stage 2, so these are either **run-to-run variation** or
**code that changed between 2026-09-14 and today** (the 2026-09-16 checkpoint/resume
commit touched Stage 2's flow). **Suspected, not measured** — telling them apart needs a
same-code repeat (Lesson 22). It does not touch the recall figure: the list-level diff is
exactly one story, and that one is a twin addition.

## Correction (2026-09-27, same day)

A same-code repeat scored **92.2%** and disagreed with this run on 3 of Jeff's stories.
The detector is not deterministic at full-tractate scale, so: the 94.1 → 93.1 difference
is **inside the noise**; the claim that the lost story *"is the one the re-ask predicted"*
is **retracted** (in the repeat, `yevamot_050` was found through a page-level proposal,
78a:17, that this run did not make); and the "page-level Stage 2 moved" section above is
**run-to-run variation**, not code drift. → [`detector-is-not-deterministic`](2026-09-27-detector-is-not-deterministic.md)
