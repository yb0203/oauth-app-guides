#!/usr/bin/env bash
# Deploy the Next.js frontend to Vercel (login: yb0203, team scope: legalowl) from the last commit,
# so half-finished edits in the working tree never ship.
set -euo pipefail

SCOPE="${VERCEL_SCOPE:-legalowl}"
PROJECT="${VERCEL_FRONTEND_PROJECT:-oauth-guides-web}"
API_URL="${API_URL:-https://oauth-guides-api.vercel.app}"
REF="${REF:-HEAD}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="${STAGE_DIR:-$ROOT/.deploy/frontend}"

mkdir -p "$STAGE"
find "$STAGE" -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} +
git -C "$ROOT" archive "$REF" frontend | tar -x -C "$STAGE" --strip-components=1

cd "$STAGE"
if [ ! -f .vercel/project.json ]; then
  vercel link --yes --project "$PROJECT" --scope "$SCOPE"
  printf '%s' "$API_URL" | vercel env add NEXT_PUBLIC_API_URL production --scope "$SCOPE" >/dev/null
fi
vercel deploy --prod --yes --scope "$SCOPE"
