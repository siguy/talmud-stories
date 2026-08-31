# False Positive Learning Plan

**Created:** 2026-03-27
**Status:** Active — integrate into every new tractate run

---

## The Problem

The detector produces ~15% false positives: passages it classifies as stories that Jeff says
are not stories. These are almost all legal discussions with narrative framing (a rabbi goes
somewhere, then the entire passage is legal debate). The detector sees the narrative setting;
Jeff sees through it to the legal substance.

We proved through experiments on Ketubot that:
- **Prompt engineering makes it worse** — adding disqualifiers causes the model to over-reject real stories (0.93 → 0.57)
- **Few-shot examples from the same tractate cause overfitting** — the model memorizes specific pages instead of learning patterns (0.93 → 0.89)
- **ML classifiers on text features can't distinguish them** — FPs and TPs look the same at the keyword level (best classifier caught 6/26 FPs but killed 15 TPs)

## What We Know About the False Positives

From Ketubot (26 false positives analyzed):

**By detector confidence:** 4 YES, 8 HIGH_CONFIDENCE, 14 LOW_CONFIDENCE — spread across all levels, no clean threshold.

**By error pattern:** 10 are LEGAL_FALSE_POSITIVE (canonical review), rest from prior rounds. All share the same structural characteristic: narrative setting + legal content.

**By text features:** 50% contain physical action words. 33% contain "halakha." Average 1.4 segments, 135 words. These overlap heavily with true positives (68% actions, 18% halakha, 1.6 segments, 171 words). No separable clusters.

**Jeff's language for rejecting them:**
- "There are no events. This is just a legal discussion."
- "The 'action' is in what they tell the rabbi. But that is just the dialogue."
- "It is a hypothetical legal case."
- "This is just a reference to the story mentioned above."
- "The one event is not really an event in a story."

## The Plan: Three Tiers

### Tier 1: Cross-Tractate Few-Shots (Do NOW with Kiddushin)

When running the detector on Kiddushin, use Ketubot's false positive examples as few-shot
examples. This is NOT contamination because the examples are from a different tractate.

**Specifically:**
- Add 3-5 Ketubot false positive passages to the Stage 2 prompt as negative examples
- Use the ABSTRACT pattern descriptions from `error_taxonomy.md`, not page-specific text
- Example: "A passage from Ketubot where a rabbi 'sat before' another rabbi and the entire
  passage is legal debate was classified as a story but the expert said it was NOT — the
  narrative setting did not make it a story."

**How to measure:** Compare Kiddushin results with and without these cross-tractate few-shots.
If false positive rate drops without recall loss, the patterns generalize.

**Implementation:**
1. In `src/ground_truth.py`, the `generate_few_shot_examples()` method already pulls
   LEGAL_MISIDENTIFICATION examples. When running on Kiddushin, these come from Ketubot
   (the only labeled tractate), so there's no contamination.
2. No code changes needed — the existing pipeline already does this correctly when running
   on a tractate that's NOT Ketubot.
3. The KEY thing is to NOT load Kiddushin's own feedback as few-shots when evaluating
   Kiddushin. Only use Ketubot examples.

### Tier 2: Track False Positive Rate Across Tractates (Do with EVERY new tractate)

After Jeff reviews Kiddushin stories, analyze the false positives:

1. **Count:** What fraction of detected stories are false positives? (Ketubot: 26/182 = 14%)
2. **Pattern match:** Do they match the same 6 error patterns from `error_taxonomy.md`?
3. **New patterns:** Are there false positive types we haven't seen before?
4. **Cross-tractate consistency:** If Kiddushin FPs match Ketubot FPs, the taxonomy generalizes.
   If they don't, each tractate may need its own calibration.

**Store results in:** `docs/golden/fp_analysis_<tractate>.md`

**Update:** `docs/golden/error_taxonomy.md` with any new patterns discovered.

### Tier 3: Fine-Tuning (Do when we have 200+ labeled examples across 2+ tractates)

The research says 200 examples is where fine-tuning significantly outperforms prompting
(Mansar 2024). Ketubot has 182 labeled stories. Kiddushin review of ~30 stories brings us
to ~212. At that point:

1. Format the golden labels as training data for Gemini Flash fine-tuning (Vertex AI)
2. Train on BOTH tractates — this teaches the model what stories look like generally,
   not just in one book
3. Evaluate on a held-out set (leave-one-tractate-out: train on Ketubot, test on Kiddushin,
   and vice versa)
4. Compare fine-tuned model's composite score to the 0.93 prompt-based baseline

**Decision gate:** Only proceed with fine-tuning if cross-tractate few-shots (Tier 1) don't
already solve the problem. If Kiddushin false positive rate is already <10% with Ketubot
few-shots, fine-tuning may not be worth the infrastructure cost.

---

## Checklist: Before Running Any New Tractate

- [ ] Few-shot examples come from OTHER tractates only (never from the tractate being run)
- [ ] Abstract pattern descriptions from error taxonomy included in prompt
- [ ] Run detector and save results
- [ ] Generate review UI for expert
- [ ] After expert review: count false positives, classify by error pattern
- [ ] Compare FP rate and patterns to Ketubot baseline (14%, mostly LEGAL_FALSE_POSITIVE)
- [ ] Update error taxonomy if new patterns found
- [ ] Update this document with findings

## Checklist: After Expert Review of New Tractate

- [ ] Score against expert labels using `evaluate_golden.py`
- [ ] Analyze false positives: count, confidence distribution, error patterns
- [ ] Compare to Ketubot false positive profile
- [ ] If total labeled examples ≥ 200: evaluate whether fine-tuning is warranted
- [ ] Update `lessons/` with any new findings
- [ ] Store FP analysis in `docs/golden/fp_analysis_<tractate>.md`

---

## Key References

- `docs/golden/error_taxonomy.md` — the 6 error patterns with Jeff's language
- `docs/golden/research_overfitting_and_generalization.md` — why prompt engineering failed, ranked alternatives
- `lessons/` — Lessons 2 (same-page overfitting), 5 (prompt ceiling), 7 (post-processing > prompt changes), 8 (abstract > specific)
- `docs/golden/findings_v10_golden_dataset.md` — full Ketubot session writeup
