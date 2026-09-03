# The speech-act contradiction touches 6 golden entries, not 110 — and half of those are a boundary defect

> **Superseded in part, same day.** Jeff's 2026-09-02 email — which arrived after this
> ran — rules that *retracted, considered, responded, sent (a message)* are not actions.
> This screen counted them as actions. Under his rule the count is **17, not 6**, and
> **9 of the 13 additions dissolve into the span defect this finding names below** —
> which is why its central claim stands and its number does not. →
> [`quasi-speech-acts and the span confound`](2026-09-03-quasi-speech-acts-and-the-span-confound.md)

**2026-09-03.** Phase 6a of [`story-criteria`](../../work/2026-08-30-story-criteria.md),
first proposed 2026-08-29, described as *"~$0.10, needs nobody, changes nothing"*, and
**never run for five weeks** while the contradiction it sizes was called a 44%-of-the-golden
problem.

```bash
python3 scripts/measure_speech_act_blast_radius.py --dry-run   # no API calls
python3 scripts/measure_speech_act_blast_radius.py --out results/criteria/speech_act_blast_radius.json
```

## The contradiction

| 2026-03-17, across 187 reviews | 2026-07-06, as a general rule |
|---|---|
| *"The actions mentioned in the reasoning — stating, objecting, asking questions — are all part of a dialogue, and not really events."* | *"speech-acts don't count… minimally there must be some action beyond the speech."* |

Both are Jeff's. The golden was built on the first; the second would demote every entry
where nothing happens but speech.

## Measured

| | |
|---|---|
| `LOW_CONFIDENCE` golden entries examined | **110** (Ketubot 77, Kiddushin 33) |
| judged | 110 — **0 failed** |
| **speech only** | **6** — all Ketubot |
| share of the bucket | **5%** |
| share of the 249 accepted golden entries | **2.4%** |

**110 was the candidate bucket, not the affected set.** Every prior document — the Wave 6
plan, the work item, `STATUS.md`, and my own summary yesterday — carried "110 entries, 44%
of the golden" as the size of the problem. It is **6**, and the difference cost one script
and eleven minutes.

## And on reading them, the 6 are not one thing

Hand-read, which the count alone cannot do:

| entry | what it actually is |
|---|---|
| **112a:11** | the Amorite and the man of Eretz Yisrael arguing about dates — **genuinely all speech** |
| **7a:1** | Rav Ami permits, the Sages object, he answers — **genuinely all speech** |
| **17a:10** | R. Yehuda *would* suspend Torah study for a funeral — a **standing practice**, not an event |
| **15a:0** | *"The incident transpired among the wagons…"* — the incident is **referred to, not narrated**; our span holds the reference |
| **54a:22** | *"A certain person said to his heirs, in his will:"* — the span **ends there.** The bequest, and everything that follows from it, is outside our boundary |
| **85a:13-14** | the woman before Rav Beivai's court — the span cuts before the action |

**Three of the six are not criteria cases at all.** They are spans that stop before the
thing that happens. A boundary that ends early makes a story look like speech, and a
classifier asked "does anything happen *here*" will answer no — correctly, about the wrong
question.

So the criteria question, honestly stated, is about **three entries**, and up to three more
are [Boundaries](../capabilities/4_boundaries.md) work that this measurement found by
accident.

## What this changes

**`story-criteria` is not the project's biggest open question.** It was ranked that way on
the 110 figure — mine included, yesterday. At 6 entries, with half of them mis-bounded
rather than mis-classified, it is a small item.

**6b becomes a much better question.** The plan was to send Jeff *"N stories in your golden
would be demoted by your newer rule"* with N unknown and feared large. It is 6, they fit in
one email, and three of them he can settle in a sentence. That is a far cheaper ask than
the one we were preparing, and it can ride along rather than needing its own round.

**Nothing in any golden changed.** This is a count. Whether those entries stop being
stories is his ruling, and the file says so in its own `note` field.

## The method note worth keeping

The screen asks **"does anything non-speech happen?"** — never *"is this a story"*. Getting
a model to answer the second would be producing the expert's verdict with a machine, which
is the one thing this project must not do. Emotional and internal reactions count as
action, because his 2026-07-06 rule says so explicitly; a screen that missed that would
have over-reported the blast radius in the direction that flatters the urgency of the work.

**And the count needed reading.** 6 is the measurement; *three of the six are a different
defect* is what a human found by looking at them. A count is where an investigation starts.

## The five weeks

The plan said 6a needed nobody, cost ten cents, and changed nothing. It sat unrun while the
number it would produce was quoted as 110 in four documents. **A measurement that cheap,
blocking a question that large, should never wait** — and the reason it waited is worth
naming: it was filed under a phase of a wave, behind two other phases, one of which is
genuinely blocked on Jeff. The blocked phase made the whole item look blocked.
