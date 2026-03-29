# FOR SIMON: What This Project Is and What We've Learned

*Last updated: March 2026*

---

## What This Project Does

We built a tool that reads pages of the Babylonian Talmud and identifies which passages contain narrative stories, as opposed to legal discussions, hypothetical scenarios, or analytical commentary. Jeff Rubenstein, a Talmud scholar at NYU, validates the results.

Think of the Talmud as a massive transcription of centuries of rabbinic debates. Most of it is legal argument — rabbis disagreeing about what the law should be. But scattered throughout are **narrative stories**: a rabbi travels somewhere, something happens, there are consequences. These stories are important for understanding rabbinic culture, but they're embedded in thousands of pages of legal text with no clear markers saying "story starts here."

Our detector is like a metal detector sweeping a beach. It beeps at anything that might be metal. Most of the time it's right (coins, jewelry). Sometimes it beeps at bottle caps (legal discussions that look like stories because they have characters and settings). The expert reviewer is the person who digs up the find and decides if it's treasure or trash.

## How It's Built

The detector is a 4-stage pipeline that uses Google's Gemini Flash model (a large language model, like ChatGPT but from Google):

**Stage 1 — Event Triage:** Quickly scans each page and classifies every paragraph as "narrative event," "verbal act," "deliberation," or "habitual action." Pages with fewer than 2 narrative events are skipped entirely. This filters out ~60% of pages (pure legal discussion).

**Stage 2 — Story Detection:** For the remaining pages, a detailed prompt asks the model to identify stories using 6 criteria: identifiable characters, multiple events, causal chain, temporal progression, descriptive (not hypothetical), and change of outcome. The model classifies each candidate as YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, or NOT_A_STORY.

**Stage 3 — (Disabled):** Was an adversarial validation step. Turned off because it didn't improve results.

**Stage 4 — Post-Processing:** Trims story boundaries using event types, detects stories that span page boundaries (the Talmud's pagination is arbitrary — stories don't stop at page breaks), and removes duplicates.

Running the full pipeline on a tractate (book) costs about $0.30 in API fees and takes ~5-10 minutes.

## The Golden Dataset

Jeff reviewed all 189 detected stories across the entire tractate of Ketubot (marriage contracts). We processed his feedback into a **golden dataset** — 182 stories with definitive labels. This is our ground truth.

We score the detector against this golden dataset using three metrics:
- **Classification F1 (0.92):** Does the detector find the same stories Jeff finds? (Yes, 98.7% of them)
- **Boundary IoU (0.98):** For stories it finds, does it get the start/end right? (Nearly perfect)
- **Merge F1 (0.86):** Does it catch stories spanning page boundaries? (Pretty good — 16 of 19)

The **composite score is 0.93 out of 1.0**. That's very good.

## The 26 False Positives (The Interesting Problem)

The detector finds 26 passages that Jeff says are NOT stories. These are almost all the same pattern: a legal discussion with a narrative setting. A rabbi goes to visit another rabbi, sits down, and then the entire passage is a legal debate. The detector sees "rabbi went somewhere" and calls it a story. Jeff sees through the narrative framing to the legal substance and says it's not.

We tried three approaches to fix this:

1. **Prompt engineering:** Added Jeff's reasoning ("dialogue is not events") to the prompt. **Result: Made things worse.** The model became too conservative and started rejecting real stories too.

2. **Few-shot examples from Jeff's corrections:** Showed the model specific passages Jeff rejected. **Result: Catastrophic overfitting.** The model memorized "reject anything from page 7a" instead of learning the general principle. Pages where we had examples lost 20 stories; pages without examples were unaffected.

3. **Post-processing classifier:** Trained a machine learning model on text features (legal word density, action word count, etc.) to filter false positives after detection. **Result: The features don't separate.** Half the false positives have physical action words, and many real stories have legal language. The ML classifier couldn't find a threshold that catches false positives without killing real stories.

