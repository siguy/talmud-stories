# "Learn all the stories" sign-up — plan (v1)

*Written 2026-11-08; **rewritten 2026-11-13** for Simon's decisions after Daniel Septimus's reply (weekly
commitments, weekly email, doubling up); **updated 2026-11-14**: mockups settled (§3a); then revised after a
four-reviewer plan review ([`signup-plan-review-2026-11-14.md`](signup-plan-review-2026-11-14.md)): §5–§11 rewritten. Builds on the reader in [`septimus-viewer-plan.md`](septimus-viewer-plan.md).
Work item: [`work/2026-11-08-septimus-signup.md`](../../work/2026-11-08-septimus-signup.md).*

## 1. Goal

Daniel Septimus wants family, friends and community to **collectively learn every story in Shas** by the first
yahrzeit of his father, Joe Septimus. Jeff Rubenstein is fine with it. People **commit to an amount of learning per
week until the yahrzeit**; the committed group covers the whole story list. v1 = the bare minimum that makes that run.

**Deadline.** Joe Septimus died on **8 Elul**. 8 Elul 5786 = Friday 21 August 2026, so the first yahrzeit is
**8 Elul 5787 = Friday 10 September 2027** (computed with `pyluach`; 5787 is a leap year, which is why it falls in
September). Daniel to confirm. A config value (`yahrzeit` in `site/config.js`), never hard-coded.

**The list covers all of Shas but its size is not final** (Simon, 2026-11-13): all 37 tractates are on the site,
**about 1,800 stories**, and the count may move either way (a "how many did we miss" analysis and a possible
ship-rule change are in progress). So every list is **dated**, every sizing number is **derived from the data at
build time** (§2), and assignment must survive stories being added or removed mid-campaign (§7).

## 2. The numbers that shape the design

**A dated snapshot, not the plan's inputs.** Measured 2026-11-13 on `site/data/` at `main` `6105b19` (1,897 stories);
another session's site is already at 1,784. The build derives these numbers from the data every time
(`index.json`: total stories, words, hours at `readingWpm`, whole-group minutes per week, people at 10 min/week,
stories per 10 min), and the landing page, progress page and any text for Daniel read them from there. Nothing below is
hard-coded anywhere.

| | value |
|---|---|
| Tractates | 37 (3 reviewed by Jeff: Ketubot, Kiddushin, Gittin; 34 labelled "not yet reviewed") |
| Stories | 1,897 on that date (**about 1,800, not final**) |
| English words | **428,045** (mean 226, median 166, longest 2,674) |
| Weeks from a December 2026 launch to 10 Sep 2027 | ~40 |

**Reading pace: one config value, `readingWpm` in `site/config.js`**, used for both the time shown per story and the
weekly allocation. 150 wpm (today's value) is too fast for this (Simon, 2026-11-13): people read slowly, in Hebrew
**and** English, and stop to think. Pace is measured in English words of the passage per minute. Options
(snapshot arithmetic on the 2026-11-13 list: 428,045 words, mean 226 words a story; 40 weeks. Rebuilt from the data each build):

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
1. **Landing page** (one short screen, before sign-in; mockup settled 2026-11-14, §3a): title, the dedication, one
   sentence ("A few minutes a week, from <launch date> until his yahrzeit, 8 Elul."), the progress card, then one
   button, "Sign in with Google to join", with "We email you your stories each week." under it. **No numbered steps
   and no explanation on this page** (Simon, 2026-11-14). What "a story" is here, which tractates Jeff Rubenstein has
   checked, and which list this is ("Story list v1, dated <date>") move to a small linked page, **"How the stories
   were chosen"**; the list date also shows on the progress page.
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

### 3a. Mockups (settled with Simon, 2026-11-14)

Made before any code, so the look is agreed first. Images and editable HTML:
[`signup-mockups/`](signup-mockups/). The build copies these; it does not re-design them.

| Screen | File | Settled |
|---|---|---|
| Landing | `1-landing.png` | Progress card first, then sign-in. No 1-2-3 steps. About 45 words |
| Minutes a week | `2-minutes.png` | 5 / 10 / 15 / 30 / Other; "10 minutes a week is about 3 stories."; "Join" |
| My stories | `3-my-stories.png` | This week; still open from earlier weeks; group progress; "about N min" per story |
| Progress | `4-progress.png` | "Shas completed N times", the current round, then per tractate (cycles option, §4) |
| Weekly email | `5-weekly-email.png` | Three story cards, one button, Daniel's line as a placeholder |

**Style rules** (full list: [`.stitch/DESIGN.md`](../../.stitch/DESIGN.md)):
- The sign-up looks like the same site as the reader: navy top bar, gold-edged cards, Cardo and Frank Ruhl Libre.
  Colours and fonts come from `site/style.css`, never from a mockup.
- The reader's look is borrowed from sefaria.org, so anything the reader lacks is taken from Sefaria (captured
  2026-11-14), not invented: **main buttons are solid navy**; **sign-in is a white, navy-outlined button with the
  Google "G"**; the **dedication is a plain grey box in italic serif**. No Sefaria logo or assets.
