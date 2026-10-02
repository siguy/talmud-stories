---
title: Move the public project page to the Vercel hub, current and in plain language; retire GitHub Pages
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [index.html, approach.html, history.html, validation.html, docs/findings/, ../../../../simonbrief-hub/app/page.tsx, ../../../../simonbrief-hub/app/talmud-stories/, ../../../../simonbrief-hub/public/projects/]
finding: docs/findings/2026-10-02-public-site-moved-to-hub.md
superseded_by:
---

# Move the public project page to the Vercel hub; retire GitHub Pages

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then [`STATE.md`](../../STATE.md) and the top of
[`STATUS.md`](../../STATUS.md), then this.

## The problem

Two public surfaces describe this project, and both describe the project of **February 2026**.

| surface | where it lives | what it says today |
|---|---|---|
| Hub card | `~/simonbrief-hub/app/page.tsx` (Next.js on Vercel, project `simonbrief`) | "222 pages analyzed, 153 stories found, 92.1% accuracy" — links out to GitHub Pages |
| Project site | GitHub Pages, `main` `/` of this repo: `index.html`, `approach.html`, `history.html`, `validation.html` | v7/v8, one tractate, "96.3% accuracy", the 2-event triage rule, boundary trimming, history ends Feb 2026 |

GitHub Pages has not deployed since 2026-05-25. Every build since has errored, so the
2026-08-30 edits to `index.html` were never live. **That is no longer worth fixing.
Decision (Simon, 2026-10-02): retire GitHub Pages; the project lives on the Vercel hub.**

### What is out of date in the content

- **A single "accuracy" figure** stands in for what we now measure separately. The old
  92.1% / 96.3% were expert agreement on passages the detector proposed. That measures
  how often we're right when we say "story", not how many stories we find. The unpublished
  2026-08-30 "96%" uses the retired 4-gram matcher and must not be published.
- **Scope:** one tractate on the site; now five expert lists, four tractates detected.
- **Pipeline:** missing the twin pass, the rule register (`docs/STORY_RULES.md`) and the
  Mishnah filter. It still shows boundary trimming (reverted) and the "2+ narrative
  events" triage rule (now 1+).
- **History** ends in Feb 2026. **Validation** describes the old YES/HIGH/LOW review.

## Decisions (Simon, 2026-10-02)

1. **Numbers are typed in by hand**, each with an as-of date. No generator, no test.
2. **Publish the twin-pass result as one number** (Yevamot, rounded, labelled
   "with the new second pass"). Take it from the twin-pass and determinism findings on
   publish day, not from this item.
3. **The audience is general readers.** Plain language throughout. No BLIND/CIRCULAR or
   capability jargon on the page; that precision goes in a short "how we measured"
   footnote.
4. **No GitHub Pages.** New page(s) on the Vercel hub.

## Method

Stop and show Simon after steps 2, 4 and 6.

1. **Set up the hub safely.** `~/simonbrief-hub` has **uncommitted work on
   `feat/homepage-polish` that touches `app/page.tsx`**, which is not ours. Do not edit that
   checkout. Use `git worktree add` from `main` on a new branch
   `feat/talmud-stories-page`. Coordinate with Simon on the card edit if his branch merges first.
2. **Page structure.** Proposed: **one page, `/talmud-stories`**, matching the existing
   project subpages (`app/seder-remixed/page.tsx` is the template: same eyebrow/heading,
   FadeIn sections, back link, palette). Sections:
   1. *What this is.* Stories hidden inside the Talmud's legal debate, with no index.
   2. *How it works.* Five plain steps: skim each page for events → ask the AI which
      passages are stories → a second look beside each story found for its "twin" →
      tidy start and end → join stories split across pages. Use the R. Zadok / Rav Kahana
      pair as the one worked example.
   3. *How well it works.* Three numbers in plain words, as of a date:
      - **How many we find:** share of the stories on Prof. Rubenstein's own 2005 lists
        (written 20 years before this tool) that it finds. One figure per tractate, or a
        range. Add the twin-pass figure as one number.
      - **How often "story" is right:** classification precision (~0.92–0.95 as re-read
        2026-09-29). Re-check on publish day.
      - **How often the edges are right:** boundary hit rate.
   4. *How an expert keeps it honest.* Jeff reviews the results. His rulings become
      written rules in his own words. Next is two different AI models judging every
      passage, with Jeff seeing only the passages where they disagree. Say plainly that
      this is planned and the first test was a no-go, and why.
   5. *What we got wrong along the way.* Three or four short stories, told as lessons:
      measuring agreement instead of what we missed, retracting the no-triage ablation,
      the search window that flattered recall, and finding that the detector isn't
      perfectly repeatable.
   6. *Team & credits.* Carry over from `index.html` as written.

   Show Simon this outline before writing copy.
