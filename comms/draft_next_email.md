# Open questions for the next email to Jeff

**Started 2026-08-30.** A running collection, not a sent message. The last email —
[`email_jeff_2026-08-30.md`](sent/2026-08-30-email-jeff.md) — closed with "Not yet asked — add
to the next email"; this file is that list, so it stops living in three places at once.
When the next email is sent, record it as its own dated file and delete this one.

Order below is the order to ask in. Item 1 is new today.

---

## 0. NEW — we ran Gittin, without looking at your list

**Why it leads:** it is the first tractate we have detected that nobody here had ever
looked at, and it is the whole point of the project — Ketubot and Kiddushin exist to make
us good enough to do this where no list exists. Measured in
[`gittin-first-run`](../docs/findings/2026-08-31-gittin-first-run.md).

**The four we did not find are not bugs, and the draft must not offer to fix them.**
Diagnosed 2026-09-01: 57a was re-run and reproduces both of its misses exactly, so they are
not nondeterminism. Three of the four are passages where **nothing happens except speech or
custom** — the class his 2026-07-06 rule tells us to reject and his 2005 list includes:

| miss | Stage 1 label | why we rejected it |
|---|---|---|
| **38b** seg 6 — `אמר רבה: בהני תלת מילי נחתי בעלי בתים מנכסיהון` | `VERBAL_ACT` | a dictum; no event |
| **57a** seg 12 — the exchange on the land of Israel's fertility | — | talk, no action |
| **57a** seg 20 — `אשקא דריספק חריב ביתר`, *"they were accustomed, when a boy was born, to plant a cedar"* | `HABITUAL` | customary practice, not a single event |
| **46b** — `פירקן…` in the redemption sugya | — | we propose segs 15-17; his unit starts at the legal frame at seg 14 (the Jeff-2005 / Jeff-2026 boundary difference, Lesson 24) |

So they are the sharpest cases we have for `jeff:speech-act-policy` — each one is a passage
where **his own two answers disagree**, on a tractate where nothing of ours has ever
touched his list. Ask him to rule, do not promise a fix.

**Draft — as it would go to him:**

> We ran the detector over all of Gittin (178 dapim) last night, before opening your 2005
> list — no Gittin example was ever in the prompts, and the code that finds stories cannot
> read your file. Then we scored ourselves against your 112 stories: **we found 108.**
>
> The four we did not are the same question, and it is one you have already answered twice
> in two different ways. You told us in July that a passage where rabbis only speak is not
> a story. Your 2005 list includes these:
>
> - **38b** — `אמר רבה: בהני תלת מילי נחתי בעלי בתים מנכסיהון` — Rabba's three matters by
>   which householders become impoverished. A saying, with no event.
> - **57a** — the exchange about the land of Israel's fertility: *"you are lying!"*, and the
>   answer about the deer's hide. Talk, and nothing done.
> - **57a** — `אשקא דריספק חריב ביתר` — Beitar and the shaft of the carriage, which opens
>   with a custom: when a boy was born they planted a cedar, when a girl, a pine.
> - **46b** — the redemption case. We do find it; we begin it one line later than you do,
>   at the incident rather than at Rav Asi's ruling.
>
> Our detector rejects the first three **because you told us to**. We would rather have your
> ruling than quietly pick one of your two answers: should passages like these be in the
> corpus, out of it, or in with a *borderline* flag?
>
> **We also propose about 30 Gittin passages that are not on your list.** Most are the same
> class — a named sage issuing a ruling. Two look to us like real stories, and a yes or no
> on each would be worth a lot:
>
> - **43a** — Rabba bar Rav Huna publicly retracts his ruling after Rav Ḥisda challenges
>   him, and reads a verse to say that one only truly understands a teaching after
>   stumbling in it.
> - **25a** — `תניא נמי הכי: מעשה, וקדמו בנות לבנים` — the children racing to Jerusalem for
>   the Paschal offering, and the daughters arriving first.

**Do not dress this up as 100%.** A looser matching rule scores it 112/112; that rule
credits a proposal anywhere within a fourteen-segment window and has been shown to credit
the wrong passage on the same daf. **108/112 survives checking every case by name**, and it
is the number to send.

**Whether he marks his own additions separately no longer gates anything.** The value of his
answer is the training signal for the tractates nobody has listed.

---

## 1. NEW — Mishnah stories: one bucket, or out of the database?

