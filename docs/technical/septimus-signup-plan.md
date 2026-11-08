# "Learn all the stories" sign-up — plan (v1)

*Written 2026-11-08. Builds on the reader in [`septimus-viewer-plan.md`](septimus-viewer-plan.md) (do not rebuild it).
Work item: [`work/2026-11-08-septimus-signup.md`](../../work/2026-11-08-septimus-signup.md).*

## 1. Goal

Daniel Septimus wants family, friends and community to **collectively learn every story** by the first
yahrzeit of his father, Joe Septimus (about 9–10 months out; **exact date not confirmed**, Simon to confirm with Daniel).
Jeff Rubenstein is fine with it. v1 = the **bare minimum** that lets this happen; everything else waits for v2.

## 2. The numbers that shape the design (measured 2026-11-08 on `site/data/*.json`)

| | stories | English words | median words/story | hours at 150 wpm | hours at 230 wpm |
|---|---|---|---|---|---|
| Ketubot | 100 | 25,963 | 182 | 2.9 | 1.9 |
| Kiddushin | 53 | 11,961 | 184 | 1.3 | 0.9 |
| Gittin | 119 | 26,068 | 181 | 2.9 | 1.9 |
| Yevamot | 95 | 21,985 | 163 | 2.4 | 1.6 |
| **All** | **367** | **85,977** | **176** | **9.6** | **6.2** |

Words = whitespace tokens of the English with HTML stripped (the Davidson translation, bold literal + plain gloss).

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

## 4. Sign-up by time: default and the open question

**Default (proposed): a one-time total.** "I'll give 15 minutes." No schedule, no per-day amount, no deadline
other than the yahrzeit. Reason: the whole list is ~10 hours, so per-day framing assigns fractions of a story.
People who want more press "Give more time" and get another batch.

Alternative discussed on the call: **minutes per week until the yahrzeit**. Not v1 unless Simon/Daniel prefer it;
it changes only the copy and the multiplier (minutes/week × weeks left), not the data model.

## 5. Data model (Firestore)

Three things, nothing more:

```
users/{uid}         { name, email, createdAt, pledgedMinutes,   // from Google; pledged = running total
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

## 8. Backend: options and recommendation

The static site cannot hold shared state; it needs sign-in and a small database.

| | Firebase Auth + Firestore | Supabase (Postgres + Auth) | Vercel functions + hosted Postgres + Auth.js |
|---|---|---|---|
| Google SSO | Built in, one switch | Needs a Google OAuth client set up in GCP, pasted into Supabase | Needs the same OAuth client plus Auth.js code |
| Cost at hundreds of users | Free tier covers it (50k reads/day). On `simon-main` (billing already linked) it is pay-as-you-go: cents/month | Free tier, but **free projects pause after a week without traffic** — a real risk over 10 months | Free tiers, but three services to keep alive |
| Code we must own | Static pages + security rules. **No server** | Static pages + row-level-security SQL | A server (API routes), schema, migrations |
| For a non-engineer owner | Google Cloud console Simon already uses; data viewable in a web table | One more account and dashboard | Most moving parts |
| Data export | Console, `gcloud firestore export`, or a small script → CSV | SQL / CSV, easiest | SQL / CSV |
| Fits Simon's accounts | Google Cloud (`simon-main`, logged in; feedback endpoint already there) | New account | Vercel (yes) + a DB vendor |

**Recommendation: Firebase Auth + Firestore on the existing Google Cloud project `simon-main`.** Site stays on Vercel.
Fewest moving parts, no server to keep running, Google sign-in is native, and it lives where the feedback endpoint
already lives. Set a $5 budget alert on the project.

Notes: the Firebase web config (including its "API key") is meant to be public and goes in `site/config.js`; access
is controlled by the security rules and the authorised-domain list, not by hiding it. Restrict the key to the site's
domain in the console. No other secret is needed in v1.

**What Simon does after confirming (~10 min, his login):** add Firebase to `simon-main`, enable Google sign-in,
create the Firestore database, add the site's domain to authorised domains, copy the web config. Claude writes the rules
and a deploy command for them.

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
| Yahrzeit date unconfirmed | Not used in v1 logic; shown on the page only once confirmed |

## 11. Open questions

1. **Backend:** Firebase on `simon-main` (recommended) — confirm. *(asked 2026-11-08)*
2. Time model: one-time total (default) vs minutes per week.
3. Exact yahrzeit date; Daniel's wording for the Joe Septimus page.
4. Does Yevamot (not yet reviewed) count toward "all the stories" for the progress bar?

## 12. Found while planning (fixed in PR a)

`main`'s `site/data/` predates Jeff's 2026-10-25 rulings (#68). Rebuilding adds `ketubot-65a-10-10` (borderline) and
drops `gittin-89a-19-19`, so 2 tests in `tests/test_site_data.py` fail on `main` (note set and extensions no longer
match the story set). PR a rebuilds the data and reconciles the note/extension files; the new story's note stays hidden
until approved.
