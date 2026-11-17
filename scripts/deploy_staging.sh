#!/bin/bash
# Deploy the current checkout's site/ folder to the STAGING site, https://talmud-stories-staging.vercel.app
# (docs/technical/septimus-staging.md). Never touches the real site, talmud-stories.vercel.app.
# It names the staging Vercel project explicitly, so it does not matter which project site/.vercel is linked to.
# These two ids are not secrets.
#   ./scripts/deploy_staging.sh            # deploy site/
#   ./scripts/deploy_staging.sh --rules    # also deploy firestore.rules to the staging database
set -euo pipefail
cd "$(dirname "$0")/.."
export VERCEL_ORG_ID=team_f7gLUYzpaJL91awl2OKKAFP3
export VERCEL_PROJECT_ID=prj_cFJ3kWSvgRDXlgCSoRHXyoa7JYxT   # talmud-stories-staging
echo "Deploying $(git branch --show-current) @ $(git rev-parse --short HEAD) to staging"
(cd site && vercel deploy --prod --yes)
if [ "${1:-}" = "--rules" ]; then
  firebase deploy --only firestore:rules --project septimus-stories-staging
fi
