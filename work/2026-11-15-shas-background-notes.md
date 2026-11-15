---
title: Background notes (and a "why it's here" line) for every story on the Septimus site
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [site/data/notes/, site/app.js, site/style.css, scripts/build_site_notes.py, scripts/approve_notes.py, scripts/draft_site_notes.py, src/prompts/site_note_v2.md, tests/test_site_notes.py, docs/findings/2026-10-12-septimus-note-flags.md]
finding:
superseded_by:
---

# Background notes (and a "why it's here" line) for every story on the Septimus site

**Self-contained.** A fresh session executes this with no other context.
Read [`docs/technical/septimus-viewer-plan.md`](../docs/technical/septimus-viewer-plan.md) §4 first, then this.

## The problem

The site has 1,897 stories in 37 tractates. Only 4 tractates have background notes
(the "Background: what's going on here?" box), from the October drafting round:

| | stories | have a note | approved |
|---|---|---|---|
| Gittin | 111 | 111 | 73 |
| Ketubot | 86 | 86 | 64 |
| Kiddushin | 52 | 52 | 36 |
| Yevamot | 85 | 72 | 44 |
| other 33 tractates | 1,563 | 0 | 0 |
| **total** | 1,897 | 321 | 217 |

Counted 2026-11-15 by joining `site/data/<t>.json` story ids to `site/data/notes/<t>.json`.
Recount before starting; the site data moves.

- Yevamot lost 13 notes when its v14 re-run changed story ids.
- `scripts/build_site_notes.py` hardcodes the 4 tractates (`TRACTATES = [...]`).
- The October drafting prompt and parts were never committed (they were in a cloud scratch dir).

**New: a "why" line.** Each note also says why the Gemara tells this story *here*: what
legal or aggadic point in the surrounding discussion it supports, illustrates or challenges.
It goes at the end of the Background box (decision 3). Answering it needs the text *around* the story,
not just the story itself, so the drafter is shown neighbouring segments as context.

## Decisions (Simon, 2026-11-15)

1. **Approval.** Simon spot-checked the October notes. A note ships `approved: true` if it
   passes the automatic checks and its drafter raised no flag (`approve_notes.py --all --unflagged`).
   Held notes stay draft, listed in `results/site_notes/held.json`.
2. **The 104 October notes that are not approved were never reviewed**, not rejected. They
   follow rule 1. In October Simon approved exactly the unflagged ones (0 of 69 flagged
   notes approved, bar one in Yevamot), so the 35 unflagged keep their text and are
   approved, and the 69 flagged are redrafted whole.
3. **The "why" goes inside the Background box**, as its last section ("Why is this story here?").
4. **Existing notes keep their text and only gain `why`.** Re-merging keeps `approved` only
   when `note` is unchanged, so this keeps every approval.

## Method

1. **Prompt, committed.** `src/prompts/site_note_v2.md`: the October output shape
   `{id, note, people[≤5], terms[≤4], flag}` plus `why` (1–2 sentences, ≤300 chars). Rules:
   answer from the text shown; name only people in the passage; `why` describes the
   *surrounding discussion*, never the halakha in the abstract; if the context does not
   show why, say so in `flag` and leave `why` empty, rather than guess.
2. **Drafter.** `scripts/draft_site_notes.py export|import`, the same export-to-files /
   subagent / import pattern as `scripts/judge_via_subagents.py` (no API key, Claude Code
   subagents). Each prompt holds the story's segments (Hebrew + English) plus ~3 segments
   before and after it from the tractate's cached Sefaria text (`scripts/tractates.py`
   `Paths`). About 20 stories per subagent, so ~80 subagents for the ~1,580 missing notes.
   Pilot first: 20 stories from 3 tractates, read by Simon, then the rest.
   *Audit for truncated passages over ~30 KB, as with the judge.*
3. **Builder.** `build_site_notes.py` reads every tractate in `site/data/index.json` rather
   than a hardcoded list, accepts `why`, and keeps the person-in-passage check. New checks:
   `why` ≤300 chars and no Hebrew/HTML. A note that fails a check is written as draft, not
   dropped. Flags are appended to `docs/findings/2026-10-12-septimus-note-flags.md`.
4. **Approval.** `approve_notes.py --tractate <t> --unflagged` (new flag) applies decision 1.
5. **Site.** `app.js` renders `why` as the last section of the Background box; check at 390px.
6. **Yevamot.** Redraft the 13 notes lost to the id change in the same run.

## How you know it worked

- Every story id in `site/data/*.json` has a note; a test (`tests/test_site_notes.py`)
  asserts there are no missing or unknown ids, for every tractate.
- Approved count = notes − flagged, per tractate; printed by the builder.
- 20 random new notes are read by Simon in the browser at `?notes=draft` before the bulk
  approval.
- A story page shows the "why" in the agreed place, at phone width (screenshot).
- `python3 -m pytest tests/ -q` passes (mind `reference_pytest_tests_shadowed`).

## Guardrails

- Never edit `results/canonical/*`, `scripts/evaluate_golden.py` or `STATUS.md`.
- A note never changes which stories ship. Flags are a second opinion for the project team,
  never a filter (L-045: gates narrow, never promote).
- Unapproved notes stay hidden from readers (the `?notes=draft` gate in `app.js` remains).
- The "why" must not claim more than the surrounding text shows; an empty `why` is better
  than an invented one.

## When done

Write the finding to `docs/findings/<date>-shas-background-notes.md`, add an `## Outcome`
section below, and `python3 scripts/board.py finish 2026-11-15-shas-background-notes`.
