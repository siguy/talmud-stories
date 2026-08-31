# Decision: pause the rewrite, fix the measurement first (2026-08-30)

**In one line:** we built a replacement before proving the thing it replaces was
actually broken — so we are going to test that first, for about 10 lines of changes
instead of the 433 already written.

Full technical findings: [`wave5b_review_2026-08-30.md`](2026-08-30-wave5b-review.md).
That file exists so this plan can be **revived and fixed** if the cheap path fails.

---

## The problem we are trying to solve

A story sits inside a paragraph of Talmud. It usually does not start at the first word
— there is an editorial lead-in first — and it usually ends before the paragraph does,
because the Talmud starts commenting on the story. Finding the right *paragraphs* is
solved. Trimming correctly *within* the first and last paragraph is not.

## What we built, and why we are not running it

The current approach asks the model one question: "which clause does the story start at,
and which does it end at?" It scores about 50% against boundaries Jeff has stated.

So we built a replacement: label every clause with a role, then compute the boundary
from the labels. Three independent reviews said **the idea is right but do not run it
yet**, for three reasons.

### 1. The ruler is broken

We planned to grade the new approach against 52 examples of Jeff's boundary decisions.
But only ~16 can be checked at all (29 of the rest are Ketubot, which was never run),
two of them **contradict each other**, and three are duplicates. A perfect run scores
50/52 and nothing says so. Effective sample: about 14. "Beat 50%" would mean getting 8
right instead of 7 — one case.

### 2. We never gave the current approach a fair test

The current prompt receives a one-sentence summary of the story to help it judge where
the story ends. There is a bug: the field it reads is empty on **all 95 stories**, so it
falls back to a joined list of events — **which drops the story's ending**.

We have been asking "where does this story end?" while handing over a description with
the ending removed. And **35 of the 52 test targets are end-boundaries**. The handicap
points exactly at the thing being measured.

That is a one-line fix. The current approach may not be bad; it may just have been
running with a weight on it that we attached.

### 3. Our new code lies when it breaks

If the model call fails, the new runner records `clause_kept_full` — the same value that
means *"the model read this and judged the whole paragraph to be story."* A completely
failed run is indistinguishable from a successful one, and scores 6%/38%, identical to
the legitimate no-trim baseline. It also writes a fabricated speech profile into the
dataset meant to answer Jeff's question.

This is the same shape as a failure this project already paid for once (v10's silent
regex fallback). It is now [Lesson 21](../../lessons/README.md).

## What we are doing instead

| # | Step | Cost |
|---|---|---|
| 1 | Fix the lying-when-broken bug + write the failure test that keeps it fixed | small, no API |
| 2 | Fix the one-line summary bug | 1 line |
| 3 | Run the **current** approach on Ketubot (both inputs already on disk) | 2 commands, pennies |
| 4 | Re-grade — sample goes from ~14 to ~45 | free |
| 5 | Human hour: resolve the 2 contradictory targets, verify the anchors | 1 hour |

**Then decide.** If a properly-fed current approach still gets ~50%, the rewrite has
earned its place — and now against a baseline we can trust. If it jumps to 70%, we
nearly rewrote 400 lines to fix a one-line bug.

## If the cheap path does not work

Revive Wave 5b using [`wave5b_review_2026-08-30.md`](2026-08-30-wave5b-review.md), which
holds every finding as a fix list: the P0 correctness bugs, the scope cuts (3 roles
instead of 8, Hebrew only, one assembly rule), the 22 tests to write, and two claims in
the original plan that turned out to be **wrong** — most importantly that "English
sentences nest over Hebrew clauses," which is false on 21% of segments and which the
cross-language check depended on.

And change **one thing at a time**. As designed, Wave 5b altered the taxonomy, added an
English channel and added an assembly-rule choice at once, judged on ~14 cases — so no
result would have been attributable to any cause.

## Why this is written down

Three reviews' worth of findings were produced in one session. Without this record they
would be gone at the next context clear, and the same 433 lines would be run with the
same defects. That is Lesson 17, applied to a code review rather than to expert feedback.
