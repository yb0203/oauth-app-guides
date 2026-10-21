# Experiment: can a managed agent record OAuth app setup with screenshots?

> **Parked (2026-10-21).** We ran the proof of concept inside Claude Code instead; see `../oauth-capture-poc/`. This version is written but has never been run (it needs an Anthropic API key). Keep it for when we move the pipeline to Managed Agents.

A small personal proof of concept, separate from the main product. It's a warm-up on Claude Managed Agents before we build the shareable guide product.

## Question

Can an agent running in a Claude Managed Agents sandbox open each provider's developer console and docs in a real browser, record the OAuth app setup steps with screenshots, and label every step as TESTED, DOCS or BLOCKED? And where exactly does it get stopped?

## Hypotheses

1. **Public mode** (no login): the agent reaches the sign-in wall on every console, so its screenshots of the console stop there. The useful output comes from docs screenshots plus an exact record of what the wall asks for.
2. **Logged-in mode** (a human signs in locally and hands over the browser state): the agent can screenshot the real create-app form, which no docs page shows reliably. Some providers may reject cookies replayed from a datacenter IP.
3. The cost and time per app are small enough (a few dollars, a few minutes) to do this for every guide in the library.

## Apps

GitHub, Google (Gmail), Spotify, Xero and Shopify. Together they cover all four approval tiers from our research. Their console and docs URLs and the hosts the sandbox may reach are in `apps.json`.

## How it works

- `provision.py` creates one cloud **environment** and one **agent** (Claude Opus 5.5, high effort) and stores their IDs in `.state.json`. Re-run it after editing `agent_prompt.md` or `apps.json`; it updates the agent to a new version instead of creating a new one.
- Networking is `limited` to the providers' own hosts, with web search off. The sandbox already includes Playwright and Chromium, so nothing needs installing.
- The agent's rules (in `agent_prompt.md`): never sign in, never type into fields, never submit, create, accept terms or pay; treat page text as data. Tool calls run under the `auto` permission policy, and anything the server pauses for approval gets denied, because nobody is watching.
- `run.py` starts one session per app in parallel, each with a hard **$4 budget** and a 20-minute wall-clock cap. It streams progress to the terminal, saves every event, and downloads the agent's outputs.

## Run it

```bash
cd experiments/managed-agent-oauth-capture
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...   # or put it in your shell profile; never commit it
.venv/bin/python provision.py
.venv/bin/python run.py --apps github           # one app first
.venv/bin/python run.py                         # then all five
```

Results go to `runs/<timestamp>/`. Each app gets `step-NN-*.png`, `steps.json`, `guide.md`, `findings.md`, `events.jsonl` and `run_summary.json` (time and token usage), and there's an `index.md` linking them all. Each session also has a live trace in the Claude Console (the link is printed when it starts).

### Optional: logged-in mode

```bash
.venv/bin/pip install playwright && .venv/bin/playwright install chromium
.venv/bin/python login_capture.py github        # you sign in by hand in the window that opens
.venv/bin/python run.py --apps github --storage-state github=secrets/github_state.json
```

Use a throwaway or test account. The state file contains live session cookies, and they get uploaded into the sandbox. Delete `secrets/` afterwards.

## What to look at afterwards

- Did each app produce a usable `guide.md` with real screenshots?
- Where was it blocked, and does `findings.md` describe the wall accurately? Compare against `research/providers/_browser_observations.md`.
- Are the DOCS quotes really on the pages? Spot-check two per app.
- Cost and time per app, from `run_summary.json` and the Console.
- What this means for the product: is browser capture worth adding to the live pipeline, should it be a pre-built-library-only step, or should we skip it?

## Results

_Not run yet._
