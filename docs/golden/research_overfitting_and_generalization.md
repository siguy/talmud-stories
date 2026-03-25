# Research: Overfitting, False Positives, and Generalization

**Date:** 2026-03-25
**Context:** After detector improvement experiments regressed from 0.93 to 0.89/0.57

---

## The Problem We Hit

When we added Jeff's corrections as few-shot examples to the detector prompt, performance
dropped instead of improving. Pages 2-60 (where the examples came from) lost 20 stories.
Pages 61-112 (no examples from there) barely changed. Classic train-test contamination.

## What the Research Says

### 1. This Is a Known Phenomenon ("Over-Prompting")

A 2025 paper by Tang & Tuncel ("The Few-shot Dilemma: Over-prompting Large Language
Models," arXiv:2509.13196) tested across GPT-4o, Gemini, LLaMA, and Mistral and found
there's an **optimal number of examples per model** — beyond which performance drops.
Going from 128 to 282 examples pushed us past that optimum.

A Microsoft/York study found that in-context learning is "a brittle and superficial kind
of learning that relies heavily on statistical cues from the prompt rather than a deep
understanding of the task." The model leans on the statistical structure of the examples
(what specific pages look like), not the underlying rules (what makes a legal discussion
different from a story).

### 2. The Distinction We're Asking the Model to Make Is Genuinely Hard

Our 24 NOT_A_STORY passages vs 158 real stories share many surface features:

| Feature | NOT_A_STORY | Real Stories |
|---|---|---|
| Has physical actions | 50% | 68% |
| Has "incident" language | 25% | 50% |
| Contains "halakha" | 33% | 18% |
| Avg word count | 135 | 171 |
| Avg segment count | 1.4 | 1.6 |

Half the false positives have physical actions. Many real stories lack "incident" markers.
The features overlap too much for any simple filter. The distinction is structural — it
requires understanding whether the narrative framing serves as a vehicle for legal debate
(NOT a story) or whether legal elements serve the narrative (IS a story). That's expert-
level Talmudic literary analysis.

### 3. Confidence Filtering Doesn't Work Either

The 26 false positives are spread across all confidence levels:
- 4 at YES (highest confidence)
- 8 at HIGH_CONFIDENCE
- 14 at LOW_CONFIDENCE

But 64 of 156 true positives are also LOW_CONFIDENCE. Filtering by confidence would
lose more real stories than it removes false positives.

---

## Approaches That Could Work (Ranked by Practicality)

### A. Abstract Pattern Descriptions Instead of Specific Examples

**What:** Replace page-specific few-shot examples with abstract pattern templates from
our error taxonomy. Instead of "Ketubot 7a_1-1 is NOT a story because..." write
"A passage where two rabbis debate a legal principle, with no physical actions and no
change of state, is NOT a story — even if it names specific rabbis."

**Why it helps:** The model can't memorize "Ketubot 7a" if we never mention it. We
already have the abstract patterns in `docs/golden/error_taxonomy.md` — the mistake
was using them alongside the specific examples.

**Source:** Wan et al., "Synthetic Prompting" (arXiv:2302.00618) showed that LLM-
generated abstract demonstrations outperform specific examples.

**Effort:** Low. Rewrite the few-shot section of the prompt.
**Risk:** Low. If it doesn't help, no regression risk since we're not adding specific examples.

### B. Leave-One-Group-Out Evaluation

**What:** When evaluating pages 2-30, use few-shot examples only from pages 31-112.
When evaluating 31-60, use examples from 2-30 + 61-112. Never evaluate on the same
pages the examples come from.

**Why it helps:** Eliminates the train-test contamination entirely. We can still use
specific examples — just not from the pages being tested.

**Source:** Standard practice from ML cross-validation, specifically group k-fold.
Research at Galileo AI warns about keeping related data in the same fold.

**Effort:** Medium. Need to modify the run scripts to dynamically select examples
based on which pages are being processed.
**Risk:** None — this is a measurement improvement, not a model change.

### C. Post-Processing Classifier (Most Promising for Generalization)

**What:** Keep the detector as-is (0.93 baseline). Add a second-stage lightweight
classifier (logistic regression or LightGBM) trained on features extracted from the
26 false positive passages vs. the 156 true positives. Features would include:

- Ratio of legal terminology ("halakha", "ruling", "stipulation") to narrative markers
  ("went", "came", "gave", "died")
- Presence of hypothetical framing ("if a man...", "in a case where...")
- Dialogue-only indicators (all segments classified as VERBAL_ACT in triage)
- Aramaic structural markers (interrogatives הֵיכִי, מַאי that signal Talmud meta-analysis)
- Segment count (false positives average 1.4, true positives 1.6)
- Detector confidence level

This classifier would ONLY run on passages the detector already flagged as stories.
If the classifier says "this looks like a false positive pattern," the story gets
downgraded or flagged for review.

**Why it helps:**
- Can't cause catastrophic regression (it only touches detected stories, never misses new ones)
- Trained on actual error distribution, not general patterns
- Interpretable — we can see which features drive rejections
- Sidesteps the few-shot contamination problem entirely (separate model)
- **Generalizable**: if the same false positive patterns appear in Bava Metzia (legal
  discussions with narrative settings), the classifier catches them there too

**Source:** The LlmCorr framework (ACL 2024) uses exactly this pattern — LLMs as base
classifiers with post-hoc correction from error-pattern databases. Ensembling LLM outputs
with lightweight models (arXiv:2512.07246) confirms LightGBM works well here.

**Effort:** Medium. Need to extract features, train classifier, integrate into pipeline.
**Risk:** Low — worst case it doesn't improve things, but it can't make them worse.

### D. Dynamic Per-Input Example Selection

**What:** For each Talmud page being classified, embed the page text and find the 3-5
most similar passages in the example bank that are from DIFFERENT pages. Use only those
as few-shot examples for that specific page.

**Why:** Research on dynamic few-shot prompting (PubMed 40460022) showed 21% F1
improvement over static example sets in clinical note classification. More relevant
examples = better classification, without contamination.

**Effort:** Medium-high. Need embedding infrastructure and similarity search.
**Risk:** Low.

### E. Fine-Tuning Gemini Flash

**What:** Fine-tune Gemini 2.5 Flash via Vertex AI on our 182 labeled examples.

**Why:** Research by Mansar (2024) found that fine-tuning with 200 examples significantly
outperforms few-shot prompting. We have 182 — right at the threshold. A second tractate's
labels would put us well over 200.

**Key finding from research:** Adding few-shot examples during fine-tuning provides NO
additional benefit — the two approaches are alternatives, not complements.

**Source:** Google's Vertex AI documentation + Mansar's empirical study.

**Effort:** High. Need Vertex AI setup, training pipeline, billing.
**Risk:** Medium. Fine-tuned model might overfit to Ketubot literary style.

### F. Many-Shot In-Context Learning

**What:** Instead of 3-5 examples, include ALL 182 labeled examples in the prompt using
Gemini Flash's long context window. But only use examples from pages NOT being evaluated.

**Why:** DeepMind (NeurIPS 2024 spotlight) showed log-linear improvement from few-shot
to many-shot across 9 of 10 datasets. But this only works if contamination is solved first.

**Effort:** Low (just a longer prompt), but expensive per run.
**Risk:** Higher token costs per run. May hit over-prompting ceiling.

---

## How We're Currently Treating the False Positives

**We're measuring them but not acting on them.**

The golden dataset correctly labels 24 passages as NOT_A_STORY. The eval framework
measures 26 false positives (26 rather than 24 because some FPs have no golden match
at all — they're stories the detector finds that aren't in the golden dataset).

At inference time (running on new text), nothing uses this knowledge. The detector
still produces these false positives. For Ketubot specifically, we have the golden
labels and could do a direct lookup — but that's not detection, it's cheating.

For new tractates, we'll get the same types of false positives. The question is
whether we:

1. **Accept them** — present all detected stories to Jeff, note that ~15% are likely
   false positives. Jeff reviews everything anyway.
2. **Flag them** — run the post-processing classifier (approach C) to flag likely
   false positives, so Jeff can prioritize reviewing those.
3. **Filter them** — automatically remove likely false positives before Jeff sees them.
   Riskier (might remove real stories) but reduces Jeff's review workload.

**Recommendation:** Approach C (post-processing classifier) with flagging (not filtering).
Flag likely false positives with a confidence score so Jeff can focus on them, but don't
auto-remove anything. This preserves recall while giving Jeff actionable guidance.

---

## Recommended Next Steps (In Order)

1. **Now:** Try approach A (abstract examples) — low effort, no risk. Just rewrite the
   few-shot section to use pattern descriptions instead of page-specific passages. Re-run
   and evaluate.

2. **Next session:** Build approach C (post-processing classifier). Train on the 26 FPs
   vs 156 TPs using the features above. Test with leave-one-group-out evaluation.

3. **When Jeff has time:** Run detector on Bava Metzia. Use Ketubot examples as few-shots
   (no contamination since it's a different tractate). Have Jeff review ~30 stories.
   This validates both the detector and the post-processing classifier on unseen data.

4. **If we want to push past 0.95:** Fine-tune Gemini Flash once we have 200+ labeled
   examples (Ketubot 182 + Bava Metzia ~30 = 212).

---

## Key Sources

- Tang & Tuncel, "The Few-shot Dilemma: Over-prompting LLMs" (arXiv:2509.13196, 2025)
- Wan et al., "Synthetic Prompting" (arXiv:2302.00618, 2023)
- Agarwal et al., "Many-Shot In-Context Learning" (NeurIPS 2024 spotlight)
- LlmCorr framework, "Harnessing LLMs as Post-hoc Correctors" (ACL 2024)
- Mansar, "How Much Data Do You Need to Fine-Tune Gemini?" (2024)
- Microsoft/York, "LLM In-Context Learning Is Learning, But Not How You Think" (2025)
- Clinical note classification comparison: PMC 10871377 (2024)
- Dynamic few-shot prompting: PubMed 40460022 (2025)