**Why it matters:** it decides whether four Ketubot passages are in or out, and it is
currently being decided by a filter nobody can see. Blocks nothing, but every number we
report against the golden is slightly wrong until it is settled.
Measured in [`mishnah_filter_delta_2026-08-30.md`](../docs/findings/2026-08-30-mishnah-filter-delta.md).

**Draft — as it would go to him:**

> When you reviewed Kiddushin you wrote, about the five-women betrothal case on 50b:
> *"This story is in the Mishnah, so it should be catalogued with Mishnah stories, not
> Talmud stories."*
>
> We built that in, and it has an effect we did not expect: it now removes two Ketubot
> stories you marked **correct** in the earlier round. Both are *ma'aseh* precedents
> quoted inside a Mishnah:
>
> - **Ketubot 14b** — מעשה בתינוקת שירדה למלאות מים מן העין, ונאנסה
> - **Ketubot 77a** — מעשה בצידון בבורסי אחד שמת, והיה לו אח בורסי
>
> We read your Kiddushin note as asking for a **separate catalogue**, not for these to be
> dropped: the database holds them, tagged as Mishnah, and the Talmud tally simply does
> not count them. That reading fits both things you told us, and it is what we will build
> unless you say otherwise.
>
> The one thing we cannot decide for you: is a story quoted inside a Mishnah part of this
> project at all, or does the database begin at the Gemara?

**If he says separate catalogue** (what we expect): the fix is small — keep withholding
from the Talmud tally, but display and score the Mishnah bucket.
**If he says out entirely:** the four golden entries should be retired, and Ketubot's
false-negative count drops from 15 to 11 for the right reason rather than by accident.

**Do not send him** the 54b / 95b cases. Those two are a tagger bug of ours — plain Gemara
mis-labelled at a chapter boundary — and asking about them would put a question of ours in
his mouth.

### Added 2026-09-01 — Gittin shows the same story landing on both sides of the rule

The first Gittin run (2026-08-31, blind: 100% loose / 96.4% strict against his 2005 list of 112 stories)
turned up **three pairs where one story is counted twice** — the Mishnah copy withheld by
the filter, and the Gemara's own citation of it kept:

| withheld, inside the Mishnah | kept, the Gemara citing it |
|---|---|
| Gittin 10a — `מעשה והביאו לפני רבן גמליאל לכפר עותנאי` | Gittin 10b — `והא קתני: מעשה והביאו…` |
| Gittin 45b — `מעשה בצידון` (the vow to divorce) | Gittin 46a — `אמר ר' יוסי בר' יהודה: מעשה בצידון` |
| Gittin 74a — `מעשה בצידון` (the coat) | Gittin 74b — `אמר רשב"ג: מעשה בצידון` |

His 2005 list has **neither** member of any pair. This is worth one added sentence in the
draft, because it is the question from a third side and it is not hypothetical:

> On Gittin we hit a case your Kiddushin note does not settle. The same *ma'aseh* often
> appears twice — once in the Mishnah, and again where the Gemara quotes it back. Our rule
> files the Mishnah copy separately and keeps the Gemara's citation, so one story is
> catalogued twice under two different headings. Should the pair be one entry, and if so
> which text is the one you would cite?

**Send it.** Sending Gittin examples costs a measurement convenience — the list stops being
a perfectly clean denominator for that tractate — and nothing else. The goal is to find every
story in every tractate; his telling us which were his and which were ours is exactly the
signal we want, not contamination. Pair it with item 5 if convenient, but do not hold the
question for it.

---

## 2. Parked — at what error rate does review become worse than starting from scratch?

Carried from [`email_jeff_2026-08-30.md`](sent/2026-08-30-email-jeff.md). That number sets the
Classification gate (`FRAMEWORK.md` §2b) and only he can answer it. Every other gate in the
framework is provisional because this one is unanswered.

---

## 3. Owed — a correction about Ketubot 77a

The last email said 77a is a story "our own set has." It is not. Our golden holds a
*different* 77a story — the Sidon tanner, seg 8, the very passage item 1 is about — while
his 2005 entry is at segs 13-14 (`אזל ר' אלעזר אמרה לשמעתא`). Two stories on one daf,
conflated by our locator's coarse window. The substance stands (we do miss his); the claim
did not. Measured in
[`recall_miss_diagnosis_2026-08-30.md`](../docs/findings/2026-08-30-recall-miss-diagnosis.md)
and `docs/history/2026-08-29-PLAN-wave6-story-criteria.md`.

Worth pairing with item 1 in the same email: the correction and the scope question are
about the same page, and the pairing is the clearest way to show him why the daf matters.
