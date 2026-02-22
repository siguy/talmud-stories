# Email to Jeff: v8 Delta Review

**Subject:** v8 Story Detection — Focused Review of Cross-Page Fixes (only 18 stories need close review)

---

Hi Jeff,

Based on your review of pages 61-112 (96.3% accuracy — thank you!), I built v8 to fix the main issue you flagged: **stories cut off at page boundaries**.

**What changed:** The pipeline now detects when stories continue across pages and merges them. 16 stories now span two Talmud pages (up from 7). The total story count dropped from 113 to 103 because page-2 fragments got absorbed into their parent stories.

**Instead of re-reviewing all 103 stories, I built a focused delta review that shows only what changed.** This saves you from re-reading the 69 stories that are identical to v7.

## Your Review Link

**Delta Review (recommended — only changes):**
https://siguy.github.io/talmud-stories/validation/ui/ketubot_61-112_v8_delta.html

**Full v8 Review (all 103 stories, if you want it):**
https://siguy.github.io/talmud-stories/validation/ui/ketubot_61-112.html

## How the Delta Review Works

Stories are organized into 3 tiers:

**Tier 1 — Cross-Page Merges (8 stories)**
Stories that now span two pages. In v7 they were cut off at the page boundary. Please verify the merged version covers the full narrative. Text from *both* pages is shown with a divider.

**Tier 2 — New, Status-Changed, or Removed (10 stories)**
- 5 newly detected stories
- 1 status flip (NOT_A_STORY became a real story)
- 4 truly removed stories — please confirm removal is correct

**Tier 3 — Absorbed + Reclassified (31 stories)**
- 11 stories that were on page 2 of a cross-page story and got absorbed into the merge (quick confirm the merge is right)
- 20 classification changes (e.g. YES to HIGH_CONFIDENCE) — quick glance

**Skipped:** 69 unchanged stories (not shown)

## What I'm Looking For

1. **Tier 1:** Do the merged cross-page stories now capture the full narrative? Or did any merge go too far / not far enough?

2. **Tier 2:** Are the 5 new stories correct? Are the 4 removals correct?

3. **Tier 3:** Quick scan — do the absorbed stories make sense as part of their parent?

## Time Estimate

- Tier 1 + 2 (18 stories): ~20-30 minutes
- Tier 3 (31 stories, quick scan): ~15 minutes
- Total: ~35-45 minutes
- Auto-saves progress — you can do it in multiple sessions

## How to Give Feedback

Same as before — use the Correct/Incorrect buttons on each story card, add notes if needed, then click "Download Feedback JSON" at the bottom when done. The feedback is stored separately from your v7 review (won't overwrite anything).

Thanks,
Simon
