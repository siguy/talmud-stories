# The staging site

A second copy of the Septimus site for trying changes before they reach the real one. Set up 2026-11-15.

| | Real site | Staging |
|---|---|---|
| Address | `talmud-stories.vercel.app` | **`talmud-stories-staging.vercel.app`** (shows a "Staging" label in the top bar) |
| Vercel project | `talmud-stories` | `talmud-stories-staging` |
| Firebase project (sign-in and database) | `septimus-stories` | `septimus-stories-staging` |
| Plan | Free (Spark), no billing | Free (Spark), no billing |

**They share nothing.** A sign-up on staging is a record in the staging database only; it can be wiped at any time.
The switch is the last block of `site/config.js`: on the staging address the site uses the staging Firebase project.

## Deploy to staging

```bash
./scripts/deploy_staging.sh            # the site
./scripts/deploy_staging.sh --rules    # the site and firestore.rules
```

It deploys whatever is checked out, so say which branch is on staging when asking someone to look.

## Run the weekly script against staging

**First run 2026-11-15:** with a test launch date of Monday 2026-11-09, it handed the one test account 2 stories
(Berakhot 3a and 3b), wrote the public summary, and a second run changed nothing. The script takes its project from
the key, not from `site/config.js`, and logs `database: project …` so a run can never hit the wrong one.

It needs a service-account key for `septimus-stories-staging` (Firebase console → Project settings →
Service accounts → Generate new private key). Keep the file outside the repo if you can; `.gitignore` refuses `*firebase-adminsdk*.json` either way. Then:

```bash
pip install -r requirements-septimus.txt
FIREBASE_SERVICE_ACCOUNT="$(cat $HOME/keys/septimus-stories-staging-firebase-adminsdk-fbsvc-79363ae1db.json)" \
  python3 scripts/septimus_weekly.py --dry-run --date 2026-12-07 --config /path/to/a/config-with-a-launch-date.js
```

Drop `--dry-run` to write. `--config` lets a test run use a launch date without editing `site/config.js`.

## Multi-week test, 2026-11-15

`scripts/staging_multiweek_test.py`: five test accounts plus Simon's own, the weekly script run for pretend weeks 2
to 11 (launch Sunday 2026-11-08), the script playing the people between runs. 171 hand-outs, 149 different stories,
the first 149 of the list (Berakhot 3a into Shabbat 33a).

| Checked | Result |
|---|---|
| A second run of the same week changes nothing | Pass |
| New weeks continue from where the last hand-out ended; no gaps in list order | Pass |
| Nobody over their minutes; no story held by two people in one round | Pass |
| Readers (10 and 30 min) got stories every week and were never paused | Pass |
| A 10-minute person holding nothing was given a 29-minute story ("longer than usual") | Seen |
| Unread stories handed back after three weeks and given to someone else | Pass |
| Stop my stories: open stories handed back, nothing new | Pass |
| Delete my data, for real: sign-in account gone, record gone, no row carries the id | Pass |
| A person who never read: paused at week 8 (joined for week 2), nothing new after | Pass |
| Resume: stories again the next week | Pass |
| Public total equals stories really marked learned (135); per-tractate adds up | Pass |
| Database reads per run | 11 rising to 173 |

Three checks in the first version failed because the test assumed Simon's account had read nothing; he had marked
both week-1 stories learned. The script was right. Those checks were replaced.

**One thing the run showed that the rules allow but may not be wanted:** someone who learned one story in week 1
and nothing since is never paused. Simon's account let stories lapse in weeks 2, 3, 5, 6 and 8 and kept being given
more. The pause rule only caught people who had *never* learned anything. **Changed the same day (Simon):** two
lapses at least three weeks apart with nothing learned in between now pauses anyone.

The test accounts (`test-a` to `test-d`@example.com) and their rows are still on staging.

## Load test, 2026-11-15

`scripts/staging_load_test.py`: 300 pretend people (3,920 minutes a week pledged; 60% read everything, 25% half,
15% nothing) added to staging, four more pretend weeks run, then removed again.

| Week | Stories handed out | People served | Run time | Database reads |
|---|---|---|---|---|
| 13 | 1,204 | 301 | 43 s | 498 |
| 14 | 876 | 257 | 90 s | 2,010 |
| 15 | 821 | 247 | 58 s | 2,964 |
| 16 | 1,012 (and 308 handed back) | 289 | 130 s | 3,845 |
| ordinary daily run | 0 | | 26 s | 4,779 |

Free limits are 50,000 reads and 20,000 writes a day, and the job is allowed 15 minutes. With 300 people the
script uses under a tenth of the reads. Reads grow by about 1,000 a week at this size, so a 44-week campaign would
end near the limit: watch it (launch checklist, "After launch"). 300 people at these minutes learn almost all of
Shas in four weeks (1,777 of 1,897 stories).

## The scheduled job on GitHub: not tested yet

Needs the staging key stored as the repository secret `FIREBASE_SERVICE_ACCOUNT_STAGING` (Simon:
`gh secret set FIREBASE_SERVICE_ACCOUNT_STAGING < ~/keys/septimus-stories-staging-firebase-adminsdk-fbsvc-79363ae1db.json`),
and GitHub only offers "Run workflow" for a workflow file that is on `main`. So: merge, then Actions → Septimus
weekly → Run workflow with "staging" and "dry_run" ticked.

## How it was set up (to repeat or audit)

1. `PROJECT_ID=septimus-stories-staging APP_NAME=septimus-site-staging bash firebase/setup.sh`
2. Firebase console → Authentication → Get started → Google → Enable. Public-facing name
   "Stories of the Talmud (staging)"; support email: the septimus-stories Google Group.
3. Authorised sign-in domains: `talmud-stories-staging.vercel.app` added (exact host; never a wildcard).
4. `firebase deploy --only firestore:rules --project septimus-stories-staging`
5. `vercel project add talmud-stories-staging`, then the deploy script.

## To wipe staging

Firebase console for `septimus-stories-staging`: Authentication → delete the test users; Firestore → delete the
`users`, `assignments`, `runs`, `sent` and `progress` collections.
