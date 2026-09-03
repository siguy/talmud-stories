# Jeff's quasi-speech-act rule takes the count from 6 to 17 — and 9 of the 13 additions are the span defect again

**2026-09-03, later the same day.** Extends
[`the speech-act contradiction touches 6 golden entries`](2026-09-03-speech-act-blast-radius.md)
(PR #36). That finding is not overturned. Its central claim — *"three of the six are
not criteria cases at all, they are spans that stop before the thing that happens"* —
turns out to be the finding, and it is larger than three.

## What arrived after PR #36 was merged

Jeff, 2026-09-02, having read 25 Gittin passages:

> "a lot of the AI's confusion had to do with speech-acts or quasi speech-acts that
> could seem like actions but are really more connected to a legal discussion, not a
> story. What if it was taught that words like **"retracted," "considered,"
> "responded" and even "sent"** (when what he sends is a message or question) should
> not be evaluated as actions for our purposes."

**PR #36's screen counted exactly those verbs as actions.** Not as an oversight — it
ran hours before the email. Its own `what_happens` cells, for entries it cleared:

| entry | PR #36 `what_happens` | Jeff's rule |
|---|---|---|
| Ketubot 69a:10 | *"retracted, came, stood, silent"* | **retracted** — his word |
| Kiddushin 44b:6 | *"reversed, sent question"* | **sent a question** — his exact carve-out |
| Kiddushin 50a:5 | *"Rav Ḥisda brought the case"* | brought a case = legal framing |
| Ketubot 111a:10-11 | *"man came"* | came before |
| Ketubot 53a:12 | *"Man came, wife died"* | came before; the death is the premise of a query |

So the 6 was a correct answer to the question as it was then asked. Under Jeff's
newer rule it is **17** (Ketubot 13, Kiddushin 4).
Screen: `scripts/screen_quasi_speech_acts.py`, lexicon `src/speech_act_lexicon.py`,
output `results/criteria/quasi_speech_act_screen.json`, `gemini-3-flash-preview`.

## But the two screens agree on only 4 of 19

| | n |
|---|---|
| union of both screens' speech-only calls | 19 |
| **both screens agree** | **4** — Ketubot 7a:1, 54a:22, 85a:13-14, 112a:11 |
| this screen only (quasi-speech-acts) | 13 |
| PR #36 only | 2 — Ketubot 15a:0, 17a:10 |

Two reasonable implementations of one question, differing by a model version and a
prompt, agree on a fifth of the candidates. **Neither 6 nor 17 is a number to put in
front of Jeff as a count.**

## And extending the span dissolves most of the difference

PR #36 hand-read its 6 and found 3 were spans ending before the action. Measured over
this screen's 13 additions — re-run with up to 2 extra following segments
(`scripts/test_span_extension_confound.py`):

**9 of 13 flip to "something happens".**

| entry | what appears in the next two segments |
|---|---|
| Ketubot 10a:9-10 | *"They brought him the cloth, and he soaked it in water and laundered it"* |
| Ketubot 111a:10-11 | *"and he died"* |
| Ketubot 66b:9 | *"riding on a donkey and leaving Jerusalem… gathering barley"* |
| Ketubot 69a:10 | *"Ravina provided one-tenth of the estate… gave her intermediate-quality land"* |
| Ketubot 65a:10 | *"I should not have to be ashamed"* — the emotional reaction Jeff counts |
| Ketubot 53a:12, 65a:5, Kiddushin 44b:6, 72b:10 | flip |
| **hold** | Ketubot 105a:13, 50b:9-10, Kiddushin 40b:7, 50a:5 |

Two of the nine flip for bad reasons — Kiddushin 44b flips citing *"they reversed the
names and sent the question"*, which is the disputed verb itself, and 72b on
*"Ameimar permitted… to marry"*, a ruling. **The confound test has its own noise, and
saying so is the point.**

## What is actually true

1. **Jeff's word list is right and is needed.** Without it a screen counts *sent a
   question*, *retracted an opinion*, *came before* and *brought the case* as events.
   That is a real defect in what we ran this morning, now fixed in the lexicon.
2. **A flat word list would be wrong.** The verbs flip on their object — sending a
   *messenger* is an event, sending a *question* is not; retracting a *get* is an
   event, retracting an *opinion* is not. Hence three tiers: T1 disqualifies, T2
   triggers scrutiny only, T3 is the positive target that stops the rule eating real
   stories. The most common quasi-action across the bucket was **"came before" — 31 of
   110 passages**, 14 of which contain a real event anyway.
3. **The criteria question stays small — about 3 entries.** PR #36's estimate survives
   this. The count moved 6 → 17 and then most of the 13 dissolved into the same
   boundary defect PR #36 named. Consistent, and it means `story-criteria` still is
   not the project's biggest item.
4. **The dominant defect is Boundaries, not criteria.** Across both screens, spans that
   stop before the action account for more speech-only calls than genuine speech-only
   passages do. That is a
   [Capability 4](../capabilities/4_boundaries.md) finding that two independent
   attempts to size a Capability 3 question both walked into.

## What must not be sent to Jeff

**A count.** "N of your stories would be demoted" is exactly the claim this cannot
support — it was 6 this morning, 17 this afternoon, and ~8 of those 17 are our own
truncation. The email now leads with his rule, agrees with it, gives him the three
stable cases, and tells him plainly that our spans often stop early. →
[`comms/2026-09-03-email-jeff-DRAFT.md`](../../comms/2026-09-03-email-jeff-DRAFT.md)

## Method notes

- Model self-reported `confidence` was **`high` on 110 of 110** — zero variance, zero
  signal. Jeff's "weaken the confidence" half cannot be wired to it. Confidence is
  structural instead: a T2 verb present AND no T3 event. → Lesson 34(d), which
  predicted this for schema fields and now has a case in a model's own output.
- Both screens are single runs (Lesson 22). Given they disagree on 15 of 19, the
  honest report is the disagreement, not either number.
- This finding was produced on a stale branch that predated PR #36 and duplicated its
  filenames. **Check `main` before running a phase that is described as never-run.**
