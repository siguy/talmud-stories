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

## Step b built (2026-11-15)

Branch `septimus/signup-b`. New: `site/signup.js`, `site/signup.css`, `firestore.rules`, `firebase.json`,
`tests/test_firestore_rules.py`; one-line hooks in `site/app.js` and `site/index.html`; a `signup` block in
`site/config.js`. Review and outcomes: `docs/technical/signup-b-review-2026-11-15.md`.

- **Verified** at phone width against the local emulators (fake account): land, sign in, choose minutes, Join,
  "You're in", return visit, Save, sign out; the record holds exactly the four planned fields with `src`; the rules
  refuse reading another record and changing `src`. 49 rules tests pass. The reader still works at `#/browse`.
- **Not verified:** a real Google account. It cannot work until `firestore.rules` is deployed to `septimus-stories`
  (the live database refuses every read, so the page says "Could not load your sign-up."). Deploying is Simon's call:
  `firebase deploy --only firestore:rules --project septimus-stories`. Then Simon signs in once on the site.
- **Rules tests need a real Java** (`brew install openjdk`); without it they skip and say so.
  `REQUIRE_RULES_TESTS=1` makes a skip a failure.
- **To test locally:** `firebase emulators:start --only auth,firestore --project demo-septimus`, serve the repo root,
  open `/site/?emulator=1`. `?inapp=1` shows the in-app-browser state. Both switches work on localhost only.
- **After the Jeff-responses branch merges:** change the two `#/` links in `site/app.js` to `#/browse` and delete the
  click listener marked `TODO(signup)` in `signup.js`; bump `config.js?v=` in `index.html`. That branch and this one
  both edited the plan document, so expect one conflict there (site files merge cleanly, tested).
- **Placeholders awaiting Daniel:** `launchDate`, `yahrzeit`, `contactEmail`, `communities` in `site/config.js`; the
  About Joe Septimus page text.
- Screens built without a mockup, in the reader's style, because the b checklist listed them: "You're in",
  "How the stories were chosen", "Your data", About (placeholder), the in-app-browser notice. Show Simon.

## Step c built (2026-11-15)

Branch `septimus/signup-c` (stacked on `septimus/signup-b`). `scripts/septimus_assign.py` (pure rules),
`scripts/septimus_weekly.py` (runner and database access), `.github/workflows/septimus-weekly.yml` (daily, **off**
until the repository variable `SEPTIMUS_WEEKLY_ENABLED` is `true`), `requirements-septimus.txt`. Review, outcomes and
the builder's choices Simon has not yet confirmed: `docs/technical/signup-c-review-2026-11-15.md`.

- **Verified:** logic and runner tests under plain pytest; the real database code against the local emulators
  (needs a virtualenv with `requirements-septimus.txt` and a real Java); a 200-person, 40-week simulation.
- **Never run against the live database.** Before it can be: a service-account key stored as the GitHub secret
  `FIREBASE_SERVICE_ACCOUNT` (Simon creates it; never in the repo), a launch date that is a Monday in
  `site/config.js`, the rules deployed, and Daniel's answers.
- **Not built:** the counts email to Simon (step e, needs the email service); deletion of all personal data six
  months after the yahrzeit (`TODO(before launch)` in the runner).
- **Step d must:** show "longer than usual" using `is_longer_than_usual`; not list released rows; add "Resume"
  (the person clears their own `pausedAt`), "Stop my stories" and "Delete my data".

## Step d built (2026-11-15), except the story-page button

Branch `septimus/signup-d` (stacked on c). In `site/signup.js`: My stories (`#/my`), mark as learned from that list,
Progress (`#/progress`), stop / delete / cancel deletion on "Your data", paused and stopped notices with "Resume".
Review and outcomes: `docs/technical/signup-d-review-2026-11-15.md`. Screenshots of the built screens (test data):
`docs/technical/signup-screens/`.

- **Verified** at phone width against the emulators with fake accounts and seeded rows.
- **Left for after the Jeff-responses branch merges** (needs `site/app.js`): the "Mark as learned" button on the
  story page, "Back to my stories", "Next story", and keeping the reader's per-device tick in step. One
  `TODO(signup d…)` comment in `signup.js` marks it.
- **Step s** should put the Shas order of tractates into `index.json`; until then `SHAS_ORDER` in `signup.js` is
  checked against `scripts/tractates.py` by `tests/test_signup_shas_order.py`.
- **Simon has not seen** the screens that had no mockup: stop / delete / cancel deletion, paused / stopped / resume,
  "You're in", "How the stories were chosen", "Your data", About (placeholder), the in-app-browser notice.

**Staging exists (2026-11-15):** `https://talmud-stories-staging.vercel.app`, its own Firebase project
`septimus-stories-staging`; see `docs/technical/septimus-staging.md`. Test there, not on the real site.

**The one to-do list is `docs/technical/septimus-launch-checklist.md`** (2026-11-15); tick items there.

## What is left, in order (2026-11-15)

1. Simon: look at the built screens; confirm the builder's choices in the b, c and d review files.
2. ~~Deploy the rules~~ **Done 2026-11-15** from `septimus/signup-d` (Simon's go-ahead). Signed out, the live
   database now answers 404 for `progress/summary` (readable, not yet written) and 403 for `users`, `assignments`,
   `runs`, `sent`. Still to do: Simon signs in once with a real Google account (locally: serve the repo root and
   open `/site/`; `localhost` is an authorised sign-in domain).
3. When the Jeff-responses branch merges: step s (field test, `list_version`, `published_at`, Shas order in the
   data), the story-page button, the two `#/` links and the `config.js?v=` bump.
4. Step e (weekly email, counts email to Simon): needs the email service and sending domain chosen, and Daniel's
   sender and wording.
5. Before launch: the six-months-after deletion job; a service-account key in GitHub secrets; switch the workflow on.
6. Daniel: launch date, yahrzeit date, communities, About text, "finishing".

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
