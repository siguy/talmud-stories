# Lesson 23 — An exam built only from corrections cannot see a regression

**2026-08-30**

The boundary test set was built entirely from Jeff's correction notes, so
every question was a case where the plain boundary was already wrong.
That makes trimming look free: on Ketubot 61-112 the corrections ruler
scored no-trim at 33% and Wave 5 at 67% — a doubling. Scored against
Jeff's detector-blind 2005 list instead, the plain boundary was
**already 79% right** and Wave 5 moved hit+near from 85% to 84%.

Same runs, same day. One ruler says "doubled it", the other says
"roughly flat, possibly slightly worse".

The builder's own header warned about this ("measures fixing known
failures, NOT avoiding new ones") and we quoted the numbers anyway,
because it was the only ruler we had.

**Rule:** any evaluation set assembled from an expert's *corrections* is
a fixed-the-known-failures metric and nothing else. Before quoting it as
progress, obtain a NEUTRAL sample — data the expert produced without
seeing your output — and report both. If no neutral sample exists,
getting one is the highest-value work available, ahead of any tuning.

**Why:** a corrections-only set has a direction baked in. Every question
asks "did you move this boundary?", never "did you leave the right one
alone?", so the metric rewards the more aggressive change every time. We
nearly tuned further on a number that was measuring our own selection.

**How to apply:** (a) Jeff's 2005 list had been on disk since
2026-08-28, used only for a recall count; the boundary information was
sitting in the same column. Re-read raw expert material for uses beyond
the one it was fetched for. (b) Report corrections and neutral scores
side by side, never pooled into one headline. (c) A bigger ruler also
fixes Lesson 22: the noise floor went from 7 points on 15 targets to
0 on 168.
