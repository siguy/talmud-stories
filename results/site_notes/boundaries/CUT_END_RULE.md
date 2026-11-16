# How a cut story-end is sorted (written 2026-11-15, before any calibration result was read)

Used by the calibration of the full boundary review (`docs/history/2026-11-15-PLAN-full-boundary-review.md`, step 3,
metric B). The sorter is a different model from the reviewer (Simon, Decision 5). Simon reads the `lost` pile.

You are shown one story whose end a reviewer moved earlier than the end in Jeff Rubenstein's 2005 story list.
`kept_end` is the last segment(s) the site would still show; `cut` is every segment the reviewer removed that Jeff's
list still included. Put the case in exactly ONE pile:

- **fine** -- everything cut is the Gemara's discussion: a question on the story, a proof drawn from it, a
  comparison with a mishna or baraita, other sages' opinions about it, the lesson or *halakha* the Gemara derives.
  Jeff's 2005 list ran on into discussion, and for ends it is an upper bound (rule R-B2, `docs/STORY_RULES.md`).
- **ruling** -- the cut includes a ruling that is the **outcome of the events**: the verdict a judge or sage gave in
  this very case, or what he told the people in the story to do, *and nothing narrative*. Simon's rule (Decision 2)
  is to keep such a ruling, so this counts against the reviewer's rule-following, but it is not lost narrative.
  (Jeff's own answer, `jeff:boundary-end-rule`, is open.)
- **lost** -- the cut includes any **event of the story**: something a character did or said in the story's own
  action (not a sage commenting afterwards), the story's resolution, a second scene of the same incident. One such
  segment is enough. **When unsure between ruling and lost, choose lost.**

Answer, for each case: `{"<key>": "fine" | "ruling" | "lost"}` plus a one-line reason in a separate `reasons` object.
