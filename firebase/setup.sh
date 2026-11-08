#!/bin/bash
# One-time Firebase setup for the Septimus sign-up (docs/technical/septimus-signup-plan.md §8).
# Run on Simon's machine, where gcloud is logged in. Idempotent: every step checks before it acts.
# Free Spark plan: this script never links billing. Nothing it prints is secret.
#   PROJECT_ID=septimus-stories ./firebase/setup.sh
set -euo pipefail
PROJECT_ID=${PROJECT_ID:-septimus-stories}   # must be globally unique; pick another if taken
LOCATION=${LOCATION:-nam5}                   # Firestore multi-region (US). Cannot be changed later
APP_NAME=${APP_NAME:-septimus-site}
command -v gcloud >/dev/null || { echo "install gcloud first"; exit 1; }
command -v firebase >/dev/null || npm i -g firebase-tools
firebase login --no-localhost 2>/dev/null || true   # no-op if already logged in

# 1. Project
if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud projects create "$PROJECT_ID" --name="Septimus Stories"
fi
# 2. Firebase on the project
if ! firebase projects:list 2>/dev/null | grep -q "$PROJECT_ID"; then
  firebase projects:addfirebase "$PROJECT_ID"
fi
# 3. APIs
gcloud services enable firestore.googleapis.com identitytoolkit.googleapis.com --project "$PROJECT_ID"
# 4. Firestore database
if ! gcloud firestore databases describe --database="(default)" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud firestore databases create --location="$LOCATION" --project "$PROJECT_ID"
fi
# 5. Web app + its public config
APP_ID=$(firebase apps:list WEB --project "$PROJECT_ID" 2>/dev/null | grep -o '1:[0-9]*:web:[0-9a-f]*' | head -1 || true)
if [ -z "$APP_ID" ]; then
  firebase apps:create WEB "$APP_NAME" --project "$PROJECT_ID"
  APP_ID=$(firebase apps:list WEB --project "$PROJECT_ID" | grep -o '1:[0-9]*:web:[0-9a-f]*' | head -1)
fi
echo "--- public web config (safe to commit; goes in site/config.js) ---"
firebase apps:sdkconfig WEB "$APP_ID" --project "$PROJECT_ID"
# 6. Security rules, once firebase/firestore.rules exists (added in the sign-up PR b)
if [ -f "$(dirname "$0")/firestore.rules" ]; then
  (cd "$(dirname "$0")" && firebase deploy --only firestore:rules --project "$PROJECT_ID")
fi
cat <<EOF

Two clicks remain (no command line exists for them), in https://console.firebase.google.com/project/$PROJECT_ID/authentication
  a. Get started -> Sign-in method -> Google -> Enable -> Save
  b. Settings -> Authorized domains -> Add domain -> talmud-stories.vercel.app
Billing: none linked (Spark). Check: gcloud billing projects describe $PROJECT_ID
EOF
