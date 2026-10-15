#!/usr/bin/env bash
# Deploy the feedback function to Google Cloud (Cloud Functions 2nd gen = Cloud Run). Run on a machine where
# `gcloud auth login` is done. Usage:  PROJECT=my-project ./deploy.sh
#   optional: REGION (default us-central1, a free-tier region), REPO (default siguy/talmud-stories),
#             ALLOWED_ORIGIN (the site's URL; default * until the site is hosted), NAME (default septimus-feedback)
# The GitHub token (fine-grained, Issues read/write on this one repo) is read from a hidden prompt and goes
# only into Secret Manager: never into the repo, a flag, or shell history.
set -euo pipefail
: "${PROJECT:?set PROJECT=<gcp project id>}"
REGION="${REGION:-us-central1}"; REPO="${REPO:-siguy/talmud-stories}"; ALLOWED_ORIGIN="${ALLOWED_ORIGIN:-*}"; NAME="${NAME:-septimus-feedback}"
HERE="$(cd "$(dirname "$0")" && pwd)"

gcloud config set project "$PROJECT" >/dev/null
if [ "$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)')" != "True" ]; then
  echo "Billing is not enabled on $PROJECT. Link a billing account (console.cloud.google.com/billing) and re-run." >&2; exit 1
fi
gcloud services enable cloudfunctions.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

if ! gcloud secrets describe github-feedback-token >/dev/null 2>&1; then
  gcloud secrets create github-feedback-token --replication-policy=automatic
fi
if [ -n "${GITHUB_FEEDBACK_TOKEN:-}" ]; then TOKEN="$GITHUB_FEEDBACK_TOKEN"   # non-interactive: export it in YOUR shell, never paste it into a chat
else read -r -s -p "Paste the GitHub fine-grained token (hidden), then Enter: " TOKEN; echo; fi
printf '%s' "$TOKEN" | gcloud secrets versions add github-feedback-token --data-file=-
unset TOKEN GITHUB_FEEDBACK_TOKEN
# the function's runtime service account must be able to read the secret
SA="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding github-feedback-token --member="serviceAccount:$SA" --role=roles/secretmanager.secretAccessor >/dev/null

BUILD="$(mktemp -d)"; trap 'rm -rf "$BUILD"' EXIT
cp "$HERE/index.js" "$HERE/package.json" "$HERE/../feedback-worker.js" "$BUILD/"
gcloud functions deploy "$NAME" --gen2 --runtime=nodejs20 --region="$REGION" --source="$BUILD" \
  --entry-point=feedback --trigger-http --allow-unauthenticated \
  --memory=256Mi --max-instances=2 --min-instances=0 --timeout=30s \
  --set-env-vars="REPO=$REPO,ALLOWED_ORIGIN=$ALLOWED_ORIGIN" \
  --set-secrets="GITHUB_TOKEN=github-feedback-token:latest"
URL="$(gcloud functions describe "$NAME" --gen2 --region="$REGION" --format='value(serviceConfig.uri)')"
echo; echo "Done. Put this in site/config.js as feedbackEndpoint: $URL"
echo "Then lock CORS to the real site:  re-run with ALLOWED_ORIGIN=https://<your-site>"
