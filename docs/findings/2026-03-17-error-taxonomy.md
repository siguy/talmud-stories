# Error Taxonomy: Lessons from Jeff Rubenstein's Expert Review

**Source:** 187 expert reviews across all of Ketubot (canonical_review_anonymous_2026-03-17)
**Analysis:** docs/golden/canonical_feedback_analysis.json

This document captures the **systematic error patterns** our story detector makes, organized by how to fix them. Each pattern includes Jeff's actual language so the detector can learn from his reasoning.

---

## 1. LEGAL_FALSE_POSITIVE (11 instances, 21% of errors)

**What it is:** Legal discussions, hypothetical scenarios, or references to stories that get incorrectly classified as narrative stories.

**This is our #1 false positive pattern.**

### Detection Heuristics

The passage is likely NOT a story if:
- The "events" are rabbis making legal arguments, stating opinions, objecting, asking questions
- The scenario is hypothetical ("if a man..." / "in a case where...")
- It references a story told elsewhere but doesn't narrate the events itself
- There is only one action followed by a legal ruling
- All "activity" is dialogue — no one does anything physical, travels, or changes state

### Jeff's Reasoning Patterns

> "There are no events. This is just a legal discussion." (7a_1-1)
> "Not even a story. Just a legal decision. The 'action' is in what they tell the rabbi. But that is just the dialogue." (13b_16-16)
> "The actions mentioned in the reasoning, 'stating, objecting, asking questions' are all part of a dialogue, and not really events." (21b_7-8)
> "This is just a reference to the story mentioned in the Talmud above. A rabbi overlooked what another rabbi said about this incident. That does not constitute a story." (15b_2-2)
> "It is a hypothetical legal case." (13b_0-0)
> "The one event, that a rabbi found another in the study hall, is not really an event in a story." (25a_9-10)

### Key Insight for Generalization

**Dialogue ≠ Events.** Just because rabbis speak, argue, or rule does NOT mean something "happened." An event must change the state of the world. Legal reasoning, no matter how heated, is not a narrative event.

**A narrative setting does not make a story.** "Rabbi X sat before Rabbi Y and said..." provides a setting, but if everything that follows is legal debate, it's still not a story.

---

## 2. BOUNDARY_OVEREXTENSION (5 instances, 9% of errors)

**What it is:** The story boundary includes the Talmud's analytical commentary ON the story, which is not part of the story itself.

### Detection Heuristics

The story boundary should END when:
- The text shifts from narrative to analysis ("The Gemara asks...", "What did he think initially?")
- An interrogative appears that questions the story's logic (מַאי, הֵיכִי, מְנָא)
- A legal principle is derived from the story
- The text explicitly references the story from outside it

### Jeff's Reasoning Patterns

> "The last line is the Talmud's comment on the story and not part of the story itself." (85b_9-9)
> "The following lines is the Talmud's discussion about the story." (60b_5-9)
> "The last few words are not part of the story, as they are the Talmud's comment." (104b_7-15)
> "The last few words are not part of the story but are the Gemara's comment on the story." (23a_13-16)
> "The final line is the Talmud's question on the story and should be omitted." (54a_13-14)

### Key Insight for Generalization

**Stories end when the narrative arc resolves.** The rabbi's ruling that resolves the case IS part of the story. The Talmud's ANALYSIS of why the rabbi ruled that way is NOT. Look for the structural shift from "what happened" to "what does this mean."

### Aramaic Structural Markers to Detect

- מֵעִיקָּרָא מַאי סְבַר ("What did he originally think?") — meta-analysis
- הֵיכִי עֲבַד הָכִי ("How could he do this?") — analytical question
- טַעְמָא דְּ ("The reason is that...") — legal reasoning about the story
- Questions beginning with interrogative + future/conditional

---

## 3. BOUNDARY_UNDEREXTENSION (10 instances, 19% of errors)

**What it is:** The detected story misses its beginning (on a prior page or earlier in the same page) or its ending (continuing further than detected).

### Detection Heuristics

The story probably STARTS EARLIER if:
- Segment 0 of the current page continues a narrative from the previous page
- The detected story starts mid-action (no setup, no characters introduced)
- Jeff says "the first half is not quoted" — the narrative setup is missing

The story probably ENDS LATER if:
- A rabbi's concluding reflection on the events is in the next paragraph
- The story continues with "the next paragraph" which is the resolution
- Cross-page continuation flags are not set

### Jeff's Reasoning Patterns

