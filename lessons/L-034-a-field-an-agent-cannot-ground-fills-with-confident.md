# Lesson 34 — A field an agent cannot ground fills with confident noise

**2026-08-31**

The first draft of the work-item schema had twelve frontmatter fields, including `kind`
(measure / diagnose / fix / build / decide / record) and `feeds_back_to` (which
capabilities' gates this work changes). Both had careful justifications. Review cut the
schema to six.

The evidence that they would have gone wrong was already on disk:

- `tasks/NEXT/02_ketubot_77a.md` carried **"Capability: 2 Detection"**, stated plainly at
  the top. Commit `abdc4af` — *"Correct the 77a diagnosis: Classification, not
  Detection"* — overturned it. The label had been written confidently at the moment the
  brief was opened, when establishing that very diagnosis was the entire point of the
  brief.
- `feeds_back_to` would have had **zero instances**. Every worked example involved
  Publication, which has no metric defined and no work started.

The failure mode is specific to who does the writing here. A person who does not know a
field's value tends to leave it blank. An LLM session does not — it produces a plausible,
well-formed, confident value. **A blank looks like a gap and gets investigated. A confident
wrong value looks like data and gets built on.**

**Rule:** do not add a field whose correct value the writer cannot know at the moment they
must first write it. If the honest answer is "they'll find out later," the field must stay
editable and **nothing may key off it** — which is why capability lives in the frontmatter
and not in the filename or the branch name.

**Why:** essentially all work in this repo is done by LLM sessions, so every taxonomy field
is a place where fluency substitutes for knowledge. The six surviving fields are all things
the writer genuinely knows when they open an item — the title, which tractate, what blocks
it — or that are explicitly editable. That is the whole reason the schema is small, and it
is written down here so it does not get quietly re-expanded by someone who only sees six
fields and thinks the model is thin.

**How to apply:**
(a) For each proposed field, ask: **at the moment this is first written, does the writer
actually know it?** Not "could they guess well" — know.
(b) **A field with no current instances has no evidence it is right.** Wait until there are
three real cases, then design it from them.
(c) **Prefer prose to a new enum.** Vague prose reads as vague; a wrong enum reads as
certain. `## Outcome` carries the reasoning precisely because a generated table cell
cannot.
(d) The same test applies to anything an agent fills in: a confidence label, a category, a
severity. Ask what it costs when it is confidently wrong, then decide whether the field
earns its place.
