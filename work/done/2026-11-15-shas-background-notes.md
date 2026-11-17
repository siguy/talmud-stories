---
title: Background notes (and a "why it's here" line) for every story on the Septimus site
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [results/site_notes/, scripts/review_site_boundaries.py, scripts/build_site_data.py, site/data/, results/shas_run/septimus_site_decisions.json, results/shas_run/site_summaries_written.json, tests/test_site_data.py, site/index.html, .gitignore, site/data/notes/, site/app.js, site/style.css, scripts/build_site_notes.py, scripts/approve_notes.py, scripts/draft_site_notes.py, src/prompts/site_note_v2.md, tests/test_site_notes.py, docs/findings/2026-10-12-septimus-note-flags.md]
finding:
superseded_by:
---

# Background notes (and a "why it's here" line) for every story on the Septimus site

**Self-contained.** A fresh session executes this with no other context.
Read [`docs/technical/septimus-viewer-plan.md`](../../docs/technical/septimus-viewer-plan.md) §4 first, then this.

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
Recount before starting; the site data moves. *(Main moved to 1,811 stories with permanent ids on 2026-11-15; the run used those.)*

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

## Outcome

Done 2026-11-15. **Every story on the site has a note: 1,811 of 1,811; 1,805 carry a `why`; 1,651 approved, 160 held.**
Counts from `python3 scripts/build_site_notes.py --report`, asserted by `tests/test_site_notes.py`.

- **How.** Two pilots before the run. Pilot 1 (20 stories): the `why` repeated the note on legal stories, so the prompt
  split the jobs (note = the story, why = the frame). Pilot 2 (30 stories, 13 tractates) was checked against the text
  by an independent subagent: 27/30 fine, 28/30 whys add something. Its three faults became prompt rules: keep the text's
  force ("kill", not "deal with"), credit the right speaker (a Sage vs the Gemara), no outside facts about people.
  Then 90 subagent batches of 20 (`results/site_notes/shas1/`), 0 invalid answers, every story code matched.
- **Why the plan review mattered.** It caught that this branch was behind main (1,897 stories, a `tier` field main had
  dropped), and that answers were filed by file number only, so one skipped file would have shifted a batch's notes onto
  the wrong stories. Fixed by merging main and by a story code each answer must repeat.
- **Approval** (Simon): spot-checked October notes keep their text and gain only a `why`; everything that passes the
  checks and is unflagged is approved. A drafter flag marks the passage for the team (`passage_flags.json`, listed in
  `docs/findings/2026-10-12-septimus-note-flags.md`) and holds a never-reviewed note.
- **Held, 160:** 149 drafter flags (story cut off, two passages joined, mostly legal argument) and 11 where the note
  names someone who appears only in the surrounding discussion. These are questions about story boundaries as much as
  about notes; they stay draft until someone reads them.
- **Seen in passing, not fixed here:** Ketubot 2b and 3a tell the same ferry story twice; several flagged pairs are
  one story split across two site entries (e.g. Rav Yehuda and Rav Nahman's court case).

### Follow-up, same day: boundaries fixed (Simon 2026-11-15)

Simon: drop the legal argument, finish cut-off stories, a person from the surrounding discussion is fine
background, two cards that are really one story become one. **Now 1,804 stories (7 merged), every one with a note;
1,739 approved, 65 held.**

- `scripts/review_site_boundaries.py`: the 154 flagged passages, each shown with 5 segments either side and which
  other site story owns them, went to 8 subagent reviewers: 43 keep, 94 adjust, 12 merge (incl. 5 pairs the reviewers
  described as one story but could not merge across a 1-2 segment gap; a merge may now bridge up to 2 segments).
  Applied as display-only boundaries: 99 stories widened, 27 trimmed (new `start_trim` / `end_trim` in
  `boundary_extensions.json`, schema and build), 7 merges in `septimus_site_decisions.json`. 3 refused and left as
  they were (an extension of 5, a pair 4 apart, a story nested inside another); Bava Batra 58a's merge dropped
  because two site cards overlap there.
- The 98 stories whose text changed were redrafted (`results/site_notes/bfix1notes`), merged cards got a written
  summary from their note's first sentence.
- The name check is a printed warning, not a hold (14 warnings).
- **Still held, 65:** passages a fresh reader still doubts after the review -- mostly two incidents joined (needs a
  split, which the site cannot do) or a story whose events sit outside the passage. Listed in
  `docs/findings/2026-10-12-septimus-note-flags.md`. Reviewers named two that look like no story at all
  (`bava_kamma-51a-0-0`, `nazir-20a-1-2`); they still ship, without an approved note.
- Word pins in `tests/test_site_data.py` moved with the boundaries (Ketubot -1,902 words: trimmed argument).
