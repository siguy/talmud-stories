# Lesson 17 — Feedback and lessons must be durable gates, not passive notes

**2026-08-28**

This session repeated two already-recorded mistakes: (1) Lesson 9
(fixture ≠ production) — Wave 4 shipped on 14/14 hand-picked fixtures
and then failed 11/15 in the wild; (2) memory
`feedback_boundary_corrections.md` ("never split feedback processing
again") — yet Jeff's feedback was again processed partially and the
nuance nearly lost. The lessons existed and did not prevent
recurrence, because a lessons file is a passive record only consulted
if someone remembers to.

**Rule:** Every substantive piece of expert feedback goes into a
durable, status-tracked ledger the moment it arrives
(`validation/feedback/jeff_<date>_feedback_ledger.md`), and every
recurring lesson gets converted from prose into an **executable gate**
where possible.

**Why:** Feedback scattered across emails, JSON, .docx, and
conversation gets processed once, partially, then lost on the next
context clear. The cost is real: Jeff repeats himself and trust
erodes.

**How to apply:** (a) On any expert reply, create/append the ledger
FIRST, before analysis or code — one row per note, with status
open/addressed and where addressed. (b) Turn key lessons into gates:
no detector ships without scoring on a FRESH held-out sample (not its
own fixture); build a criteria-conformance test from
`docs/findings/2026-07-06-jeff-story-definition-criteria.md`; assert
structural invariants (Lesson 16's clause-boundary check). (c) Before
replying to the expert, walk the ledger's open-items tracker so
nothing is dropped.