- **Green means "learned" only** (progress fill, the done tick). It is never a sign-in or join button.
- Anything in [square brackets] on a mockup is a placeholder (launch date, sender, Daniel's line). Story names,
  summaries and numbers on the mockups are invented samples.

**How the mockups are made** (reusable): the `stitch` skill (`~/.agents/skills/stitch/`, CLI `stitch`) with the
private Stitch project "Talmud Stories: learning sign-up" (id in `.stitch.json`). Capture the real reader pages and
upload them as the style reference, write `.stitch/DESIGN.md` from `site/style.css`, then `stitch generate screen
--device MOBILE` with the exact copy in the prompt. Three things learned the hard way: Stitch **invents copy** (footer
lines, taglines) unless told "use only this copy", so read every screen before showing it; `stitch edit screen` often
**fails to save**, so small changes are faster made in the downloaded HTML and re-uploaded with `stitch upload screen`;
and screens generated in parallel **may not appear on the canvas**, so share the per-screen link the upload returns,
and keep the PNGs in the repo as the copy of record.

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

Each decision is marked **Simon decided** or **to confirm with Daniel** (Simon, 2026-11-13). The seven questions in
§12 went to Daniel on 2026-11-13; no reply yet. **Revised 2026-11-14 (Simon): do not wait for him.** Every
to-confirm item is a config value or a marked placeholder, and b and c are built now on the proposed defaults.
Nothing goes live to real people until he answers (§9).

| | Decision | Status |
|---|---|---|
| Unit | **Minutes per week**, converted to stories by word count at `readingWpm` | Simon decided |
| Reading pace | One config value, **75 wpm** (§2) | Simon picked 75 (2026-11-13); **asked Daniel 2026-11-13** |
| Cadence | **Week by week** from the pool; no full schedule at sign-up | Simon decided |
| Start | **Fixed launch date**: sign-ups open first, everyone starts the same week | Simon decided; **date to confirm with Daniel** |
| Order | **In order through Shas, starting at Berakhot** (traditional order, then daf, then segment); **consecutive** stories per person | Simon decided (start point 2026-11-14) |
| Missed stories | **Roll over 2 weeks** on the person's list, then **released** to the pool | Simon decided |
| People who never read | **Paused** after two rounds of releases with nothing learned, with one "still with us?" email | Simon decided 2026-11-14 |
| A story longer than the weekly minutes | Handed out anyway, labelled "longer than usual" | Simon decided 2026-11-14 |
| Leaving | "Stop my stories", "Delete my data", and a fixed deletion date after the yahrzeit (§6) | Simon decided 2026-11-14 |
| After the yahrzeit | Hand-outs stop; landing page shows the final total and a thank-you; reading stays open | Simon decided 2026-11-14 |
| No Google account | A contact line under the button; added by hand | Simon decided 2026-11-14 |
| More commitment than list | **Double up**: nobody turned away; stories learned more than once | Simon decided |
| What "cover the entire thing" means | cycles / copies per story / per-person paths (below) | **Asked Daniel 2026-11-13. Build on cycles meanwhile** (Simon, 2026-11-14), behind one config value so another answer is a small change |
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

### Decisions after Simon tried staging (2026-11-15)

- **As simple as possible; no added machinery.** Staging goes live with no edits: the same files run in both
  places, and the site picks its database from its own address.
- **The week starts on Sunday.** Stories are handed out, and the weekly email goes out, on **Sunday morning**
  (US Eastern). The launch date must be a Sunday. Everything in this plan that said Monday now means Sunday.
- **Three flow changes, built:** three links under the title on every page (My stories · All stories · Progress;
  "Join" for people who have not joined); signed in, the front page is My stories (the "You're in" screen is gone);
  "Mark as learned" on the story page when the story is yours.
- **Parked:** sample stories on the front page; **"Give me another story"** (agreed, after launch); marking your
  stories inside the tractate lists; "Next story" on the story page.
- A story read without being assigned does not count toward the group total.

## 5. Data model (Firestore)

Revised 2026-11-14 after the plan review ([`signup-plan-review-2026-11-14.md`](signup-plan-review-2026-11-14.md)):
no stored pool state, no name or email in the database.

```
users/{uid}                    { createdAt, minutesPerWeek, src,            // written by the person at "Join"
                                 deleteRequested: false,                    // set by the person
                                 pausedAt: null,                            // set by the script; the person may clear it (resume)
                                 lastLearnedWeek, lapses: [week] }          // script only: what the pause rule needs
assignments/{week_uid_storyId} { uid, storyId, round, week,                 // week = campaign week, 1..~40
                                 assignedAt, doneAt: null | ts, releasedAt: null | ts }
runs/{week}                    { startedAt, finishedAt, counts }            // one per campaign week; makes a re-run a no-op
sent/{week_uid}                { sentAt }                                   // one per email; makes a re-send impossible
progress/summary               { learned, byTractate: {t: n}, round, roundsCompleted,
                                 openInRound, joined, listVersion, updatedAt }   // public, script-written
```

- **Name and email are never stored here.** The script reads them from the sign-in system (Firebase Auth) when it
  needs them. A person therefore cannot make the weekly email go to someone else's address.
- `minutesPerWeek: 0` means "stopped". There is no separate active flag.
- An assignment row is one person's copy of one story. Rows are not unique per story (doubling up).
- The row id is fixed (`<week>_<uid>_<storyId>`), so writing the same hand-out twice changes nothing.
- No pool pointer, no released queue, no list document: launch and yahrzeit dates live in `site/config.js`, the list
  version in `site/data/index.json`.
- Export for Simon: sign-ups from Firebase Auth, plus `users` and `assignments`. What Daniel and the family receive is
  **community counts and names**, not anyone's reading log, unless he asks.

## 6. The weekly hand-out (a Python script on a schedule)

**`scripts/septimus_weekly.py`**, run by a scheduled GitHub Action and by hand when needed. Daily it refreshes
`progress/summary` and handles delete requests; on **Sundays (US Eastern, early morning)** it also hands out stories and sends the
email. Not a Cloud Function: the browser never needs a server, and this keeps the project on the free plan (§8).

The hand-out is **one pure function**, tested with plain pytest on a fixture copy of the story data:

```
assign_week(story_order, assignments, users, week, wpm) -> rows to write, rows to release, people to pause
```

**How it decides, in order:**
1. **Nothing before launch or after the yahrzeit week.** If the launch date is unset or in the future, or the week is
   past the yahrzeit, it hands out nothing.
2. **Release.** A row assigned in week W and still not learned is released by the week W+3 run (it stayed on the
   person's list for W, W+1 and W+2). The write re-checks that `doneAt` is still empty, so a story marked learned at
   that moment is not also handed to someone else.
3. **Pause the quiet.** A person who has let stories lapse in two hand-outs at least three weeks apart, with
   nothing learned in between, gets `pausedAt` and one "still with us?" email. This covers someone who never read
   and someone who read at first and then stopped (Simon, 2026-11-15); marking any story learned resets the count. Tapping "Resume" (the person clearing
   their own `pausedAt`) undoes it. Stories released because the person stopped do not count as lapses.
4. **Which stories are free.** A story is *covered in round N* if a row for it exists in round N that has not been
   released. The current round is the lowest N in which some story on the list is not covered.
5. **Hand out.** People are served in sign-up order (`createdAt`). Budget = `minutesPerWeek` (capped at 120 by the
   script as well as by the rules) minus the reading time of their still-open stories. Each person gets the first
   uncovered stories in list order while the running total stays within budget; always at least one story if the
   person holds nothing open. Nobody is handed a story they already hold, and a story is not handed back to the
   person who let it lapse in that same run. When a round has no uncovered stories left, the next person continues in round N+1.
6. **Reading time** is `words / wpm` at the script's own 75 wpm. The data's `minutes` field is computed at 150 wpm
   and is not used.

What falls out of rule 4 without any special handling: a released story is uncovered again and, being earlier in the
list, goes out first; a story added to the list is uncovered and is reached in order; a story removed from the list
is simply never offered.

**Order through Shas** is the traditional order, **starting at Berakhot** (Simon, 2026-11-14): the order of `TABLE`
in `scripts/tractates.py`, then daf, then segment. Not the site's home-page order, which lists the reviewed
tractates first.

**A story longer than someone's weekly minutes** is handed out anyway under the at-least-one rule, labelled "longer
than usual" (Simon, 2026-11-14). That person gets nothing new until it is learned or released.

**Rounds and "finishing".** A round is *complete* when every story on the list has a row in that round with a done
mark. The headline is "Shas completed N times"; the progress page also shows "K stories still open in round N", so a
story nobody reads is visible instead of silently blocking a siyum. Group "learned" = distinct stories with at least
one done mark in the current round.

**Safe to re-run.** The script first creates `runs/<week>`; if it already exists and finished, it stops. Row ids are
fixed, so a run that died halfway can be run again. A person who joins mid-week waits for the next Sunday run.

**Each run emails Simon its counts** (new sign-ups, total minutes, stories handed out, released, people paused), so
anything odd, including a wave of fake sign-ups or a missed week, is visible within a week. A `PAUSE` setting stops
hand-outs without a deploy.

**Marking learned** is the person's own write to their own row (`doneAt`). Their tick shows at once; the group total
catches up at the next daily run and is labelled with its time.

### Access rules (`firestore.rules`, in the repo, tested in the emulator)

- `users/{uid}`: readable and writable only by that person. On create: only `createdAt` (must equal the server time),
  `minutesPerWeek` (whole number 1 to 120), `src` (short, lowercase letters, digits and hyphens),
  `deleteRequested: false`. On update: only `minutesPerWeek` (0 to 120) and `deleteRequested`, and clearing `pausedAt` (resume). Never
  `createdAt`, `src`, setting `pausedAt`, or the script's `lastLearnedWeek` and `lapses`.
- `assignments`: a person can read their own rows and change only `doneAt` on them, to the server time or back to
  empty. Rows are created only by the script.
- `runs`, `sent`: script only. `progress/summary`: anyone can read, only the script writes.
- Nobody can list other people's records. No client deletes.
- Rules decide shape and ownership; the script decides fairness (the minutes cap, the `src` allowlist, the pause).

**Checked 2026-11-14:** the live database has no rules deployed, is empty, and refuses anonymous reads (HTTP 403 on
`users`, `assignments`, `meta`, `progress`). So nothing is exposed today; the first rules deployed are the ones above.

### Leaving

- **"Stop my stories"** sets `minutesPerWeek: 0`; open stories are released at the next daily run.
- **"Delete my data"** sets `deleteRequested`; the next daily run removes the sign-in account and the `users` record
  and blanks `uid` on that person's rows, so group totals stay true.
- **Unsubscribing from email** is handled by the email service and stops email only. It is not leaving.
- **Everyone's personal data is deleted** (accounts and `users` records; rows anonymised) on a fixed date after the
  yahrzeit, a config value: six months after (Simon, 2026-11-14).

## 7. A list that changes, and story ids

- A person's place is their **rows**, each holding a story id, not a position. Adding or removing other stories does
  not touch them (and see §6 rule 4).
- A row whose story is no longer on the list shows "no longer on the list" and drops off at release. A learned one
  stays counted as history, not as progress on the current list.
- Progress is always reported against the current list, with its date.
- **Ids are `tractate-daf-start-end`, so a boundary change changes the id** and looks like one story removed and one
  added. To keep that from happening mid-campaign, **the list (ids and order) is frozen at launch** as list v1;
  `site/data/index.json` carries `list_version` and `published_at`.
- **Deferred until a v2 list actually exists:** the old-id to new-id overlap map and the one-off migration that
  rewrites `storyId` on existing rows (match by segment overlap, never an exact key — Lesson 36; ambiguous splits and
  merges printed for a person to decide). With no stored pointer, that migration is the whole job.
- Tests for `assign_week` include: a story added early and late in the list, a story removed while someone holds it,
  a story released and re-offered, and the list changing size mid-round.

## 7a. What the sign-up reads from the story data

The sign-up reads the same files as the reader (`site/data/index.json`, `site/data/<tractate>.json`).

- **Fields it may use:** `id`, `tractate`, `ref`, `refs`, `start_segment`, `summary`, `words`, `reviewed`, and from
  `index.json` the tractate totals, `list_version` and `published_at`. Nothing else. Not `minutes` (§6 rule 6).
- **One test** in `tests/test_site_data.py` asserts those fields exist with the right types in every tractate file.
  No separate schema file: the only other reader is in this repo.
- **Sizing numbers are read from the data at build time** (§2), never typed in: the list was 1,897 on 2026-11-13 and
  1,864 on another branch a day later.
- **Room for later:** people, themes and background notes are optional fields the sign-up ignores.

**The test waits.** The session "Jeff's responses and implications" (branch `claude/jeff-responses-analysis-e4238c`,
not merged on 2026-11-14) is changing these files: 80 added stories with an `included_by` tag, 85 summaries, and
`tier`, `biblical` and `biblical_reason` removed. Until it merges, b and c add new files only and do not edit
`scripts/build_site_data.py`, `site/data/` or `tests/test_site_data.py`; c's tests run on a fixture copy.

## 8. Backend: decision

**Firebase Auth + Firestore on the free Spark plan; the site stays on Vercel; the weekly work is a Python script
run by a scheduled GitHub Action.** (Revised 2026-11-14. The 2026-11-13 plan used a scheduled Cloud Function, which
needs the paid Blaze plan; the review showed nothing here needs one.)

**Project: `septimus-stories`** (created 2026-11-08; Firestore `nam5`; Google sign-in on; authorised domain
`talmud-stories.vercel.app`, a placeholder: add the final domain when it exists; exact hosts only, never a
`vercel.app` wildcard).

Why Firebase and not the alternatives (unchanged from 2026-11-08): Google sign-in is one switch; the free plan needs
no card so it cannot charge; the site needs no server of its own; Simon already uses the Google console. Supabase's
free projects pause after a week without traffic; Vercel functions plus a hosted database is three services to keep
alive.

**(a) Free-plan limits.** Spark allows 50,000 reads and 20,000 writes a day. A Sunday run for a few hundred people is
a few thousand writes; reading every assignment row is about 50,000 reads only at the very end of the campaign, so
the daily refresh reads only what changed since the last run and recounts fully on Sundays. Public pages read
`progress/summary` only. Exceeding a quota means reads fail until midnight Pacific; it never costs money.

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

**(c) Secrets.** Two exist, both stored as GitHub Actions secrets and never in the repo: a service-account key that
lets the script write to Firestore and read sign-in records, and the email service's API key. The Firebase web config
in `site/config.js` (including its "API key") is public by design; restrict that key in the Google Cloud console to
Firebase APIs and the site's addresses.

**(d) Email.** A transactional email service (for example Resend, Postmark, Brevo or Amazon SES) with a dedicated
sending subdomain and its SPF, DKIM and DMARC records. Never "From: …@gmail.com" through a service. Free tiers cover
a few hundred weekly recipients; past that, typically $15–20 a month. Unsubscribe is the service's own, with the
standard one-click header and a confirm page (mail scanners open links). The script skips unsubscribed and
hard-bounced addresses, and writes `sent/<week>_<uid>` before sending.

**(e) The schedule.** GitHub's scheduler can start late and occasionally skips a run. The script therefore works out
which campaign week it is from the date, not from how many times it has run, and its daily run does the Sunday work
if Sunday's was missed. The count email to Simon is the alarm.

**(f) Exports.** `firebase auth:export` (names and emails) and `scripts/export_signups.py` (rows and progress), run
on Simon's machine. Exports go in a restricted Google Sheet, not email attachments, and are deleted afterwards.

**Setup** stays as in [`firebase/setup.sh`](../../firebase/setup.sh) (idempotent, never links billing) and
[`firebase/LOCAL_CLAUDE_PROMPT.md`](../../firebase/LOCAL_CLAUDE_PROMPT.md).

## 9. Build order (one PR each, branch `septimus/signup-*`, titles start `[Septimus]`)

| PR | What | Done when |
|---|---|---|
| ~~a~~ | Word count + reading time in the export | **Done** (#79) |
| ~~m~~ | Mockups of the five screens | **Done** 2026-11-14 (§3a) |
| b | **Built 2026-11-15** (branch `septimus/signup-b`; review: [`signup-b-review-2026-11-15.md`](signup-b-review-2026-11-15.md)). Still to do: deploy `firestore.rules` and one real Google sign-in by Simon. Landing page, Google sign-in, `?src=`, minutes question, "You're in" screen, "How the stories were chosen" and "Your data" pages, `firestore.rules` | Matches mockups 1 and 2 at 390 px; the b checklist below passes; rules tested in the Firestore emulator. **Build now**, placeholders for launch date, yahrzeit and community names. New files only (§7a) |
| c | **Built 2026-11-15** (branch `septimus/signup-c`; review: [`signup-c-review-2026-11-15.md`](signup-c-review-2026-11-15.md); the counts email waits for step e). `assign_week` and `scripts/septimus_weekly.py` (hand-out, release, pause, progress summary, counts email to Simon), the scheduled Action | pytest on a fixture: 3 fake people over 4 simulated weeks get consecutive stories within budget; a missed story is released at W+3 and goes to someone else; a re-run changes nothing; the §7 list-change cases pass; a long story is handed out and labelled. **Build now** on rounds and 75 wpm. **Running it against the live database waits for** Daniel's "finishing" answer and a launch date |
| s | The field test and `list_version` / `published_at` (§7a) | Every tractate file passes. **Waits for** the Jeff-responses branch to merge |
| d | **Built 2026-11-15 except the story-page button** (branch `septimus/signup-d`; review: [`signup-d-review-2026-11-15.md`](signup-d-review-2026-11-15.md); screenshots: [`signup-screens/`](signup-screens/)). My stories, mark as learned, stop / delete my data, progress page | Matches mockups 3 and 4; released rows are not listed (marking a released row learned stays allowed by the rules: Simon, 2026-11-15); one "Mark as learned" button on a story that is yours, which also sets the old per-device tick; "Back to my stories" and "Next story"; "Saved" only after the write is confirmed. **Waits for** c |
| e | Weekly email (service, subdomain, unsubscribe, link that marks learned without signing in) | Matches mockup 5; a test send to Simon renders on a phone; a re-run sends nothing twice. **Waits for** sender and wording (Daniel) |
| f | About Joe Septimus page | Linked from the landing page; placeholder clearly marked for Daniel. **Buildable now** |

**b checklist** (from the review):
- The `users` record is written at "Join", not at sign-in; abandoning the question shows it again next visit.
- After "Join": a "You're in" screen with the minutes, the start date ("Your first stories arrive Sunday <date>" once
  launched), Change, and Browse the stories.
- A returning signed-in person sees "Signed in, 10 min a week" and a link, not the sign-in button.
- The landing page takes `/`; the tractate list moves to `#/browse`; existing `#/t/` and `#/s/` links keep working.
- "[N] people have joined" comes from `progress/summary` and is hidden until that exists.
- `?src=` is kept in the URL and in the browser's storage so it survives leaving an in-app browser; checked against
  an allowlist; never displayed raw.
- In-app browsers (WhatsApp, Instagram, Gmail): detected; a large "Copy link" button and one picture of "Open in
  browser". No tricks to force it open.
- "Other" minutes: a whole number, 1 to 120. The minutes screen shows the email address and "Not you? Switch account".
- Under the sign-in button: "No Google account? Email [contact]". Those people are added by hand.
- The sign-in popup opens directly from the tap. Vercel preview sites cannot sign in; accepted.
- Names from Google and `src` are inserted as text, never as HTML (`site/app.js` builds pages with `innerHTML`).
- "Your data", linked before sign-in: what is stored (Google name and email, the community link, which stories you
  read and when), who sees it (Simon; the family sees community counts and names), that nothing about a person is
  public, how to stop or delete, 13 or older.
- Aa control on every new page; targets at least 44 px; the minutes choice is a labelled radio group.

**Order (2026-11-14):** b, then c, in one session; s as soon as the Jeff-responses branch merges; d after c and s;
e and f when Daniel answers. b and c are each compared with their mockup in a real browser before being called done.

Each verified in a real browser at phone width (Playwright, Chromium) before it is called done.
`python3 -m pytest tests/test_site_data.py tests/test_bookkeeping.py -q` before each push.

## 10. Risks

| Risk | Handling |
|---|---|
| Heavy oversubscription makes "finish Shas" meaningless | Rounds: each completed pass is a siyum (§6); Daniel asked 2026-11-13 |
| People commit and vanish | Released at W+3; paused after two rounds of releases with nothing learned (§6) |
| A story nobody reads blocks a siyum | "K stories still open in round N" on the progress page |
| GitHub's scheduler skips Sunday | The daily run does Sunday's work if it was missed; the counts email is the alarm (§8e) |
| The daily run uses too many free reads | About 21,000 of 50,000 a day with 200 very committed people (c review); revisit near 500 people |
| Someone games the hand-out or the email | Rules bound every field; email comes from the sign-in system; the script caps minutes (§6) |
| Emails land in spam | Dedicated sending subdomain with SPF/DKIM/DMARC, low volume, plain content, one-click unsubscribe |
| A boundary change breaks someone's place | List frozen at launch; migration written when a v2 exists (§7) |
| 34 of 37 tractates are not expert-reviewed | Labelled "not yet reviewed" on the list and story pages and on "How the stories were chosen" |
| Sign-in blocked in WhatsApp/Instagram in-app browsers | Detect, "Copy link" and one picture (§9 b checklist) |
| Personal data kept too long, or no way to leave | Stop, delete, and a fixed deletion date after the yahrzeit (§6) |
| Yahrzeit date unconfirmed | Config value; shown once Daniel confirms |

## 11. Open questions for Simon

None blocking b or c. Decided 2026-11-14 (plan review): script instead of a Cloud Function, so **no paid plan and no
card**; order starts at Berakhot; long stories handed out anyway; stop / delete / deletion date; a "Your data" note
before sign-in; pause the quiet; a contact line for people without Google; hand-outs stop after the yahrzeit.

Also confirmed by Simon, 2026-11-14 (these were the builder's choices until he saw them):
- **The landing page becomes the site's front page** (`/`); the tractate list moves to `#/browse`.
- **At most 120 minutes a week.**
- **Personal data is deleted six months after the yahrzeit** (still a config value).
- **"Quiet" means two rounds of handed-back stories with nothing ever marked learned**, about six weeks, then one
  "still with us?" email and a pause.

Still to choose before step e: the email service and the sending domain.

## 12. Questions for Daniel (plain English, ready to paste)

*Sent to Daniel on 2026-11-13 as a Google Doc plus an email (`comms/sent/2026-11-13-daniel-signup-*`, on branch
`septimus/daniel-brief`). No reply by 2026-11-14.*

> Hi Daniel, a few things to settle before we build the sign-up for learning all the Talmud stories in your father's memory:
>
> 1. **What does "finishing" mean?** All of Shas's stories (about 1,800 at the moment; the number isn't final) are only about 60–95 hours of reading, so if a few
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

