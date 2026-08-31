# Email 1 — drafted 2026-08-31, NOT SENT

**Status: ready for Simon to send from his own client**, as with every previous one.
When it goes out, move this file to `comms/sent/<date>-email-jeff.md` with a note on what
was actually sent, and update the status column in [`JEFF.md`](JEFF.md) for all five slugs.

Contents, in the order fixed by [`JEFF.md`](JEFF.md) § "Ask order":
correction owed → `jeff:boundary-end-rule` → `jeff:mishnah-scope` →
`jeff:deliverable-shape` → `jeff:appendix-separate`.

**Deliberately NOT in this email:** `jeff:speech-act-policy` and
`jeff:miss-rate` / `jeff:review-error-rate`. Those are Email 2, and both need our phase 6a
count before they are answerable at all. Do not add them here.

**Two numbers to keep straight if this is edited.** Start boundaries agree **7/7**; end
boundaries **agree 16 of 19** — the 3 that differ are the systematic ones (Lesson 24). And
the Mishnah filter now removes **two** Ketubot stories, not four: the other two were our
own chapter-boundary tagger bug, fixed 2026-08-30, and must not be put to him.

---

Dear Jeff,

One correction we owe you, one question sharpened since last week, and three short ones.
Nothing below needs more than a line or two in reply.

**The correction, first.** Last week's note told you that Ketubot 77a is a story "our own
set has." That was wrong, and how it was wrong is worth a sentence. There are two stories
on that daf. Yours, from the 2005 list, is the Rav / R. Elazar / Shmuel exchange —
אזל ר' אלעזר אמרה לשמעתא קמיה דשמואל. Ours is a different passage earlier on the page, the
Sidon tanner. Our matching tool used a window wide enough to span both and reported them
as one entry. The substance stands — we do miss your 77a story — but the claim as written
was not true.

### 1. Where a story ends

Last week's question, with something we did not have then.

Because your 2005 list writes each story out in full, we could line its boundaries up
against the corrections you have sent this year. They agree on where a story *begins*:
7 of 7. On where it *ends* they agree 16 of 19 — and all three that part company are the
same thing, the legal discussion after the story. The 2005 list keeps it; your recent
notes say it need not be quoted.

That is not a contradiction. An index of where to find a story and a tool that displays
one are different jobs, and you were doing different jobs. We have settled that much
ourselves: we build for the 2026 answer and treat the 2005 list as an upper bound.

What neither source settles is your own example — *"A man stole another man's cow and sold
it. Rava ruled…"* When the ruling is the thing that shows the event actually happened
rather than being hypothetical, is it part of the story we display, or the discussion that
follows it? The three Ketubot passages in last week's note (60b, 52b, 105b) are still the
clearest cases; a line on any one of them would settle it.

### 2. Do stories inside the Mishnah belong in this project?

When you reviewed Kiddushin you wrote, about the five-women betrothal case on 50b:
*"This story is in the Mishnah, so it should be catalogued with Mishnah stories, not Talmud
stories."*

We built that in, and it has an effect we did not expect: it also removes two Ketubot
stories you kept in the earlier round — 77a you marked correct, and 14b you asked us to
demote to borderline rather than drop. Both are *ma'aseh* precedents quoted inside a
Mishnah:

- **Ketubot 14b** — מעשה בתינוקת שירדה למלאות מים מן העין, ונאנסה
- **Ketubot 77a** — מעשה בצידון בבורסי אחד שמת, והיה לו אח בורסי

We read your Kiddushin note as asking for a **separate catalogue**, not for these to be
dropped: the database holds them, tagged as Mishnah, and the Talmud tally simply does not
count them. That reading fits both things you have told us, and it is what we will build
unless you say otherwise.

The one thing we cannot decide for you: is a story quoted inside a Mishnah part of this
project at all, or does the database begin at the Gemara?

### 3. What the first release should be — a yes or no

Your July answer asked for a living, crowd-sourced, editable database, with contested cases
kept and flagged. We think that is the right end state, and we would like to get there by
shipping something narrower first.

The proposal: **a published, citable corpus with a feedback channel.** The text is
versioned and static, so a citation resolves to fixed words. Any reader can flag an entry —
*not a story* / *borderline* / *missing* — with a note. You, or a small group you choose,
adjudicate, and accepted corrections ship in the next release.

The honest tradeoff, because it is the part you would notice later: **a citable release
cannot also be silently mutable.** Live editing and stable citation pull against each
other, and versioned releases are how other scholarly corpora resolve it. If you want edits
visible the moment they are made, that is a different product, and much better to know now.

Does the corpus-plus-feedback version meet your need for a first release?

### 4. One small ask, and it costs you a line

A handful of entries in the Kiddushin list turned out to be stories we had sent you,
merged into the list. We noticed only because the appendix you built them from survived as
its own file in the same folder — nothing inside the list itself would have shown it.

It matters more than it looks. A list that contains our own output can no longer tell us
what we *miss* — and what we miss is the one thing we cannot measure any other way. Your
2005 Ketubot list is the most valuable thing we have precisely because it predates us.

So: when you add stories that came from our output, could you keep them in a separate file,
or mark them? Gittin, Yevamot and Eruvin are still clean, and they stop being clean the
moment we send you results for them.

---

Thank you — particularly for the 2005 lists. Used as a blind test, your Ketubot list is
still the only reason we know what we are failing to find.

Simon