3. **Copy, by hand.** Read every figure from `STATE.md` and the named findings on
   publish day. Put an "as of <date>" line under the numbers and a 3–4 line "how we
   measured" footnote. Old figures appear only in section 5, labelled as history.
4. **Build it.** Add `app/talmud-stories/page.tsx`. Point the homepage card's `link` at
   `/talmud-stories`. Rewrite the card description in one plain sentence using the
   same headline number. Refresh `public/projects/talmud-stories.png` only if Simon wants
   it. Then `npm run build`. Preview with the dev server and check desktop and 375px,
   no console errors, all links.
5. **Show Jeff** every sentence that quotes or characterises him, before deploy.
6. **Deploy.** Merge in the hub (Vercel deploys on push). Confirm live `/talmud-stories` and the card.
7. **Retire GitHub Pages**, only after step 6 is live:
   - Check that no open review is waiting on a Pages URL. The last sent link was
     `comms/sent/2026-06-03-email-jeff-wave3-round2.md`; confirm that round is closed.
   - Replace `index.html` with a one-line redirect to the Vercel page. Delete
     `approach.html`, `history.html` and `validation.html`; git keeps them.
   - Disable Pages: `gh api -X DELETE repos/siguy/talmud-stories/pages`. **This is
     outward-facing; confirm with Simon first.** After this, old review links in sent
     emails stop resolving. That's expected; note it in the finding.
   - Update the docs that cite Pages URLs: `docs/technical/VERSION_HISTORY.md`,
     `docs/communication/*`. Leave `comms/sent/` alone; it's the record of what was sent.
8. Write `docs/findings/<date>-public-site-moved-to-hub.md`: what moved, which numbers
   were withdrawn and why.

## Progress

- 2026-10-02: steps 1–4 done. Hub branch `feat/talmud-stories-page` (worktree
  `~/simonbrief-hub-talmud`, commit ec11836) adds `app/talmud-stories/` and repoints the
  card. Builds; checked in the browser at desktop and 375px with no console errors and no
  horizontal scroll. **Not pushed.** Next: step 5 (Jeff sees the [Jeff] sentences), then
  step 6 (deploy).
- Copy as built: `docs/brainstorms/2026-10-02-public-page-copy.md`, plus one addition:
  Hillel ran ahead himself "for three mil" (Ketubot 67b seg 2, real text).
- The hub's existing `app/page.tsx` already fails one eslint rule (line 201, unescaped `'`).
  It isn't ours and doesn't block `next build`.

- 2026-10-02: **step 6 done, live at https://simonbrief.com/talmud-stories.** Rebased
  onto the merged homepage polish (31d32ed) and fast-forwarded hub `main` to a427d40.
  Vercel production deploy succeeded. The card text now echoes the page's opening.
  Step 5 was skipped: Simon said publish, and Jeff hasn't seen the page.
  The hub homepage is now light-themed and this page is dark; Simon didn't ask to change that.
  **Remaining: step 7 (retire GitHub Pages) and step 8 (finding).**

## How you know it worked

- Live `https://<hub>/talmud-stories` returns 200 and renders at desktop and 375px.
- Homepage card links there, with no `github.io` link left in the hub
  (`grep -r github.io ~/simonbrief-hub/app`).
- No "accuracy", 92.1, 96.3, 153 or 172 on the new page outside the history section.
- Every figure matches `STATE.md` or its named finding on the publish date and carries that date.
- `gh api repos/siguy/talmud-stories/pages` returns 404 after step 7.
- `python3 -m pytest tests/ -q` passes in this repo.

## Guardrails

- No figure from the retired 4-gram matcher. No composite score (Critical Rule 5).
- Don't invent a new visual style. Match the existing hub subpages.
- Don't touch the hub's `feat/homepage-polish` working tree.
- Don't hand-edit `STATE.md` / `WORK.md`, and don't rewrite `STATUS.md` on this branch.

## When done

Write the finding, add an `## Outcome` section below, and
`python3 scripts/board.py finish 2026-10-02-public-site-refresh`. **Never delete it.**

## Outcome

**Done 2026-10-02.** The public page is live at https://simonbrief.com/talmud-stories (hub
`a427d40`). The homepage card links to it and echoes its opening. GitHub Pages is
disabled: the API returns 404 and `siguy.github.io/talmud-stories/` returns 404. The three
sub-pages were removed, and `index.html` is a pointer. Finding:
[`2026-10-02-public-site-moved-to-hub`](../../docs/findings/2026-10-02-public-site-moved-to-hub.md).

**Why GitHub Pages and not a repair:** the Pages build had failed since 2026-05-25, so the
"fixed" 2026-08-31 numbers never went live. Simon chose to retire it, so one site
holds the project instead of two.

**Deviations from the method:** step 5 (Jeff sees the page first) was skipped because
Simon said publish. The page is dark while the redesigned hub homepage is light; Simon
didn't ask to match them. Numbers are hand-typed and dated per Simon, with no test.
