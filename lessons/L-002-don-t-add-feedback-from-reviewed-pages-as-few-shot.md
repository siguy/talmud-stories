# Lesson 2 — Don't add feedback from reviewed pages as few-shot examples for those same pages

**2026-03-25**

**What happened:** We expanded the detector's few-shot example bank from 128 to 282 entries by adding Jeff's canonical review corrections. The new examples were mostly from pages 2-60. When we re-ran the detector, it massively over-rejected stories on pages 2-60 (72 → 52 stories) while pages 61-112 barely changed (110 → 109). Classic train/test contamination.

**Rule:** Few-shot examples must come from a different dataset than what you're evaluating on. If Jeff reviews Ketubot, use those examples when detecting stories in Bava Metzia, not when re-running on Ketubot.
