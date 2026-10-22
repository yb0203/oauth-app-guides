# OAuth App Guides: verified setup and approval paths for agent builders

**Live app:** https://oauth-guides-web.vercel.app · **API:** https://oauth-guides-api.vercel.app/api/health
**Try:** open a curated guide ([Gmail](https://oauth-guides-web.vercel.app/guides/google-gmail)), toggle "Your situation", ask the guide a question, or type any app on the home page and watch the agent research it live.

## The problem, as we understood it

Every user connection an AI agent makes (a user's Gmail, Xero or Shopify) depends on a **provider OAuth app**: the client registration the developer creates at the provider. Composio supplies one ("managed") for 123 toolkits. For the other 211, and whenever a developer wants their own branding, rate limits or scopes, the developer must register their own app and often get it approved.

That's where developers get stuck. The answer depends on their situation (internal or external users, which scopes they need), on a reviewer's queue they don't control, and on rules that changed several times in 2026. A chatbot answer from memory was wrong on several of these points in our own testing (`research/providers/_verification.md`). So the product is not "write a guide". It's **a research and verification process whose output is a guide**.

## What it does

- **Five curated guides** covering all four difficulty tiers: GitHub (instant), Xero (verify to scale), Gmail and Shopify (review required), and Spotify (partner only).
- **Decision-first guide pages.** "Your situation" toggles re-render the verdict: a difficulty ladder, your hands-on hours vs the provider's wait, and confidence. For example, Gmail goes from Instant (internal only) to Review in days (send only) to Review plus a paid security audit lasting weeks (read email). The answers are kept in the URL, so a shared link keeps the decision.
- **Steps you can act on:** who does each step (you, the agent, or either, with the reason a human is needed), copy buttons for values like Composio's callback URL, warnings before irreversible steps, and an inline citation on every fact showing the exact quote, where it was found (including collapsed sections), and the source.
- **"Ask this guide":** grounded Q&A over that guide only, with citations, plus **Apply** buttons that set your situation and update the verdict. If the guide doesn't cover a question, it says so instead of guessing.
- **Live generation for any app:** the agent resolves the app against Composio's catalog, finds the provider's official docs, extracts claims in parallel, probes the developer console's sign-in wall, writes the guide, then **re-checks every quote on the live page** before publishing. You watch each stage stream in.

## Evidence model (the core decision)

Every fact carries one of four labels:
**TESTED** (observed by our tooling, for example the sign-in wall), **DOCS** (official provider docs, with the exact quote re-found on the live page), **COMMUNITY** (third-party pages), or **UNCERTAIN** (not verified, so it's shown as such and never quietly omitted).

- Quotes are checked in code, not by a model: normalized text matching over the page's visible **and hidden** text. Google hides its limits in collapsed sections, and a visible-text-only checker gave false "not found" results.
- A quote that can't be re-found is downgraded to UNCERTAIN. Conflicting docs are shown side by side (Xero's docs say 5 uncertified apps per organisation on one page and 2 on another).
- A source counts as DOCS only on the provider's own domains. Third-party pages are COMMUNITY.

## How we used agents

1. **Research (Claude Code sessions plus parallel subagents):** 10 providers researched against official docs, then a separate verification pass re-opened 28 pages and checked about 75 quotes (`research/providers/`). It found and fixed one wrong citation. A Composio catalog and prior-art study is in `research/composio/`.
2. **Setup-attempt proof of concept** (`experiments/oauth-capture-poc/`): agents tried to do the OAuth app setup themselves with a read-only browser on 5 apps. **Every console stopped at sign-in after one redirect**, and everything after that is human-only: terms, Register, payment, review. So the product doesn't pretend an agent can create the app. It probes the wall (TESTED evidence), does the research, drafts the materials (minimum scopes and their justification, consent-screen values, a privacy-policy outline), and hands over clearly at the human steps. We also considered Browser Use with test accounts; the reasoning for not using it is in that folder's README.
3. **The product's agent pipeline** (`backend/`): the code orchestrates, and free LLMs (OpenRouter) do only narrow jobs, extracting claims and writing the guide, with outputs validated against a schema. Search, fetching, the probe and verification are plain code.
4. **Building it:** an orchestrator session with separate backend, frontend and data sessions working in parallel against one contract (`docs/CONTRACT.md`).

## What we verified, and what we couldn't

| Check | Result |
|---|---|
| Research quotes re-opened by an independent pass | about 75 checked across 10 providers; 1 wrong source fixed; the rest held |
| Setup proof of concept (5 apps) | 68 of 68 quotes verified; 8 of 8 in an independent re-check; 1 false negative found (hidden text) and fixed |
| Curated guides (5) | Every DOCS quote re-checked live (`data/guides/_quote_checks.md`); all validate against `data/schema/guide.schema.json` |
| Backend tests | 302 offline tests and 13 live-network tests pass |
| Live smoke run on production (scored against our answer key, `evals/score.py`) | _see `evals/RESULTS.md`_ |

**Couldn't verify:** anything behind a console login (real form fields, logo limits, where secrets are generated), community-reported wait times (anecdotal), and costs with no official figure (Google CASA). Those show as UNCERTAIN or "check on first sign-in".

## Key decisions

- **Why not just a prompt?** Memory-based answers were stale or wrong on Spotify's user cap, GitHub's token default and the difficulty tiers. The value is live docs plus verification plus structure plus Composio specifics. See `docs/SPEC.md` §1 and §14.
- **Focused scope:** depth on the BYO OAuth-app path (registration, review, limits, gates), across 5 varied apps plus live generation, rather than shallow coverage of 100.
- **Bring-your-own first:** even for Composio-managed apps, the guide covers registering your own app; the managed option goes in "Should you bring your own app?".
- **No agent-driven setup,** based on the proof of concept: the agent probes and prepares; the human signs in, accepts terms and submits.
- **HTTP first, browser as fallback:** a plain HTTP fetch found 4 of 5 quotes. On the Vercel Python host there's no Chromium, so the fallback is off (`BROWSER_FALLBACK=off`) and JavaScript-only pages are marked UNCERTAIN.
- **Free models only** (OpenRouter), with code doing everything a model doesn't need to do.

## Limitations

- Generation takes about 1 to 4 minutes on free models. Long or flaky runs end in a clearly labeled degraded guide, never a hang.
- On production, JavaScript-only docs and JavaScript sign-in redirects (for example Xero, Spotify) can't be rendered without Chromium, so those probes and claims may show as UNCERTAIN. Locally, with Playwright installed, they work.
- Generated guides are stored in the function's temporary storage, so a permalink to a generated guide can expire on a cold start. Curated guides are permanent.
- Free-model rate limits apply (20 requests per minute). Concurrent generations may slow down.
- A guide is true as of its "last verified" date. Provider rules change often.

## Run it locally

```bash
# backend (Python 3.12)
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env              # add OPENROUTER_API_KEY; LLM_MODE=fake replays a labeled demo run
.venv/bin/uvicorn app.api:app --port 8000
.venv/bin/pytest -m "not network"

# frontend (Node 22+)
cd frontend && npm install && npm run dev      # http://localhost:3000, uses NEXT_PUBLIC_API_URL (default http://localhost:8000)
```

Deploy: `scripts/deploy_backend.sh` (Vercel Python), `scripts/set_backend_env.sh` (env vars, secrets read from `backend/.env`, never printed), and `scripts/deploy_frontend.sh` (deploys from git HEAD).

## Repository map

`docs/` spec, test plan, contract · `research/` provider and Composio research with verification logs · `experiments/` setup-capture proof of concept (plus a parked Managed Agents version) · `data/guides/` curated guides · `backend/` FastAPI pipeline · `frontend/` Next.js app · `evals/` scorer and run captures · `scripts/` deploy.

No credentials are in this repository.
