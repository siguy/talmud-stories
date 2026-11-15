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
FIREBASE_SERVICE_ACCOUNT="$(cat /path/outside/the/repo/staging-key.json)" \
  python3 scripts/septimus_weekly.py --dry-run --date 2026-12-07 --config /path/to/a/config-with-a-launch-date.js
```

Drop `--dry-run` to write. `--config` lets a test run use a launch date without editing `site/config.js`.

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
