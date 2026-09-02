# Jeff's answers, 2026-09-01 — three questions closed, one rule reversed, and his list corrected in two places

**Received 2026-09-01 20:35, recorded 2026-09-02.** Verbatim reply:
[`jeff comms/9-02-2026/jeff-reply-2026-09-01.txt`](../../jeff%20comms/9-02-2026/jeff-reply-2026-09-01.txt).
He answered questions 1-4 and said he expects to reach the 25-passage review page next.

## 1. `jeff:mishnah-scope` — ANSWERED, and our pipeline is already doing it

> *"10a is just the Mishnah itself, that the printers included in the printing of the
> Talmud, but not technically part of the Talmud… the second instances (Gittin 10b, 46a,
> 74b), where the Talmud quotes the story from the Mishnah, can be included."*

The rule: **a Mishnah story belongs to the Mishnah corpus; the Talmud's quotation of it is
a Talmudic story.** Eventually both, cross-referenced ("Mishnah Gittin 1:5 with a parallel
in Bavli Gittin 10b") when the program runs on all of rabbinic literature.

That is exactly what Stage 4g does: it withholds 10a / 45b / 74a and keeps 10b / 46a / 74b.
**The "double count" was not a defect** — it was the two halves of his answer, and we were
right on both. Two consequences:

- The three `HIGH_CONFIDENCE` Gittin extras are **correct proposals**, not noise. The
  screen's `mishnah_pair` bucket dissolves.
- `mishnah_stories[]` must become a **catalogued bucket, not a deletion** — his answer is
  the separate-corpus reading, which is what the 2026-08-30 measurement predicted. The
  Ketubot entries the filter removes (14b, 77a) are Mishnah stories: they belong in the
  Mishnah corpus and should stop being counted as Talmud false negatives.

## 2. `jeff:speech-act-policy` — no general rule, and two of the three cases are OURS to fix

> *"Sometimes dialogue can be counted as stories… when there is conflict and implied
> change. But these would always be borderline. Unfortunately there are no real hard and
> fast rules… These lists, as I said, are provisional, so there may be some mistakes."*

| case | his ruling | what it means for us |
|---|---|---|
| **57a Beitar** `אשקא דריספק חריב ביתר` | **"clearly a story"** — the custom is the frame; *"one day the emperor's daughter passed by"* is the event | **A real miss.** A habitual opening followed by a single event is a story, and our HABITUAL rejection stops at the frame |
| **57a** the exchange on fertility | **"not a story… The list was wrong. Great to have the AI correct it!"** | **We were right and his list was wrong.** The recall denominator loses one |
| **38b** `אמר רבה: בהני תלת מילי` | **a story** — R. Yoḥanan's two families, uprooted: two actions, causal connection | **A real miss**, and a harder one: the story is *embedded inside* a dictum |

**Recall, corrected: 108 of 111.** One of the four "misses" was never a story.

## 3. `jeff:opening-formula` — ANSWERED, and it reverses our decision

> *"These opening formulae are not technically part of the stories. But they are important,
> as, for example, תניא indicates the Talmud thinks the story is Tannaitic… If not too much
> trouble, we should include them."*

We rejected the rule on 2026-09-01 because it *fixed 9 targets and broke 8*. **His answer
re-reads the 8.** They are targets where his own 2005 start sits after the formula — and he
says the lists "were sloppy and preliminary, and we had not worked this out." Re-measured
against all four blind sets under his stated standard:

| | |
|---|---|
| start targets, all four sets | **289** |
| our late starts the formula rule fixes | **10** |
| our late starts late for some other reason | 17 |
| targets where **his** start sits after a formula | **10** — now the ruler's error, not ours |

So the rule is no longer a wash: it is **+10 with 10 ruler corrections**, and it is
**principled rather than tuned** (Lesson 37) — the expert stated it in words. The 17
remaining late starts are a separate, unexplained population and must not be folded in.

**The blind boundary sets need a note**: for starts, a 2005 target that begins after an
introducing formula no longer defines the right answer.

## 4. The two passages we proposed and he did not

| | his ruling | ours | verdict |
|---|---|---|---|
| **Gittin 43a** — Rabba bar Rav Huna retracts | *"Probably not a story, although could be low confidence… all speech except… placing an interpreter"* | `HIGH_CONFIDENCE` | **confidence too high** |
| **Gittin 25a** — `מעשה, וקדמו בנות לבנים` | *"Yes, this should be high confidence"* | `HIGH_CONFIDENCE` | **correct** |

First two data points for Classification on a tractate with no review round: 1 right, 1
over-confident.

## What this unblocks

1. **Include the introducing formula in the story start** (Boundaries) — now principled,
   measured at +10, and it needs a deterministic implementation plus a note on both 2005
   boundary sets.
2. **A habitual frame does not end the search** (Detection) — Beitar is a custom followed
   by an event, and we stopped at the custom.
3. **A story embedded inside a dictum** (Detection) — 38b, harder, and the only one of the
   three with no obvious mechanism.
4. **`mishnah_stories[]` becomes a bucket, not a deletion** (Classification / Publication).
5. **The confidence axis has its first two expert data points** on Gittin.

Question 5 — the 25-passage review round — is still with him.

---

## Addendum, same day: R-C3 and R-C4 were implemented, measured, and did not work

The rate justified trying (19% of uncovered `HABITUAL` segments sit inside one of his
stories). The prompt now carries both rules with his case and date. Then:

| | before | after |
|---|---|---|
| strict recall | 108 / 112 | **108 / 112** |
| the four known misses | 4 | **4** |
| stories proposed | 147 | 145 |
| boundaries, his 2026 standard | 86% / 88% | 85% / 89% |

7 proposals gained, 9 lost, and most of both are the same stories re-bounded — churn of a
size the noise floor produces on identical code, which no same-code repeat was run to
separate (Lesson 22). **The honest reading is: no measured effect.**

**Beitar is not proposed at all — not even as `NOT_A_STORY`.** That relocates the problem:
it is not that Stage 2 judges the passage and rejects it on the habitual frame, it is that
Stage 2 never offers it. Classification wording cannot fix a candidate that is never
generated, and the two remaining cases (57a:20, 62a:11) have the same signature.

The wording stays, pinned by a test, because the rule is his and it is faithfully written
down; the shipped Gittin artifact stays the pre-change run, because nothing measured
better. The next attempt should be aimed at Detection's coverage of a page — the
"find more stories" pass — rather than at the criteria.
