# Jeff Rubenstein's Story-Definition Criteria

**What this is:** Jeff's own, explicit answer to "what counts as a story" —
the single most useful thing he has given the project, because it is the
boundary the detector cannot yet find on its own. Encode this into the
detector's Stage 2 criteria and into a conformance test set.

**Source:** Jeff's Part 2(c) answer,
[`jeff comms/Simon Brief Questions.docx`](../../jeff%20comms/Simon%20Brief%20Questions.docx)
(reply to [`docs/golden/v10/email_draft_jeff_wave4_and_roadmap.md`](../v10/email_draft_jeff_wave4_and_roadmap.md), 2026-07-06).
Logged in [`validation/feedback/jeff_2026-07-06_feedback_ledger.md`](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md).

**Current detector criteria this must be reconciled with:**
[`src/story_detector_v10.py`](../../src/story_detector_v10.py) (Stage 2 prompt,
6-criterion block) and the ground-truth few-shots in
[`src/ground_truth.py`](../../src/ground_truth.py).

---

## The core test: hypothetical vs. actually-happened

> "Legal problems/cases are hypothetical and do not refer to events that
> happened. Stories are about events that happened (even if the story is
> fictional)." — Jeff

| | Legal case | Story |
|---|---|---|
| Refers to | a *hypothetical* situation | an event that *happened* (even if fictional) |
| Form | "**If** I steal a cow, and sell it, and it dies…" | "**A certain man** stole a cow…" |
| Can contain action? | **Yes** — but the action is hypothetical | Yes — the action actually occurred |

**This is the discriminator the detector was missing.** "Is there physical
action" fails (half of false alarms have action; two-thirds of real stories
do). The real axis is **hypothetical vs. factual/actual**.

**The mixed case Jeff flags explicitly:** a legal ruling *based on a real
event* can be a story —
> "A man stole another man's cow and sold it. Rava ruled…. In this case you
> may have a story."

So: a factual narrated event + a subsequent ruling → the *narrated event* is
the story (the ruling is its resolution, not a disqualifier). This is the
opposite of the current "Rabbi stating a legal opinion → disqualify" rule when
a real event precedes the ruling.

## Speech-acts alone are not stories

> "By most traditional definitions of a story, speech-acts don't count." — Jeff

- "Rabbi X and Rabbi Y were sitting and discussing. X said… Y ruled… Z
  responded…" → **not a story.**
- Borderline: "Rabbi X **jumped up** and stated…" — technically an action, but
  Jeff says it "does not make much of a difference" from "stated." Scholars
  debate these.
- **Jeff's recommended resolution:** establish an explicit rule and apply it
  consistently — e.g. *"speech-acts don't count unless accompanied by action"*
  — **or** mark such cases **borderline** and let database users decide. But
  **minimally there must be some action beyond the speech.**

## Emotional reactions DO count

> "an emotional reaction, e.g., 'Rabbi X was embarrassed'… generally should be
> considered events/actions and count toward a story." — Jeff

Treat internal/emotional change (embarrassed, distressed, rejoiced) as a
qualifying event, not mere speech.

---

## Scope reminder (from Part 2(b))

The target database includes **halakhic stories, not only aggadic ones.** Jeff:
"we have included halakhic stories, which Ein Yaakov generally omits… our
purpose is a database of all stories." Do not let any aggada-only heuristic
(e.g. an Ein Yaakov cross-check) narrow the detector's scope.

---

## How to operationalize (actions)

1. **Rewrite the Stage 2 criteria** around the hypothetical-vs-actual axis as
   the primary test, demoting "has physical action" to a secondary signal.
   (New detector version — do not edit v10 in place; see the versioning rule in
   memory `feedback_detector_versioning.md`.)
2. **Add a speech-act rule** — pick one policy (default: "speech-acts require
   an accompanying non-speech action") and expose a `borderline` flag for the
   contested cases, which the crowd-sourced DB will surface rather than
   silently decide.
3. **Count emotional reactions** as qualifying events in the criteria.
4. **Build a conformance test set** of labeled minimal pairs — hypothetical
   legal case vs. matched factual story; pure discussion vs. discussion+action;
   emotional-reaction cases — and gate every future detector on it. This is how
   the criterion stops being a lesson that gets forgotten (see
   [`tasks/lessons.md`](../../tasks/lessons.md) Lesson 17).
