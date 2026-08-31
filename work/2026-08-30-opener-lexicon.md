---
title: Mine the story-opener lexicon instead of hand-writing it (was Wave 7)
capability: [triage, detection]
tractate: [ketubot]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, src/prompts/]
finding:
superseded_by:
---

# Mine the story-opener lexicon instead of hand-writing it (was Wave 7)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.1–1.2, then this. Full draft:
[`docs/history/2026-08-28-PLAN-wave7-opener-lexicon.md`](../docs/history/2026-08-28-PLAN-wave7-opener-lexicon.md).

## The problem

Triage and start-snapping lean on **five hand-written Hebrew introducers**
(`_STORY_INTRODUCERS`, `src/story_detector_v11.py:2002`). They were invented, not derived,
and openers outside the list are systematically invisible. Two measured misses against
Jeff's blind 2005 Ketubot list:

| miss | opener | shape |
|---|---|---|
| Ketubot 67b | `אמרו עליו על הלל הזקן` | "They said about him…" |
| Ketubot 82b | `בראשונה היו כותבין` | institutional / historical narrative |

Both are unmistakable stories. 82b compounds with a triage skip.

## Method

1. **Mine, don't invent.** Extract opening n-grams from the 149 blind stories plus the
   golden, rank by story-frequency against corpus-frequency.
2. **Use as a triage prior only, never as a classifier** — adding an opener may never by
   itself promote a passage to story (Lesson 15).
3. **Measure per-opener precision before shipping each one.** `בראשונה` is common in
   non-narrative contexts; firing on 200 pages to recover 1 story is a cost decision, not
   a free win. **No opener ships unmeasured.**

## Gates

Recovers 67b with no regression elsewhere · triage skip-rate change reported explicitly
(currently 56% of Ketubot pages) · both composites regenerated same-day (Lessons 6, 11).

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.
