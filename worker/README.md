# Feedback worker (one-time setup, ~10 min)

Turns a "Report a problem" submission on the site into a GitHub issue labelled `story-feedback`
(machine-readable JSON inside), which Claude reads directly. Free Cloudflare tier is plenty.

1. Create a **fine-grained GitHub token**: only this repo, permission *Issues: Read and write*, nothing else.
2. `npm i -g wrangler && wrangler login`
3. From this folder: `wrangler deploy feedback-worker.js --name septimus-feedback --compatibility-date 2026-10-01`
4. `wrangler secret put GITHUB_TOKEN --name septimus-feedback` (paste the token)
5. In the Cloudflare dashboard → the worker → Settings → Variables: `REPO` = `siguy/talmud-stories`;
   `ALLOWED_ORIGIN` = the site's URL once it is hosted.
6. Put the worker URL in `site/config.js` (`feedbackEndpoint`).

Until step 6, the site's form falls back to opening a pre-filled GitHub issue (needs a GitHub login).
If the repo is public, feedback issues are public: keep the repo private or tell people not to leave contact details.

## Alternative: Google Cloud (instead of Cloudflare)

Same function, ported to Cloud Functions 2nd gen in `worker/gcp/`. Effectively free at this volume (monthly free tier)
but the project **must have a billing account linked** (a card).

1. Create the fine-grained GitHub token as above (Issues read/write on this repo only).
2. `gcloud auth login`, then create or pick a project and link billing.
3. `PROJECT=<project-id> ./worker/gcp/deploy.sh` (optional `REGION`, `ALLOWED_ORIGIN`, `REPO`). It enables the APIs, asks for the token
   at a hidden prompt (stored only in Secret Manager), deploys with `--max-instances=2`, and prints the URL.
4. Put the URL in `site/config.js` (`feedbackEndpoint`), redeploy the site, then re-run the script with
   `ALLOWED_ORIGIN=https://<the site>` to lock CORS.

Status: the handler logic is unit-tested with mocks (valid/invalid payload, honeypot, wrong method, GitHub failure); the deploy
script is syntax-checked but has **not been run against a real GCP project** (the cloud sandbox has no GCP credentials).
