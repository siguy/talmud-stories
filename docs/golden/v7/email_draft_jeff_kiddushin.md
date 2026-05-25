# Email Draft: Jeff — Kiddushin Results Ready for Review

**To:** Jeff Rubenstein
**Subject:** Kiddushin Results Ready — Testing if the Detector Generalizes

---

Hi Jeff,

We ran the detector on Kiddushin, as you suggested. The results are ready for review:

**https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review.html**

Same review UI as before — Correct/Incorrect for each story, notes field for anything that needs explanation.

## What We Learned from Ketubot

After processing all of your corrections, we built a definitive Ketubot dataset (182 stories) and an evaluation framework that scores the detector on three dimensions: classification accuracy (F1=0.92), boundary precision (IoU=0.98), and cross-page merge detection (F1=0.86). The overall composite score is **0.93**.

We then tried to use your corrections to improve the detector — adding your reasoning patterns as instructions, using your examples as few-shot training data. **It made things worse.** The detector learned to reject the specific Ketubot passages we showed it rather than learning the general principle. Pages 2-60 (where most examples came from) lost 20 stories; pages 61-112 barely changed. We reverted everything.

The takeaway: **0.93 appears to be the ceiling for prompt-based detection on Ketubot.** The remaining errors are the 26 false positives you identified — legal discussions with narrative framing — where the distinction requires exactly the kind of expert literary judgment that makes this project valuable. The detector can't learn that distinction from prompts alone.

## What Kiddushin Tests

This is the first time the detector has seen text outside Ketubot. It uses your Ketubot corrections as reference examples, but the Kiddushin text is entirely new. So this answers the big question: **does the detector generalize, or did we just get good at Ketubot?**

We're targeting a **0.85+ composite score** on Kiddushin. If it hits that, the approach works across tractates and we can scale. If it falls significantly below, we need to investigate whether the detector learned Ketubot-specific patterns.

## What the Detector Found

- **96 stories** across 162 pages (67% of pages were pure legal content, skipped automatically)
- 34 YES, 16 HIGH, 46 LOW confidence
- **12 cross-page stories**, including 3 caught by a new continuation check we built — instead of asking "is there a story at this boundary?" (which produced too many false positives), we ask "does THIS specific detected story continue on the next page?" Much more precise.

The high LOW_CONFIDENCE count (46) suggests the same pattern as Ketubot — many borderline legal/narrative passages. We expect roughly 15% of detected stories to be false positives matching the patterns you know well.

## What Would Help Most

- **Even 30 reviewed stories** gives us enough to score the detector on Kiddushin and compare to Ketubot
- If you spot false positive patterns that are **different** from the Ketubot taxonomy, those are especially valuable — they'd tell us what we're missing
- With your Kiddushin feedback combined with Ketubot (~270 labeled examples total), we'd have enough data to explore fine-tuning the model on your labels directly — which research suggests would break through the 0.93 ceiling

Thank you as always,
Simon
