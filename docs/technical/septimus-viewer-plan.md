# Septimus family story viewer — full plan

*Written 2026-10-14. Tracking issue #62. Short version and handoff: `work/2026-10-12-septimus-story-viewer.md`.*

## 1. Purpose and audience

Daniel Septimus (former CEO of Sefaria) asked for the stories this project found in the tractates done so far,
in a form his family can learn from, in memory of his father, Joe Septimus, a Torah scholar.
Readers are **not scholars**, mostly on **phones**. It is a reading tool with a feedback door, not a review tool.
Success = Daniel opens it on his phone and reads a story end to end, and a mistake a reader spots lands where we
(and Claude) can act on it.

## 2. Decisions already made (Simon, 2026-10-12 unless noted)

| Decision | Choice |
|---|---|
| Tractates | Ketubot, Kiddushin, Gittin, **and Yevamot** (Yevamot has no expert round: shown as "not yet reviewed") |
| What counts as a story | Golden classification **YES + HIGH_CONFIDENCE**; **BORDERLINE** as its own tier; **LOW_CONFIDENCE not shipped**; NOT_A_STORY never |
| Mishnah-internal stories | Included, flagged (never shown to Jeff) |
| Authority | The golden decides what ships. A second opinion (note-drafters' flags) does not remove anything |
| Feedback | Inline per story and per passage, auto-filled, readable by Claude on submission; start simple |
| Boundaries | Cut-off stories may be widened **for display only**, by whole segments; the golden is never edited |
| Review/hosting | Simon reviews on a Vercel site called "Talmud Stories" (2026-10-13) |

## 3. Architecture

Static site, no backend of its own: `site/` = `index.html`, `style.css`, `app.js`, `config.js`, `vercel.json`, `data/`.
Hash routing (`#/`, `#/t/<tractate>`, `#/s/<id>`). Reads from `site/data/`:

- `index.json`, `<tractate>.json` — **derived** by `scripts/build_site_data.py` (never hand-edited) from the goldens of the
  reviewed tractates and the two v14 runs + judges of every other one. The contract is below.

### 3.1 The data contract (`site/data/schema/story.schema.json`, JSON Schema draft 2020-12)

Enforced by `tests/test_site_data.py::test_every_site_data_file_matches_the_schema`, which validates every tractate file
and `index.json` (`#/$defs/index`); `redirects.json` (`#/$defs/redirects`) by `test_story_id_registry_matches_the_site_data`. The schema forbids unknown story fields, so a dropped field cannot quietly return.
Readers: `site/app.js`, `worker/feedback-worker.js`, the planned sign-up app (`septimus-signup-plan.md`), analysis scripts.

**Tractate file** `{tractate, reviewed, stories[], out_of_scope[]}`. `stories` is what the site shows; `out_of_scope`
(biblical, R-S1, Simon 2026-11-13) is retained and never shown by default.

| Story field | Type | Meaning |
|---|---|---|
| `id` | string, `^<slug>-<daf>-<start>-<end>(-vN)?$` | **Permanent** identity from `site/data/story_ids.json` (below). Reads as the span it was *minted* with; never parse a span from it |
| `span` | `[{ref, start, end}]`, 1-2 pieces | The story's **current** source span (before any display extension); the registry records the same |
| `tractate`, `ref`, `refs[]` | slug; Sefaria refs | First page; every page the shown segments touch (1-3) |
| `start_segment` | int | Start segment of the source span on `ref` |
| `segments[]` | `{ref, i, he, en}`, all required | What the reader sees, after any display extension. `ref`+`i` locate a segment exactly |
| `summary` | string, may be `""` | One reader-facing sentence: detector/golden summary, else the same passage's in run 2, else `results/shas_run/site_summaries_written.json` (only where all are empty) |
| `classification` | `YES` / `HIGH_CONFIDENCE` / `LOW_CONFIDENCE` | Detector grade. **Data only — the viewer never shows it** (Simon 2026-11-14), and the feedback payload no longer carries it; triage looks it up by `id`. `LOW_CONFIDENCE` only via an `include` decision or a `promote` rule |
| `reviewed`, `in_mishnah` | bool | Tractate reviewed by Jeff; Mishnah story (always false today) |
| `extended` | `null` or `{start_back ≤2, end_forward ≤4, reason}` | Display-only widening of `span`; never changes the id |
| `words`, `minutes` | int ≥1 | English words shown; `ceil(words / readingWpm)` |
| `included_by` | string, **optional** | The `promote` rule that added it (`septimus_site_decisions.json`) |

`out_of_scope[]` entries have the same fields plus a required `out_of_scope_reason` (`"biblical (R-S1): <which gate>; …"`).
**Removed 2026-11-14 (Simon):** `tier` (always `"story"`), `biblical` (always false in `stories`), `biblical_reason`
(always null in `stories`; the reason lives in `out_of_scope_reason`), and the index's `borderline` count (always 0).

**`index.json`** `{reading_wpm, tractates[{tractate, name, he, reviewed, story, in_mishnah, out_of_scope, words, minutes}]}` —
`story` is the number of shipped stories. The home page reads only this file.

**Permanent story ids — built 2026-11-14** (`scripts/story_ids.py`, registry `site/data/story_ids.json`).
Before this an id *was* its span, so a golden correction, a re-run moving an end segment or a cross-page re-bounding gave
the same story a new id and orphaned its read-checkmark, feedback, extension, note and (planned) claim. Now an id is
minted **once** and kept. Every id that existed when the registry was created is exactly the old span id (all 1,847
shipped + 102 out of scope), so nothing already shipped changed; new ids are minted the same way from the span they are
born with (`-v2`, `-v3` if that string was ever used).
- Registry entry: `{tractate, status: active | redirect | retired, span, redirect_to?}`, one line per id, keys sorted,
  so an unchanged rebuild changes no byte. Covers shipped **and** out-of-scope stories (a story can move between them).
- Each build matches every story to the entry it **overlaps most by segments** (Lesson 36), largest overlap first, one
  story per entry. Shift → id kept, `span` updated. Split → the larger part keeps it, the other mints. Merge → the
  merged story keeps the id it overlaps most, the other becomes `redirect_to` it. Gone → `retired`, never given to
  another passage; the *same* passage returning revives its own id (its checkmarks come back). A redirected id is never
  revived. A tractate not built in a run is untouched.
- **A tie is refused**, naming the ids (one story overlapping two entries equally, or two stories one entry). Settle it
  by setting the winning entry's `span` in `story_ids.json` to the new span and rebuilding.
- `site/data/redirects.json` `{old id: current id | null}` (chains followed; `null` = retired) is derived each build.
  `site/app.js` loads it with `index.json`: a link to a merged id `location.replace`s to its successor, a retired id
  shows "no longer on the list", and a read-checkmark saved under a merged id moves to the successor (a retired one is
  kept, uncounted).
- Keyed by the permanent id: `boundary_extensions.json`, `notes/<t>.json`, `results/shas_run/site_summaries_written.json`,
  feedback (`story_id`; the worker's `ID_RE` accepts `-vN`) and the sign-up app's `claims/{storyId}`. An extension is
  relative to the span it was decided on, so when a story's span moves the build **does not apply** it and names it
  until it is re-decided. A note or extension keyed to a merged/retired id is named by the build, never re-keyed
  automatically.
- Tests (`tests/test_site_data.py`): registry ↔ data (every story active with its exact span; matching today's stories
  against the registry changes nothing; redirects valid), and a synthetic round trip (twice-built byte-identical, shift,
  split, merge, tie refused, retire, never reused, revival, chains, other tractates untouched).
- First live case, the same day: the 2026-11-14 golden fix of Ketubot 106a (2-3 → 3-3) keeps `ketubot-106a-2-3`, with
  its note and written summary, at span 3-3.
- **Display merges** (`septimus_site_decisions.json` `merge`, 2026-11-14): two cards joined into one would tie, so the
  build sets the `keep` entry's span to the merged span first (the documented tie settlement, from a recorded decision);
  the other member then `redirect`s to it. A member with a display extension is refused. The merged card takes the
  summary written for `keep`.
- `boundary_extensions.json` — display-only widenings: `{id: {start_back ≤2, end_forward ≤4, reason}}`.
- `notes/<tractate>.json` — AI-drafted background notes: `{id: {note, people, terms, approved}}`. **Shown only when `approved: true`**
  (or `?notes=draft` for reviewers).
- Hebrew already carries nikud in the cached Sefaria segments (asserted by tests); English is the William Davidson translation.
  Attribution to Sefaria is in the footer and links out to sefaria.org.

Per-reader state is `localStorage` only (read checkmarks, language, text size), wrapped in try/catch; the site works without it.

Feedback path: form on each story → `POST feedbackEndpoint` (Cloudflare Worker in `worker/`) → GitHub issue labelled
`story-feedback` with a JSON block. If no endpoint is configured, the form opens a pre-filled GitHub issue instead.

## 4. Status by phase

| Phase | What | State | PR |
|---|---|---|---|
| 1 | Data export + tests (counts vs the goldens) | **Done** | #61 |
| 2 | Mobile viewer (cards, daf lists, vowelled Hebrew/English, read tracking, Sefaria links) | **Done**, checked at 390px | #63 |
| 3 | Inline feedback + worker | **Built; worker not deployed** | #64 |
| 4 | Background notes (all 367 drafted, unapproved) + 40 display-only boundary extensions | **Built; nothing approved** | #66 |
| 5 | Publish (Vercel), dedication, hand to Daniel | **Not started** | — |

Counts shipped (YES+HIGH / borderline): Ketubot 87/13, Kiddushin 52/1, Gittin 115/4 (3 Mishnah), Yevamot 95/0 (5 Mishnah).

## 5. Remaining work, with acceptance criteria

### 5.1 Deploy a review site (Simon / local Claude)
- Vercel project `talmud-stories`, root `site`, framework Other, no build; preview URL for review (login-gated), production later.
- **Done when:** the site loads at phone width from the URL; a story page shows Hebrew with vowels and English; `?notes=draft` shows DRAFT-badged notes.

### 5.2 Review and approve notes (Simon, with Claude)
- Read drafts at `?notes=draft`. Approve per tractate or per story: `scripts/approve_notes.py`.
- Review priority: Yevamot (not expert-reviewed), stories carrying the "Extended" tag, the 90 still-flagged stories
  (`docs/findings/2026-10-12-septimus-note-flags.md`), then spot-check the rest (all 367 were AI-drafted from the full text of each story).
- **Done when:** every note shown to readers is approved; unapproved ones remain hidden. No note states a generation, teacher or
  relationship that the text does not support.

### 5.3 Decide the 40 boundary extensions (Simon)
- Keep, or delete entries from `boundary_extensions.json` and rebuild. Least certain: the 6 start extensions (e.g. `yevamot-77a-0-0`) and
  `yevamot-102a-7-8`.
- How much of a story's end to show is still Jeff's open question (`jeff:boundary-end-rule`); these are readability choices, not rulings.

### 5.4 Deploy the feedback worker (Simon: needs his accounts)
- Steps in `worker/README.md` (fine-grained GitHub token, Issues read/write on this repo only; Cloudflare free tier; set `REPO`, `ALLOWED_ORIGIN`).
- Put the URL in `site/config.js` (`feedbackEndpoint`); redeploy.
- **Done when:** a test submission from the site creates an issue with label `story-feedback`, the story id, and (for a passage) its exact ref/index and text.
- Keep the repo private (feedback can contain names), or tell people not to leave contact details.

### 5.5 Dedication and copy (Daniel)
- Replace the placeholder ("In memory of Joe Septimus.") in `site/app.js` with Daniel's wording; confirm he is comfortable with
  the Sefaria-inspired look (no Sefaria logo or assets are used).

### 5.6 Publish (Simon)
- Merge the PRs in order (#61 → #63 → #64 → #66) or set the Production Branch; share an unlisted URL with Daniel. `noindex` is already set.
- **Done when:** Daniel has read a story on his phone and knows how to report a problem.

## 6. The feedback loop after launch

1. A reader submits → issue `[Feedback] <ref> segment <n>: <category>` appears, labelled `story-feedback`, `tractate:<name>`.
2. Claude triages from the issues: translation/Hebrew problems → source issue (Sefaria text), logged; "not really a story" / boundary problems → recorded
   for Jeff as an annotation, **never edited into the golden** (STORY_RULES: his lists are evidence); typos in notes → fix the note.
3. Fix = edit `site/data/notes/*.json` or `boundary_extensions.json` and rebuild; reply on the issue and close it.
4. Periodically bring the boundary and "not a story" items to Jeff with the story ids.

## 7. Quality gates

- `python3 -m pytest tests/test_site_data.py tests/test_bookkeeping.py -q` must pass: shipped counts equal the goldens' YES/HIGH/BORDERLINE counts
  (stories + `mishnah_stories`), every segment has Hebrew and English, Hebrew has nikud, every story has a note and none ships unapproved,
  extensions are bounded (≤2 back, ≤4 forward) and reference real stories, the worker rejects malformed input.
- Verify with **counts**, never the composite score (CLAUDE.md rule 5). Never edit `results/canonical/*` or `scripts/evaluate_golden.py`.
- Real-browser check at phone width before saying any UI change works (CLAUDE.md rule 1).
- The wider suite has 16 failures identical on `main` (missing files/modules in the cloud container); not ours.

## 8. Risks and how each is handled

| Risk | Handling |
|---|---|
| AI-drafted notes misstate something | Hidden until approved; drafts were written from each story's full text; people's descriptions limited to what the text supports; footer says "written with AI" and links to Report a problem |
| Yevamot unreviewed by Jeff | Labelled "not yet reviewed" on the card, list and story; Simon may drop it |
| Mishnah stories unreviewed | Labelled; same |
| Widened passages differ from what Jeff reviewed | "Extended" tag with explanation; display-only; deletable per story |
| Some golden stories end mid-sentence (data issue in the golden's segment ranges) | Handled by the 40 extensions; the remaining 90 flagged stories are listed for Jeff; nothing silently altered |
| Feedback endpoint abused | Honeypot field, input whitelist and length caps in the worker; token limited to Issues on one repo; rate limiting not yet added (add Cloudflare rate-limit rule if spammed) |
| Feedback token expires | Calendar reminder at creation (1-year expiry); form falls back to a GitHub-issue link if the worker fails |
| Public URL exposes drafts via `?notes=draft` | Unlisted + `noindex`; acceptable for review; remove the flag path or password-protect before wide sharing if drafts remain |
| Sefaria terms | Attribution in footer and link-outs; confirm the William Davidson edition's CC BY-NC terms suit a non-commercial family site; ask Daniel |
| Repo public → feedback issues public | Keep the repo private or move feedback to a separate private repo |

## 9. Open questions

1. Daniel's dedication wording and whether he wants a name/byline on the site.
2. Keep Yevamot in the first release, or hold it until reviewed?
3. Which of the 40 extensions to keep (Simon's review).
4. Hosting beyond review: Vercel production domain, or a custom domain Daniel prefers?
5. A glossary page and a "what is the Talmud" intro page for newcomers (not built; optional).
6. Should read-progress sync across devices? Today it is per device; sync would need accounts or a backend, which this plan deliberately avoids.

## 10. Not in scope

Editing the goldens; running the detector on new tractates; Eruvin (blind list exists, no detector run, no review); accounts or logins;
search; audio; analytics (none collected today).
