# Trim asymmetry — and the two rulers disagree about the task (2026-08-30)

The neutral ruler (`tests/expert_boundary_targets_2005.json`, 229 scorable Ketubot
boundaries) can do what the corrections ruler never could: name the boundaries we had
**right** and broke. Reading that list changed the conclusion twice.

## 1. The surface pattern

Per boundary, no-trim vs Wave 5:

| | fixes | regressions |
|---|---|---|
| **start** trims | 15 | 2 |
| **end** trims | 7 | 12 |

Every end regression cuts too EARLY, never too late. Drifts on Ketubot 61-112:
`-6 -6 -6 -6 -4 -3 -2 -2 -2 -1`.

Capping end-trims at 3 clauses (`MAX_END_TRIM_CLAUSES` in `src/story_detector_v11.py`):

| variant | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|
| no trimming at all | 172 | 18 | 39 | 75% | 83% |
| trim both ends | 183 | 10 | 36 | 80% | 84% |
| start-trim only | 183 | 13 | 33 | 80% | 86% |
| **start + end capped at 3** | **185** | **11** | **33** | **81%** | **86%** |

Pure post-filter on the model's answer, so these are exact — re-filtered from existing
artifacts, no API calls.

## 2. But the regressions have TWO causes, not one

Reading the actual Hebrew that was cut splits them cleanly:

**(a) Definitional — the majority (~9 of 12).** The model removed stam-Talmud material
exactly as our prompt instructs, and Jeff's 2005 unit simply included it:

- Ketubot 77b — `אָמַר אַבָּיֵי... וְלָא הִיא` — rabbinic legal give-and-take after the story
- Ketubot 52b — `מֵעִיקָּרָא מַאי סְבַר, וּלְבַסּוֹף מַאי סְבַר?` — classic stam analysis
- Ketubot 60b — `וְהִלְכְתָא: מֵת — מוּתָּר` — the halakhic ruling
- Ketubot 80b — `מַאן דַּחֲזָא סָבַר... וְלָא הִיא` — stam explanation

**These are not model errors.** Jeff's 2026 review notes say the opposite of his 2005
list: *"The legal discussions that follow the story need not be quoted."*

**(b) Genuine over-cutting — the minority (~3 of 12).** The model removed text that is
plainly narrative:

- Ketubot 62a — `רַבִּי יוֹחָנָן הֲוָה קָסָלֵיק בְּדַרְגָּא... אִיפְּחִתָא דַּרְגָּא תּוּתֵיהּ` — R. Yochanan
  climbing the stair, the stair collapsing. **A whole second story, discarded.**
- Ketubot 105b — `מָר עוּקְבָא הֲוָה שְׁדֵי רוּקָּא קַמֵּיהּ, אֲתָא הָהוּא גַּבְרָא כַּסְּיֵיהּ` — Mar Ukva
  and the man who covered the spit; full narrative with dialogue. Also discarded.

That is a real defect, and it is **detection-shaped, not boundary-shaped**: where two
stories share a segment, we trim to the first and throw the second away. Same family as
the open multi-story item (Kiddushin 12a).

## 3. The finding that matters: the two rulers encode different tasks

The cap helps one ruler and hurts the other:

| | neutral (2005, n=229) | corrections (notes, n=20) |
|---|---|---|
| trim both ends | 80% / 84% | **70% / 80%** |
| end-trim capped at 3 | **81% / 86%** | 65% / 75% |

And the disagreement is concentrated on one edge:

```
START boundaries  n= 7   7 identical              -> 100% agreement
END   boundaries  n=19  16 identical, 3 disagree  ->  84% agreement
```

(START n is small; the regression reading above is the stronger evidence.)

**A story's beginning is a fact about the text. Its ending depends on what the story is
for.** Jeff in 2005 was building a story *index* — where to find the story in its sugya
— so he kept the surrounding legal discussion. Jeff in 2026 is reviewing a tool that
displays stories, so he says cut it.

**This is a product decision, not a tuning decision.** Until it is made, any end-boundary
number can be moved by choosing a ruler.

## 4. RESOLVED — we build for the 2026 reviewer, and the cap is REVERTED

Simon settled §3 on 2026-08-30: **we build for Jeff-2026, the tool reviewer.** The
product displays stories to a reader; the surrounding legal give-and-take is not part of
what we show. That decision does three things.

**(a) It re-reads the 2005 list as an UPPER BOUND, not a target.** Under the 2026
standard a story ends at or before Jeff-2005's ending — he kept the legal frame, we cut
inside it. So ending EARLIER than his boundary is expected, and ending LATER is wrong
under both standards. Scored that way, on 105 Ketubot end boundaries:

| variant | exact | earlier (expected) | **LATER (wrong either way)** |
|---|---|---|---|
| no trimming | 79 | 3 | **23** |
| Wave 5, uncapped | 78 | 17 | **10** |
| Wave 5 + cap at 3 | 80 | 9 | **16** |

**End-trimming is good after all.** It more than halves the definite overshoots, 23 → 10.
The earlier §1 table said the opposite only because it scored the 2005 boundary as a
target, which counted "cut the legal frame" — the thing we were asked to do — as a
failure.

**(b) The cap is reverted.** It scored better only against the 2005 standard; against the
one we build for it undoes the trims that fix real overshoots (10 → 16). Removed from
`src/story_detector_v11.py`, with a note in place so it is not re-invented.

**(c) The genuine bug in §2(b) survives the decision.** Ketubot 62a and 105b discard a
whole second story — at 105b the entire Mar Ukva episode, which Sefaria's own English
renders in full. That is wrong under any definition, and the depth cap was never the
right fix for it. The right guard is *never trim away a clause that is itself narrative*
— see §5.

## 5. What the elegant fix would be

Not a depth cap — a depth cap is a magic number standing in for a real signal. Cause (b)
is precisely *"we trimmed away text that is itself narrative."* The principled rule is
**never trim away a clause that is narrative in its own right**, which needs a per-clause
narrative signal — exactly what Wave 5b's labeller produces, used as a **guard on the
trim** rather than as the boundary mechanism. That is a one-role version of Wave 5b, and
it is now testable, because the ruler is stable.
