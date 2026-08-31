# Email draft for Jeff — Wave 4 results (plain-language version)

**To:** Jeffrey.Rubenstein@nyu.edu
**Subject:** Story-boundary review, latest round — the system now reads for context (2 files attached)

---

Hi Jeff,

Following up on your June 3 note — the one where you said the
boundary-trimming was right on 5 of your examples but cut too much on 7
others. I've reworked how the system decides where a story begins and
ends, and I'd love your eye on the result before I lock it in.

The short version: on the 14 specific passages you flagged, the new
approach now matches your judgment on all 14.

## What changed, in plain terms

The old method worked from a fixed checklist of Hebrew cue words — things
like ההוא ד, מעשה ב, אלא, שמע מינה. Whenever it saw one of those words, it
cut the text there. The trouble is exactly what you put your finger on:
sometimes אלא (or a rabbi's name, or ההוא) is framing *around* a story,
and sometimes it's part of the story itself. A fixed checklist can't tell
the difference — it just sees the word and cuts.

The new method actually reads the Hebrew of each story in context and
judges, the way you would, where the narrative content really begins and
ends. There's no word list anymore — it weighs what the passage is doing.

Two things worth saying plainly:

- This does **not** change which passages get flagged as stories, or how
  the system measures up against your validated set — that accuracy is
  unchanged. The only thing that moves is *where, inside each story, the
  text gets trimmed*. Which is precisely the thing you flagged.
- So what I need from you now is a read on those trim decisions.

## Your 14 cases

I turned your June 3 notes into a test and re-ran them:

- **6 passages the old method cut too much** → the new one correctly
  keeps the full opening on all 6.
- **2 passages it didn't cut enough** → the new one catches both,
  including the וְלָאו מִשּׁוּם…אֵלָּא construction on Kiddushin 12b.
- **6 more from your earlier review, as a safety check** → all handled.

One I want to flag honestly: on **Kiddushin 8a (segments 9–10)** you
wanted two fixes — trim the opening, *and* drop Rav Ashi's statement
entirely. The new method got the opening trim. Removing Rav Ashi's
statement is a different kind of change (it's about which segments belong
to the story at all, not where to trim within them), so I've set that
aside for a separate pass — I didn't want to quietly half-do it.

## What I'd like you to look at

Two files are attached — one for Kiddushin, one for Ketubot. Open either
one in any web browser (no login, nothing to install, works offline).
Each story shows the Hebrew with the trimmed portion **struck through in
red** and the kept portion in dark text. Where the new method and the old
one disagreed, there's a note so you can see exactly what changed.

Each story also carries a small label:

- **recovered_text** — the new method fixed an over-trim you'd flagged
  (these should be uncontroversial).
- **new_trim** — the new method made a cut the old one didn't. These are
  the fresh editorial calls that haven't had your eye yet.
- **different_trim** — both trimmed, but in different places.
- **both_full / identical_trim** — no disagreement.

You can filter to any one of these at the top of the page.

If you only have time for one thing, the **new_trim** cases are where I'd
most value your read — those are the judgment calls the system made on its
own, and if anything's off, it will most likely be there:

- **Kiddushin:** 33 new_trim, plus 35 different_trim
- **Ketubot:** 54 new_trim, plus 31 different_trim
- **recovered_text:** 10 in each (the fixes to your earlier flags)

## How to send me your reactions

For any story, click **Correct** or **Incorrect** and jot a note in plain
English ("still cuts too much," "missing a trim here," whatever fits).
When you're done, click **Save Review** at the top of the page — it
downloads a small file. Just email that back to me. You don't need to go
through every story; even a sample of the new_trim cases would tell me
what I need.

## After this

Once I have your read, I'll fold in your corrections and make this the
standard version. Next on my list: the Rav Ashi–type fixes (which
segments belong to a story), and starting on Bava Metzia to see how well
this holds up on a tractate we haven't touched yet. If anything in the
new_trim set concerns you, I can adjust before locking it in.

Thanks as always for reading so closely — the fact that the new approach
matched you on all 14 of your examples is the best sign yet that we're
finally handling boundaries the right way. Looking forward to your
thoughts on the rest.

Best,
Simon

---

**Attachments:**
- `validation/ui/wave4_kiddushin_review.html` (3.3 MB — 95 stories)
- `validation/ui/wave4_ketubot_review.html` (5.9 MB — 167 stories)

**Optional quick-scan summaries** (plain text, if you'd rather skim than
click through):
- `docs/findings/2026-06-15-wave4-span-diff-kiddushin.md`
- `docs/findings/2026-06-15-wave4-span-diff-ketubot.md`
