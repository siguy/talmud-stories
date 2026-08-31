# Lesson 14 — When the detector overtakes the golden, FPs are a recall win in disguise

**2026-05-25**

**Context:** Wave 3 added iterative Stage 2 + embedded-story few-shots.
On Ketubot this recovered 7 stories the golden had as FNs (recall
+0.044). On Kiddushin the same changes surfaced 7 NEW story candidates
v8 had not detected — 5 of which scored as false positives because the
Kiddushin golden was built from v8 output + Jeff's prior reviews.
Inspecting the 7 by hand: most are real rabbinic narratives, and one is
the EXACT story Jeff flagged as missed in his 2026-04-23 review
(Kiddushin 33a seg 5, Rabbi Hiyya in bathhouse). The gate read this as
a regression (-0.0103 composite).

**Rule:** When a detector improvement causes the FP count to rise but
the new "FPs" overlap previously-flagged-as-missed cases or look like
real stories under inspection, that's the detector overtaking the
golden — not a quality regression. Treat as Lesson 13 (ship + flag).

**Why:** A golden built from an older detector's output records that
detector's coverage as the ceiling. A better detector finds more, and
the metric punishes it. Re-disabling the improvement to chase
agreement with a stale frozen target loses real quality without
gaining anything.

**How to apply:** Before bisecting prompt changes to "fix" an FP
regression, dump the new-only detections and check by hand against the
expert's prior missed-stories list. If ≥1 new FP corresponds to a
known missed case, the gate result is misleading — ship, flag the new
detections for the next review pass, and expect the golden to update.
