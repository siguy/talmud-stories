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

## The Day We Fixed the Ruler (2026-08-30)

This is the most important thing in the file, so read it even if you skip the rest.

**The setup.** We had a test for whether the program picks the right start and end of a
story. It had 52 questions, 35 of them gradeable. We'd been tuning against it for weeks.

**The problem, which nobody noticed for months.** Every one of those 52 questions was
built from Jeff's *corrections* — places he'd told us we were wrong. That's like grading
a student only on the questions they missed last time. Two things follow, and both are
bad. Any change looks like a huge improvement, because you're only measuring the cases
that were already broken. And you can never, ever detect that you broke something that
used to work, because "used to work" isn't in the test.

The test file's own header said this out loud. We quoted its numbers anyway, because it
was the only test we had. That's the real lesson: a warning you've read and worked
around is not a warning you've heeded.

**The fix, and where it came from.** Simon pushed: why only 52? Use everything Jeff gave
us. It turned out Jeff wrote a list of Ketubot stories in **2005** — twenty years before
this program existed, so it couldn't possibly be contaminated by our output — and he
wrote each story out **in full Hebrew**. We'd had that file on disk for two days and had
used it only to count how many stories we'd found.

The full text was the boundary information. If you know exactly where a story's text
starts and ends, you know the boundaries.

**The engineering bit.** You can't just search for Jeff's text in the Talmud, because
Jeff transcribed from his own edition — unvocalised, and abbreviated (א"ל where the
printed text has אמר ליה). Exact search finds almost nothing. What works is *sequence
alignment*: the same family of algorithm that `git diff` uses to line up two versions of
a file, and that biologists use to line up DNA. It finds the longest run of matching
pieces and tolerates the gaps. 147 of 149 stories aligned, with 99% of Jeff's letters
matched in the right order.

**The payoff.** 35 gradeable questions became 249. And here's the number that mattered:
we ran the *identical program twice* and scored it on both tests. On the old 15-question
test it scored 60% and then 67% — a 7-point swing from nothing but the AI's own
randomness. On the new 168-question test it scored 79% and 79%. **The ruler stopped
wobbling.** Every tuning decision we'd made before that was, in a real sense, unfalsifiable.

**Then it immediately told us something we didn't want to hear.** On the old test, our
fancy boundary-trimming doubled the score on half the corpus: 33% to 67%. On the new
neutral test, the plain untrimmed version was *already 79% right*, and the trimming
barely moved it. The gain was real but a fraction of what we'd claimed.

**And then a second twist, which is the subtlest thing in this project.** We read the
list of boundaries we'd had right and broken — a list the old test could never have
produced. The pattern was sharp: trimming the *start* of a story helped 15 times and
hurt twice. Trimming the *end* helped 7 times and hurt 12, and every single failure cut
too early.

So I capped end-trimming, and the score went up. Then I checked it against the *other*
ruler, and the score went **down**.

Reading the disputed cases explained it. The program was cutting the rabbinic legal
discussion that follows a story. Jeff's 2005 list keeps that. Jeff's 2026 notes say
*"the legal discussions that follow the story need not be quoted."* Both are Jeff. Neither
is wrong. In 2005 he was building an **index** — where to find a story in its context —
so the legal frame belonged. In 2026 he's reviewing a tool that **displays** stories, so
it doesn't.

Split by which edge: the two Jeffs agree on where stories *begin* 7 times out of 7, and
disagree about where they *end*.

**Why that's the deepest thing here.** A story's beginning is a fact about the text. Its
ending depends on what the story is *for*. We had been treating "where does the story
end" as a question with a right answer, and it isn't — it's a product decision wearing
the costume of a measurement. No amount of prompt engineering resolves it, and any number
we quote can be moved by choosing a ruler.

**What a good engineer takes from this:**

1. **Ask what an artifact was made for, not just whether it's accurate.** Two datasets
   from the same expert can encode two different questions. We had an "84% agreement"
   number and nearly used it to justify merging them. The 16% that disagreed wasn't
   noise — it was the entire definition of one edge.
2. **Measure your instrument before you trust your measurements.** Running the same code
   twice and reporting the spread costs one extra run. We'd been quoting single-run
   comparisons for weeks, where the effects we chased were smaller than the wobble.
3. **A test built from failures is a fixed-the-failures test, and nothing else.** If it's
   all you have, say so every time you quote it.
4. **Re-read your raw inputs.** The 2005 file had been fetched for one purpose and the
   answer to a completely different question was sitting in the same column.
5. **The best change of the day involved no AI at all.** It came from reading a list of
   twelve failures and noticing they all pointed the same direction. Analysis beat
   engineering, and it usually does.

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
