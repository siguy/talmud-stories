# Lesson 8 — Abstract patterns generalize; specific examples memorize

**2026-03-25**

**What we found:** Research on "Synthetic Prompting" (Wan et al., 2023) shows that abstract pattern descriptions outperform specific examples in few-shot prompts. Our error taxonomy already has the abstract patterns ("dialogue is not events," "narrative settings don't make stories"). The mistake was adding those patterns alongside the specific passages. The specific passages caused memorization; the abstract patterns alone would have been safer.

**Rule:** When converting expert feedback into prompt guidance, use the expert's reasoning patterns, not their specific examples. "A passage where all activity is verbal acts is NOT a story" > "Ketubot 7a_1-1 is NOT a story."
