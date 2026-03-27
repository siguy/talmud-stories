# Email Draft: Jeff — Kiddushin Results Ready for Review

**To:** Jeff Rubenstein
**Subject:** Kiddushin Story Detection Results — Review UI Attached

---

Hi Jeff,

Following your suggestion, we ran the story detector on Kiddushin (2a-82b). The results are ready for your review at this link:

**https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review.html**

It shows every detected story with the full English and Hebrew text so you can evaluate each one. Works in any browser (Chrome, Safari, Firefox).

## What We Did

We ran the same detection pipeline we used on Ketubot, now on all 162 pages of Kiddushin. The detector uses Ketubot examples as reference points (your prior corrections), but this is the first time it has seen Kiddushin text — so this is a clean test of whether it generalizes.

**Results:**
- **96 stories detected** across 53 pages (109 pages were pure legal content and skipped)
- 34 classified as YES (definite story), 16 as HIGH confidence, 46 as LOW confidence
- **12 cross-page stories** detected — stories that span a page boundary
- 3 of those cross-page stories were found by a new "continuation check" we built specifically for catching stories that break across pages

## How to Use the Review UI

Open the link above in any browser.

**For each story you'll see:**
- The story summary and classification (YES / HIGH / LOW)
- The full English and Hebrew text with the detected story highlighted in yellow
- Context segments before and after the story (unhighlighted) so you can judge boundaries
- For cross-page stories: both pages shown with a purple divider marking the page break

**Filter buttons at the top** let you view:
- All stories, or just YES / HIGH / LOW confidence
- Cross-page stories only (to check merge accuracy)
- Unreviewed stories (to track your progress)

**For each story, click:**
- **Correct** — the detector got it right (it's a real story with good boundaries)
- **Incorrect** — something is wrong (add a note explaining what)

**In the notes field, it's most helpful to note:**
- **False positive** — this isn't really a story (legal discussion, hypothetical case, etc.)
- **Boundary issue** — the story starts too early/late or ends too early/late (note where it should start/end)
- **Merge issue** — this story should be combined with an adjacent one, or a merge is wrong

When you're done, click **Save Results** at the top right. It will show a JSON block you can download and send back.

## What We Expect

Based on Ketubot (where the detector scored 0.93 composite), we expect roughly:
- **~85% of detected stories to be correct**
- **~15% to be false positives** — mostly legal discussions with narrative framing (the same pattern from Ketubot)

## What to Watch For

From our Ketubot error analysis, the detector's main mistakes are:

1. **Legal discussions where all "events" are verbal** — rabbis asking, objecting, ruling. No physical actions or changes of state.
2. **Hypothetical scenarios** — "if a man..." passages that describe what *could* happen, not what *did* happen.
3. **Narrative settings followed by legal debate** — a rabbi goes somewhere or sits before another rabbi, but the substance is legal argumentation, not narrative.
4. **Stories that should start earlier or end sooner** — boundary issues where the detector includes too much Talmudic commentary after the narrative ends, or misses the opening.
5. **Stories that continue across page boundaries** — we detect 12 of these, but there may be others we missed.

## What's Most Helpful

- **Review as many as you can** — even 30 stories gives us solid data to evaluate the detector on a new tractate
- **Prioritize LOW confidence stories** — these are the ones where the detector is least sure, and your judgment is most valuable
- **For false positives, a brief note is gold** — even "not a story, legal discussion" tells us what pattern it matched
- **For boundary issues, note where the story should start/end** — a Hebrew phrase or segment number helps us fix it precisely

## Next Steps After Your Review

Once we have your feedback:

1. **Score the detector on Kiddushin** — compare to the Ketubot baseline (0.93). If it scores 0.85+, the detector generalizes well.
2. **Analyze the false positives** — are they the same patterns as Ketubot, or new ones? This tells us if our error taxonomy is comprehensive.
3. **Build a Kiddushin golden dataset** — just like Ketubot, your corrections become the definitive ground truth.
4. **Evaluate fine-tuning** — with Ketubot (182 stories) + Kiddushin (~80-90 stories from your review), we'll have ~270 labeled examples. Research suggests that at 200+ examples, fine-tuning the model on your labels would significantly outperform the current prompt-based approach. This would be our path to pushing past the 0.93 ceiling.
5. **Continue to more tractates** — if the detector generalizes, we can run it on additional tractates with confidence, building toward a comprehensive dataset of Talmudic narratives.

Thank you for continuing to make this work possible — your expertise is what makes the difference between a useful tool and a guessing machine.

Best,
Simon
