#!/bin/bash
# Stores the GitHub token in Secret Manager. The token is typed hidden and never written to disk or the repo.
set -euo pipefail
PROJECT=simon-main
gcloud services enable secretmanager.googleapis.com --project "$PROJECT"
read -rsp "Paste the GitHub token (hidden), then press Enter: " T; echo
if gcloud secrets describe feedback-github-token --project "$PROJECT" >/dev/null 2>&1; then
  printf %s "$T" | gcloud secrets versions add feedback-github-token --project "$PROJECT" --data-file=-
else
  printf %s "$T" | gcloud secrets create feedback-github-token --project "$PROJECT" --data-file=- --replication-policy=automatic
fi
NUM=$(gcloud projects describe "$PROJECT" --format "value(projectNumber)")
gcloud secrets add-iam-policy-binding feedback-github-token --project "$PROJECT" \
  --member "serviceAccount:${NUM}-compute@developer.gserviceaccount.com" --role roles/secretmanager.secretAccessor >/dev/null
echo "Token stored."
