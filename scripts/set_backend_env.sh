#!/usr/bin/env bash
# Set the backend's production env vars on Vercel. Secrets are read from backend/.env and piped
# straight into the CLI; they are never echoed.
set -euo pipefail

SCOPE="${VERCEL_SCOPE:-legalowl}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="${STAGE_DIR:-$ROOT/.deploy/backend}"
FRONTEND_ORIGINS="${FRONTEND_ORIGINS:-https://oauth-guides-web.vercel.app,http://localhost:3000}"

cd "$STAGE"
[ -f .vercel/project.json ] || { echo "Run scripts/deploy_backend.sh first (it links the project)."; exit 1; }

key="$(grep -E '^OPENROUTER_API_KEY=' "$ROOT/backend/.env" | head -1 | cut -d= -f2-)"
[ -n "$key" ] || { echo "OPENROUTER_API_KEY missing from backend/.env"; exit 1; }

set_var() {  # name value
  vercel env rm "$1" production --yes --scope "$SCOPE" >/dev/null 2>&1 || true
  printf '%s' "$2" | vercel env add "$1" production --scope "$SCOPE" >/dev/null
  echo "set $1"
}

set_var OPENROUTER_API_KEY "$key"
set_var LLM_MODE live
set_var BROWSER_FALLBACK off
set_var GENERATED_DIR /tmp/generated
set_var CORS_ORIGINS "$FRONTEND_ORIGINS"
unset key
