# Lesson 28 — Read the source format, not the converter's output

**2026-08-30**

Jeff's Kiddushin list was parsed by running `textutil` over the `.doc` and
reading the result line by line. That returned 105 stories. Nine were his
English review notes, and because `.doc` stores annotations in a separate
character range, `textutil` dumped them all at the end of the file, where
they inherited the last daf reference seen — Kiddushin 81b appeared to
hold **eleven** stories. Four parallels-column entries were also counted
as stories, and Hebrew range labels (`כב ע"ב-כג ע"א`) were dropped.

Nothing errored. The file parsed, returned plausible Hebrew, and the
count was in the right ballpark.

The information needed to get it right was in the file the whole time.
Reading the OLE streams directly recovers the table (`0x07` terminates
each cell and again the row), so the four columns separate exactly, and
`PlcfandRef` gives every comment's **anchor position in the main text** —
so the notes attach to the passage Jeff was actually looking at, which is
the only form in which they are worth anything to `NEXT/08`.

**Rule:** when an artifact is ground truth, parse its native format. A
converter is lossy in ways that are invisible downstream: it discards
structure (tables, columns), relocates content (comments, footnotes), and
never says it did. Reach for `textutil`/`pandoc` output for *reading* a
document, never for *ingesting* one.

**Why:** the loss is silent and it lands in the denominator. A recall
number computed on 105 entries where 9 are not stories is wrong, and
nothing about the pipeline would have shown it — the same failure shape
as Lesson 21.

**How to apply:** (a) Validate a new parser against a known answer before
trusting it on new data — this one is asserted against Ketubot's
established 149, so a structural mistake fails loudly. (b) Cross-check
extracted text against an independent renderer character-for-character;
that check caught a retained annotation marker in 6 of 95 entries. (c)
When a count looks implausible on one key (81b with 11), treat it as a
parser bug until proven otherwise, not as a quirk of the data.
