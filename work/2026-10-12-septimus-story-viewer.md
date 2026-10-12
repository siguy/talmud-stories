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
