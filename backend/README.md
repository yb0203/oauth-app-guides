# Backend

FastAPI service that serves guides and runs the generation pipeline. It streams progress using the AI SDK UI message stream protocol (see `docs/CONTRACT.md` §3 and §4).

## Run

```bash
cd backend
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/playwright install chromium     # only needed for the browser fallback
cp .env.example .env                      # add OPENROUTER_API_KEY for live runs
LLM_MODE=fake .venv/bin/uvicorn app.api:app --port 8000     # recorded run, no network
.venv/bin/uvicorn app.api:app --port 8000                   # live (LLM_MODE=live)
```

Try it:

```bash
curl -N -X POST localhost:8000/api/generate -H 'content-type: application/json' -d '{"app":"xero"}'
```

## Environment

`OPENROUTER_API_KEY`, `LLM_MODEL_PRIMARY`, `LLM_MODEL_FALLBACK` (free OpenRouter models), `LLM_MODE` (`live` or `fake`), `CORS_ORIGINS`, `GENERATE_RATE_LIMIT` (generations per 10 minutes per IP, 0 disables), `FAKE_SPEED` (1 = about 15 s per fake run). `LLM_OUTPUT_MODE=tool` switches from prompted JSON to tool-call output.

## Tests

```bash
.venv/bin/pytest -m "not network"     # unit tests, no network
.venv/bin/pytest -m network           # live pages (may flake; re-run once)
```

## How a run works

`resolve` (catalog lookup) → `find_docs` (ddgs search, fetch, topic check) → `research` (one LLM extraction per docs page; every quote is checked against the page in code) → `probe` (read-only GET of the developer console) → `synthesize` (one LLM call, validated against the Pydantic `GuideContent` schema, retried, then the fallback model) → `verify` (every DOCS quote re-checked over visible and hidden text; failures become UNCERTAIN) → `publish` (JSON under `generated/`, gitignored).

About 6 to 8 LLM calls per run (cap 15), with backoff on 429. Fetching is plain HTTP first; Chromium (Playwright) is used when the page text is under 500 characters, the status is 4xx, or the result is an error.

## Docker

Build from the repository root (the API reads `data/` and `research/composio/`):

```bash
docker build -f backend/Dockerfile -t oauth-guides-backend .
docker run -p 8000:8000 --env-file backend/.env oauth-guides-backend
```

## Ask this guide

`POST /api/guides/{slug}/ask` answers questions about one guide only (CONTRACT §4b). Body: `{"question", "situation", "history"}` or a useChat body. The guide is flattened into citable facts (`app/ask.py`); fake mode and the live fallback use BM25 keyword retrieval, live mode makes one LLM call. Both are post-checked: unresolvable `[n]` markers and unknown situation options are dropped.
