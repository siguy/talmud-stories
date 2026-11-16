# Full boundary review of the Septimus site (2026-11-16)

Plan: `docs/history/2026-11-15-PLAN-full-boundary-review.md`. Work item: `work/done/2026-11-15-full-boundary-review.md`.
Display only: `site/data/boundary_extensions.json` and the `merge` list. No golden, run, story id or
`evaluate_golden.py` touched; the composite score was not used. Every number here is **measured** from the files
under `results/site_notes/boundaries/` unless marked otherwise.

## What was done

Every site story was reviewed for where it starts and ends (trim the legal argument, finish a cut-off story, merge a
story split across two cards), or skipped by name:

| | stories |
|---|---|
| on the site before | 1,792 |
| decided earlier by `bfix1`, not re-reviewed (Decision 3) | 144 |
| merged cards, skipped by name (no display change is possible on them) | 3 |
| calibration, CIRCULAR set: Ketubot (`bcal1`) 83, Kiddushin + Gittin (`bcal2`) 149 | 232 |
| calibration, BLIND set: Yevamot (`bcal2`) | 76 |
| main run, 33 tractates (`bfull1`) | 1,337 |

Reviewers: Claude Code subagents (Opus), 20 stories per batch, 85 batches in all. 0 invalid answers in the end; 11
answers with invented story codes (written by agents cut off by a usage limit before they had read those files) were
rejected by the code check and their batches re-run.

## Calibration (against Jeff's 2005 lists; reviewer never saw them)

Gate fixed before the run (Decision 4) and passed on a frozen prompt:

| | measurable | narrative lost | starts kept | left alone (C) |
|---|---|---|---|---|
| Ketubot | 73 | 0 | 73 | 62 / 63 |
| Kiddushin | 41 | 0 | 41 | 39 / 39 |
| Gittin | 76 | 0 | 76 | 63 / 63 |
| Yevamot (BLIND) | 54 | 0 | 54 | 43 / 43 |

- **Narrative lost** = starts cut + cut ends sorted `lost`. 6 ends were cut earlier than Jeff's; a different model
  (Sonnet) sorted all 6 as `fine` (Gemara discussion; R-B2: his 2005 end is an upper bound) against
  `results/site_notes/boundaries/CUT_END_RULE.md`, written before any result was read. No `lost` and no `ruling` cases.
- **E:** no merge of two of Jeff's stories; one extension past his end (Kiddushin 12a, +1 segment: the Sages' reply
  to Rav Hisda in the same incident, not legal argument).
- **D (benefit):** few of the "extra" segments relative to Jeff were removed (Ketubot 3 of 23). Read case by case,
  most extras are not argument: Rava's settling answer (an outcome ruling, Decision 2), or one card where Jeff split
  a passage into two stories. Indicated, not measured: the calibration tractates were already curated, so this set
  tests "leave good boundaries alone" far more than "fix bad ones" (the plan said so).
- The Yevamot target file was built for this (`tests/expert_boundary_targets_2005_yevamot.json`, 102/102 aligned;
  every target's segment exists in the site's run with matching Hebrew).

## Main run

`bfull1`: 1,243 keep, 87 adjust, 7 merge proposals (1 agreed from both sides; 5 refused as disagreements, then upheld
by the second reader; 1 was the other half of an agreed pair). 15 cards answered "TWO STORIES" (plus 6 in
calibration): two incidents in one card that moving the ends cannot separate. They stay as they are (a split is not
possible today).

## Second reader (Sonnet, independent, before and after only)

Every change was read (there were fewer than the planned random 100 ordinary adjusts), plus 40 random keeps:
153 read, 0 invalid.

- Random adjusts: 3 of 54 disagreed = **5.6%** (gate: up to 10% applies everything but the disagreed).
- Trims removing half or more of a story: 4 of 33 disagreed. All 6 merges agreed, including 5 disputed ones.
- Deletes (back to the detector's span, undoing an older display extension): 2 of 7 disagreed. Both would have cut
  the story's ending (Gittin 5b, Yevamot 102a). Deletes were added to the always-read set during this run; without
  that they would have been applied.
- Random keeps: 1 of 40 judged not a whole story (Shabbat 147b:4; left for a later look).
- **Held, 9:** `avodah_zarah-2b-1-15`, `avodah_zarah-56b-4-4`, `avodah_zarah-68b-10-11`, `bava_batra-125a-5-5`,
  `bava_kamma-20b-1-1`, `niddah-60b-7-9`, `pesachim-112b-16-16`, `gittin-5b-21-21`, `yevamot-102a-7-8`.

Simon read 20 before/after pairs (`results/site_notes/boundaries/bfull1/sample.html`) and approved the apply.

## Applied

110 stories changed: 18 in calibration tractates, 92 in the main run (80 trims/extensions + 6 merges, both cards).
Site: 1,786 stories (6 merged away), 0 segments shown in two cards, every extension applied. One change undone by
hand afterwards: `taanit-23b-9-9` had been widened over Taanit 23b:8, which a `remove` decision took off the site on
2026-11-14 ("drop 8-8, do not widen 9-9"). The site test for removals caught it; `plan()` now refuses any widening
onto a removed passage, by name, with a test.

Notes: 104 changed stories still on the site were redrafted (`results/site_notes/bfull1notes/`), 0 invalid; 102
approved (Decision 6), 2 held on drafter flags. Six merged cards got written summaries.

Pinned word counts (`SITE_WORDS`): Ketubot +183, Kiddushin +37, Gittin −495, Yevamot −1,096, Berakhot +92.

## What the script now does (`scripts/review_site_boundaries.py`)

`export` takes every site story or a narrowed set (`--ids-file`, `--only`, `--flags [FILE]` for a {id: concern}
list such as reader feedback), skips `--after` runs and merged cards by name, and builds each file from the source
span with a "start no earlier than / end no later than" line. `apply` refuses by name: an adjust on a merged card, a
merge onto a trimmed card or one the other card disputed (unless the second reader upheld it), a third card joining a
merge, any segment shown in two cards (against every card in the tractate), and any widening onto a removed
passage. It writes `applied.json` once, and marks each changed story's note for redraft. `calibrate`,
`second-export` / `second-import` and `sample-html` are new. Tests: `tests/test_review_site_boundaries.py` (19), plus
two site tests (no segment in two cards; every changed story has a note drafted after the change).

## Caveats

- **Undoing a merge is not clean** (story ids never revive). Trims and extensions undo from `applied.json`.
- The BLIND check is one tractate (Yevamot). The 32 other main-run tractates have no expert list. The second reader
  is the only check there.
- The second reader is a model, and it has not been checked against Jeff.
- **Legal argument is still on the site in many stories.** The change rate was low (8%), and the reviewer was told to
  prefer the smallest change and to keep a segment that mixes story and argument (segments cannot be cut in the
  middle). The second reader judged argument still shown in **12 of 40 random keeps (30%)** and in 44 of the 87
  changes it read. That is the second reader's view, not checked against Jeff: indicated, not measured. Some of it sits
  inside segments that cannot be split; how much could be trimmed at segment level is the open question for a
  follow-up.
