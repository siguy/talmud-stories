# Lesson 10 — Narrow questions beat open-ended detection for precision

**2026-03-27**

**What happened:** We tried two approaches for catching cross-page stories the merge passes missed. The first (sliding-window boundary check) asked "is there a story at this page boundary?" — an open-ended detection question. It found 28 false positives across ~100 boundaries because the LLM is too generous about what counts as a story. The second (Stage 4f continuation check) asked "does THIS specific detected story continue on the next page?" — a yes/no question about a known story. It caught 3 genuine cross-page stories with 0 false positives on Kiddushin.

**Rule:** When you need to extend an existing detection (not find new things), frame the question as narrowly as possible. Give the LLM the specific thing to check against, not an open search. "Does story X continue?" is fundamentally different from "Find any story at this boundary" — the first constrains the answer space, the second invites false positives.

---

*Add new lessons below this line. Date each entry.*
