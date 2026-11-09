# "Learn all the stories" sign-up — plan (v1)

*Written 2026-11-08. Builds on the reader in [`septimus-viewer-plan.md`](septimus-viewer-plan.md) (do not rebuild it).
Work item: [`work/2026-11-08-septimus-signup.md`](../../work/2026-11-08-septimus-signup.md).*

## 1. Goal

Daniel Septimus wants family, friends and community to **collectively learn every story** by the first
yahrzeit of his father, Joe Septimus. Jeff Rubenstein is fine with it. v1 = the **bare minimum** that lets this happen;
everything else waits for v2.

**Deadline.** Joe Septimus died on **8 Elul**. 8 Elul 5786 = Friday 21 August 2026, so the first yahrzeit is
**8 Elul 5787 = Friday 10 September 2027** (computed with `pyluach`; 5787 is a leap year, which is why it falls in
September). Daniel to confirm. It is a config value (`yahrzeit` in `site/config.js`), never hard-coded.

**Sequencing.** The story finder runs across all of Shas first
([`shas-finder-plan.md`](shas-finder-plan.md)); this sign-up reads the list that produces. PR a below
(word counts) can land on today's four tractates in the meantime; the sign-up opens to the public on list v1.

## 2. The numbers that shape the design (measured 2026-11-08 on `site/data/*.json`; re-measured after the PR a rebuild)

| | stories | English words | median words/story | hours at 150 wpm | hours at 230 wpm |
|---|---|---|---|---|---|
| Ketubot | 101 | 26,050 | 176 | 2.9 | 1.9 |
| Kiddushin | 53 | 11,961 | 184 | 1.3 | 0.9 |
| Gittin | 118 | 25,987 | 181 | 2.9 | 1.9 |
| Yevamot | 95 | 21,985 | 163 | 2.4 | 1.6 |
| **All** | **367** | **85,983** | **176** | **9.6** | **6.2** |

Words = whitespace tokens of the English with HTML stripped (the Davidson translation, bold literal + plain gloss),
over the segments the reader is shown. Each story carries `words` and `minutes`; `index.json` carries per-tractate
totals. Pinned in `tests/test_site_data.py` (`SITE_WORDS`).

- One story is **about a minute** of reading. The longest is 2,674 words (~18 min at 150 wpm).
- The **whole current list is under 10 hours**. With a few dozen people, everyone gets a handful of stories.
- At Daniel's ~3,000 stories across Shas: roughly 700k words, **~80 hours at 150 wpm**. Still small.
- So the sign-up unit is **minutes**, not hours, and a **one-time total** is enough (see §4). A per-day schedule
  over 30 days would assign a fraction of a story per day.

**Reading speed:** default **150 words/minute** ("study pace": Talmud English is dense and readers stop to think).
One constant in `site/config.js`, not hard-coded. Reading time shown = `ceil(words / wpm)` minutes, minimum 1.

## 3. Scope

### v1 (build now)
1. **Word count + reading time** per story in the data export (`scripts/build_site_data.py`), with tests.
2. **Sign in with Google**, nothing else asked at sign-in.
3. **Sign up by time:** "How much time will you give?" — buttons 5 / 15 / 30 / 60 min + "other". The system **assigns**
   unclaimed stories that add up to about that time.
4. **My stories:** the assigned list, each linking to the existing story page; a **"Mark as learned"** button.
5. **Progress (the field):** per tractate, every story with words, minutes and status (open / taken / learned),
   plus "N of M learned, K left" overall and per tractate. Visible without signing in.
6. **About Joe Septimus** page: structure and a clearly marked placeholder; Daniel supplies the words.
7. **Landing page + sign-in flow (critical, Simon 2026-11-09; not built yet).** One screen before sign-in: what this
   is (learning every story in the Talmud together, in memory of Joe Septimus, by 8 Elul 5787), what "a story" means
   here (narratives found by software and checked by a scholar, Jeff Rubenstein; unreviewed tractates say so), the
   progress so far, and one button: "Sign in with Google to join". After sign-in: the minutes-per-week question, then
   "Your stories". Nothing else is asked.
8. **Which list this is**, shown on the landing page and the progress page: "Story list v1, dated <date>:
   stories our software rates as most likely; it will grow as the work improves." From `index.json`'s
   `list_version` / `published_at`.

