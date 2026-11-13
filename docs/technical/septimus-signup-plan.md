# "Learn all the stories" sign-up — plan (v1)

*Written 2026-11-08; **rewritten 2026-11-13** for Simon's decisions after Daniel Septimus's reply (weekly
commitments, weekly email, doubling up). Builds on the reader in [`septimus-viewer-plan.md`](septimus-viewer-plan.md).
Work item: [`work/2026-11-08-septimus-signup.md`](../../work/2026-11-08-septimus-signup.md).*

## 1. Goal

Daniel Septimus wants family, friends and community to **collectively learn every story in Shas** by the first
yahrzeit of his father, Joe Septimus. Jeff Rubenstein is fine with it. People **commit to an amount of learning per
week until the yahrzeit**; the committed group covers the whole story list. v1 = the bare minimum that makes that run.

**Deadline.** Joe Septimus died on **8 Elul**. 8 Elul 5786 = Friday 21 August 2026, so the first yahrzeit is
**8 Elul 5787 = Friday 10 September 2027** (computed with `pyluach`; 5787 is a leap year, which is why it falls in
September). Daniel to confirm. A config value (`yahrzeit` in `site/config.js`), never hard-coded.

**The list is complete** (Simon, 2026-11-13): all 37 tractates are on the site (`main` at `6105b19`). List
versioning stays (§7) for a later v2.

## 2. The numbers that shape the design (measured 2026-11-13 on `site/data/`, `main` at `6105b19`)

| | value |
|---|---|
| Tractates | 37 (3 reviewed by Jeff: Ketubot, Kiddushin, Gittin; 34 labelled "not yet reviewed") |
| Stories | **1,897** |
| English words | **428,045** (mean 226, median 166, longest 2,674) |
| Weeks from a December 2026 launch to 10 Sep 2027 | ~40 |

