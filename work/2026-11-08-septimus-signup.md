---
title: "Learn all the stories" sign-up for the Septimus yahrzeit (v1)
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [site/, scripts/build_site_data.py, tests/test_site_data.py, docs/technical/septimus-signup-plan.md, firebase/, firestore.rules, firebase.json, scripts/septimus_weekly.py, .github/workflows/]
finding:
superseded_by:
---

# "Learn all the stories" sign-up for the Septimus yahrzeit (v1)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this. **Full plan:
[`docs/technical/septimus-signup-plan.md`](../docs/technical/septimus-signup-plan.md)** (scope, data model,
assignment, list versions, backend choice, risks). Builds on the reader from
[`2026-10-12-septimus-story-viewer.md`](2026-10-12-septimus-story-viewer.md).

## The problem

Daniel Septimus wants his community to collectively learn every story in Shas by his father Joe Septimus's first
yahrzeit (8 Elul 5787). People sign in with Google and commit minutes per week; each week they get consecutive
stories in order through Shas, by email and on a My stories page; missed stories roll over 2 weeks, then return to
the pool; when commitments exceed the list, stories are learned more than once.

## Method

PRs b–f in plan §9: landing + sign-in + commitment; weekly job (assignment, rollover, cycles); My stories + progress;
weekly email; Joe Septimus page. (a, word counts, done in #79.) Backend: Firebase Auth + Firestore on
`septimus-stories` on the free plan; the weekly hand-out and email are a scheduled Python script (plan §6, §8).

**Update 2026-11-14:** the five screens are mocked up and settled (plan §3a, `docs/technical/signup-mockups/`). Build
b and c now on the proposed defaults; the data contract (plan §7a) waits for the Jeff-responses branch to merge.

**Plan review 2026-11-14** (`docs/technical/signup-plan-review-2026-11-14.md`): the weekly work is a Python script
on a scheduled GitHub Action, not a Cloud Function (no paid plan); no stored pool pointer; access rules tightened;
stop / delete paths added. Plan §5–§11 rewritten accordingly.

## Resume here (written 2026-11-14, before a context compaction)

**State.** Plan, review and mockups are done and agreed. **No sign-up code exists.** Next action: build step b, then
c, on a new branch `septimus/signup-b` cut from `septimus/signup-mockups` (which holds everything below).

**Read these, in this order, before writing code:**
1. `docs/technical/septimus-signup-plan.md`: §3a (mockups and style rules), §4 (decisions), §5 (data), §6 (hand-out,
   access rules, leaving), §7a (which story fields may be read), §9 (build order and the 13-item b checklist), §11.
2. `docs/technical/signup-mockups/*.png` and `html/`: the five settled screens. The build copies these.
3. `.stitch/DESIGN.md`: colours, fonts and components, taken from `site/style.css` and from sefaria.org.
4. `docs/technical/signup-plan-review-2026-11-14.md`: section D lists what steps d and e must not forget.

**What Simon decided in this thread (all recorded in the plan; listed here so none is re-asked):**
- Do not wait for Daniel. His seven questions went out 2026-11-13 (Google Doc plus email); no reply yet. Everything
  he owes is a config value or a marked placeholder. Nothing goes live to real people until he answers.
- The story list does not need to be final to build. It is frozen (ids and order) at launch.
- Landing page: title, dedication, one sentence, **progress card, then sign-in**. No 1-2-3 steps, not wordy.
- The look is the Septimus reader's, whose inspiration is sefaria.org. Navy main buttons, a white Google-style
  sign-in button, a grey dedication box. Green means "learned" only.
- Mockups come first for any new screen, made with the `stitch` skill (plan §3a says how, and what goes wrong).
- 75 words a minute. "Finishing" is repeated rounds of Shas until Daniel says otherwise.
- The weekly work is a Python script on a scheduled GitHub Action. No paid Firebase plan, no card.
- Order through Shas starts at Berakhot (`TABLE` in `scripts/tractates.py`), not the site's home-page order.
- Long stories are handed out anyway; quiet people are paused; stop / delete / deletion six months after the
  yahrzeit; a "Your data" note before sign-in; a contact line for people without Google; hand-outs stop after the
  yahrzeit; at most 120 minutes a week; the landing page takes `/` and the tractate list moves to `#/browse`.

**Cautions for the build:**
- **Stay out of the story data.** The session "Jeff's responses and implications" (branch
  `claude/jeff-responses-analysis-e4238c`, worktree `shas-preflight-d2ae6f`, local only on 2026-11-14) is editing
  `scripts/build_site_data.py`, `site/data/` and `tests/test_site_data.py`. b and c add new files and do not edit
  those. c's tests use a fixture copy of the data. **Before editing `site/index.html` or `site/app.js`, check whether
  that branch has changed them** (`git diff main...claude/jeff-responses-analysis-e4238c -- site/index.html site/app.js`).
- **Real Google sign-in needs Simon.** Rules and flow are tested against the Firestore emulator; the last check, a
  real account signing in, is Simon signing in once in the browser pane. Never enter a password.
- **The live database** (`septimus-stories`) had no rules deployed, was empty and refused anonymous reads on
  2026-11-14. Deploying rules is an outward-facing step: ask first.
- **Who builds.** The main session writes b and c; one independent Opus review per step, given the code and the plan
  but not the builder's opinion (Simon, 2026-11-14).
- The data's `minutes` field is at 150 wpm. Compute reading time from `words` at 75.
- Stitch project "Talmud Stories: learning sign-up" is private to Simon's Google account; its id is in
  `.stitch.json`. Its canvas listing is unreliable; the PNGs in the repo are the copy of record.

**Not blocking b or c:** the email service and sending domain (before step e); the field test (step s) waits for the
Jeff-responses branch to merge; `septimus/daniel-brief` has one local commit moving the sent files, not pushed at
Simon's request.

## How you know it worked

- At 390 px in a real browser: land, sign in, commit 10 min/week; the account is recorded with its `?src=`.
- Emulator test over 3 simulated weeks: consecutive stories within each budget; a missed story rolls over 2 weeks,
  then goes to someone else; re-running a week changes nothing.
- A test weekly email to Simon renders on a phone and its unsubscribe link works.
- Per-tractate progress counts add up to the stories learned.

## Guardrails

- The goldens decide what is a story; boundary widenings stay display-only. Never edit `results/canonical/*`.
- AI notes stay hidden until approved. No secrets in the repo. No scope beyond plan §3 v1.

## When done

Write the finding to `docs/findings/<date>-septimus-signup.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish 2026-11-08-septimus-signup`. **Never delete it.**