The existing reader (cards, daf lists, story pages, Hebrew/English, "Open on Sefaria", feedback form, approved notes)
keeps working unchanged; the sign-up wraps it. The per-device "mark as read" checkmark stays as it is.

### Later (not v1 — list, do not build)
- One broadcast reminder email to everyone who signed up (v1 already keeps their email, see §5).
- Post-sign-up "why are you participating?" dropdown (Hadar, Drisha, other community, family, friend, other) and the
  honour board / pie chart. Data slot reserved: `users/{uid}.community` (§5).
- "Pick my own stories" (tick unclaimed stories in the field). Cheap: same claim write as assignment.
- "Take more" / second readers once every story is taken.
- AI "explain what's going on" buttons; collaboration; personalised reminders; rich profiles.
- Context before/after a story beyond the existing "Open on Sefaria" link.

## 4. Sign-up by time: minutes per week (decided)

**Decided (Simon, from his call with Daniel, 2026-11-09): people choose minutes per week**, until the yahrzeit.
Buttons: 5 / 10 / 15 / 30 min a week + "other". The system converts that to a total
(`minutes/week × weeks left until the yahrzeit`) and assigns stories for **the next 4 weeks** at a time, so nobody
is handed months of stories up front and the pool is not emptied by a few early sign-ups. When a person's batch is
learned (or 4 weeks pass), "Get next stories" assigns the next batch at the same rate.
`users/{uid}.minutesPerWeek` replaces `pledgedMinutes` in §5.

Scale check (mean story 234 words ≈ 1.6 min at 150 wpm): 15 min/week ≈ 40 stories/month per person. Today's 367
stories (~10 h) need about 10 people at 15 min/week for one month; ~3,000 stories (~80 h) over ~43 weeks need about 8 people at 15 min/week, or more people at less.

## 5. Data model (Firestore)

Three things, nothing more:

```
users/{uid}         { name, email, createdAt, minutesPerWeek,   // from Google; the rate they chose
                      community: null }                         // reserved for the post-sign-up question (Later)
claims/{storyId}    { uid, list: "v1", assignedAt, doneAt: null | timestamp }
                    // doc id = story id → at most one live claim per story, enforced by the database
meta/list           { current: "v1", publishedAt: "2026-11-xx" }
```

- **Unclaimed** = no claim doc. **Taken** = claim with `doneAt == null`. **Learned** = `doneAt` set.
- No names or emails in `claims` (the field view is public; it shows status, never who).
- Who participated (for Daniel) = `users`, exportable (§8).

## 6. Assignment algorithm

1. Read all claims (one query) and the static story list for the current version.
2. **Available** = no claim, or a claim that is **stale**: `doneAt == null` and `assignedAt` older than **30 days**
   (constant). Stale claims return to the pool automatically; nobody has to release them.
3. Order available stories in **reading order** (tractate order as on the home page, then daf, then segment), and take
   from the **first open gap**, so a person gets **consecutive stories** (often the same daf) instead of a scatter,
   and the list fills from the front, which makes "how many are left" honest.
4. Add stories until the total minutes ≥ pledge. Always at least one story; stop before exceeding the pledge by more
   than 50% unless that would mean zero stories.
5. Write the claims in **one transaction** that re-checks each story is still available; if someone else got one first,
   retry with the next (Firestore transactions retry automatically on conflict).
6. **Not finishing:** after 30 days an unfinished claim is stale and can be reassigned; the original person still sees
   it, marked "released — someone else may take it". Their "Mark as learned" still works if nobody has re-taken it.
   A person can also press **"Give back"** on any unfinished story (deletes their claim).
7. **Pool empty:** "Every story is taken. K are still being learned." No second readers in v1.

Security rules (no server code in v1):
- `claims`: anyone may read. Create only if signed in and `uid == auth.uid`. Take over only if the existing claim is
  stale. Update only your own claim, only `doneAt`. Delete only your own unfinished claim.
- `users/{uid}`: read/write only by that user.
- `meta`: read-only for clients.

## 7. List versions and stable ids

- v1 freezes today's ids (`tractate-daf-start-end`). `site/data/index.json` gains `list_version` and `published_at`.
- A **new list (v2, …)** is built by the same script and ships with `site/data/lists/v1_to_v2.json`:
  each v1 id → the v2 id it **overlaps most by segments** (overlap, never an exact key — Lesson 36), or `null`.
