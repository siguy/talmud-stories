# Lesson 12 — Most boundary feedback is text-internal, not segment-level

**2026-05-24**

**Context:** Wave 2 implemented Issue #3 (start-boundary snap) and Issue #4
(end-boundary trim) as deterministic segment-level post-processors. On audit
of all 16 boundary cases Jeff flagged on Kiddushin: every single one is
text-internal — the introducer Jeff wants the story to start at, or the
commentary he wants trimmed, sits INSIDE the start/end segment, not in a
separate adjacent segment. Segment-level snap/trim cannot reach these.

**Rule:** Before designing a mechanical post-processor, audit the actual
evidence at the granularity the post-processor operates on. If feedback is
"the story should start with X" and X is in the SAME segment as the detector's
start, no segment-level fix will help — you need sub-segment text editing or
a re-segmentation pass.

**Why:** Wave 2's snap-forward fired 0 times and trim fired 0 times because
of this mismatch. The only post-processor that landed real wins (3 biblical
demotions + 3 extend-back snaps) was the biblical-actor filter and the
"introducer in the segment BEFORE detector's start" extension — neither of
which were in Jeff's flagged-case list. The flagged cases will require Wave 3
text-level changes.

**How to apply:** When the user reports "the story should start at X" with X
quoted in Hebrew, immediately check whether X is in the same segment the
detector picked. If yes, route to text-level work; if no, segment-level
post-processing can address it.
