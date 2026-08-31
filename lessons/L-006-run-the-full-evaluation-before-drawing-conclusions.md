# Lesson 6 — Run the full evaluation before drawing conclusions

**2026-03-25**

**What happened:** The first experiment evaluation only covered pages 2-60. The composite score was 0.44, which looked catastrophic. But much of that was because the evaluator penalizes for every golden story not in the detected results — and all 61-112 stories were "missing" since we hadn't run that range yet.

**Rule:** Always run the full evaluation pipeline before interpreting results. Partial evaluations are misleading when the scoring function considers all pages.
