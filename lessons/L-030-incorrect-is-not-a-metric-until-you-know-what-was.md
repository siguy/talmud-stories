# Lesson 30 — "Incorrect" is not a metric until you know what was rejected

**2026-08-30**

Classification precision was 86% on Ketubot and 68% on Kiddushin, and the
scoreboard called Classification our weakest capability on that basis.
Both numbers came from counting `verdict: incorrect` in the review rounds.

But a reviewer clicking "incorrect" is not saying *this is not a story*.
Sorting the notes by what Jeff actually objected to:

```
Ketubot  2026-03-17 (n=173)  classification 9 · boundary 7 · confidence 4 · merge 1
Kiddushin 2026-04-23 (n=89)  confidence 10 · classification 7 · boundary 3 · unreadable 9
Kiddushin 2026-07-06 (n=15)  boundary 5 · unreadable 6
```

Most rejections are boundary complaints, merge complaints, or disagreement
about our *confidence level* — three other capabilities, pooled into one
number and reported as Classification. Separated, both tractates sit near
92-95% and the 86-vs-68 gap mostly evaporates.

The `adjust` verdict makes it sharpest: it means "this IS a story, the
boundary is wrong." Counting it against Classification converts a
boundary failure into a fake precision problem.

**Rule:** a verdict vocabulary that records *that* the expert disagreed but
not *what with* cannot measure any single capability. Before quoting a
precision number, sort the rejections by which capability they indict. If
that cannot be done from the data, the number is an all-causes error rate
— say so, and report it as a range whose width is the part you could not
read.

**Why:** we spent months treating Classification as the weakest capability
and Kiddushin as far worse than Ketubot. Both conclusions were mostly an
artifact of pooling. Worse, the pooled number is the one that would have
been "improved" by tuning the classifier — which would have done nothing,
because the errors were largely in the boundary code.

**How to apply:** (a) Fix it at the source: the review UI should make the
reviewer say which thing is wrong. Re-deriving intent from free text has a
ceiling — 24 notes here were unreadable, and that is the width of the
range. This is now the point of `NEXT/04`. (b) Report per round, never
pooled across rounds: each round judged a different detector version, and
pooling lets whichever round has the most verdicts set the headline
(Lesson 24). (c) When a metric is a range, quote both ends. A point
estimate you cannot defend is worse than an honest interval.