> "The first line is missing from the previous page of Talmud (12a)." (12b_0-0)
> "The first half of the story is not quoted here." (53a_2-3)
> "The story begins with the previous line." (77b_6-8)
> "The next paragraph should also be included." (103a_24-32)
> "The story continues with a few words from the top of 70a." (69b_10-12)
> "The next paragraph is part of the story." (85a_8-8)

### Key Insight for Generalization

**Always check the edges.** When detecting a story:
1. Look at the segment BEFORE the detected start — does it set up the narrative?
2. Look at the segment AFTER the detected end — does it resolve the narrative?
3. Look at segment 0 of the next page — does the story continue there?
4. Look at the last segments of the previous page — does the story start there?

**A rabbi's reflection on events IS part of the story** if it's the narrative conclusion. Abaye saying "I learned from this that..." is still narrative closure.

---

## 4. CONFIDENCE_MISCALIBRATION (9 instances, 17% of errors)

**What it is:** The story is correctly identified but assigned the wrong confidence level.

### Patterns

**HIGH → LOW (7 instances):**
- Habitual/repeated actions ("what they would do") → LOW_CONFIDENCE
- Minimal causality between events → LOW_CONFIDENCE
- Mostly dialogue with minimal physical action → LOW_CONFIDENCE
- Two events but no causal chain between them → LOW_CONFIDENCE

**LOW → YES/HIGH (2 instances):**
- Story with clear temporal progression and change → promote to YES

### Jeff's Reasoning Patterns

> "It is not a one-time event, but recounts what the rabbis 'would' do, i.e., repeatedly." (17a_10-10)
> "Two events but no real causality." (25b_6-6)
> "Low confidence. It is mostly a legal case. The action 'explaining' is dialogue, not really an action." (21a_10-11)
> "There is too little change or causality to be high confidence." (8a_13-13)

### Key Insight for Generalization

**Causality is the key differentiator.** HIGH_CONFIDENCE requires:
- Multiple events in a causal chain (A caused B, B led to C)
- Temporal progression (first X, then Y, finally Z)
- Change in outcome (before vs. after)

If events are present but merely listed without causality, it's LOW_CONFIDENCE at best.

**Habitual ≠ Narrative.** Describing what someone habitually does is description, not narrative. Narrative requires a specific, one-time sequence of events.

---

## 5. MERGE_NEEDED (17 instances, 32% of errors)

**What it is:** Stories that should be one entry are split into two (or more), either on the same page or across page boundaries.

### Cross-Page Merges (most common)

The continuation text at the top of the next Talmud page is systematically missed. Our cross-page merge logic looks for stories that end at the last segment of page N and start at segment 0 of page N+1, but:
- The continuation is often just 1-3 lines at the top of the next page
- These lines are currently treated as independent entries or missed entirely
- Jeff has flagged this issue on at least 10 different stories

### Same-Page Merges

Two adjacent story entries on the same page are actually one story:
- They share the same characters and narrative arc
- The second entry is explicitly "the continuation of" the first
- The detector split them because of a paragraph break in the source text

### Jeff's Reasoning Patterns

> "This should be merged with the previous story, as it is really the continuation of that story." (25b_5-5)
> "This is the second half of the story." (8b_6-10)
> "The story continues with a few words from the top of 70a." (69b_10-12)
> "It is also part of a longer story and should be quoted with the rest." (103b_3-3)

### Key Insight for Generalization

**Always verify segment 0 of the next page.** If a story ends at the last segment of page N, the first few segments of page N+1 very often contain the story's conclusion. This is a structural feature of the Talmud's page layout — stories don't end at page boundaries.

---

## 6. MERGE_INCORRECT (1 instance)

**What it is:** A cross-page merge was attempted but included the wrong segments.

### Jeff's Note

> "I think something got confused here. The first selection, from 111a, is a low-confidence story. The second passage highlighted here, from 111b, is not a story." (111a_23-25)

### Key Insight

When merging cross-page, verify that the content on the second page is actually a CONTINUATION of the story on the first page, not a separate passage that happens to be on the next page.

---

## Summary: The 5 Rules for Better Detection

1. **Dialogue is not an event.** Legal discussions where rabbis argue are not stories, no matter how many "actions" the dialogue contains.

2. **End stories at the narrative resolution.** The Talmud's analytical commentary comes AFTER the story — don't include it.

3. **Check page boundaries.** Stories routinely span Talmud pages. Always look at the edges.

4. **Require causality for high confidence.** Multiple events without causal chains = LOW_CONFIDENCE at most.

5. **Merge before presenting.** Adjacent entries sharing characters + narrative arc = one story. Don't split at paragraph breaks.
