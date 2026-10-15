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

- `index.json`, `<tractate>.json` — **derived** by `scripts/build_site_data.py` from `results/canonical/{ketubot,kiddushin,gittin}_canonical.json`
  and `results/v11/yevamot/yevamot_v11.json`. Each story: `id` (`tractate-daf-start-end`, from the golden's range), `ref`, `refs`, `tier`,
  `classification`, `reviewed`, `in_mishnah`, `extended`, `summary`, `segments[{ref,i,he,en}]`.
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
