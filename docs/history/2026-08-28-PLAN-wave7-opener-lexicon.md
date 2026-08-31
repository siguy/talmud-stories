# Wave 7 Plan — Story-opener lexicon coverage

**Status:** DRAFT — executable without Jeff. Scheduled, not floating.
**Why it exists:** Simon's 2026-08-28 instruction to make this a real scheduled wave
rather than a "tracked separately" note, and to include Jeff on it before the next
review round.

---

## Problem

The detector leans on a hardcoded list of story introducers (`הָהוּא`, `מַעֲשֶׂה בְּ`,
`תַּנְיָא`…) for Stage-1 triage override and Stage-2 start-snapping. Openers outside
that list are systematically invisible.

Measured evidence from the 2026-08-28 recall run against Jeff's 2005 Ketubot list:

| Miss | Opener | Shape |
|---|---|---|
| Ketubot 67b | `אמרו עליו על הלל הזקן` | "They said about him…" — attributed anecdote |
| Ketubot 82b | `בראשונה היו כותבין` | "Originally they would write…" — institutional/historical narrative |

Both are unmistakable stories (Hillel and the poor man; Shimon ben Shetach's ketubah
takanah). Neither opener is in the lexicon. 82b compounds with a triage skip.

## Why this is a separate wave

It is a **different axis** from Wave 6. Wave 6 changes *what counts as a story*;
Wave 7 changes *where we look for one*. Bundling them makes score movement
unattributable — the mistake Wave 4 correctly avoided.

It also carries a known hazard: the lexicon is exactly the kind of surface-pattern
rule Lesson 15 says cannot carry semantic weight. So the lexicon must stay a
**recall prior** (a reason to look harder) and never a **classifier** (a reason to
accept). Adding an opener may never, by itself, promote a passage to story.

## Approach

1. **Mine candidate openers**, don't invent them. Take the 149 stories in Jeff's 2005
   list plus the 278 golden stories, extract opening n-grams, and rank by
   story-frequency vs. corpus-frequency. Openers earn their place by evidence.
2. **Use them as a triage prior only** — a page containing a high-precision opener is
   never skipped by Stage 1. This directly patches the triage hole that cost us 20a,
   72b, and 82b.
3. **Measure precision before shipping each opener.** `בראשונה` is common in
   non-narrative contexts; if it fires on 200 pages to recover 1 story, that is a
   triage-cost decision, not a free win.

## Gates

| Gate | Threshold |
|---|---|
| Recall vs Jeff's 2005 list | recovers 67b; no regression elsewhere |
| Triage skip rate | report the change explicitly (currently 56% of Ketubot pages) |
| Both composites, regenerated today | no regression (Lessons 6, 11) |
| Per-opener precision | reported per opener; no opener ships unmeasured |

## For Jeff (next package, not a separate ask)

Include the mined opener list and ask whether any are wrong or any obvious ones are
missing. This is cheap for him — a scan, not a review round — and it is exactly the
kind of thing 20 years of reading gives him and the corpus does not.

## Cost

Mining is $0. Triage re-runs on affected pages ~$0.10–0.20 per tractate.
