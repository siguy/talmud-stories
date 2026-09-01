# DRAFT — Email 1 to Jeff, prepared 2026-09-01

**NOT SENT.** Simon sends from his own client. When it goes out, move this to
`comms/sent/<date>-email-jeff-scope.md`, record it in the sent log in
[`JEFF.md`](JEFF.md), and delete
[`draft_next_email.md`](draft_next_email.md) — its item 1 is folded in below and its
items 2–3 are items 1 and 5 of the ask order.

**Contents = Email 1 of the ask order in [`JEFF.md`](JEFF.md)**: the 77a correction,
`jeff:boundary-end-rule`, `jeff:mishnah-scope`, `jeff:deliverable-shape`,
`jeff:appendix-separate`. The other two questions are Email 2 and wait on phase 6a —
**do not fold them in**, and in particular do not ask about Kiddushin 58a: he answered it
in 2005.

**Hebrew passages** should go inline as they did on 2026-08-30 (that email had an HTML
twin for exactly this reason — `comms/sent/2026-08-30-email-jeff.html`).

---

Dear Jeff,

Four things, and a correction we owe you first.

## 1. A correction

In my last email I said Ketubot 77a is a story our own set already has. That was wrong,
and wrong in an interesting way. Our set holds a *different* 77a story — the Sidon tanner
who died — while your 2005 entry is the passage a few lines later,
אזל ר' אלעזר אמרה לשמעתא. Two stories on one daf, and our matching tool was coarse enough
to read them as one. The substance of what I told you stands — we do miss the story you
listed — but the claim as I put it did not.

## 2. The boundary question, sharpened

I asked in August where a story ends when the ruling is what makes it a story at all, and
you said you would get to it. I am not re-asking, because we have since found something
that narrows it considerably.

On the 32 Ketubot boundaries where your 2005 list and your later review notes cover the
same passage, the two of them **agree on every start — 7 out of 7 — and disagree only on
ends, 3 times out of 19.**

So this is a narrow question, not a broad one. It is not "what counts as a story"; the two
sources never disagree about where one begins. It is only the far edge: your 2005 lists
keep the legal material that resolves a case, and your review notes say the legal
discussion afterwards need not be quoted. Both are yours, written for different purposes.
**Which should the published corpus follow?**

This is the only thing blocking us from scoring boundaries at all.

## 3. Stories inside a Mishnah — in the database, or out?

When you reviewed Kiddushin you wrote, about the five-women betrothal case on 50b:

> *This story is in the Mishnah, so it should be catalogued with Mishnah stories, not
> Talmud stories.*

We built that in, and it had an effect we did not expect: it removes two Ketubot stories
you had marked **correct** in an earlier round. Both are *ma'aseh* precedents quoted
inside a Mishnah:

- **Ketubot 14b** — מעשה בתינוקת שירדה למלאות מים מן העין, ונאנסה
- **Ketubot 77a** — מעשה בצידון בבורסי אחד שמת, והיה לו אח בורסי

And a third case has just turned up from the other direction. Our detector proposes the
**incident of Beit Ḥoron at Ketubot 71a** — a real *ma'aseh*, but one whose home is
Nedarim, quoted in Ketubot as a legal precedent. Your 2005 list does not have it. That may
be exactly right, and if so it tells us something we cannot infer on our own.

We read your Kiddushin note as asking for a **separate catalogue**, not for these to be
dropped: the database holds them, tagged as Mishnah, and the Talmud tally simply does not
count them. That reading fits both things you have told us, and it is what we will build
unless you say otherwise.

The one thing we cannot decide for you: **is a story quoted inside a Mishnah — or quoted
into a tractate from elsewhere — part of this project at all, or does the database begin
at the Gemara of the tractate itself?**

## 4. What we think the first version should be — a yes or no

In July you described a living, crowd-sourced, editable database, with contested cases
kept and flagged. We think that is the right destination, and we would like to propose a
first version that gets most of it much sooner:

**A published corpus, versioned and citable, with a feedback channel on every story.**
Readers flag *not a story* / *borderline* / *missing*, with a note. You or a small group
adjudicate. Accepted corrections ship in the next release.

The honest tradeoff, because it is the part you should decide rather than us: **a citable
release cannot also be silently mutable.** If a scholar cites story 214 in Ketubot, that
citation has to resolve to the same text next year. Live edits and stable citation pull
against each other, and versioned releases are how other scholarly corpora resolve it.

Does that meet your need for a first version, or do you want edits visible immediately —
which is a different product, and much better to know now than later?

## 5. One small request, and it expires

Your Kiddushin list included an appendix of stories you and our system found together. Two
of us merged that into the main list, and it took us a while to notice — which matters,
because a list you wrote before seeing our output is the only honest way we can measure
what we miss. Once our results have been mixed in, that property is gone and cannot be
rebuilt.

Gittin, Yevamot and Eruvin are still clean, because we have not sent you anything about
them yet. **When we do, could you keep anything prompted by our output in a separate file,
or just mark those entries?** One line from you protects three tractates' worth of
measurement.

Thank you — and the boundary question in §2 is the one that unblocks the most.

Simon

---

## Notes for Simon, not for the email

- **§2's figures were wrong in the first draft of this file and are now corrected.** The
  source table
  ([`2026-08-31-kiddushin-boundary-set.md` §5](../docs/findings/2026-08-31-kiddushin-boundary-set.md))
  counts **agreement**: starts 7/7, ends 16/19, overall 84% (27/32). `JEFF.md` summarised
  that as *"split on ends 16/19"*, which reads as 16 disagreements — and it was drafted
  that way here before the source was checked. The true disagreement is **3 of 19 ends**.
  `JEFF.md` has been corrected too. **Do not restate this from memory**; it is a count of
  three and the email says so.
- **Ketubot only.** The Kiddushin overlap is 14 boundaries with 3 starts, and the finding
  says plainly that the Ketubot pattern does not reproduce there. §2 claims nothing about
  Kiddushin.
- **§3's Ketubot 71a** is from
  [`2026-09-01-unread-proposals-screened.md`](../docs/findings/2026-09-01-unread-proposals-screened.md).
  It is deliberately framed as *"that may be exactly right"* — it is evidence for the
  scope question, not an accusation that he missed one.
- **Kiddushin 25b and 27a** from the same screen are **held for Email 2**, where they
  belong with `jeff:speech-act-policy`. Adding them here would turn a four-question email
  into a six-question one.
- **Do not include Kiddushin 58a.** His own 2005 margin note reads *"Not sure this is a
  story. Very minimal."* — asking would spend a scarce verdict on a question he answered
  twenty years ago.
- **Ketubot 112b** is not in this email at all. Its proposal had a malformed span
  (`start_segment -2`), which **#18 has since fixed** — `validate_story_spans()` now clamps
  or drops such spans inside `detect_stories()`, and it turned up a second, previously
  unknown case (`Ketubot 22a`, a reversed `10..0`). But the screen that surfaced 112b read
  **pre-fix** output, so the span we hold for it is still the bad one. It needs a re-run
  under the validator before it is worth showing him — not a question, a rebuild.
- **§5's timing is the live constraint.** It has to reach him *before* we send any
  new-tractate results, not after.
