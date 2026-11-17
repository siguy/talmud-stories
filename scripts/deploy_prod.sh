#!/bin/bash
# Deploy the REAL site, https://talmud-stories.vercel.app, from main. (Staging: scripts/deploy_staging.sh.)
# Rule: everything is tried on staging first; the real site only ever gets what is on main.
# It refuses to run unless this checkout is on main, has nothing uncommitted, and matches GitHub's main.
# These two ids are not secrets.
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$(git branch --show-current)" = "main" ] || { echo "Not on main. The real site is only deployed from main."; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "There are uncommitted changes. Commit or discard them first."; exit 1; }
git fetch -q origin main
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "This main is not the same as GitHub's main. Run: git pull"; exit 1; }
export VERCEL_ORG_ID=team_f7gLUYzpaJL91awl2OKKAFP3
export VERCEL_PROJECT_ID=prj_2QzXDZY6Szfmfjit88Jk6tf9Fbja   # talmud-stories (the real site)
echo "Deploying main @ $(git rev-parse --short HEAD) to the REAL site"
(cd site && vercel deploy --prod --yes)
