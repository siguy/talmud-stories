#!/bin/bash
# Deploys the feedback endpoint to Google Cloud Run. Run from anywhere. See worker/README.md.
set -euo pipefail
cd "$(dirname "$0")"
PROJECT=simon-main; REGION=us-central1; SERVICE=septimus-feedback
REPO=${REPO:-siguy/talmud-stories-feedback}; ORIGIN=${ALLOWED_ORIGIN:-https://talmud-stories.vercel.app}
BUILD=$(mktemp -d); cp server.js package.json "$BUILD"/; cp ../feedback-worker.js "$BUILD"/
gcloud run deploy "$SERVICE" --project "$PROJECT" --region "$REGION" --source "$BUILD" \
  --allow-unauthenticated --max-instances 2 --memory 256Mi \
  --set-env-vars "REPO=$REPO,ALLOWED_ORIGIN=$ORIGIN" \
  --set-secrets "GITHUB_TOKEN=feedback-github-token:latest"
gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format "value(status.url)"
