#!/usr/bin/env bash
# Deploy the FastAPI backend as a Vercel Python function (login: yb0203, team scope: legalowl).
#
# Vercel only uploads the project folder, but the API reads data/guides and research/composio from the
# repo root. So we stage a minimal mirror of the repo layout and deploy that:
#   index.py                      -> exposes the FastAPI `app` (Vercel's FastAPI entrypoint)
#   backend/app/**                -> the API package
#   data/guides, data/schema      -> curated guides + schema
#   research/composio/*.csv       -> catalog
# Runtime env (set once with scripts/set_backend_env.sh): OPENROUTER_API_KEY, LLM_MODE=live,
# BROWSER_FALLBACK=off (no Chromium on Vercel Python), GENERATED_DIR=/tmp/generated, CORS_ORIGINS.
set -euo pipefail

SCOPE="${VERCEL_SCOPE:-legalowl}"  # yb0203 login; legalowl is its only team
PROJECT="${VERCEL_BACKEND_PROJECT:-oauth-guides-api}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="${STAGE_DIR:-$ROOT/.deploy/backend}"

rm -rf "$STAGE/backend" "$STAGE/data" "$STAGE/research"
mkdir -p "$STAGE/backend" "$STAGE/data" "$STAGE/research/composio"
rsync -a --exclude '__pycache__' "$ROOT/backend/app" "$STAGE/backend/"
rsync -a "$ROOT/data/guides" "$ROOT/data/schema" "$STAGE/data/"
cp "$ROOT"/research/composio/*.csv "$STAGE/research/composio/"

# Runtime deps only: no test tools, no Playwright (the browser fallback is off on this host).
grep -v -i -E '^(pytest|pytest-asyncio|playwright)' "$ROOT/backend/requirements.txt" > "$STAGE/requirements.txt"

cat > "$STAGE/index.py" <<'PY'
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "backend"))

from app.api import app  # noqa: E402  (FastAPI instance picked up by Vercel)
PY

cat > "$STAGE/vercel.json" <<'JSON'
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": { "index.py": { "maxDuration": 300 } }
}
JSON

cd "$STAGE"
if [ ! -f .vercel/project.json ]; then
  vercel link --yes --project "$PROJECT" --scope "$SCOPE"
fi
vercel deploy --prod --yes --scope "$SCOPE"
