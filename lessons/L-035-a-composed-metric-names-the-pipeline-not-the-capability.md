# Lesson 35 — A composed metric names the pipeline, not the capability

**2026-08-31**

Kiddushin's Detection recall was 93.3% against Ketubot's 96.0%, and the scoreboard
recorded it as *"the first like-for-like comparison of the two tractates"* — Kiddushin
below the 95% gate, Ketubot above. `docs/capabilities/2_detection.md` carried it as the
capability's current value.

Both numbers count stories found over stories on the expert's list. Neither is a Detection
number. A story is missing from that count if Detection failed **or** if Triage discarded
the page before Stage 2 ever saw it. Splitting the two:

```
                      Ketubot   Kiddushin
  Triage recall         98.0%      95.6%
  Detection | survived  97.9%      97.7%    <- one story apart
  end-to-end            96.0%      93.3%
```

**Detection is the same on both tractates.** The entire 2.7-point gap is Triage, which
Kiddushin skips 62% of the tractate to buy against Ketubot's 56%. We had spent a session
reading a Triage result as a Detection weakness, on the only two tractates we can measure
at all — and the fix that reading implies (a smarter Stage 2 prompt) could not have moved
it, because the pages were never examined.

FRAMEWORK §2b already said `triage × detection = end-to-end`. The formula was in the file;
the number quoted next to it was the product, labelled as one of the factors.

**Rule:** when capabilities compose, a metric measured at the end of the chain belongs to
the chain. Before quoting it against a single capability's gate, ask which stages could
have produced each failure, and condition on the ones upstream. Charging an upstream
loss to a downstream capability double-counts it — the upstream stage has its own gate.

**Why:** this is the same shape as Lesson 30, one level up. There the pooling was across
*reasons for a rejection*; here it is across *stages of a pipeline*. Both produce a number
that moves when a capability you are not measuring changes, and both send the fix to the
wrong place. And both were quoted for months, because a pooled number is not wrong in any
way that shows — it is a real measurement of a real thing, just not the thing named beside
it.

**How to apply:** (a) State the conditioning in the metric's own name: *"recall given the
page survived triage"*, not *"detection recall"*. (b) Report the composed figure too — it
is what the product ships — but as a separate row, never as the capability's value.
(c) When two tractates or two versions differ on a composed metric, split it before
explaining the difference; the explanation is usually in a different column than the one
you were looking at. (d) The split is cheap: `measure_recall_vs_expert_list.py` already
reads the per-page `skipped_by_triage` flag it needed all along.
