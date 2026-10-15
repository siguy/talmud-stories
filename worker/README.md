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

## Alternative: Google Cloud Run (this is what is deployed)

Same code (`feedback-worker.js`), wrapped by `worker/gcp/server.js` (no dependencies). Effectively free at this volume,
but the project needs a billing account linked. Defaults: project `simon-main`, region `us-central1`, repo `siguy/talmud-stories-feedback` (private).

1. Create the fine-grained GitHub token (Issues read/write on the **feedback** repo only).
2. `gcloud auth login`, then `worker/gcp/set-token.sh` (hidden prompt; the token goes only into Secret Manager).
3. `worker/gcp/deploy.sh` (override with `REPO`, `ALLOWED_ORIGIN`). It prints the service URL.
4. Put the URL in `site/config.js` (`feedbackEndpoint`) and redeploy the site.
5. Token expires after a year: re-run `set-token.sh`, then `deploy.sh`. Errors: `gcloud run services logs read septimus-feedback --project simon-main --region us-central1`.

Verified 2026-10-15: a submission from the live site created a labelled issue in the feedback repo.
