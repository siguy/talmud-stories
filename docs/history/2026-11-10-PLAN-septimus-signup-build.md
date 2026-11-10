# Plan: build the Septimus sign-up (what exists, what is missing, in what order)

*Written 2026-11-09 (filed under the 11-10 plan name). Inventory of `main` at `2886e9b`. Design decisions live in
[`docs/technical/septimus-signup-plan.md`](../technical/septimus-signup-plan.md) (call it "the design"); this file
is the **build** plan. Work item: [`work/2026-11-08-septimus-signup.md`](../../work/2026-11-08-septimus-signup.md).
Nothing was deployed, no Firebase/Google Cloud setting changed, no code edited to produce this.*

**Bottom line.** Only the *ingredients* exist: the story reader, per-story `words`/`minutes`, and a Firebase
project with its public config. **No sign-up code exists** (no sign-in, no database rules, no minutes question, no
assignment, no progress). The biggest gap is the whole client-side sign-up layer. First thing to build: the
**Firestore security rules + their tests**, because they touch no file the Shas run writes.

## 1. Inventory: built / partly built / planned only / not planned

| Piece | Status | Evidence |
|---|---|---|
| Story reader (tractate cards, daf lists, story page, Hebrew/English, Sefaria link, feedback, AI notes) | **built** | `site/app.js:36-175`; `site/index.html` |
| Per-device "mark as read" | **built** (browser-only, not shared) | `site/app.js:11,34,103-105` (localStorage `septimus-read`) |
| `words` and `minutes` per story, totals in `index.json` | **built** (#79) | `scripts/build_site_data.py:209-215,222-238`; `tests/test_site_data.py:78-95`; `site/data/index.json` |
| Reading speed as one config value | **built** | `site/config.js:5` (`readingWpm: 150`), read by `build_site_data.py:202-206` |
| Definite-only story filter | **built** | `build_site_data.py:56-65`; `docs/technical/septimus-story-filter.md` |
| Firebase project `septimus-stories` (Spark, Firestore nam5, Google provider, authorised domain) | **built, outside the repo** (done by hand 2026-11-08; not re-verified here, no API calls allowed) | design §8; `site/config.js:9-16` (public web config, PR #78) |
| Firebase setup script | **built** but only creates project, Firestore, provider notes | `firebase/setup.sh:24-39`; its step 6 deploys rules only `if firebase/firestore.rules exists` (`:37-40`), and that file does not exist |
| **Firebase SDK loaded in the page** | **not built** | no `firebase` reference in `site/app.js` or `index.html` (config only) |
| **Google sign-in** | **planned only** | design §3 item 2, §8(b); no code |
| **Firestore rules** | **planned only** | design §6 "Security rules" (prose); no `firestore.rules`, no `firebase.json`, no `.firebaserc` in the repo |
| **Data model** (`users`, `claims`, `meta`) | **planned only** | design §5 (prose); nothing writes it |
| **Minutes-per-week question** | **planned only**; *decided* (5/10/15/30 + other) | design §4; no UI |
| **Assignment logic** (4-week batch, reading order, stale reclaim) | **planned only** | design §4, §6; no code |
| **Progress tracking** (mark learned shared across devices, counts, field view) | **planned only** | design §3 items 4-5; today's progress bar is per-device (`app.js:43-48`) |
| **Landing page / "about the list" / About Joe Septimus** | **planned only** | design §3 items 6-8; `app.js:50-52` has one dedication line only |
| `yahrzeit`, `list_version`, `published_at` fields | **planned only** | design §1, §7; absent from `site/config.js` and `site/data/index.json` |
| Stable story ids | **built** (`<tractate>-<daf>-<start>-<end>`) | `build_site_data.py:148`, asserted unique `:229-230` |
| Hosting + deploy | **built** (Vercel, push-to-deploy; whole site is `noindex`) | `site/vercel.json:1-5`; `.gitignore` has `.vercel`. Not re-verified live |
| Feedback endpoint (Cloud Run worker) | **built** | `site/config.js:3`; `worker/` |
| Data export for Simon (`scripts/export_signups.py`, `auth:export`) | **planned only** | design §8(c); script does not exist |
| Broadcast reminder email, "why are you here" question, pick-your-own, second readers | **not planned for v1** (listed as Later) | design §3 "Later" |
| Emulator-based tests for rules | **not planned yet; needs a decision** (Java not installed on this Mac, the Firestore emulator needs it) | `java -version` fails here |
| Browser tests | **partly**: Playwright is installed for Python (`import playwright` works), no site test uses it | none under `tests/` for `site/app.js` |

Two things in the design that the build must settle (details in §4):
- The design says claims go stale after **30 days** but assignments are **4 weeks**. Those need one number. Recommend
  stale = **35 days** (4 weeks + 1 week grace).
- Design §6 says "assign from the first open gap in reading order". With many people signing up at once that makes
  everyone fight for the same front stories. Handled in piece 4.

## 2. What changes when ~36 tractates and ~2,500 stories arrive (Sunday 2026-11-15)

Today's site was built for 5 tractates and 443 stories. Concretely, from the code:

| Today | Problem at 36 tractates | Fix |
|---|---|---|
| `home()` fetches **every** tractate JSON before drawing (`app.js:39`). Now ~1.4 MB; at 36 × ~300 KB ≈ **10 MB** on a phone | Slow first screen, burns mobile data, would hurt exactly the family members we most want | Home reads only `index.json` and a new light **`catalog.json`** (id, tractate, ref, words, minutes only; ~2,500 rows ≈ 200 KB). Full text loads only when a tractate/story is opened |
| `HE` and `NAME` are hard-coded for 5 tractates (`app.js:3-4`); `route()` rejects any other (`app.js:180`) | The 31 new tractates would 404 | Names (English, Hebrew, Seder order) move into `index.json`, written by the build script |
| One card per tractate, flat (`app.js:40-49`) | 36 cards is a long scroll | Group by Seder (Zeraim, Moed, Nashim, Nezikin, Kodashim, Tohorot) with collapsible headers |
| Progress per card computed from all stories in memory (`app.js:41-48`) | Needs every tractate loaded | Counts come from the database (piece 5), totals from `index.json` |
| `tests/test_site_data.py` asserts goldens and a note for every story (`:13-62`), `GOLDEN_COUNTS` is the five tractates | Fails or silently ignores the new ones. The notes test needs a notes file per tractate; new tractates will have none | Shas PR must decide: generate notes or relax the test for tractates with no notes (the reader already copes, `app.js:84`) |
| `SITE_WORDS` pins five word totals (`test_site_data.py:78`) | Same | Shas PR re-pins from `index.json` |
| Story ids are unique only per tractate file (`build_site_data.py:229`) | Safe today because the id starts with the tractate; confirm for the new ones | Add a cross-tractate uniqueness assertion |
| ~80 hours of text at 150 wpm (design §2) | Fine for people, **big for the database read quota** | Progress design in piece 5 |
| `index.json` has no list version or date | The landing page and the later "v2 list" migration need them | Shas PR adds `list_version: "v1"`, `published_at` |

Firestore (Spark) daily limits: 50,000 reads / 20,000 writes. The design's plan to *count* instead of *read* is right
but 72 count queries per home visit would still be ~72 reads a visit. **Recommended:** the home page shows **one
overall bar** (2 count queries: taken, learned = a handful of reads). A tractate's own page loads only that
tractate's claims (a query on a `tractate` field the claim must carry, up to ~200 docs). Estimated ≈ 200 reads per
real visit, so ≈ 250 visits a day before the free quota runs out. Reads fail until midnight Pacific rather than costing
money; if Daniel mails hundreds at once, move to the Blaze plan that day with a $5 alert (design §8a).

## 3. Which pieces can start now (before the Shas PR) and which must wait

`python3 scripts/board.py lanes` (run 2026-11-09): 40 open items, **3 lanes**; `septimus-signup` and `shas-finder-run`
sit **together in the one serial lane** because both declare `site/`, `scripts/build_site_data.py`, `tests/`.
The board is right about the shared files, but only some of this work touches them.

**Can start now: only writes NEW files, never `site/data/`, `site/app.js`, `scripts/build_site_data.py`, `tests/test_site_data.py`:**

| Piece | New files only |
|---|---|
| A. Firestore rules + tests | `firebase/firestore.rules`, `firebase/firestore.indexes.json`, `firebase.json`, `.firebaserc`, `tests/firestore/…` |
| B. Assignment logic as a pure module (input: catalog rows + claims + minutes → list of story ids), unit-tested with plain Node or Python | `site/signup/assign.js`, `site/signup/assign.test.mjs` |
| C. Sign-in + sign-up screens as separate modules, developed against an emulator or a fake backend, and mounted by a **one-line hook** in `app.js` at merge time | `site/signup/auth.js`, `site/signup/view-*.js`, `site/signup/signup.css` |
| D. About Joe Septimus page text and structure | `site/signup/about.js` |
| E. `scripts/export_signups.py` (reads the database; Simon's login) | new script |
| Browser test harness (Playwright) | `tests/browser/…` |

**Must wait for the Shas PR (merged Sunday):**

| Piece | Why |
|---|---|
| `catalog.json`, `index.json` additions, tractate names, `list_version` | Written by `build_site_data.py`, which Shas also edits |
| `app.js` changes: lazy loading, Seder grouping, hooking in the sign-up screens, shared progress | Same file the Shas run edits |
| `test_site_data.py` re-pin | Same file |
| Final assignment dry-run on the real ~2,500-story list | Needs the data |

Rule for the parallel work: nobody edits `site/app.js` except the single mount-point PR after Shas merges. Add
`writes:` entries to the work item to match, and split it: **`septimus-signup-core`** (new files, runs now) and
**`septimus-signup-integrate`** (blocked by the Shas PR). Then `board.py lanes` shows they can be different lanes.

## 4. The remaining pieces, in build order

Each is its own PR, branch `septimus/signup-*`, title starting `[Septimus]`. "Browser" = a real browser at phone
width (390 px), per CLAUDE.md Critical Rule 1. I can drive Chromium with Playwright against the **local emulators**;
**I cannot sign in to real Google** (typing a password is off-limits), so each piece ends with a short manual check
Simon does on his phone.

**Piece 1 [now] — Firestore rules and the data model (design §5-6).**
Files: `firebase/firestore.rules`, `firebase.json`, `.firebaserc`, `firestore.indexes.json`. Collections: `users/{uid}`
{name, email, createdAt, minutesPerWeek, community:null}; `claims/{storyId}` {uid, **tractate**, list, assignedAt,
doneAt}; `meta/list` read-only. Add the `tractate` field to the claim (not in the design; needed so a tractate page
reads only its own claims).
*Done when:* rules unit tests pass (see §5 for the list of cases) **in the Firestore emulator**. That needs Java
(not installed here), see decision D4. *Browser test:* none yet; this piece is database-only.
*Deploy:* **not done by this plan.** `firebase deploy --only firestore:rules` is run by Simon (or a local session at his
request), after he has read the rules.

**Piece 2 [now] — Assignment as a pure function.**
`assign(catalog, claims, minutesPerWeek, now) → [storyIds]`: 4 weeks of minutes, reading order, stale claims
reclaimable, ≥1 story, stop before exceeding by >50% (design §6.4). Recommended tweak: **start each person at the first
open gap *after a random offset within the first open tractate*** only if contention shows up in the pilot; v1 keeps
strict first-gap and relies on the transaction retrying with the next story (Firestore re-runs the transaction on
conflict). Cap one batch at 120 minutes/week × 4 so one transaction stays far below Firestore's 500-write limit.
*Done when:* unit tests cover: exact fill, over-run limit, empty pool, stale reclaim, 36-tractate list, two people
assigned from the same snapshot overlap (shows why the transaction is required). *Browser test:* none (pure code).

**Piece 3 [after Shas, small mount PR] — Firebase SDK, Google sign-in, the minutes question.**
Load the Firebase web SDK pinned to one exact version (look up the current version in the official docs first,
CLAUDE.md "fetch current docs"); load it only when the user taps "Sign in", so the reader stays fast for people who
never sign in. `signInWithPopup` (design §8b). Detect in-app browsers (WhatsApp, Instagram, Gmail) and show "open in
Safari/Chrome". Minutes question: buttons 5 / 10 / 15 / 30 + other (design §4). On first sign-in write `users/{uid}`.
*Done when / browser:* against the Auth + Firestore emulators at 390 px: tap sign in → emulator account chooser →
returns to the site signed in; question appears once; reload keeps the session; sign out works; in-app-browser banner
shows when the user agent is spoofed. *Simon's manual check:* real Google sign-in on iPhone Safari and Android Chrome
(popups are the known weak spot).

**Piece 4 — "Get my stories": the claim transaction.**
Reads the catalog and current claims, runs `assign`, writes up to N claim docs in **one transaction** that re-checks
each is still free. Handles "pool empty", "already have an open batch" (show it instead of assigning more).
*Browser (emulator):* account A pledges 15 min → gets consecutive stories summing ≈15 min; account B pledges at the
same moment (two tabs) → no story appears in both; A reloads → same list; B cannot write A's claim from the console.

**Piece 5 — My stories, mark as learned, give back, progress.**
"My stories" list (query `claims` where `uid == me`), each links to the existing story page; "Mark as learned" sets
`doneAt`; "Give back" deletes an unfinished claim. Progress: one overall bar on home (count queries), per-tractate
statuses (open / taken / learned, **no names**) loaded when a tractate is opened. The old per-device "read" tick stays
for browsing but the sign-up status is the one that counts.
*Browser:* mark learned on tab 1 → overall count on a second browser profile rises after reload; per-tractate counts on
the field sum to `index.json`'s story totals; a signed-out visitor sees progress but no buttons.

**Piece 6 — Lazy loading and 36-tractate home page (the "Sunday" change).**
Home reads `index.json` + `catalog.json` only; Seder grouping; names from `index.json`; test updates. Can be folded
into the Shas merge PR or follow it immediately.
*Browser:* throttle to "Slow 4G" in Chromium: home draws in under ~3 s; network panel shows no tractate JSON fetched
until one is tapped; every tractate opens and a story page renders in each of the 36 (script loops the list); Hebrew
nikud and RTL still correct.

**Piece 7 — Landing page, "which list is this", About Joe Septimus.**
One screen before sign-in (design §3 item 7-8), About page with clearly marked placeholder text until Daniel supplies
his. *Browser:* signed-out first visit lands on it; one button; progress visible; list version/date shown from
`index.json`; About linked from home; no console errors at 390 px and at 1280 px.

**Piece 8 — Export and operations.**
`scripts/export_signups.py` (claims + progress to CSV), a short runbook for Simon (how to export emails, how to see who
has stalled claims). *Done when:* run against the emulator with seeded data and the CSV matches.

**Piece 9 — Pilot, then open.** Daniel + ~10 friendly people, one week; fix what they hit; then open.

## 5. Security

**Principle:** there is no server in v1, so *the rules are the server.* Every guarantee below must be a rule that has a
test.

| Data | Who can read | Who can write |
|---|---|---|
| `users/{uid}` (name, email, rate) | only that user (a Daniel/Simon export runs with their own admin login, outside the site) | only that user; fields limited to the schema; `minutesPerWeek` a number 1-240; `email` equal to the token's email |
| `claims/{storyId}` | anyone, including signed-out (the progress field is public) | **create:** signed in, `uid == auth.uid`, doc id matches the `tractate-daf-start-end` pattern and its prefix equals `tractate`, `assignedAt == request.time`, `doneAt == null`, exactly the allowed fields. **Take over:** only if the old claim is stale (`doneAt == null` and `assignedAt` older than 35 days). **Update:** owner only, only `doneAt` from null to `request.time`. **Delete:** owner only, only while unfinished |
| `meta/list` | anyone | nobody (changed only by an admin tool) |
| anything else | nobody | nobody (default deny) |

Rule tests to write (piece 1): signed-out cannot write; cannot claim as someone else; cannot claim an already-held
fresh story; can take a stale one; cannot set `doneAt` on another's claim; cannot change `uid`; cannot add extra
fields; cannot read another's `users` doc; cannot delete someone's finished claim; malformed ids rejected.

**Known limits (stated, accepted for v1):** a signed-in user could claim many free stories under their own account;
visible in the console and undoable. Rules cannot easily cap claims per user without a server; the cheap guard is the
stale rule returning them. Claims show an opaque `uid` publicly (no name or email), so a stranger can see "the same
anonymous person took these 40 stories" but not who. If Daniel wants even that hidden, claims become readable only
by their owner and the public progress comes from a counter document instead (more code; not recommended for v1).

**No personal data in URLs.** Routes are `#/t/<tractate>` and `#/s/<storyId>` (story ids carry no person data).
Never put uid, email, name or minutes in a hash or query string; the feedback form already sends `page_url`
(`app.js:159`), so this matters: keep the signed-in state out of the URL entirely. The Firebase `apiKey` in
`config.js` is public by design; protection is the rules plus the authorised-domain list. No secrets in the repo.
The `noindex` header (`site/vercel.json`) stays so search engines do not list family members' activity.

**Privacy copy:** the sign-in screen must say what the email is used for (design §10: "occasional reminders about this
project"). Daniel approves wording (D-Daniel 4).

## 6. What Daniel Septimus must decide or provide

1. **Yahrzeit date.** Plan says 8 Elul 5787 = Friday 10 Sep 2027 (computed, unconfirmed). Also: *is it the Hebrew
   date or the secular date that people should aim for?*
2. **Text for the "About Joe Septimus" page**: a few paragraphs, the Hebrew name (e.g. "ben …"), whether to include a
   photo and permission to use it.
3. **The dedication line** and the project's name on the landing page (currently "Stories of the Talmud", "In memory of
   Joe Septimus").
4. **Approve the wording** of: what we do with sign-up emails; one reminder email or none; whether he will send it
   (we only export the list; he or Simon sends one BCC mail).
5. **Who may join.** Anyone with a Google account (recommended; the link is the only gate and the site is `noindex`),
   or an allow-list of emails (more work, more friction)?
6. **Whether the progress page may show names** of people who have learned (recommended: **no**, v1 shows counts only).
7. **Who the audience is and the launch date**: a list of people for the pilot (about 10), then the wider list; when
   he wants it to go out (avoid the week of 11/23-11/27, US Thanksgiving).
8. **Do the unreviewed tractates count** toward "all the stories"? Most are unreviewed by Jeff; the design default
   is yes, labelled. His call whether that is acceptable for his community.
9. **A permanent web address** he is happy to share (the Vercel one is a placeholder). If he buys a domain it must be
   added to the Firebase authorised-domain list by Simon.
10. **Jeff Rubenstein's name on the landing page** — confirm Jeff is comfortable being named (the footer already names him).

## 7. Realistic schedule

Today is Monday 2026-11-09; the Shas run is going tonight; its PR is due Sunday 11-15. The yahrzeit is ~43 weeks away
and 80 hours of reading needs only ~2 hours a week across the whole community (about 8 people at 15 min/week), so
**the launch date has plenty of slack. Quality beats speed.** Estimates assume focused sessions.

| When | What | Notes |
|---|---|---|
| Tue 11-10 → Thu 11-12 | Pieces 1 and 2 (rules + tests, assignment function) in parallel, new files only; decisions D1-D5 answered | Rules tests need Java (D4) |
| Fri 11-13 → Sun 11-15 | Piece 7 text drafts, piece 8 script; screens (piece 3-5 modules) built against a fake backend / emulators; Shas PR merges | Nothing touches `app.js` |
| Mon 11-16 → Wed 11-18 | Integrate: pieces 3 + 6 (SDK, sign-in, minutes, lazy loading with real 36-tractate data), re-pin tests | First time the whole thing runs on real data |
| Thu 11-19 → Tue 11-24 | Pieces 4 + 5 (claim transaction, my stories, learned, progress), browser tests | |
| Wed 11-25 → Sun 11-29 | Rules deployed by Simon; real-phone checks; piece 7 with Daniel's text | Thanksgiving week: little feedback expected |
| Mon 11-30 → Sun 12-06 | **Pilot** with Daniel and ~10 people | |
| ~Sun 12-13 | **Public launch** (target; moves with Daniel's text arriving) | Risk: text from Daniel is the likeliest delay |
| Dec → Aug 2027 | Monthly check of unclaimed/stale; one reminder email; list v2 migration if the finder improves (design §7) | |

Biggest schedule risks: (1) the Shas PR is late or its data breaks `test_site_data.py` (it will fail until re-pinned);
(2) Google popup sign-in misbehaves on some phones, which would force a move to Firebase Hosting (a config change,
about a day); (3) Daniel's wording/dates arrive late.

## 8. Decide before starting (Simon)

Each has a recommendation. Plain-language tradeoff first.

| # | Decision | Recommend | Tradeoff |
|---|---|---|---|
| D1 | **Split the work item** into `signup-core` (new files, now) and `signup-integrate` (after Shas)? | **Yes** | One item means the board forces everything to wait for Shas. Two items let rules, assignment and text start tonight without touching the files Shas is writing |
| D2 | **Order stories are assigned in:** Seder order (Berakhot first) or reviewed tractates first? | **Seder order** | Seder order is what people expect and keeps "how many left" easy to read. Reviewed-first protects early readers from software-only tractates, but the shipped filter is already "definite in both runs" |
| D3 | **Stale-claim window:** 30 days (design) vs 35 | **35** | Matches the 4-week batch plus a week of grace, so nobody loses a story the day their batch ends |
| D4 | **How to test the rules:** install Java (e.g. `brew install openjdk`) so the Firestore emulator runs | **Install it** | The emulator is the only way to test rules without touching the live database. The alternative is testing rules by hand on the real project, which risks real data and can't be repeated |
| D5 | **Progress on the home page:** one overall bar only (cheap), or per-tractate bars (nicer, ~36x the reads) | **Overall bar; per-tractate when opened** | Keeps us inside the free quota with room. If the quota is ever exceeded the site's reader still works; only the progress numbers go blank until midnight Pacific |
| D6 | **Real-phone sign-in:** Simon does the manual sign-in check on his iPhone and one Android | **Yes** | I can't type Google passwords. The automated tests use fake emulator accounts instead |
| D7 | **Who deploys the rules and any Firebase change** | **Simon, or a local session he starts** | Nothing here touches the live project; rules are the security of the whole system, so a human reads them first |
| D8 | **Hosting:** stay on Vercel, switch to Firebase Hosting only if phone sign-in fails | **Stay on Vercel** | Push-to-deploy and per-PR previews beat having everything in one Google project |
| D9 | **Pilot first** (Daniel + ~10) before the wider list | **Yes** | Cheap insurance: real people find confusing wording in a week |

## 9. How this gets tested, in one place

- `python3 -m pytest tests/ -q` (includes `test_bookkeeping.py`) before every push, as always.
- Rules: emulator unit tests (piece 1).
- Assignment: pure unit tests (piece 2).
- Everything user-visible: Playwright (Chromium) at 390 px and 1280 px against local emulators, with a screenshot
  attached to each PR; then a manual real-Google check by Simon on a phone.
- Data scale (piece 6): script opens all 36 tractates and a story in each; Slow-4G timing on home.
