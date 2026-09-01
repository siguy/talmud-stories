# The three pristine lists are parsed — and Eruvin has 74 stories, not 73

**2026-09-01.** Capability: Detection / ground truth. No API calls.
Item: [`parse-new-tractate-lists`](../../work/done/2026-09-01-parse-new-tractate-lists.md).
Follows [`2026-09-01-expert-list-daf-attribution.md`](2026-09-01-expert-list-daf-attribution.md).

## What was missing

Gittin, Yevamot and Eruvin are the only **pristine** ground truth this project holds: no
detector has ever run on those tractates, so nothing of ours can have been merged into
them (Lesson 29). `STATUS.md` recorded the half that was blocking everything:
`build_boundary_testset_2005.py` and `measure_recall_vs_expert_list.py` accept a list that
is not the Ketubot `.doc` **only** as pre-parsed JSON (`--expert-json`), and none existed.

## What the parse produced

| list | stories | blind | in recall denominator | references verified against the text |
|---|---|---|---|---|
| Gittin | **112** | 112 | 112 | 111 / 112 |
| Yevamot | **102** | 102 | 102 | 99 / 102 |
| Eruvin | **74** | 74 | 74 | 73 / 74 |

→ `results/expert_lists/{gittin,yevamot,eruvin}_2005.json`

All three are **wholly blind** — no `הוספתי` marker, no appendix, and not one English
review remark, unlike Kiddushin's list. That is asserted as a property (every entry's
`blind` and `counts_for_recall` flag), never inferred from the filename (FRAMEWORK §3).

## Eruvin had 74 all along

`73` was the line-based parser's count and it was wrong twice over. Eruvin's table stores
its columns **right-to-left**, so in `textutil`'s flattened stream each location cell
follows its story. Two consequences:

1. Every entry took the **previous row's** daf — 53 of 73 mis-attributed, the subject of
   the companion finding.
2. The document's **first story** precedes any location cell at all, so it was dropped
   silently: `מעשה באדם אחד מבקעת בית חורתן` (Eruvin 11a).

The parser now reads the column order off each document's own header row instead of
assuming it. Getting that wrong does not fail — it returns a healthy-looking list of the
right size, each entry on a real nearby daf.

## References: resolved where the document is ambiguous, reported where it is not

- A row whose location cell names **more than one daf** cannot say from the document alone
  which story sits where. Those are anchored against Sefaria (`ref_source: text_anchored`,
  coverage recorded) — which daf a passage occupies is an objective fact about the Talmud,
  not a judgement about what counts as a story, so the list stays as blind as it was. Three
  Gittin rows moved.
- A **single-label** reference is Jeff's own statement about where a passage belongs, so it
  is **never moved**. Where it disagrees with the text the entry is flagged
  (`ref_in_text_window: false`) and the disagreement is reported: 1 Gittin, 3 Yevamot,
  1 Eruvin, 1 Kiddushin. Those five are a question for him, not a defect to fix.

This also replaces the three hand-written Kiddushin `REF_OVERRIDES` with the measurement
they encode, and it **independently validates the existing Kiddushin ground truth**:
re-parsed with anchoring, **0 references move**, and 94 of its 95 agree with the text.

## The regression guard

Generalising the parser must not change what it thinks a story **is**:

- **Ketubot 149** and **Kiddushin 95** — unmoved, asserted per list.
- Kiddushin's recall denominator still **90**, strictly blind still **89**.
- `kiddushin_2005.json` gains two verification fields (`text_coverage`,
  `ref_in_text_window`) and **no ground-truth field changes**.
- Kiddushin recall reproduces at **93.3% / 95.6% / 97.7%**, every measurement field in
  `results/recall/kiddushin_jeff2005_matches.json` identical.

30 tests in `tests/test_new_tractate_expert_lists.py`; suite 180 → 210.

## What this unblocks

`build_boundary_testset_2005.py` can now build blind boundary sets for all three
(`load_units` already reads `results/sefaria/*.json`), and per-daf triage and detection
measurement has a denominator: **288 blind stories** across the three tractates, against
239 for Ketubot and Kiddushin combined. A detector run there is a clean floor test — the
first this project has had on a tractate it has never seen.

**Ask Jeff to keep his appendix separate before that run's results reach him** (Lesson 29).
These three lists are clean now; the window closes the moment we send him output.