**The lesson:** The difference between "legal discussion with narrative framing" and "narrative with legal elements" requires the kind of domain expertise Jeff has. It can't be automated with current techniques on this amount of data. The detector's 0.93 is likely its ceiling for Ketubot.

## What Good Engineers Think About Here

**1. Know when to stop optimizing.** We could have spent weeks tweaking prompts, but the experiments showed diminishing returns after the first attempt. The 0.93 baseline was already excellent. The remaining errors are genuinely hard.

**2. Train/test contamination is subtle.** Using labeled examples from the same data you're testing on sounds obviously wrong, but in prompt engineering it's easy to do accidentally. Our few-shot examples came from Ketubot pages, and we were evaluating on Ketubot pages. Classic mistake, important lesson.

**3. The detector is a tool, not a replacement for expertise.** The best workflow is: detector finds candidates (98.7% recall), expert makes final calls. Trying to make the detector replace the expert led to regressions.

**4. Cost estimates matter.** We initially planned $100 for 50 experiments. Actual cost: $0.30 per run ($15 total). The wrong estimate didn't change the outcome, but it did cause us to build unnecessary infrastructure before checking.

## Technologies Used and Why

| Technology | Why We Chose It | What We Considered |
|---|---|---|
| Gemini Flash | Cheap ($0.30/tractate), fast, good at instruction-following | Claude (too expensive for bulk runs), GPT-4 (tested, slightly worse) |
| Sefaria API | Free access to all Talmud text in English + Hebrew + Aramaic | Scraping (fragile), local databases (outdated) |
| Python | Simon's language, good for data processing | Node.js (considered, but Python has better ML libraries) |
| scikit-learn | Quick ML experiments for the classifier test | PyTorch (overkill), manual stats (too limited) |
| HTML review UIs | Jeff can open in any browser, no setup needed | Google Sheets (tried, too limiting), web app (too complex) |

## Kiddushin: The Generalization Test

We ran the detector on Kiddushin (2a-82b, 162 pages) — the first tractate beyond Ketubot. Jeff suggested it. This is the key test: does the approach generalize?

**Results:** 96 stories detected (34 YES, 16 HIGH, 46 LOW). 67% of pages were pure legal content (skipped). 12 cross-page stories found, including 3 caught by a new "continuation check" — instead of asking "is there a story at this boundary?" (which produced too many false positives in testing), we ask "does THIS specific story continue on the next page?" Much more precise.

**Status:** Review UI sent to Jeff. Awaiting his feedback to score against the Ketubot baseline (target: 0.85+ composite).

## What's Next

1. **Score Kiddushin** once Jeff reviews. If 0.85+ composite, the detector generalizes and we can scale to more tractates.

2. **Fine-tuning path:** With Ketubot (182 stories) + Kiddushin (~80-90 from Jeff's review), we'll have ~270 labeled examples. Research suggests fine-tuning at 200+ examples would push past the 0.93 ceiling.

3. **If Kiddushin scores low:** Investigate whether the detector learned Ketubot-specific patterns. Different literary style? Different story types? Would need targeted improvements.

## Key Concepts Worth Remembering

**F1 Score:** A single number that balances precision (what fraction of things you called "story" actually are stories) and recall (what fraction of actual stories you found). Range 0-1. Our 0.92 means both precision and recall are high.

**IoU (Intersection over Union):** For two overlapping ranges (detected story boundaries vs golden boundaries), how much do they overlap? 1.0 = perfect overlap. Our 0.98 means boundaries are nearly perfect.

**Overfitting:** When a model memorizes specific training examples instead of learning general patterns. Like a student who memorizes test answers instead of understanding the material — they ace the practice test but fail the real one.

**Few-shot learning:** Showing a model a few examples of what you want before asking it to do the task. Like giving someone three sample paintings and saying "find more like these." The risk is the model focuses on surface features (same colors) instead of deeper patterns (same artistic movement).

**Ground truth / Golden dataset:** The definitive set of correct answers, verified by an expert. Everything else is measured against this. Ours has 182 stories labeled by Jeff Rubenstein.
