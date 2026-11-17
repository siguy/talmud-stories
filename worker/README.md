# Feedback endpoint

Turns a "Report a problem" submission on the site into a GitHub issue labelled `story-feedback`
(machine-readable JSON inside), which `scripts/feedback_triage.py` reads. It runs on Google Cloud Run;
the code (`feedback-worker.js`) is plain fetch/Request and `gcp/server.js` wraps it. The feedback repo
`siguy/talmud-stories-feedback` is private: never point `REPO` at the public main repo.

## Setup (Google Cloud Run)

Same code (`feedback-worker.js`), wrapped by `worker/gcp/server.js` (no dependencies). Effectively free at this volume,
but the project needs a billing account linked. Defaults: project `simon-main`, region `us-central1`, repo `siguy/talmud-stories-feedback` (private).

1. Create the fine-grained GitHub token (Issues read/write on the **feedback** repo only).
2. `gcloud auth login`, then `worker/gcp/set-token.sh` (hidden prompt; the token goes only into Secret Manager).
3. `worker/gcp/deploy.sh` (override with `REPO`, `ALLOWED_ORIGIN`). It prints the service URL.
4. Put the URL in `site/config.js` (`feedbackEndpoint`) and redeploy the site.
5. Token expires after a year: re-run `set-token.sh`, then `deploy.sh`. Errors: `gcloud run services logs read septimus-feedback --project simon-main --region us-central1`.

Verified 2026-10-15: a submission from the live site created a labelled issue in the feedback repo.

## Tests

`node --test worker/feedback-worker.test.mjs` (Node 20+, no install). The python suite runs it too
(`tests/test_site_data.py::test_feedback_worker_builds_a_safe_issue`, skipped if `node` is missing), so `python3 -m pytest tests/ -q` covers the worker.
No network: GitHub is a mocked `fetch`. Covered: every story id in `site/data` builds an issue, whole-story and
per-passage, with nothing the app sends dropped; bad ids and categories refused; every field capped; the handler's
CORS, methods, bad JSON, honeypot, the exact GitHub request, upstream 4xx/5xx and network failure; and
`gcp/server.js` (the deployed wrapper) spawned for real: round trip, the 100 KB limit, and staying up when GitHub is
unreachable.

## Redeploying after a change (2026-11-14 fixes)

The live service still runs the old code, which accepts only Ketubot, Kiddushin, Gittin and Yevamot story ids:
feedback on the other 33 tractates gets a 400 and the reader sees "Sorry, that did not send". To ship the fix:

1. `gcloud auth login` (if the session has expired).
2. `worker/gcp/deploy.sh`. The token secret (`feedback-github-token`) is already in Secret Manager, so there is
   **no** `set-token.sh` step unless the token has expired (created 2026-10-15, 1-year expiry). The script sets
   `REPO=siguy/talmud-stories-feedback` and `ALLOWED_ORIGIN` of production plus staging (comma-separated; a staging report is tagged `site: staging` and set aside by triage).
   **Check that origin is exactly the address you open the site at.** A browser refuses the worker's answer from
   any other origin (a Vercel preview URL such as `talmud-stories-git-....vercel.app`, a custom domain), and the
   reader sees the same "did not send" message. Override with `ALLOWED_ORIGIN=https://... worker/gcp/deploy.sh`.
3. The service URL does not change, so `site/config.js` needs no edit.
4. Check: submit a note on any non-reviewed tractate (e.g. an Avodah Zarah story) and confirm an issue labelled
   `story-feedback` and `tractate:avodah_zarah` appears in the feedback repo. Errors:
   `gcloud run services logs read septimus-feedback --project simon-main --region us-central1`.

The site needs a redeploy only for the fallback fix in `site/app.js` (the "Send via GitHub instead" link built a
URL too long for GitHub on long passages, with the JSON cut off mid-way). The worker fix does not depend on it.
