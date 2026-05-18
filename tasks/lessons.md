# Lessons Learned

Ongoing log of mistakes, surprises, and things worth remembering across sessions.

---

## 2026-03-25: Golden Dataset + Detector Experiments

### Lesson 1: Never split feedback processing into "auto" and "defer" without scheduling the "defer" pile

**What happened:** Across three prior feedback rounds, we categorized Jeff's corrections as "auto-apply" (classification changes) and "needs review" (boundary/merge changes). We applied the auto ones immediately but never came back to the needs-review pile. Jeff noticed — 10 of his 53 corrections in the canonical review were things he'd already told us to fix.

**Rule:** When splitting work into "now" and "later" buckets, the "later" bucket must go into a task list with a specific due date. If there's no mechanism to return to deferred work, it doesn't get done.

### Lesson 2: Don't add feedback from reviewed pages as few-shot examples for those same pages

**What happened:** We expanded the detector's few-shot example bank from 128 to 282 entries by adding Jeff's canonical review corrections. The new examples were mostly from pages 2-60. When we re-ran the detector, it massively over-rejected stories on pages 2-60 (72 → 52 stories) while pages 61-112 barely changed (110 → 109). Classic train/test contamination.

**Rule:** Few-shot examples must come from a different dataset than what you're evaluating on. If Jeff reviews Ketubot, use those examples when detecting stories in Bava Metzia, not when re-running on Ketubot.

### Lesson 3: The canonical review verdict format is different from prior rounds

**What happened:** The canonical review uses `correct/incorrect/approve/adjust` verdicts on the *already-corrected* data, while prior rounds used `correct/incorrect/confirm_remove/reject_remove` on the *base* data. We initially planned to add it as a 4th entry in the timestamp-based feedback system, but realized this would cause the canonical review's "correct" (meaning "the correction was right") to override the prior round's "incorrect" (which triggered the correction), effectively undoing the correction.

**Rule:** When combining feedback from different review rounds, understand what each verdict means in context. A "correct" on corrected data is not the same as a "correct" on base data. We solved this by processing the canonical review as a separate post-processing step.

### Lesson 4: Cost estimates should be verified before building infrastructure

**What happened:** The brainstorm estimated $2/run for detector experiments ($100 for 50 runs). Actual cost: $0.30/run (Gemini Flash, not Claude). We built autoresearch infrastructure (program.md, run_experiment.py) for a 50-experiment loop that turned out to be both cheap enough to run impulsively and also unnecessary — the error taxonomy already told us what was wrong.

**Rule:** Before building experiment infrastructure, verify: (a) the actual cost per experiment, (b) whether you already know what to try. If you know the answer, run 2-3 targeted experiments, not 50 blind ones.

### Lesson 5: Prompt engineering has a ceiling

**What happened:** We tried two levels of prompt modification — aggressive (5 new disqualifiers) and light (just confidence calibration). The aggressive version caused a catastrophic regression (0.93 → 0.57). The light version still regressed (0.93 → 0.89). The remaining 26 false positives are genuine judgment calls that can't be resolved by telling the model "legal discussions aren't stories" — it already knows that. The ambiguity is in passages that have BOTH narrative and legal elements.

**Rule:** When your baseline is already 0.93, the remaining errors are the hard cases. Prompt engineering works for systematic, clear-cut errors. It doesn't work for judgment calls that require domain expertise. The next step is either fine-tuning, a different model, or acceptance.

### Lesson 6: Run the full evaluation before drawing conclusions

**What happened:** The first experiment evaluation only covered pages 2-60. The composite score was 0.44, which looked catastrophic. But much of that was because the evaluator penalizes for every golden story not in the detected results — and all 61-112 stories were "missing" since we hadn't run that range yet.

**Rule:** Always run the full evaluation pipeline before interpreting results. Partial evaluations are misleading when the scoring function considers all pages.

---

### Lesson 7: Post-processing classifiers beat prompt modifications for precision improvements

**What we found:** Research shows that adding a lightweight second-stage classifier (logistic regression or LightGBM) trained on false positive features is more effective than modifying prompts when you need to reduce false positives without hurting recall. The ACL 2024 "LlmCorr" paper demonstrates this pattern. A post-processing classifier can only affect passages the detector already found — it can never cause new false negatives. Prompt modifications affect everything and can cause cascading regressions.

**Rule:** When trying to improve precision (reduce false positives), don't modify the detection prompt. Build a separate filter that runs AFTER detection. It's safer, more interpretable, and generalizes better.

### Lesson 8: Abstract patterns generalize; specific examples memorize

**What we found:** Research on "Synthetic Prompting" (Wan et al., 2023) shows that abstract pattern descriptions outperform specific examples in few-shot prompts. Our error taxonomy already has the abstract patterns ("dialogue is not events," "narrative settings don't make stories"). The mistake was adding those patterns alongside the specific passages. The specific passages caused memorization; the abstract patterns alone would have been safer.

**Rule:** When converting expert feedback into prompt guidance, use the expert's reasoning patterns, not their specific examples. "A passage where all activity is verbal acts is NOT a story" > "Ketubot 7a_1-1 is NOT a story."

### Lesson 9: Targeted tests on hand-picked examples don't predict production performance

**What happened:** A boundary check that correctly found 2/3 cross-page stories on hand-picked boundaries found 28 false positives when run on all ~100 boundaries. The LLM is too generous about what counts as a story at page breaks — the same false positive problem as everywhere else. Tuning the triage filter either let everything through or blocked everything.

**Rule:** When testing a new detection approach, always run on the FULL dataset, not just known examples. A technique that works on 3 hand-picked cases tells you the concept is sound but says nothing about precision at scale. Budget the full evaluation into the test — don't iterate on filters in a trial-and-error loop.

---

## 2026-03-27: Kiddushin Run

### Lesson 10: Narrow questions beat open-ended detection for precision

**What happened:** We tried two approaches for catching cross-page stories the merge passes missed. The first (sliding-window boundary check) asked "is there a story at this page boundary?" — an open-ended detection question. It found 28 false positives across ~100 boundaries because the LLM is too generous about what counts as a story. The second (Stage 4f continuation check) asked "does THIS specific detected story continue on the next page?" — a yes/no question about a known story. It caught 3 genuine cross-page stories with 0 false positives on Kiddushin.

**Rule:** When you need to extend an existing detection (not find new things), frame the question as narrowly as possible. Give the LLM the specific thing to check against, not an open search. "Does story X continue?" is fundamentally different from "Find any story at this boundary" — the first constrains the answer space, the second invites false positives.

---

*Add new lessons below this line. Date each entry.*

## Lesson 11 — LLM nondeterminism breaks historical baselines (2026-05-18)

**Context:** Wave 1 Ketubot regression check. The "0.9308 composite" baseline
(`docs/golden/baseline_ketubot.json`) was generated months ago from a specific
Gemini Flash run. Today, running the same v7 detector + same triage cache +
same prompts yields composite 0.858 — a 7-point swing from LLM drift alone.

**Rule:** When testing a detector change against a historical score, generate
a FRESH baseline from the unchanged code on the same day. Compare new-fresh
against old-fresh, not against the frozen JSON. The frozen JSON is only valid
as a sanity floor for the GOLDEN dataset itself, not for detector evaluation.

**Why:** The first Wave 1 check looked like a regression (-0.014 composite vs
the frozen 0.93), but apples-to-apples (v7 fresh vs v8 fresh) showed +0.06.
Trusting the frozen baseline would have killed a real improvement.

**How to apply:** Any "did this regress?" test must run BOTH versions today,
in the same window, before comparing. Cache the fresh baseline only for the
duration of the session.
