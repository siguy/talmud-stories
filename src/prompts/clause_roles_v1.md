# Clause-role labelling prompt — draft v1 (SUPERSEDED, kept for history)

> **Out of date as of 2026-08-30.** v1 is missing four things settled after it was
> written: the `parallel` and `variant` roles, the `is_speech` flag, and English
> sentence labelling with the Hebrew/English consistency check. See
> [`tasks/PLAN_wave5b_clause_roles.md`](../../tasks/PLAN_wave5b_clause_roles.md)
> for the current design; v2 will supersede this file.
>
> v1's known bug: it tells the model to label a clause belonging to a DIFFERENT
> story as `unclear`. That is wrong — such clauses are not unclear, they are
> `parallel` (3.1% of clauses, e.g. Kiddushin 30a clause 8, which Jeff excludes).

Design rules this follows:
- The model labels REAL UNITS; it never emits a number or a boundary (Lesson 16).
- Labels are ABSTRACT PATTERNS drawn from Jeff's recurring language, never his
  specific passages (Lesson 8 — specific examples memorize, patterns generalize).
- The boundary is assembled deterministically from the labels, outside the model.
- `unclear` is a first-class answer, so contested clauses surface instead of being
  silently decided (Jeff's own stated preference for the database).

## Label taxonomy — every label traced to Jeff's own words

| Label | Jeff's language it comes from |
|---|---|
| `narrative` | "Stories are about events that happened"; "a rabbi's concluding reflection IS the story's closure"; "an emotional reaction… should be considered events" |
| `framing` | "the transition to the story"; "It should be adjusted to the story alone without the transition"; "a narrative setting does not make a story" |
| `comment` | "The last line is the Talmud's comment on the story and not part of the story itself"; "the Gemara's comment"; "the Talmud's question on the story" |
| `legal` | "There are no events. This is just a legal discussion"; "It is a hypothetical legal case"; "stating, objecting, asking questions are all part of a dialogue, and not really events" |
| `source` | "Section 14 is not part of the story. It is the end of the baraita" |
| `unclear` | Jeff: mark borderline cases and "let database users decide" |

---

## PROMPT

You are reading one segment of Talmud to decide which parts of it belong to a
specific story, and which parts are the surrounding editorial material.

THE STORY YOU ARE LOCATING:
{summary}

THE SEGMENT, split into numbered clauses (Hebrew):
{numbered_hebrew_clauses}

THE SAME SEGMENT IN ENGLISH (Sefaria's translation of this whole segment; use it
to understand meaning — it will not line up clause-for-clause with the Hebrew):
{segment_english}

TASK: label every clause with exactly one role.

  narrative — part of the story itself. What happened, who did what, speech
              spoken BY the characters during the events, an emotional or
              internal reaction, and the ruling or reflection that RESOLVES the
              events. A ruling that settles what happened is the story's ending,
              not commentary on it.

  framing   — editorial lead-in that introduces the passage but is not part of
              the events: a setup line, or a legal question posed in order to
              bring the story in.

  comment   — the Talmud analysing the story AFTER it: asking what someone
              originally thought, questioning the story's logic, or deriving a
              legal principle from it. The test is direction: narrative tells you
              what happened; comment discusses what happened.

  legal     — legal give-and-take that is not an account of a specific event:
              hypothetical cases, abstract argument, rabbis stating and
              contesting positions with nothing occurring.

  source    — a quoted authority cited as evidence: a baraita, a mishna, or a
              scriptural verse, including the continuation of one.

  unclear   — you genuinely cannot tell. Prefer this over guessing.

RULES:
- Label EVERY clause. Use the index numbers given.
- Judge each clause in the context of the whole segment, not in isolation.
- Speech is `narrative` when a character speaks inside the events, and `legal`
  when rabbis are debating rather than acting.
- If a clause contains a story that is plainly NOT the story described above,
  label it `unclear` rather than `narrative`.
- Do not try to produce a tidy contiguous block. Label what each clause is; the
  boundary is worked out afterwards.

Return ONLY valid JSON:
{{"labels": [{{"i": <clause index>, "role": "<label>"}}, ...]}}

---

## Deterministic assembly (outside the model)

1. Boundary = **first** `narrative` clause → **last** `narrative` clause.
   Tolerates an interruption mid-story rather than truncating at it.
2. No `narrative` clause at all → keep the whole segment untrimmed and flag it.
   Never trim to nothing.
3. Any `unclear` at or adjacent to a chosen edge → emit the boundary AND flag the
   story for human review.
4. Assert the resulting offset sits on a clause edge (already enforced in v11).

## Open questions to settle by testing, not by argument

- **Assembly rule**: first→last narrative, versus the longest unbroken run of
  narrative. They differ exactly when a `comment` interrupts a story. Test both
  against the 52 expert targets; do not pick by intuition.
- **`legal` vs `comment`**: both mean "trim", so the distinction may not earn its
  keep for boundaries. It is kept because it is the raw material for the
  false-positive classifier and for Wave 6.
- **English**: measure with and without. It doubles input cost and is untested as
  a help — it failed as a *verification* signal (0/8 on start boundaries).
