# Open questions for the next email to Jeff

**Started 2026-08-30.** A running collection, not a sent message. The last email —
[`email_jeff_2026-08-30.md`](sent/2026-08-30-email-jeff.md) — closed with "Not yet asked — add
to the next email"; this file is that list, so it stops living in three places at once.
When the next email is sent, record it as its own dated file and delete this one.

Order below is the order to ask in. Item 1 is new today.

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
