# Jeff's segment numbers in the 2026-05-25 round were 1-based; we applied them 0-based

**Date:** 2026-11-14
**Fix:** `scripts/fix_jeff_segment_numbering_2026-11-14.py` (Ketubot golden, one boundary)
**Open:** `jeff:106a-elijah-split` in `comms/JEFF.md`
**Lesson:** `lessons/_say-which-number-is-segment-one.md`

## What happened

The site card `ketubot-106a-2-3` held two stories: the end of Rav Anan and Elijah, then the
Rav Yosef famine. It came from one golden edit.

1. **What we sent, 2026-05-25** (`comms/sent/2026-05-25-email-jeff-wave3.md`):
   *"Ketubot 106a segs 1-2 — Elijah stops visiting Rav Anan after a legal error; Rav Anan
   fasts until he returns"*, with a link to `https://www.sefaria.org/Ketubot.106a`. The
   numbers were our 0-based indices. The email never named the base, and the only place
   he could look the passage up was Sefaria, which counts segments from 1. **Measured** (the
   email text).
2. **His reply, 2026-05-26** (Gmail, verbatim): *"Ketubot 106a segs 1-2\*. This is a story,
   but the story is segments 2-3, not really 1."*
3. **What we did, 2026-06-03:** `scripts/apply_jeff_2026-06-03_corrections.py` read "2-3"
   0-based and moved the start of the famine entry (106a 3-3) back to 2-3.

## Which base he meant

| reading | his "2-3" is | his "not really 1" is | fits? |
|---|---|---|---|
| **1-based (Sefaria)** | our 1-2: Elijah stops coming, Rav Anan fasts, the box, *Seder Eliyahu*. This is the passage we described, and it is his 2005 list entry `ketubot_129` exactly | our 0: Rav Nahman sets the orphans' case aside, the end of the fish story. His 2005 entry `ketubot_128` ends there | **yes** |
| 0-based (ours) | our 2-3: the box (the tail of the Elijah story) plus the Rav Yosef famine, two unrelated passages | our 1: the opening of the Elijah story, so the story would be cut off from its own start | no |

**Verdict: indicated, strongly.** He never stated a base. But only one reading makes his
sentence describe a coherent passage, and that passage matches his own blind 2005 list
segment for segment. The "1-2" he was correcting was our label read in Sefaria's numbering
(Rav Nahman's ruling plus Elijah), and he dropped the "1".

**How he numbers elsewhere: he uses whatever numbers are in front of him (measured).** In
the review UIs, which print our 0-based labels, every number he wrote that can be checked
against the text fits 0-based:

| where | his words | our 0-based segment | fits |
|---|---|---|---|
| Kiddushin 12a (2026-07-06 UI) | *"two stories, each of which begins הָהוּא גַּבְרָא (sections 13 and 14)"* | 13 and 14 both open "There was a certain man" | yes |
| Kiddushin 20a (2026-07-06 UI) | *"Section 14 is not part of the story … The story ends עִמְּךָ בַּמַּאֲכָל"* | 13 ends with that phrase | yes |
| Kiddushin 8a (2026-05-26 UI) | *"line 10 … Rav Ashi's statement is not part of the story"* | 10 opens "Rav Ashi said" | yes |
| Ketubot 52b (2026-02-05 UI) | *"continues on the next page … Ketubot 53a (Segments 0-3)"* | a 0, and `53a_0-3` is the label of the card he was shown | yes |
| Kiddushin 8b (2026-07-06 UI) | *"It continues with line 0 on the next page"* | a 0, so not Sefaria's numbering | yes |

So the trap was not his habit. It was an email that gave him numbers with no base and
sent him to a page that counts differently.

## Every correction from that reply, audited

`apply_jeff_2026-06-03_corrections.py` is the only `apply_jeff_*` script that turns
segment numbers *he wrote* into a boundary. The later ones apply verdicts keyed on our
own card ids or quoted passages. (2026-09-23's Kiddushin 39b "segment 7" was Simon's prescreen note,
not Jeff's; it fits 0-based too.)

| entry | what he wrote | what we applied | which reading fits | confidence |
|---|---|---|---|---|
| Ketubot 106a | *"the story is segments 2-3, not really 1"* | famine 3-3 → **2-3** | **1-based** (see above) | high, **fixed** |
| Ketubot 7a seg 1 | *"low confidence"* | 1-1 NOT_A_STORY → LOW | a verdict on the passage we described (Rav Ami). Our 0-based 1 is Rav Ami; Sefaria 7a:1 is halakhic discussion. Since superseded: BORDERLINE (2026-09-23) | no change |
| Ketubot 26a seg 9 | *"Correct, this is not a story but just a legal discussion"* | no-op | both readings land on legal discussion | no change |
| Ketubot 102a seg 6 | *"Not a story. Just a legal argument"* | no-op (not in golden) | ambiguous. Sefaria 102a:6 (our 5, Rava's comparison) is literally a legal argument, and our 6 (the case before R. Yishmael) is what we described. Both readings give "not in golden", and R-C0 (an incident plus a ruling, with nothing else changing) agrees | no change |

**1 of the 4 items was affected, and it is fixed.** Story counts do not move (Ketubot stays
at 190 entries / 160 accepted). `GOLDEN_COUNTS` is unchanged.

## The fix

The 106a entry goes back to **3-3**: the famine passage alone, which he rated HIGH on
2026-03-17 (*"Mainly a request and a rejections"*). The correction records his words, both
readings, the evidence, and `fixed_by`. The script is idempotent and refuses if the entry is
in neither state.

**Not fixed: whether the Elijah passage is its own story.** The golden still stitches it to
the fish story (105b 14-16 → 106a 0-2), which is the extent he approved on 2026-03-08
(*"The merge and boundaries are now correct"*). His 2005 list, his 2026-02-26 note (*"What
is highlighted on 106a is an independant story"*) and this reply all say it is separate. Two
of his recent rulings disagree, so this goes to him as `jeff:106a-elijah-split`. A
"separate" answer adds one entry and trims the 105b card.

## What else copied the wrong boundary

- **Boundary test sets:** none. `tests/expert_boundary_targets_v2.json` has no 106a target.
  The 2005 set takes 106a from his list, which is right.
- **Rulers and consensus labels:** keyed on the review-round key `Ketubot 106a_3-3`, so
  already correct.
- **Site (not touched here, another session owns it):** `site/data/ketubot.json` card
  `ketubot-106a-2-3`, its summary in `results/shas_run/site_summaries_written.json` and its
  note in `site/data/notes/ketubot.json` describe both passages. On the next site build the
  card becomes `ketubot-106a-3-3` and needs a famine-only summary. Until one is written,
  the old key's summary will not match.
- **Scores:** the 2026-06-03 rescore (`docs/findings/2026-06-03-wave3-round2-ketubot-rescore.md`)
  priced this edit at −0.006 on boundary IoU>0.8. That figure was measured against the wrong
  boundary. It is historical and is not re-run here.