- A one-off migration script rewrites claims through that map: a learned v1 story stays learned on its v2 match;
  a taken one stays taken. A v1 story with no match keeps its claim under its old id, counted as history, not as
  progress on the new list. Splits/merges with ambiguous matches are printed for a person to decide, never guessed.
- New stories in v2 simply start unclaimed. Progress is always reported against the **current** list.

## 8. Backend: decision

The static site cannot hold shared state; it needs sign-in and a small database.

| | Firebase Auth + Firestore | Supabase (Postgres + Auth) | Vercel functions + hosted Postgres + Auth.js |
|---|---|---|---|
| Google SSO | Built in, one switch | Needs a Google OAuth client set up in GCP, pasted into Supabase | Needs the same OAuth client plus Auth.js code |
| Free tier | Spark: no card, so it can never charge | Free projects **pause after a week without traffic**: a real risk over 10 months | Free tiers, but three services to keep alive |
| Code we must own | Static pages + security rules. **No server** | Static pages + row-level-security SQL | A server (API routes), schema, migrations |
| For a non-engineer owner | Google console Simon already uses; data viewable as a table | One more account | Most moving parts |
| Data export | `firebase auth:export` (sign-ups) + a small script for claims | SQL / CSV | SQL / CSV |

**Decision: Firebase Auth + Firestore, on a NEW Google Cloud project, on the free Spark plan. Site stays on Vercel.**

**Project: `septimus-stories`** (created 2026-11-08; Firestore `nam5`; Google sign-in on; authorised domain `talmud-stories.vercel.app`, a placeholder: add the final domain there when it exists).

**(a) Can v1 stay on Spark (no billing)? Yes.** Checked against what v1 needs:
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

## 9. Build order (one PR each, branch `septimus/signup-*`, titles start `[Septimus]`)

| PR | What | Done when |
|---|---|---|
| a | Word count + reading time in the export; tests | Every story has `words` and `minutes`; totals equal §2; tests pass |
| b | Firebase wiring, Google sign-in, "how much time?", assignment, rules | At 390 px: sign in, pledge 15 min, get consecutive stories summing ≈15 min; a second account cannot get the same stories; rules tested in the Firestore emulator |
| c | My stories, mark as learned, give back, progress field + counts | Marking learned updates the field on another device; counts per tractate add up to the story totals |
| d | About Joe Septimus page | Linked from the home page; placeholder text clearly marked for Daniel |

Each verified in a real browser at phone width (Playwright, Chromium) before it is called done.
`python3 -m pytest tests/test_site_data.py tests/test_bookkeeping.py -q` before each push.

## 10. Risks

| Risk | Handling |
|---|---|
| The pool empties in days (list is ~10 h; a big launch could take it all at once) | Expected and fine — it means the goal is reachable. Message says so; second readers are a v2 option |
| People take stories and vanish | 30-day stale rule returns them to the pool; "K still being learned" stays visible |
| A boundary change in a later list breaks someone's progress | Overlap map + migration script (§7); nothing is ever deleted |
| Emails collected without saying so | Sign-in screen says: "We'll use your email only to send occasional reminders about this project." |
| Yevamot stories are not expert-reviewed | Already labelled "not yet reviewed"; whether they count toward "all the stories" is Simon/Daniel's call |
| Yahrzeit date unconfirmed | Config value; shown as "by 8 Elul 5787" once Daniel confirms |

## 11. Open questions

1. **Backend:** Firebase on a new project, Spark plan, Vercel hosting (§8). Confirm when the finder plan is approved.
2. Time model: one-time total (default) vs minutes per week.
3. Daniel to confirm the yahrzeit (Friday 10 September 2027) and supply the wording for the Joe Septimus page.
4. Do the "not yet reviewed" tractates count toward "all the stories" on the progress bar? (Default: yes, labelled.)

## 12. Found while planning (fixed in PR a)

`main`'s `site/data/` predates Jeff's 2026-10-25 rulings (#68). Rebuilding adds `ketubot-65a-10-10` (borderline) and
drops `gittin-89a-19-19`, so 2 tests in `tests/test_site_data.py` fail on `main` (note set and extensions no longer
match the story set). PR a rebuilds the data and reconciles the note/extension files; the new story's note stays hidden
until approved.
