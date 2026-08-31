# Lesson 9 — Targeted tests on hand-picked examples don't predict production performance

**2026-03-25**

**What happened:** A boundary check that correctly found 2/3 cross-page stories on hand-picked boundaries found 28 false positives when run on all ~100 boundaries. The LLM is too generous about what counts as a story at page breaks — the same false positive problem as everywhere else. Tuning the triage filter either let everything through or blocked everything.

**Rule:** When testing a new detection approach, always run on the FULL dataset, not just known examples. A technique that works on 3 hand-picked cases tells you the concept is sound but says nothing about precision at scale. Budget the full evaluation into the test — don't iterate on filters in a trial-and-error loop.

---

## 2026-03-27: Kiddushin Run
