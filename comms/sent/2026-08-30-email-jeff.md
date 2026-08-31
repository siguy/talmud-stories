# Email to Jeff — 2026-08-30

**Sent by Simon from his own client on 2026-08-30.** This is the draft as prepared;
Simon may have edited before sending. HTML version with the three Hebrew passages
inline — this is the version that was sent:
[`email_jeff_2026-08-30.html`](2026-08-30-email-jeff.html).

A companion web page carrying the same three passages was published privately as a
Claude artifact ("Where the Story Ends"); it is reachable from Simon's artifact gallery.
The email was made self-contained precisely so it did not depend on that link.

## The one question asked

When a ruling is what makes a passage a story at all — Jeff's own example, *"A man stole
another man's cow and sold it. Rava ruled…"* — **is that ruling part of the story we
display, or the legal discussion that follows it?**

His 2005 lists keep the legal material around a story; his review notes say
*"the legal discussions that follow the story need not be quoted."* These are not a
contradiction — they were made for different purposes — but neither answers this.
Blocks the end rule for capability 4 (Boundaries).

Three real Ketubot passages were included as illustrations: 60b seg 9 (trailing halakhic
discussion with an incident inside it), 52b seg 5 (the stam analysing the story
afterwards), 105b seg 9 (two parallel incidents — one entry or two?).

## What was reported to him

- 96% recall (143/149) against his blind 2005 Ketubot list
- Boundary test set rebuilt: 35 gradeable targets → 249; run-to-run noise 7 points → 0
- 87% of his stated boundaries fall at the text's own sentence punctuation
- On his 15 boundary corrections we went from 2 exact matches to 9
- Stage 1 discards 56% of Ketubot pages; half our known misses are there
- Owed to him: 5 stories from his list absent from our golden (20a, 53a, 67b, 72b, 82b),
  and Ketubot 77a, which he has, our golden has, and our detector never proposes

## Told, not asked

On "Rabbi X jumped up and stated" he had already told us to establish criteria and hold
to them, so we stated ours rather than re-asking: speech alone is not enough, an
emotional reaction counts as an event, the rest marked borderline. We also flagged that
we read his *"some action beyond the story"* as *"beyond the speech."*

## The ask

Whether his lists cover other tractates. **ANSWERED — four arrived the same day:**
`jeff comms/8-30-2026/` — Kiddushin 105, Gittin 112, Yevamot 102, Eruvin 73.

## Not yet asked — add to the next email

### 1. The review-cost threshold

At what error rate does reviewing our output become worse than working from scratch?
That number sets the Classification gate (FRAMEWORK §2b) and only he can answer it.

### 2. Do stories inside the Mishnah count? *(added 2026-08-30)*

Our pipeline currently **deletes** any story lying entirely within a Mishnah rather than
the Gemara. That was never a decision — it was a Wave 1 post-processor nobody revisited,
and until today two of the four Ketubot passages it removed were not Mishnah at all, just
Gemara mis-tagged at a chapter boundary (fixed; Lesson 27). Two genuine cases remain, and
both are explicitly *ma'aseh* formulas inside a Mishnah:

- **Ketubot 14b seg 11** — `אמר רבי יוסי: מעשה בתינוקת שירדה למלאות מים מן העין, ונאנסה`
  — R. Yosei's incident of the girl who went down to fill water from the spring.
- **Ketubot 77a seg 8** — `מעשה בצידון בבורסי אחד שמת, והיה לו אח בורסי`
  — the Sidon tanner. (This is the 77a story *our* golden holds — not the one on his
  blind list, which is at segs 13-14. See the correction owed above.)

**Why it is a real question and not a preference: his own two sources disagree.** His
blind 2005 Ketubot list contains no Mishnah-only story. His review rounds accepted both
of these into our golden. That is the same shape as the boundary question — the 2005
lists were an index of where a story sits in its *sugya*, the reviews are of a tool that
*displays* stories — and it may well have the same answer.

Scale is small and known: 2 on Ketubot, 1 on Kiddushin in the current output — and the
Kiddushin one (50b seg 10, `ומעשה בחמש נשים ובהן שתי אחיות`) is the same shape again, so
this is a recurring category rather than two oddities. What it decides is bigger than the
count: whether the filter should exist at all, and whether a Mishnaic *ma'aseh* belongs in
a corpus of Talmudic stories.
