# Lesson 3 — The canonical review verdict format is different from prior rounds

**2026-03-25**

**What happened:** The canonical review uses `correct/incorrect/approve/adjust` verdicts on the *already-corrected* data, while prior rounds used `correct/incorrect/confirm_remove/reject_remove` on the *base* data. We initially planned to add it as a 4th entry in the timestamp-based feedback system, but realized this would cause the canonical review's "correct" (meaning "the correction was right") to override the prior round's "incorrect" (which triggered the correction), effectively undoing the correction.

**Rule:** When combining feedback from different review rounds, understand what each verdict means in context. A "correct" on corrected data is not the same as a "correct" on base data. We solved this by processing the canonical review as a separate post-processing step.
