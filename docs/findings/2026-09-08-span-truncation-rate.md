# The span-truncation hypothesis is refuted, and it takes one of my own claims with it

**2026-09-08.** Measured over **every accepted golden span in three tractates — 365 spans,
730 calls, 0 errors**, `gemini-3.8-flash`, thinking LOW, ~101s.
`scripts/measure_span_truncation.py` → `results/criteria/span_truncation_rate.json`.
Nothing in any golden changed and no boundary moved.

## The claim being tested

On 2026-09-03 I told Simon, and wrote into four work items, that the dominant defect behind
passages reading as pure speech is **our boundaries stopping before the action** — not
Jeff's criteria question. The evidence was a 13-case sample in which **9 flipped** to
"something happens" when the span was extended by two segments, on top of PR #36's
hand-read 3 of 6.

**That was wrong twice over.**

## What the corpus says

| | n | of what |
|---|---|---|
| accepted golden spans screened | 365 | Ketubot 164 · Kiddushin 85 · Gittin 116 |
| read **speech-only** as we publish them | **52** | 14% of spans |
| flip to eventful when extended +2 segments | 15 | 29% of the 52 — **not the 69% the sample showed** |
| …of which **another golden story starts inside the extension window** | **10** | the flip is a neighbour, not a continuation |
| **genuine truncation** | **5** | **1.4% of spans**, 9.6% of the speech-only set |
| **stay speech-only when extended** | **37** | genuine criteria cases |

**Error 1 — the sample was enriched.** Those 13 were selected as the cases where two
screens disagreed. Disagreement is exactly where an extension is most likely to change an
answer. Measuring the rate on the set chosen for being marginal gave 69%; the corpus gives
29%.

**Error 2 — and this is the one that matters — the flip test had no control.** Extending a
span by two segments walks into whatever comes next, and on a dense daf what comes next is
frequently *another story*. **Ten of the fifteen flips have a different golden story
beginning inside the two-segment window** — Ketubot 66b:9 runs into a `YES` story at 10-13;
Gittin 58a:5 into a `YES` at 7. The "revealed action" is that story's, not this one's. The
original 9-of-13 result carried the same confound and nobody checked, myself included.

### The 5 that survive

| | | revealed just past the edge |
|---|---|---|
| `LOW_CONFIDENCE` | Ketubot 54a:13-14 | *"who was married to a man from Neharde'a"* |
| `LOW_CONFIDENCE` | Ketubot 100b:17-18 | *"which he was taking to Sikhra"* |
| `LOW_CONFIDENCE` | Ketubot 111a:10-11 | *"A certain man left Pumbedita to live in Astonia"* |
| `LOW_CONFIDENCE` | Kiddushin 72a:3 | *"They went and asked Rav Ḥananel"* |
| `YES` | Kiddushin 76b:9-10 | *"Rabbi Zeira would deal with converts…"* |

Five spans, one of them top-confidence. Worth fixing; not worth reordering a roadmap.

## What this does to the standing conclusion

**It reverses it.** Genuine criteria cases outnumber genuine truncations **37 to 5**.

So **Jeff was more right than I credited him**, and my correction to him was the wrong half:

- He said the machine treats quasi-speech-acts as actions. **Confirmed** — the pre-rule
  screen cleared **38 of 104** passages on a verb from his list (*"man came before Rav"*,
  *"sent question"*, *"retracted, came, stood"*).
- I replied that most of what looks like speech-only is really our truncated boundaries.
  **That is not supported.** It is 5 spans.
- The criteria question is also **larger than the three entries** the earlier work
  estimated: 37 passages across three tractates read as speech-only and stay that way when
  the surrounding text is included.

## The email must change before it is sent

[`comms/2026-09-03-email-jeff-DRAFT.md`](../../comms/2026-09-03-email-jeff-DRAFT.md) leads
with *"a good part of what looked like speech-acts masquerading as stories is our own
boundaries stopping too early — our error, not the tradition's."* **Four of its five
illustrations are among the ten confounded flips.** Sending it would have handed the expert
a confident, checkable, wrong claim about his own text. It is unsent, and this is the
argument for the standing habit of not sending on the first measurement.

## Caveats this finding does not get to skip

- **One run, one screen, thinking LOW** (Lesson 22). The direction is large enough to act
  on; the exact 5 is not.
- **"No neighbouring golden story" is not proof of continuation.** It only removes the
  confound we can see. A story the golden does not hold would not show up.
- The 37 are *screen* verdicts, not Jeff's. Whether a speech-only passage is a story is his
  ruling, and the screen has never been asked to make it.
