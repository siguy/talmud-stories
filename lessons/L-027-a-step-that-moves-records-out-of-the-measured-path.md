# Lesson 27 — A step that moves records out of the measured path is invisible by construction

**2026-08-30**

*Two sessions found this independently on the same day, from different ends — one
measuring what the filter cost, one fixing the tagger that fed it. They were written up
as separate lessons and are fused here, because they are one failure.*

`filter_mishnah_only_stories()` (Wave 1, v8) does not delete stories. It moves any story
lying entirely inside a Mishnah block out of `stories` and into `mishnah_stories`. Its
docstring says such stories "should be tallied separately."

Nothing tallies them. Neither `scripts/evaluate_golden.py` nor
`scripts/measure_recall_vs_expert_list.py` reads that key, and neither does the review UI
generator. So a story the detector **found and we deliberately dropped** scored exactly
like a story it **never found** — a false negative in the golden, a miss in recall, with
no trace in either.

Measured over `results/v10/wave4_notrim/`: the filter accounts for **4 of Ketubot's 15
golden false negatives — 27%**. Folding all four back moves golden recall 0.9085 → 0.9329.
None of the four is a detection failure. They are our own deletion, mis-filed as the
model's error since v8.

**Two of the four were not Mishnah at all** — plain Gemara mis-tagged at a chapter
boundary, where Sefaria opens a new chapter's first Mishnah with the chapter incipit
instead of `מתני׳`. Fixing the tagger alone returns those two: Ketubot TP 149 → 151,
FN 15 → 13, golden recall 90.9% → 92.1%.

The number that matters:

```
                          before fix    after fix
  blind recall (Jeff 2005)   96.0%        96.0%     <- identical, same 6 misses
  golden recall              90.9%        92.1%
```

The metric this project trusts most — the detector-blind one, the one that exists
*specifically* to catch what we never found — was unchanged by two stories being deleted
and restored. It could not have caught this. Neither could any amount of care in the
tagger, because the tagger's output isn't in the measured population.
**A silent-deletion path scores better the more it deletes.** That is the whole failure;
the tagger bug was only how it got exercised.

The mis-attribution then cost real work. Brief `tasks/NEXT/02` was opened to find out why
Ketubot 77a "is never proposed." Seg 8 is proposed in **8 of 8** runs at HIGH_CONFIDENCE
with an exact segment match to the golden. The filter removes it after the model gets it
right.

There is a second half, about where the rule came from. The filter's premise was Jeff's —
Kiddushin 50b, *"This story is in the Mishnah, so it should be catalogued with Mishnah
stories, not Talmud stories."* We turned **"catalogue separately"** into **"delete"**, and
shipped it corpus-wide without checking the generalised rule against the rest of his
labels. Had we checked, we would have found he marked **all four** affected Ketubot
stories `correct` in review.

**Rule:** any step that removes, moves, filters, reroutes or defers detector output must
(a) be visible to every harness that scores that output — write into a key a harness
already reads, or ship a test that pins its decisions on real data; and (b) be measured
against the full label set before it ships, not just against the examples that prompted
it. When adding one, ask: **which harness goes red if this step goes haywire?** If the
answer is "none", that is the defect — before any bug in the step's own logic.

**Why:** an invisible deletion is worse than a wrong one. A wrong deletion shows up as a
score drop somebody investigates. An invisible deletion shows up as a *model* failure, so
the investigation is aimed at the prompt, the model, or the few-shots — anywhere but the
twenty lines of Python that actually did it. Ours survived from v8 to v11 and sent a brief
hunting a Detection bug that did not exist.

Same family as Lesson 21 (a failed call recorded as a judgment) and Lesson 23 (an exam
that cannot see a regression): all three are cases where the measurement, not the code,
was the thing that was wrong.

**How to apply:**
(a) **Prefer a tag over a move.** `story['filtered_as_mishnah'] = True` left in place is
inert to code that does not know about it; moving it to another key is a deletion to every
reader that does not know about it. If you must move it, land the harness change in the
same commit.
(b) **When the harness is immutable** (`evaluate_golden.py`), do not edit it and do not
work around it — score twice and report the delta. See
`scripts/report_mishnah_filter_delta.py`, which imports the harness read-only and folds
the withheld stories back for the second scoring.
(c) **Do not silently fold it into the headline number either.** "Found then dropped" and
"never found" are different facts; report the second number beside the first rather than
merging them. `measure_recall_vs_expert_list.py` leaves recall at 96.0% and prints what
was withheld separately.
(d) **Generalising an expert's correction is itself a change that needs measuring** —
Lesson 18 applies at implementation time, not just at diagnosis time. Before shipping the
rule, count how many of their *other* labels it touches. One correction is evidence about
one passage.
