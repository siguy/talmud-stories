# Say which number is segment one, every time a segment number leaves the repo

**Date:** 2026-11-14
→ [`2026-11-14-jeff-segment-numbering.md`](../docs/findings/2026-11-14-jeff-segment-numbering.md)

## The rule

**When you show an expert a segment number outside a page that prints its own labels
(email, docx, chat), give it in Sefaria's 1-based numbering as a `Ketubot 106a:2` ref, and
quote the opening Hebrew words.** When a segment number comes back in his words, find the
segment by the text he quoted or described, never by the number alone. If he quoted no text,
check both bases against the passage, and if only one fits, record which one in the
correction. If both fit, ask him.

## What happened

The 2026-05-25 email said *"Ketubot 106a segs 1-2"* in our 0-based indices, gave no base,
and linked only the Sefaria page, which counts from 1. Jeff answered *"the story is
segments 2-3, not really 1"*. He was counting Sefaria's segments: that is the Elijah
passage we described, segment for segment as on his own 2005 list. We read it 0-based and
stretched the next story, the Rav Yosef famine, back over the end of the Elijah story. The
golden carried that boundary for five months, and the Septimus site showed a card with two
stories on it.

It looked right because the arithmetic was consistent ("extend the start back one
segment") and the correction cited his exact words. Nobody read the two segments the new
range covered.

In review UIs he uses the 0-based labels printed in front of him, and checked against the
text every one fits. So the base depends on the medium. You cannot learn it once and
assume it from then on.

## The guard

The project has no automatic check that a correction's range covers the text the expert
described; this rule is on you. The next email that cites a segment uses `ref:N` with Sefaria
numbering and a Hebrew quote. The 2026-10-11 email already does half of this: it gives
1-based Sefaria links with a description and no bare numbers.
