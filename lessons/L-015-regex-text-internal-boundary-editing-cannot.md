# Lesson 15 — Regex text-internal boundary editing cannot generalize

**2026-06-03**

**Context:** Wave 3 Item 4 (`edit_text_internal_boundaries`) used a
hand-built regex set to identify story-vs-framing inside the first/last
segment — markers like ההוא ד / ההיא at the start, אלא / rabbi-name
patterns at the end. Audit was 10/17 pass on Jeff's flagged cases.
Jeff's 2026-06-03 reply on the shipped Item 4: it worked on 5 of the
canonical ההוא/ההיא openers, but on 7 OTHER stories the same kinds of
markers (אלא, rabbi names) WERE the story content — and the regex
chopped them out. Jeff's diagnosis verbatim: *"crude criteria, such as
the word אלא or a rabbi's name automatically signalling the story's
end."* Net change in golden agreement: ~0 (recovered cases cancel new
over-trims).

**Rule:** Stop building deterministic regex post-processors for
text-internal semantic decisions. Surface markers (אלא, rabbi names,
תניא, מעשה ב, ההוא) are diagnostic of structure 30-50% of the time and
of story content the other 50-70%. Only a model that reads the
surrounding meaning can tell them apart.

**Why:** Our audit looked at 17 hand-picked cases drawn from Jeff's
prior boundary corrections — which biased the sample toward cases the
regex was implicitly built to fit. The 7 new failures came from
ordinary stories outside that sample, where the same markers play a
content role. Audit precision on the hand-picked sample doesn't
predict precision in the wild — same pattern as Lesson 9.

**How to apply:** When sub-segment text decisions need to be made,
either (a) emit the slice from the LLM during the detection pass with
an explicit `text_span_start` / `text_span_end` schema, or (b) skip
the slice entirely and let segment-level boundaries stand. Do NOT add
a regex post-processor; you'll move score 0 net while introducing
silent over-trims.
