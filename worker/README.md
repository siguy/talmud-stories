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
