# Lesson 7 — Post-processing classifiers beat prompt modifications for precision improvements

**2026-03-25**

**What we found:** Research shows that adding a lightweight second-stage classifier (logistic regression or LightGBM) trained on false positive features is more effective than modifying prompts when you need to reduce false positives without hurting recall. The ACL 2024 "LlmCorr" paper demonstrates this pattern. A post-processing classifier can only affect passages the detector already found — it can never cause new false negatives. Prompt modifications affect everything and can cause cascading regressions.

**Rule:** When trying to improve precision (reduce false positives), don't modify the detection prompt. Build a separate filter that runs AFTER detection. It's safer, more interpretable, and generalizes better.
