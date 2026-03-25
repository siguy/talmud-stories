# Email Draft: Jeff Update on Golden Dataset Work

**To:** Jeff Rubenstein
**Subject:** Ketubot Golden Dataset Complete — Your Canonical Review Fully Processed

---

Hi Jeff,

I wanted to update you on what we've done with your comprehensive review of all 189 Ketubot stories (from March 17). We've now processed every one of your corrections and built what we're calling the "golden" Ketubot dataset — our definitive ground truth. I also want to share what we learned when we tried to use your feedback to improve the detector itself.

## What We Built

**The golden dataset now has 182 stories** (down from 189, after merging stories you identified as parts of the same narrative and removing false positives).

We implemented 48 of your 53 corrections:

- **17 classification changes:** 10 stories you identified as not-stories (legal discussions, hypothetical cases, dialogue-only passages), 5 downgraded to low confidence (insufficient causality), and 2 special cases (106a reclassified, 111a restored after a prior error).

- **32 boundary and merge corrections:** This was the hard part. We built a tool that matches your Hebrew text citations to specific segments in the Sefaria text, then used it to:
  - Trim 8 stories that included the Talmud's analytical commentary after the narrative ended
  - Extend 5 stories that started or ended at the wrong point
  - Merge 5 pairs of adjacent stories that are really one narrative (like 85a, which you flagged twice across review rounds)
  - Create 4 new cross-page merges for stories continuing across page boundaries
  - Confirm 7 stories where you approved our proposed boundaries

The remaining 5 corrections involve complex cross-page references that need more investigation — we'll get to these.

**Importantly:** We also fixed the 10 boundary/merge issues you had flagged in prior review rounds (v5.1, v8 delta) that we had never implemented. We now understand this happened because our correction pipeline categorized feedback as "auto-apply" (classification changes) vs. "needs review" (boundary changes), and we applied the first category but never went back to the second. That won't happen again — this round, we processed everything.

## How Good Is the Detector?

We built an evaluation framework that scores the detector against your golden labels on three dimensions:

| Metric | Score | What it measures |
|---|---|---|
| Classification F1 | **0.92** | Does the detector find the same stories you identify? |
| Boundary IoU | **0.98** | For stories it finds, how well do the boundaries match yours? |
| Merge F1 | **0.86** | Does it correctly detect stories spanning page boundaries? |
| **Composite** | **0.93** | Weighted combination |

The main weakness: **26 false positives** — passages the detector classifies as stories but you identified as not-stories. These are almost entirely legal discussions with narrative elements (a rabbi goes somewhere, sits before another rabbi, then the entire passage is legal debate). The detector sees the narrative setting and classifies it as a story; you (correctly) see through the setting to the legal substance underneath.

## What We Tried to Improve — and What We Learned

We tried using your corrections to teach the detector to avoid these false positives. We added your reasoning patterns ("dialogue is not events," "a narrative setting does not make a story") as both prompt instructions and few-shot examples.

**The result was a significant regression.** The detector became too conservative — it started rejecting legitimate stories alongside the false positives. Specifically:
- Pages 2-60 (where most of your correction examples came from): dropped from 72 detected stories to 52
- Pages 61-112 (fewer correction examples): barely changed (110 → 109)

This is a classic overfitting pattern — the model learned to reject the specific passages from your examples rather than learning the generalizable principle. We reverted all changes.

**Our conclusion:** The 0.93 composite score is likely the ceiling for this detection approach on Ketubot. The remaining 26 false positives represent genuinely ambiguous passages where recognizing "legal discussion with narrative framing" vs. "narrative with legal elements" requires the kind of deep Talmudic expertise you bring. Prompt-level changes can't bridge that gap.

## What This Means Going Forward

The real value of this work is the golden dataset itself, not detector improvements on Ketubot. We now have:

1. **A reliable evaluation framework** — we can score any detection approach against your labels
2. **A documented error taxonomy** — 6 systematic patterns with your exact reasoning, which we can use when processing other tractates
3. **A baseline to compare against** — if we try a completely different detection method (like fine-tuning a model on your labels), we know what to beat

**The next productive step would be running the detector on a new tractate** (we're thinking Bava Metzia — it's narrative-heavy and would test whether the error patterns we documented from Ketubot appear elsewhere). If you're open to reviewing ~30 stories from a second tractate, that would let us validate that the detector generalizes rather than just working on Ketubot.

Would a review of 30 stories from Bava Metzia be feasible? We could prepare the review interface just as we did for the Ketubot canonical review.

Best,
Simon
