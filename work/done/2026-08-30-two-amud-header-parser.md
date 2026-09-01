---
title: Fix per-daf attribution for two-amud headers in the expert lists
capability: [detection]
tractate: [gittin, yevamot, eruvin, ketubot]
blocked_by: []
awaiting: []
writes: [scripts/parse_expert_doc.py, scripts/fetch_tractate_pages.py, results/expert_lists/]
finding: docs/findings/2026-09-01-expert-list-daf-attribution.md
superseded_by:
---

# Fix per-daf attribution for two-amud headers in the expert lists

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) §3, then this.
**No API calls. Small.** It blocks all three new-tractate `detection` items.

## The defect, measured

`parse_expert_doc` matches only **single-amud** headers, so every story sitting under a
two-amud header (`סה ע"ב-סו ע"א`) is silently credited to the **preceding daf**:

| tractate | stories mis-attributed |
|---|---|
| Gittin | 11 |
| Yevamot | 7 |
| Eruvin | 3 |
| Ketubot | 15 such headers in the document |

`python3 scripts/fetch_tractate_pages.py --verify-only` lists all 21.

One Gittin header (`יד ע"ד`) uses amud **dalet** — a Yerushalmi form with no Bavli
equivalent. Decide what it means rather than dropping it silently.

## Why it blocks the campaigns and not the existing numbers

**Ketubot's 96% recall is unaffected** and does not need re-running: `locate()` matches by
Hebrew character 4-gram across the whole corpus and never reads the parsed reference
(`abdc4af`). What is unreliable is the per-story `ref` **label** — so any **per-daf**
analysis is wrong until this is fixed, and per-daf is exactly what a new tractate's triage
and detection measurement is.

## Method

1. Extend the header pattern to ranges, and decide the rule: a story under `סה ע"ב-סו ע"א`
   belongs to the daf its **text** starts on, resolved by anchoring against Sefaria — the
   same `ref_source: text_anchored` treatment the Kiddushin parse used for its ambiguous
   row.
2. Re-run `--verify-only` and assert 0 mis-attributions.
3. Re-parse the three lists; assert the **entry counts do not move** (112 / 102 / 73).
   A count change means the fix altered what counts as a story, which it must not.

## How you know it worked

21 mis-attributions become 0, entry counts unchanged, and Ketubot's blind recall
reproduces exactly as before.

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.

## Outcome

**DONE 2026-09-01.** Fixed, and the filed defect turned out to be the smaller half of it.

Two-amud headers are now read, and a story under one is anchored to the daf its own text
starts on (`ref_source: text_anchored`), which is an objective fact about where the passage
sits rather than a judgement about what counts as a story — the list stays blind. A story
anchored *outside* its own header's span is flagged rather than silently corrected.

**The larger defect was next to it.** Anchoring every entry, not just the span ones, showed
Eruvin's list is mis-attributed in **53 of 73** entries: its table stores the columns
right-to-left, so `textutil`'s flattened stream puts each location cell *after* its story
and every entry inherited the **previous row's** daf. Gittin is 5 of 112 and Yevamot 4 of
102 by comparison. A reversed-column list is now **refused by name**, pointing at
`parse_kiddushin_list.py` — the parse it produced returned the right number of stories,
each on a real nearby daf, so nothing downstream would ever have looked wrong (Lessons 28,
38). **Eruvin detection was queued behind this item and would have been measured per daf
against a list that was 71% wrong.**

Regression guard held exactly: Ketubot recall reproduces at **96.0 / 98.0 / 97.9**, every
measurement field in the recall artifact identical, entry counts unmoved (149 / 112 / 102),
and **11 `ref` labels corrected** — the largest by 21 dapim. Only per-daf analysis was ever
affected: `locate()` never reads `ref`, which is why a corpus-wide number could not see it.

`SPAN_HEADER` had two definitions — one in the parser that could not use it, one in the
report that named the defect; now one. Suite 170 -> 180.

**Does not unblock Eruvin.** It correctly blocks it, which nothing did before.
