# Audit the bucket your conservative rule files things into

<!-- Unnumbered on purpose: lessons/README.md says to land a new lesson as
     `_<slug>.md` and number it when it reaches main, so two sessions cannot
     claim the same number. Four did on 2026-08-30; this one collided with a
     concurrent L-031 on 2026-08-31. -->

**2026-08-31**

`build_ruler.py` sorts each rejection by keyword and files anything unclear as
`unclassified` rather than guessing. That is the right design, and
[Lesson 30](L-030-incorrect-is-not-a-metric-until-you-know-what-was.md) is why.

The bucket was then never opened. It set the width of every Classification
range we quoted for months, and it was described in three places as holding
**24 notes**. Reading it took under an hour:

```
population   34, not 24  — the tally covered 4 of the 7 rounds the ruler scores
readable     27 of 34    — by a person, from the note text alone
residue       7          — every one an empty note. Nothing was hard; some were blank.
```

Not one miss was a judgment call. `legal debate` did not match
`legal (discussion|tradition)`. *"crossed out"* and *"trimmed"* are the review
UI's own words for a boundary and appeared in no rule. Twelve notes disagreed
by *affirming* — *"Yes, this is a story"* — and every rule was written to look
for a complaint. One note said *"legal dicussion"*.

Two things were hiding in there that no amount of re-reading the summary would
have found: a verdict spent on **our renderer** rather than on the data, and
four cases of the reviewer **overturning a rejection** — the opposite error,
pooled with false positives.

**Rule:** a conservative fallback bucket is a promise to come back, not a
resolution. Whenever a number's width is set by an "unknown" pile, put reading
that pile on the board as work, and **count the pile from the artifact, not from
the last document that mentioned it** — three files said 24 because each copied
the one before. If the pile is too large to read, say what sampling you did.
Until someone has read it, "conservative" and "unmeasured" are the same state.

**Corollary:** a taxonomy built from one dataset will not have a category for
the failure modes of the next one. Ours had no bucket for *the UI is broken*,
so a display defect was scored as a detector error — the same shape as
[Lesson 25](L-025-a-display-bug-can-manufacture-expert-feedback.md).

→ [`docs/findings/2026-08-31-objection-axis-hand-sort.md`](../docs/findings/2026-08-31-objection-axis-hand-sort.md)
→ [`results/rulers/objection_axes.json`](../results/rulers/objection_axes.json)
