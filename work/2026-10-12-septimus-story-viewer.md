---
title: Story viewer for the Septimus family (mobile, Sefaria-style)
capability: [publication]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [site/, scripts/build_site_data.py, docs/findings/2026-10-12-septimus-viewer.md]
finding:
superseded_by:
---

# Story viewer for the Septimus family (mobile, Sefaria-style)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The problem

Daniel Septimus (former Sefaria CEO) asked for the stories we found, from the tractates
done so far, in a form his family can learn from, in memory of his father Joe Septimus.
Audience: non-scholars, phones. Not a review tool; a reading tool with a feedback door.

## Phases

**Phase 0 — Decisions (before any code).** See "Open questions" below.

**Phase 1 — Data export (DONE 2026-10-12).** `scripts/build_site_data.py` reads the goldens
(`results/canonical/{ketubot,kiddushin,gittin}_canonical.json`) and writes one static
`site/data/<tractate>.json` plus an `index.json`.
- Ship YES + HIGH_CONFIDENCE as "story", BORDERLINE as its own tier; LOW_CONFIDENCE not shipped; Mishnah-internal stories included, flagged.
  "Possible stories" tier (or omitted — Phase 0 decision). `NOT_A_STORY` never ships.
- Each story: id, tractate, daf/amud, segment range, Hebrew (with nikud), English,
  title/one-line summary (if absent: generate, then mark as machine-written).
- Must copy `page_segments` and decide `mishnah_stories` explicitly (CLAUDE.md data rule).
- Hebrew with vowels: Sefaria's *William Davidson Edition – Vocalized Aramaic* via the
  Sefaria API, fetched at build time and cached. Check license/attribution (CC-BY-NC) and
  that every golden segment aligns to a vocalized segment; report coverage, don't assume.
- Test: counts per tractate printed and asserted against `GOLDEN_COUNTS`, never the
  composite (Critical Rule 5).

**Phase 2 — Viewer MVP (~1 day).** Static site, no backend, mobile-first.
- Home: four tractate cards, with story counts. List: stories by daf, with title, read ✓.
- Story page: Hebrew (vowelled) over English, toggle Hebrew / English / both, text-size
  control, prev/next story, link out to the full daf on sefaria.org for context.
- Sefaria visual language (own CSS, no Sefaria assets/logo): serif Hebrew, clean
  reading column, tractate-colour accents, light/dark. We imitate the feel, not the brand;
  confirm with Daniel (Phase 0).
- Read-tracking: `localStorage` checkmarks per story + "N of M read" per tractate.
  Per-device only (state this on the page); no accounts.
- Acceptance: opened in a real browser at phone width, Hebrew + English visible, story
  highlighted within its daf (Critical Rule 1), screenshot attached to the finding.

**Phase 3 — Feedback (~half day plus hosting).** Per story: "Report a problem"
(wrong text / not really a story / story cut off or too long / translation unclear) +
free-text + optional name. Needs somewhere to send it: Google Form prefilled with the story
id (zero backend, recommended), or a small hosted endpoint. Every submission carries
`story_id`, `tractate`, `detector_version`, `schema_version`. Feedback lands in a sheet we
triage by hand and feed to Jeff — it is **not** auto-ingested into any golden.

