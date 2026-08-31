# Clause-role labelling prompt — v2 (current)

Supersedes [`clause_roles_v1.md`](clause_roles_v1.md). Design and rationale:
[`docs/history/2026-08-30-PLAN-wave5b-clause-roles.md`](../../docs/history/2026-08-30-PLAN-wave5b-clause-roles.md).

**What changed from v1**
1. Added `parallel` — a different person's similar practice, or a second story.
   v1 wrongly told the model to call these `unclear`. 3.1% of clauses. Jeff
   excludes them (Kiddushin 30a clause 8, Rabbah bar Rav Huna).
2. Added `variant` — `אִיכָּא דְּאָמְרִי` "some say", an alternative version of the
   same story. Jeff **keeps** these (22b seg 18); both Wave 5 models wrongly cut it.
3. Added `speech` as a **boolean on every clause**, not a role — speech cuts across
   roles (a character speaking is story; rabbis debating is not). This is the field
   that makes Jeff's speech-act question computable.
4. Added **English sentence labelling** plus a `covers` alignment, so Hebrew and
   English labels can be checked against each other.

**Design rules held from v1**
- The model labels REAL UNITS and never emits a boundary or a number (Lesson 16).
- Rules are ABSTRACT PATTERNS from Jeff's language, never his specific passages
  (Lesson 8 — examples memorize, patterns generalize).
- `unclear` is a first-class answer so contested clauses surface.

---

## PROMPT

You are reading one segment of Talmud to work out which parts belong to a specific
story and which parts are the surrounding editorial material.

THE STORY YOU ARE LOCATING:
{summary}

THE SEGMENT IN HEBREW, split into numbered clauses:
{hebrew_clauses}

THE SAME SEGMENT IN ENGLISH, split into numbered sentences:
{english_sentences}

TASK: give every Hebrew clause and every English sentence a role and a speech flag,
and say which Hebrew clauses each English sentence covers.

ROLES

  narrative — part of THIS story. What happened, who did what, words spoken by the
              characters during the events, an emotional or internal reaction, and
              the ruling or reflection that RESOLVES the events. A ruling that
              settles what happened is the story's ending, not commentary on it.

  variant   — an alternative version of THIS SAME story ("some say...", "and some
              say it was..."). Still part of the story. Keep it.

  parallel  — a DIFFERENT story, or another person doing something similar
              ("Similarly, Rabbi X would also..."). Narrative in character but not
              part of this story.

  framing   — editorial lead-in that introduces the passage without being part of
              the events: a setup line, or a legal question posed to bring the
              story in.

  comment   — the Talmud analysing the story AFTERWARDS: asking what someone
              originally thought, questioning the story's logic, deriving a legal
              principle from it. The test is direction — narrative tells you what
              happened, comment discusses what happened.

  legal     — legal give-and-take that is not an account of a specific event:
              hypothetical cases, abstract argument, rabbis stating and contesting
              positions with nothing occurring.

  source    — a quoted authority cited as evidence: a baraita, a mishna, or a
              scriptural proof-text, including the continuation of one. A verse
              quoted BY A CHARACTER inside the events is narrative, not source.

  unclear   — you genuinely cannot tell. Prefer this over guessing.

SPEECH FLAG
  speech = true if the clause is someone speaking (dialogue, a quoted statement, a
  question put to someone). Independent of role: a character speaking during the
  events is narrative+speech; rabbis debating is legal+speech; a description of an
  action is narrative with speech false.

RULES
- Label EVERY Hebrew clause and EVERY English sentence. Use the given indices.
- Judge each unit in the context of the whole segment, not in isolation.
- Do not try to produce a tidy contiguous block. Say what each unit IS; the
  boundary is worked out afterwards.
- The English is a translation with explanatory words added by the editor. It will
  not line up one-to-one with the Hebrew. For each English sentence, list the
  Hebrew clause indices it covers.
- Editorial connectives in the English such as "The Gemara relates" or "The Gemara
  comments" are a hint about structure, NOT a rule. The same phrase sometimes
  introduces material that belongs to the story. Judge the content.

Return ONLY valid JSON:
{{"hebrew": [{{"i": <int>, "role": "<role>", "speech": <bool>}}, ...],
  "english": [{{"i": <int>, "role": "<role>", "speech": <bool>, "covers": [<int>, ...]}}, ...]}}

---

## Deterministic assembly (outside the model)

IN_STORY = {{`narrative`, `variant`}} — `variant` is included because Jeff keeps
"some say" alternatives as part of the story.

- **Rule A (`first_last`)** — boundary spans the first IN_STORY clause to the last.
  Tolerates an interruption mid-story rather than truncating at it.
- **Rule B (`longest_run`)** — the longest unbroken run of IN_STORY clauses.

They differ exactly when a `comment` or `parallel` interrupts. Test both against the
52 expert targets; do not choose by intuition.

Fallbacks: no IN_STORY clause at all -> keep the whole segment and flag it (never
trim to nothing). Any `unclear` at or next to a chosen edge -> emit the boundary and
flag for human review.

## Cross-language consistency check

Using `covers`, compare each Hebrew clause's own role against the role of the
English sentence covering it, collapsed to in-story vs not-in-story. Disagreement is
an error signal — no second model, no extra call, no expert time. Report the
disagreement rate; treat it as a review router, not a pass/fail threshold.