**Reading pace: one config value, `readingWpm` in `site/config.js`**, used for both the time shown per story and the
weekly allocation. 150 wpm (today's value) is too fast for this (Simon, 2026-11-13): people read slowly, in Hebrew
**and** English, and stop to think. Pace is measured in English words of the passage per minute. Options
(arithmetic on 428,045 words, mean 226 words a story; 40 weeks):

| Pace | Shas once | Whole group per week, one pass | People at 10 min/week for one pass | Stories per 10 min/week | Passes if 200 people give 10 min/week |
|---|---|---|---|---|---|
| **75 wpm** (Simon's starting suggestion: slow, both languages) | 95 h | 143 min (2.4 h) | 14 | ~3.3 | 14 |
| **100 wpm** (middle) | 71 h | 107 min | 11 | ~4.4 | 19 |
| **120 wpm** (English-first, some Hebrew) | 59 h | 89 min | 9 | ~5.3 | 22 |
| *150 wpm (today's value; too fast)* | *48 h* | *71 min* | *7* | *~6.6* | *28* |

Whichever pace: a **handful of people covers Shas once; hundreds cover it many times. Doubling up is the normal
case**, and "cover the entire thing" needs a definition (§4).

Words = whitespace tokens of the English shown, HTML stripped. Per story `minutes = ceil(words / readingWpm)`, min 1;
assignment sums `words / readingWpm` (not the rounded minutes). **Shown as approximate** ("about 5 min") on story rows,
story pages and the weekly email (Simon, 2026-11-13; supersedes "not displayed", 2026-11-09).

## 3. Scope

### v1 (build now)
1. **Landing page** (one screen, before sign-in): what this is (learning every story in the Talmud together, in memory
   of Joe Septimus, by 8 Elul 5787); what "a story" is here (narratives found by software; 3 tractates checked by a
   scholar, Jeff Rubenstein, the rest labelled "not yet reviewed"); which list this is ("Story list v1, dated <date>");
   progress so far; the launch date; one button, "Sign in with Google to join".
2. **Sign in with Google**, nothing else asked. A `?src=<community>` link (e.g. `?src=hadar`) is recorded silently.
3. **Commit:** one question after sign-in, "How many minutes a week will you learn until 8 Elul?" — 5 / 10 / 15 / 30
   + "other". Changeable later. Nothing else asked.
4. **Weekly assignment** (§6): each week, each committed person gets that week's stories, **consecutive, in order
   through Shas**, adding up to their minutes.
5. **My stories** (signed in): this week's stories plus rolled-over ones, each linking to the existing story page,
   with **"Mark as learned"**. The page is the source of truth.
6. **Weekly personal email**: "Your stories this week", links to each story and to My stories; one-click unsubscribe.
   The email is the nudge.
7. **Progress page** (public): stories learned, by tractate, and the coverage measure Daniel confirms (§12, question 1).
8. **About Joe Septimus** page: structure and a clearly marked placeholder; Daniel supplies the words.

The existing reader (cards, daf lists, story pages, Hebrew/English, "Open on Sefaria", feedback form, approved notes)
keeps working unchanged; the sign-up wraps it.

### Later (not v1 — list, do not build)
- **"Give me a story"** button: for (a) leftovers nobody committed to, (b) stories released by people who did not
  read them, (c) uncommitted people who want to double up. Same assignment write, one story at a time.
- Honour board / pie chart by community (data already collected via `?src=`).
- **Co-readers** (Simon, 2026-11-13; explicitly not v1): people who read the same story get more context and
  meaning and can talk with each other about it. **The only v1 implication:** keep per-story completion records
  (who read which story, when). `assignments` already holds them (`uid`, `storyId`, `doneAt`), so v1 needs nothing
  extra. **Privacy:** nobody is ever shown to another reader without opting in first; a future `users.showToCoReaders`
  defaults to false, and v1 shows no one to anyone.
- AI "explain what's going on" buttons; rich profiles; context beyond "Open on Sefaria".

## 4. The commitment mechanic

Each decision is marked **Simon decided** or **to confirm with Daniel** (Simon, 2026-11-13). Nothing that depends on
a to-confirm item is built until Simon reports back (§9 marks which PRs wait).

| | Decision | Status |
|---|---|---|
| Unit | **Minutes per week**, converted to stories by word count at `readingWpm` | Simon decided |
| Reading pace | One config value; 75 / 100 / 120 wpm (§2) | **Simon to pick, then confirm with Daniel** |
| Cadence | **Week by week** from the pool; no full schedule at sign-up | Simon decided |
| Start | **Fixed launch date**: sign-ups open first, everyone starts the same week | Simon decided; **date to confirm with Daniel** |
| Order | **In order through Shas** (site tractate order, then daf, then segment); **consecutive** stories per person | Simon decided |
| Missed stories | **Roll over 2 weeks** on the person's list, then **released** to the pool | Simon decided |
| More commitment than list | **Double up**: nobody turned away; stories learned more than once | Simon decided |
| What "cover the entire thing" means | cycles / copies per story / per-person paths (below) | **To confirm with Daniel** |
| Reminders | **Weekly personal email** + signed-in My stories page | Simon decided; **wording and sender to confirm with Daniel** |
| Community attribution | **Per-community links** (`?src=...`), not an onboarding question | Simon decided; **list of communities to confirm with Daniel** |
| Yahrzeit date | Friday 10 September 2027 (8 Elul 5787) | **To confirm with Daniel** |
| Joe Septimus page | Structure + placeholder | **Wording from Daniel** |

Options for the coverage question, so the answer can be one word:
- **Cycles (proposed):** the group reads Shas front to back; when the end is reached, cycle 2 starts at the front.
  The headline is "Shas completed N times", and each completion is a natural siyum. Released stories are re-assigned
  within their cycle before the pointer moves on, so every cycle really is complete.
- **Copies per story:** each story gets learned by up to K people at once (K = commitments ÷ list size), and the
  pointer moves K times slower. Same arithmetic, less of a story: no moment of completion.
- **Per-person path:** each person reads their own sequence from wherever they start. Simplest to explain, but the
  group never "finishes" anything together.

## 5. Data model (Firestore)

```
users/{uid}           { name, email, createdAt, minutesPerWeek, src,        // src from ?src=, first visit wins
                        emailOptIn: true, active: true }
assignments/{auto}    { uid, storyId, list: "v1", cycle, week,              // week = ISO week the job assigned it
                        assignedAt, doneAt: null | ts, releasedAt: null | ts }
pool/state            { list: "v1", cycle, next: <index into story order>,  // server-only
                        released: [storyId, …] }                            // returned stories, re-assigned first
progress/summary      { learned, byTractate: {t: n}, cycles: {n: learned}, updatedAt }   // public, server-written
meta/list             { current: "v1", publishedAt, launch, yahrzeit }
```

- Assignments are **not** unique per story any more (doubling up); each row is one person's copy of one story.
- No names or emails outside `users` (the progress page is public).
- Export for Simon and Daniel: `users` (who joined, from where) and `assignments` (who learned what).

## 6. Weekly assignment (server-side job, Monday morning US Eastern)

1. For each active user, roll-over check: their unfinished assignments older than **2 weeks** get `releasedAt` and
   their story ids go to `pool.released`.
2. Budget = `minutesPerWeek` minus the reading time of their still-open (rolled-over) stories. If ≤ 0, no new stories.
3. Take stories from `pool.released` first (oldest first), then from the pointer `pool.next` in order, adding stories
   while the running total ≤ budget; always at least one story if budget > 0. At the end of the list, the pointer
   wraps and `cycle` increments (under the cycles option).
4. Users are served in sign-up order, so each person's stories are consecutive and the list fills from the front.
5. One transaction updates `pool/state` and writes the week's assignments; the job is idempotent per week (re-running
   it for a week that is already assigned changes nothing).
6. Then the weekly email goes out (§8), and `progress/summary` is recomputed.

**Marking learned** is a client write to the user's own assignment (`doneAt` only); a small trigger keeps
`progress/summary` current between weekly runs.

Security rules: `users/{uid}` read/write by that user only (fields: `minutesPerWeek`, `emailOptIn`, `active`, and
`src` on create); `assignments` readable by their owner, updatable by their owner on `doneAt` only, created only by
the server; `pool`, `meta` server-only writes; `progress/summary` public read.

## 7. List versions and stable ids

- v1 freezes today's ids (`tractate-daf-start-end`). `site/data/index.json` gains `list_version` and `published_at`.
- A **new list (v2, …)** ships with `site/data/lists/v1_to_v2.json`: each v1 id → the v2 id it **overlaps most by
  segments** (overlap, never an exact key — Lesson 36), or `null`.
- A one-off migration rewrites assignments through that map: learned stays learned on its match; open stays open.
  A v1 story with no match keeps its rows under its old id, counted as history. Ambiguous splits/merges are printed
  for a person to decide, never guessed. The pool pointer is re-seated at the first v2 story not yet covered in the
  current cycle.

## 8. Backend: decision

The static site cannot hold shared state; it needs sign-in and a small database.

| | Firebase Auth + Firestore | Supabase (Postgres + Auth) | Vercel functions + hosted Postgres + Auth.js |
|---|---|---|---|
| Google SSO | Built in, one switch | Needs a Google OAuth client set up in GCP, pasted into Supabase | Needs the same OAuth client plus Auth.js code |
| Free tier | Spark: no card, so it can never charge | Free projects **pause after a week without traffic**: a real risk over 10 months | Free tiers, but three services to keep alive |
| Code we must own | Static pages + security rules. **No server** | Static pages + row-level-security SQL | A server (API routes), schema, migrations |
| For a non-engineer owner | Google console Simon already uses; data viewable as a table | One more account | Most moving parts |
| Data export | `firebase auth:export` (sign-ups) + a small script for claims | SQL / CSV | SQL / CSV |

**Decision: Firebase Auth + Firestore, on a NEW Google Cloud project. Site stays on Vercel.**
**Revised 2026-11-13: v1 now needs the Blaze plan** (pay-as-you-go, card on file), because of the weekly job and the
weekly email (§8d). Everything below about Spark still holds for the parts that run in the browser.

**Project: `septimus-stories`** (created 2026-11-08; Firestore `nam5`; Google sign-in on; authorised domain `talmud-stories.vercel.app`, a placeholder: add the final domain there when it exists).

**(a) What Spark covered (2026-11-08 analysis; superseded by (d) for the weekly job):**
- Google sign-in: free on Spark.
- Firestore: free on Spark up to 50,000 reads, 20,000 writes and 1 GB per day.
- Security rules and client-side transactions both work on Spark. Assignment (§6) is a client transaction that
  re-reads each claim doc it writes, and the rules (§6) stop anyone writing a claim that is not theirs or not free.
  That is safe without a server: the worst a malicious signed-in user can do is claim many free stories under their
  own account, which a person can see and undo in the console.
- **Cloud Functions need Blaze** (billing, card). v1 uses none. The later broadcast email does not need them either:
  export the sign-up emails (`firebase auth:export`) and send one BCC email from Gmail.
- **The one Spark risk is the daily read quota.** The progress page reads claim docs; at ~3,000 stories, loading
  every tractate's claims costs up to 3,000 reads. Design for it: overall and per-tractate totals use Firestore
  `count()` queries (one read per 1,000 docs counted); a tractate's per-story claims load only when someone opens that
  tractate. Indicated budget at a busy day (100 visits × ~200 reads) ≈ 20,000 reads, within the 50,000. On Spark,
  exceeding it means reads fail until midnight Pacific; it never costs money. If a launch email is going to hundreds
  of people at once, switch to Blaze that day with a $5 budget alert (cents at this volume).

**(b) Hosting: Vercel** (already live; the feedback endpoint already allows its origin). Sign-in uses
`signInWithPopup` with the default `<project>.firebaseapp.com` auth domain: no proxy, no extra OAuth setup.
Known limit: Google blocks sign-in inside in-app browsers (WhatsApp, Instagram, Gmail's viewer); the sign-in button
detects these and says "open this page in Safari/Chrome". Firebase Hosting would only be needed if popups fail on a
browser we must support; switching later is a config change, not a rewrite.

Hosting on Google Cloud instead of Vercel (not proposed; for the record):

| | Vercel (today) | Firebase Hosting (same new project) | Cloud Storage bucket / Cloud Run |
|---|---|---|---|
| Cost | Free | Free on Spark (10 GB stored, 360 MB/day transferred; ample for a text site) | Bucket needs a load balancer for HTTPS on a custom domain (~$18/month); Cloud Run needs billing |
| Sign-in | Popup; auth runs on a second domain | Same domain as auth: popup **and** redirect both work, fewest browser quirks | Same as Vercel |
| Deploy | `git push` deploys automatically, previews per PR | `firebase deploy` by hand, or a GitHub Action | Script or Action |
| Everything in one place | No: site on Vercel, data on Google | Yes | Yes |

If sign-in proves flaky on phones, Firebase Hosting is the move; otherwise Vercel's push-to-deploy wins.

**(c) Data export for Simon:** `firebase auth:export signups.csv --format=csv` (names and emails) and
`scripts/export_signups.py` (claims and progress → CSV, using his own `gcloud` login). Both run on his machine.
Firestore's managed export (`gcloud firestore export`) needs Blaze and is not used.

The Firebase web config (including its "API key") is meant to be public and goes in `site/config.js`; access is
controlled by the security rules and the authorised-domain list. No secret exists in v1.

**Setup is agent-driven, on Simon's machine** (this cloud container has no Google credentials):
[`firebase/setup.sh`](../../firebase/setup.sh) is idempotent (safe to re-run) and
[`firebase/LOCAL_CLAUDE_PROMPT.md`](../../firebase/LOCAL_CLAUDE_PROMPT.md) is the prompt a local Claude Code session
runs. Two steps have no command line and are clicks in the Firebase console (~2 min): enable the Google sign-in
provider, and add `talmud-stories.vercel.app` to authorised domains.

**(d) Weekly job + email: why Blaze, what it costs (estimated 2026-11-13; check current price pages before enabling)**

- The weekly assignment and email must run **without anyone's browser open**, so they are a scheduled Cloud Function
  (Cloud Scheduler → function). Scheduled functions require **Blaze**. Doing assignment server-side is also safer than
  the old client-transaction design: one writer, no races, simpler rules.
- **Firebase/Google cost at this scale: about $0–2 a month** (estimated). A few hundred users means a few thousand
  Firestore reads/writes a week and four job runs a month, well inside Blaze's free allowances; Cloud Scheduler gives
  3 jobs free.
- **Email needs a sending service and a domain.** Sending from a personal Gmail account is capped (~500/day) and
  lands in spam at volume. A transactional email service (e.g. Resend, Postmark, Brevo, Amazon SES) with a verified
  sending domain (SPF/DKIM DNS records) is the normal way. Cost: free tiers cover roughly a few hundred weekly
  recipients; past that, typically **$15–20 a month** (SES is cheaper, ~$0.10 per 1,000, but more setup). The API key
  lives in Google Secret Manager, never in the repo.
- **Budget alert:** a **$10/month** budget alert on the project (email to Simon at 50% and 100%). Blaze has no hard
  cap; the alert is the guard.
- One-click unsubscribe in every email (link sets `emailOptIn: false`); required practice for bulk senders.

## 9. Build order (one PR each, branch `septimus/signup-*`, titles start `[Septimus]`)

| PR | What | Done when |
|---|---|---|
| ~~a~~ | Word count + reading time in the export | **Done** (#79) |
| b | Landing page + Google sign-in + `?src=` + minutes-per-week question | At 390 px: land, read what it is, sign in, pick 10 min/week; `users/{uid}` has the right fields; rules tested in the Firestore emulator. **Buildable now** with placeholders for launch date, yahrzeit and community names |
| c | Weekly job: rollover/release, assignment in order, pool pointer; progress summary | Emulator test: 3 fake users, 3 simulated weeks: consecutive stories, budgets met, a missed story rolls over 2 weeks then is re-assigned to someone else; re-running a week changes nothing. **Waits for** the coverage answer (Daniel) and the pace (Simon) |
| d | My stories + mark as learned + progress page | Marking learned shows on the progress page; counts per tractate add up. **Waits for** c |
| e | Weekly email (service + domain + unsubscribe) | A test send to Simon renders on a phone; unsubscribe link works. **Waits for** sender, wording (Daniel) and Blaze (Simon) |
| f | About Joe Septimus page | Linked from the landing page; placeholder clearly marked for Daniel. **Buildable now** |

Each verified in a real browser at phone width (Playwright, Chromium) before it is called done.
`python3 -m pytest tests/test_site_data.py tests/test_bookkeeping.py -q` before each push.

## 10. Risks

| Risk | Handling |
|---|---|
| Heavy oversubscription makes "finish Shas" meaningless | Coverage definition (§12, question 1 for Daniel); the cycles option turns it into repeated siyumim |
| People commit and vanish | 2-week grace, then release; released stories are re-assigned first |
| Emails land in spam | Verified sending domain, low volume, plain content, unsubscribe link |
| Blaze bills without a cap | $10/month budget alert; costs estimated at a few dollars |
| A later list (v2) breaks someone's progress | Overlap map + migration (§7); nothing is ever deleted |
| 34 of 37 tractates are not expert-reviewed | Labelled "not yet reviewed" on landing, list and story pages |
| Sign-in blocked in WhatsApp/Instagram in-app browsers | Detect and say "open in Safari/Chrome" (§8b) |
| Yahrzeit date unconfirmed | Config value; shown once Daniel confirms |

## 11. Open questions for Simon (asked one per message, in this order)

1. **Reading pace:** 75, 100 or 120 English words a minute (§2)? *(asked 2026-11-13)*
2. OK to put a card on the `septimus-stories` project (Blaze) with a $10/month alert, for the weekly job and email?

Everything else is in §12, for Daniel.

## 12. Questions for Daniel (plain English, ready to paste)

> Hi Daniel, a few things to settle before we build the sign-up for learning all the Talmud stories in your father's memory:
>
> 1. **What does "finishing" mean?** All of Shas's ~1,900 stories is only about 60–95 hours of reading, so if a few
>    hundred people sign up, we'll get through everything many times over. My suggestion: we go through Shas together
>    in order, and every time we reach the end, that's a siyum and we start the next round. Does that feel right, or
>    would you rather something else (for example, each story read by several people at once)?
> 2. **Launch date:** what week should everyone start together? Sign-ups would open a few weeks before.
> 3. **The yahrzeit:** I've calculated 8 Elul 5787 as Friday 10 September 2027. Is that right?
> 4. **Weekly email:** each person gets one email a week with links to their stories. Whose name should it come from,
>    and is there wording you'd like (a line about your father, for example)?
> 5. **Reading pace:** we estimate time per story assuming people read slowly, in Hebrew and English, and stop to
>    think. We're thinking about [Simon's pick] words a minute, which makes a typical story about [N] minutes. Does that feel right?
> 6. **Communities:** you mentioned Hadar, DN, Kesher and your Brooklyn communities. Each gets its own sign-up link so
>    we can thank them by name later. What's the full list, and what should each be called?
> 7. **A page about your father:** would you write a few paragraphs about him for the site, so people who didn't know
>    him know whom they're learning for?

