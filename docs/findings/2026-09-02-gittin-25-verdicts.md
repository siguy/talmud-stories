# Jeff's 25 Gittin verdicts — 3 new stories, 18 rejections, and three answers he reversed on seeing the text

**Received 2026-09-02, `axes-2`, `applies_to: base`, detector `v11`.** Verbatim:
[`jeff comms/9-02-2026/jeff-gittin-25-review-2026-09-02.json`](../../jeff%20comms/9-02-2026/jeff-gittin-25-review-2026-09-02.json);
ingest copy at
[`validation/feedback/gittin_axes_review_2026-09-02.json`](../../validation/feedback/gittin_axes_review_2026-09-02.json).

This closes `jeff:axes-round` and answers question 5 of
[the 2026-09-01 email](../../comms/2026-09-01-email-jeff-gittin.md). Questions 1-4 came
back the day before and are written up in
[`2026-09-02-jeff-answers-gittin.md`](2026-09-02-jeff-answers-gittin.md).

**The source is an RTF whose indentation is U+00A0, not spaces.** It does not parse as
JSON until those are replaced. Nothing else was altered; the ingest copy is the same
object re-serialised. (Lesson 28's shape — the file arrived through a converter — but here
the converter was ours and the payload is plain JSON, so the parse is verifiable rather
than trusted: 25 reviews in, 25 out.)

## The reading

All 25 unlisted proposals reviewed, none skipped.

| shown | → `yes` | → `borderline` | → `no` |
|---|---|---|---|
| `HIGH_CONFIDENCE` (5) | 0 | 3 | 2 |
| `LOW_CONFIDENCE` (20) | 3 | 1 | 16 |
| **total** | **3** | **4** | **18** |

**Three stories we found that his 2005 list does not have**, all three labelled
`LOW_CONFIDENCE` by us:

| ref | his note |
|---|---|
| **Gittin 19a:16** — the man flogged by Rav Kahana | *"A very minimal story, but qualifies as a story."* |
| **Gittin 43b:4** — the woman who is half maidservant | *"The last sentence is not part of the story"* — he quotes the Hebrew to cut |
| **Gittin 70a:22** — Me'oret works her slave and he dies | *"Two acts and change. Only this part is the story: וְהָא מְעוּרַת עֲבַדָה לֵיהּ לְעַבְדַּהּ תְּלָת מִינַּיְיהוּ, וּמִית!"* |

Four more are `borderline`: 10b:6, 20a:9, 25a:10, 43a:13-14.

## Three answers he gave in prose and reversed on the page

The two messages are a day apart and can be compared. **They disagree on three of the
five passages both cover, and every time the page is the stricter reading.**

| passage | email, 2026-09-01 | review, 2026-09-02 |
|---|---|---|
| **Gittin 25a** | *"Yes, this should be high confidence"* | `borderline` — *"This is borderline, **not** high confidence"* |
| **Gittin 46a** | *"can be included"* | `no` — *"there is no story. It is filled in by the translator"* |
| **Gittin 74b** | *"can be included"* | `no` — *"the same as 46a above"* |
| Gittin 43a | *"probably not… maybe low confidence"* | `borderline` |
| Gittin 10b | *"can be included"* | `borderline` |

**The rule this establishes: a prose answer sets policy; only a verdict on the passage
settles the passage.** His Q1 answer about which corpus a Mishnah story belongs to is
unaffected — it is a cataloguing rule, and it stands. What it cannot do is certify that a
particular Gemara quotation contains a story, and for two of the three it does not.

This is worth a standing habit, because the failure is asymmetric: a policy answer is
cheap to get and feels like it settles a list of cases, and we booked three passages on
one the day before it was contradicted.

## The translator, and why 46a is not a one-off

> *"If you look at the Aramaic/Hebrew, there is no story. It is filled in by the
> translator. Not enough to go on here."*

Stage 2 renders each segment **English first, truncated at 300 characters, then Hebrew,
truncated at 200** — [`src/story_detector_v11.py:204`](../../src/story_detector_v11.py).
Boundary refinement, cross-page merge and the continuation check send **English only**
(same file, lines 913, 923, 1059, 1070, 1237, 1251). So the model reads more Steinsaltz
than Aramaic, and Steinsaltz supplies narrative connective tissue the source does not
have.

That is a **mechanism**, and mechanisms generalise. It is `suspected`, not measured — no
Aramaic-only arm has been run — and it is the subject of
[`work/2026-09-02-english-first-prompt.md`](../../work/done/2026-09-02-english-first-prompt.md).

## What the round does and does not settle

**Settles:** the Gittin extras. 147 accepted proposals, 117 matching his list, 30
unlisted — 25 sent here, 5 self-screened as duplicates or standing practice. Every one of
the 30 now has a disposition. The Classification point estimate is
[a separate item](../../work/done/2026-08-31-classification-point-estimate.md); this file is
the round, not the measurement.

**Does not settle:** the top band's precision. There are three tiers, not two — `YES`
(59), `HIGH_CONFIDENCE` (24), `LOW_CONFIDENCE` (64) — and **no extra is a `YES`**, so the
2026-09-01 email's claim that every `YES` is on his list survives this round untouched.
What the round does show is that the **middle** band is weak: 5 `HIGH_CONFIDENCE` extras
produced zero yeses.

## The instrument itself failed

**Every structured field came back empty.** `extent`, `confidence`, `grouping`, `quote`,
`quote_polarity`: null or blank on all 25. He wrote everything in `notes` — including
five explicit boundary corrections (10b, 19b, 20a, 43b, 70a), two of them quoting the
Hebrew to cut.

That is the exact failure the axis UI was built to prevent, and it happened on the UI's
first real round. `display_problem` was false throughout, so the renderer was fine — this
is not a display bug, it is the disclosure going unused.
[`work/2026-09-02-axis-fields-unused.md`](../../work/2026-09-02-axis-fields-unused.md).

The boundary corrections are not lost — they are prose, which is the state the 70 banked
targets are already in, and they will need the same mining.

## Follow-ons

| what | where |
|---|---|
| the round is read by no ruler — Lesson 38's shape, caught by the board this time | [`classification-point-estimate`](../../work/done/2026-08-31-classification-point-estimate.md) |
| 57a retracted from his own list → recall denominator 112 → 111 | [`gittin-recall-denominator`](../../work/done/2026-09-02-gittin-recall-denominator.md) |
| a Gittin golden — the first blind tractate with **negative** labels | [`gittin-golden`](../../work/done/2026-08-30-gittin-golden.md) |
| English-first prompting | [`english-first-prompt`](../../work/done/2026-09-02-english-first-prompt.md) |
| the unused axis fields | [`axis-fields-unused`](../../work/2026-09-02-axis-fields-unused.md) |
