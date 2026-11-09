# Prompt for a local Claude Code session on Simon's machine

Paste this into Claude Code, opened in your local clone of `siguy/talmud-stories`, after `git pull`.

---

Set up Firebase for the Septimus sign-up. Read `docs/technical/septimus-signup-plan.md` §8 first.

1. Check `gcloud auth list` shows Simon's account. If not, ask him to run `gcloud auth login` himself.
2. Run `PROJECT_ID=septimus-stories ./firebase/setup.sh`. If the project id is taken, ask Simon for another and re-run
   with it. The script is safe to re-run. Do **not** link a billing account: v1 stays on the free Spark plan.
3. Ask Simon to do the two console clicks the script prints (enable Google sign-in; add `talmud-stories.vercel.app`
   to authorised domains). Wait for him to say done.
4. Put the printed web config into `site/config.js` as `firebase: {...}` and the project id in the plan. This config is
   public by design; there are no secrets in this setup. Do not commit anything else, and never commit a service
   account key or token.
5. Verify: `gcloud firestore databases describe --database="(default)" --project <id>` succeeds, and
   `gcloud billing projects describe <id>` shows `billingEnabled: false` (or no billing account).
6. Commit on a branch `septimus/signup-firebase-config`, push, and open a draft PR titled
   `[Septimus] Firebase project config`. Report the project id and the PR link in one line.
