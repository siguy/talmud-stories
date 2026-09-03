# A number is an answer to the question it was built for — asking it a different question is silent

**Date:** 2026-09-03
**Found in:** three unrelated defects in one session, all the same shape
→ [`2026-09-02-classification-point-estimate.md`](../docs/findings/2026-09-02-classification-point-estimate.md),
[`2026-08-30-story-criteria.md`](../work/2026-08-30-story-criteria.md) §6a,
[`2026-09-03-loose-window-proposal-credit.md`](../docs/findings/2026-09-03-loose-window-proposal-credit.md)

## The rule

**A measurement is correct for the question it was built to answer, and gives no warning
when it is asked a different one.** Nothing errors, nothing looks wrong, and the number
that comes out is often the flattering one — because the population it was built to
describe and the population someone is about to conclude something about have quietly
drifted apart, and only one of them was ever checked.

Before quoting a number, name **out loud** the exact question it answers and the exact
population it was computed over. If either has changed since the number was built, the
number has to be rebuilt, not reused.

## Three instances, one session

**1. The Classification ruler.** Built to answer *"of the proposals judged, how many are
right?"* On Ketubot and Kiddushin that population was the whole review round. On Gittin
the round covered only the residue — proposals his list didn't already corroborate — so
the same formula now answers a different question: *"of the hardest proposals, how many
are right?"* The ruler printed **14.3%**. The tractate's actual precision is **83.7-86.7%**.
Nothing in the ruler changed; the population feeding it did, silently.

**2. The blast-radius bucket.** `story-criteria` needed *"how many golden entries does
Jeff's new rule actually demote?"* What got quoted for five weeks was **110** — the size
of the bucket that had to be *searched* (every `LOW_CONFIDENCE` entry), not the size of
the set that turns out to be affected. 110 answers *"how many entries could possibly be
touched"*; the real question needed the entries actually read. The answer was **6**.

**3. The loose recall window.** Built to answer *"did we find Jeff's story?"*, generously,
because his transcription and Sefaria's spelling disagree. Read backwards — *"is this
proposal on Jeff's list?"* — the same window silently answers a different question, and
does so wrong: 35 proposals across three tractates were credited to a list they are not
on, because they merely sat inside a story's generous search window.

## Why this is one lesson and not three coincidences

In every case: (a) the number was computed correctly, by code nobody would call buggy in
isolation; (b) it was quoted somewhere the population had shifted from what the number's
own construction assumed; (c) the drift was **silent** — no test failed, no field was
missing, nothing distinguished a valid reading from an invalid one at the point of
quotation; (d) the wrong reading was **not random** — it consistently understated the
project's actual state (14.3% instead of ~86%, 110 instead of 6, "on his list" instead of
"unverified"). A number that fails silently and fails in the pessimistic direction gets
noticed eventually. One that fails silently and flatters does not — two of these three
were caught only because a human read past the number into the underlying cases.

## What to do instead

- **State the denominator's construction next to the number, every time.** Not "83.7%"
  but "83.7%, over the 135 of 147 proposals that carry an expert label." The second form
  cannot be misquoted without visibly contradicting itself.
- **When a round, a bucket, or a window changes shape, the metric built on it needs a new
  name or a stated caveat — not silent reuse.** "Classification precision" meant one thing
  in March and a narrower thing in September; it should not have been the same header.
- **A count is not a rate, and a rate is not a verdict.** 110 is a search-space size. 35
  is a count of *unverified*, not *wrong*. Neither survives being read as more than what
  it was built to say.
- **The cheapest check is reading a sample of what the number is made of.** All three
  defects here were caught by looking at individual cases behind an aggregate, not by
  auditing the arithmetic. The arithmetic was never wrong.