**Phase 4 — Learning layer (optional, later).** Short plain-English "what's going on"
note per story, glossary of terms on tap, "Rabbi X says Y" speaker labels. LLM-drafted,
labelled as such, reviewed by Simon (and Jeff if he'll look) before it ships.

**Phase 5 — Publish.** Static host (GitHub Pages / Netlify / Cloudflare Pages) on an
unlisted URL; dedication page for Joe Septimus, worded by Daniel.

## How you know it worked

- Story counts on the site equal the golden's non-`NOT_A_STORY` counts per tractate.
- Every shipped story shows Hebrew with vowels and English; zero blank segments.
- Daniel opens it on his phone and reads one story end to end.
- A feedback submission arrives with its story id.

## Guardrails

- Goldens are read-only here; the site is a derived artifact, rebuilt by script.
- Never ship a story Jeff marked `NOT_A_STORY`. Say plainly on the site that stories were
  found by software and checked by a scholar, and which are not yet checked (circular vs
  blind distinction stays internal; the public wording is "reviewed" / "not yet reviewed").
- Sefaria text: attribute source and version, honour the license, link back.
- Ask Daniel before using any Sefaria name/logo/trade dress.

## Open questions (Phase 0)

1. Which four? Ketubot, Kiddushin, Gittin have goldens. Yevamot has detection but no
   expert round — include as "not yet reviewed", or hold until reviewed?
2. "Definitely stories" = Jeff-YES only, or also BORDERLINE (shown as a separate tier)?
3. Hosting + feedback: Google Form on an unlisted GitHub Pages URL OK for v1?
4. Does Daniel want a dedication to Joe on the front page, and in what words?
5. Is a "learning note" per story (Phase 4) wanted in v1?

## When done

Write the finding to `docs/findings/2026-10-12-septimus-viewer.md`, add `## Outcome`,
then `python3 scripts/board.py finish 2026-10-12-septimus-story-viewer`.

---

## Handoff to a local Claude (written 2026-10-14)

**State:** Phases 1–4 are built. Stacked draft PRs: #61 (plan + data) → #63 (viewer) → #64 (feedback) →
#66 (notes + boundary extensions, branch `septimus/phase-4-notes`, has everything). Tracking issue: #62.
The site is static, in `site/`; `python3 -m http.server` from there runs it. Tests: `python3 -m pytest tests/test_site_data.py tests/test_bookkeeping.py -q`.
The wider suite has 16 failures that are identical on `main` (missing files/modules in the cloud container), not ours.

**Do, in order**
1. **Vercel (needs the user's login):** `cd site && npx vercel` → project name `talmud-stories`, framework Other, no build.
   `npx vercel --prod` for production. `site/vercel.json` already sets noindex. Prefer a preview URL for review.
2. **Feedback worker (user's Cloudflare + GitHub accounts):** follow `worker/README.md`; then set `feedbackEndpoint`
   in `site/config.js` and redeploy. The worker files issues labelled `story-feedback` (JSON block inside).
3. **Review with the user** at `<site>/?notes=draft`. Notes ship only when `approved: true`:
   `python3 scripts/approve_notes.py --tractate ketubot` or `--ids <id> ...` (`--revoke` undoes).
4. **Decide the 40 display-only boundary extensions** (`site/data/boundary_extensions.json`, one entry per story).
   Delete an entry and rerun `python3 scripts/build_site_data.py` to drop it. Least certain: the 6 with `start_back: 1`
   (e.g. `yevamot-77a-0-0`) and `yevamot-102a-7-8`. Extensions are display-only; the golden is never edited, and how much
   of a story's end to show is Jeff's open question (`jeff:boundary-end-rule`).
5. After changing notes or extensions, rebuild: `python3 scripts/build_site_data.py`; for notes, `scripts/build_site_notes.py <parts_dir>`
   (the drafting parts were in a cloud scratch dir and are NOT in the repo; edit `site/data/notes/<tractate>.json` directly instead).

**Still open (the user's call):** Daniel's dedication wording (placeholder in `site/app.js`, "In memory of Joe Septimus.");
whether to keep Yevamot (shown as not reviewed); 90 stories the note-drafters flagged as possibly cut off / not stories
(`docs/findings/2026-10-12-septimus-note-flags.md`: the golden still decides what ships, flags are a second opinion).

**Rules that bind this work:** never edit `results/canonical/*` or `scripts/evaluate_golden.py`; do not rewrite `STATUS.md`;
verify with counts not the composite score; ship set = classification YES + HIGH_CONFIDENCE, BORDERLINE as its own tier,
LOW_CONFIDENCE not shipped, Mishnah-internal stories included and flagged (user decisions, 2026-10-12).
