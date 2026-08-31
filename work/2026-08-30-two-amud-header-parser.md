---
title: Fix per-daf attribution for two-amud headers in the expert lists
capability: [detection]
tractate: [gittin, yevamot, eruvin, ketubot]
blocked_by: []
awaiting: []
writes: [scripts/parse_expert_doc.py, scripts/fetch_tractate_pages.py, results/expert_lists/]
finding:
superseded_by:
---

# Fix per-daf attribution for two-amud headers in the expert lists

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §3, then this.
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
