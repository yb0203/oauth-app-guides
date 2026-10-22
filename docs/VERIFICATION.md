# Verification report

The assignment asks us to check a sample of the guidance against real sources or setup attempts, and to show what we learned, corrected, or couldn't verify. Here is everything we checked, how we checked it, what changed as a result, and what's still open.

**The one rule behind all of it:** a claim is labeled **DOCS** only if its exact quote was re-found on the live page, in its visible or hidden text, by code (`experiments/oauth-capture-poc/capture.py` and `backend/app/verify.py`), never by a language model's say-so. Anything we couldn't re-find is **UNCERTAIN**, and it's shown, not hidden.

## 1. Research verification: 10 providers (2026-10-19)

Source: `research/providers/_verification.md`.

- **What:** an independent pass re-opened **about 28 live pages** across all 10 providers and checked **about 75 quoted strings and numbers**. It fetched raw HTML with `curl` instead of the summarizing fetch tool the researchers had used.
- **Corrected:** one GitHub quote was real but attributed to the wrong page. We fixed the citation.
- **Learned:** provider docs contradict themselves. Xero's FAQ says 2 uncertified apps per organisation, and its limits page says 5. Google's pages give both "3–5 business days" and "about 10 business days" for sensitive-scope review. We show both sides of each conflict instead of picking one.
- **Composio side** (`research/composio/_verification.md`): 5 of 5 managed/BYO tags matched Composio's own toolkit pages; 123 managed and 211 BYO were re-counted from the table; 5 of 5 claims about Composio's auth model held. **New finding:** Composio's managed HubSpot app is itself still awaiting HubSpot approval.

## 2. Setup-attempt proof of concept: 5 apps (2026-10-21)

Source: `experiments/oauth-capture-poc/README.md`.

- **What:** agents tried to do the OAuth app setup themselves, with a read-only browser, on GitHub, Google, Spotify, Xero and Shopify.
- **Result:** **all 5 consoles redirected to sign-in after one hop.** Every step after that is human-only: accepting terms, Register, payment, review. We changed the product design because of this: no agent-driven setup, a sign-in wall probe instead (TESTED evidence), and agent-drafted materials.
- **Quotes:** 68 of 68 verified by the subagents, and 8 of 8 in an independent re-check.
- **Corrected:** one false negative. A subagent reported that Google's "100 test users" limit didn't exist; it does, inside a collapsed section that the checker skipped. **The checker now searches hidden text too**, and records `found_in: hidden_section`.
- **Stale material found:** both Shopify docs URLs we had saved now redirect to different pages, and a Xero docs screenshot shows "25 organisations" while the text says 5. This is why the agent finds docs fresh on every run.
- **Considered and rejected:** Browser Use Cloud with disposable test accounts. It would show real forms on easy providers, but it doesn't solve account creation, new-device sign-in checks, approvals, or apps the evaluator submits live.

## 3. Curated guides: 5 apps (2026-10-21)

Source: `data/guides/_quote_checks.md` (247 logged rows).

- Every DOCS quote in the five curated guides was re-checked live: Gmail 46, Xero 48, Shopify 49, Spotify 41, plus GitHub's (checked by the main session).
- **Failures:** a few quotes were tried on the wrong page or were worded differently from the page. Each was **reworded to the page's exact text or dropped**; none remains labeled DOCS without a match.
- **Spot checks:** the main session re-checked 2 random quotes per guide; all were found.
- All 5 guides validate against `data/schema/guide.schema.json`, and every evidence summary was recounted from the guide's own evidence objects. Two guides had used a different counting rule, which we fixed and then defined in the contract.

## 4. Fetching method check (2026-10-21)

- Plain HTTP (no browser) found **4 of 5** test quotes, including Google's hidden-section limit, because collapsed sections are still in the HTML. It failed on Xero's JavaScript-rendered docs, on Spotify's and Xero's JavaScript sign-in redirects, and on Shopify's dashboard (HTTP 406).
- **Decision:** HTTP first, with a browser fallback. Production runs on Vercel's Python runtime, which has no Chromium, so the fallback is off there and those cases become UNCERTAIN.

## 5. Live agent evaluation on production (2026-10-22)

Source: `evals/RESULTS.md`, scored by `evals/score.py` against the answer key in `docs/TEST_PLAN.md` §4.1.

| Round | Tier accuracy (GitHub, Gmail, Spotify) | Fallback drafts | Inflated labels | What changed afterwards |
|---|---|---|---|---|
| 1 | 1.5 of 3 | 1 (Gmail writer timed out) | 0 | Split the writer into two time-boxed parts; tier rubric; official org domains; console seeding |
| 2 | 2 of 3 | 0 | 0 | Instant tier when docs show no review; topic-relevance filter |
| 3 | 3 of 3 | 0 | 0 | Final version |

- **Unseen apps** (Todoist, Zoom, Dropbox, Asana, Calendly): each produced a bring-your-own guide from official docs in about 50 to 90 seconds.
- **Corrections driven by the evals:**
  - Guides for Composio-managed apps had answered "use the managed app"; they now always cover registering your own app.
  - Third-party pages had been labeled DOCS; now only official domains count.
  - Off-topic pages from the same vendor (Google Cloud connector docs) had produced junk "limits"; they're now filtered out.
- **Known misses:** the free models don't always extract numeric caps (Gmail's 100-user limits; mean key-fact recall is 0.72). The curated guides have them.

## 6. What we could not verify

- Anything behind a console login: real form fields, logo limits, where client secrets are generated, consent-screen warnings. These appear as UNCERTAIN, or as "check on first sign-in".
- Community-reported wait times, which are anecdotal and mostly seen through search snippets.
- Costs with no official figure, such as Google's CASA security assessment.
- Whether providers enforce their written terms against shared connector-platform apps (HubSpot token brokering, Xero aggregation). That's flagged as uncertain.
- Every fact is true only as of its "last verified" date. Spotify, Slack, Shopify, Xero, HubSpot and Google all changed their rules during 2026.

## 7. Performance and cost (production, 2026-10-22)

Measured on production (Vercel Python, free OpenRouter models). Each run reports its own `data-run-stats` (per-stage seconds, model calls, and the provider-reported input/output tokens per model). The batch is `evals/perf.py`; raw streams are `evals/runs/perf-*.sse`. **Actual spend** is the change in OpenRouter account usage across the batch, read from the account before and after. **Paid-model equivalent** prices the same tokens at the paid (non-`:free`) variant of each model, from OpenRouter's public model list. MiniMax M3.1 Flash has no paid variant, so its tokens are unpriced.

### Per run

| Model | App | Total | find_docs | research | synthesize | probe + verify | LLM calls (failed) | Input tokens | Output tokens | Actual cost | Paid equivalent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MiniMax M3.1 Flash (default) | GitHub | 59.1 s | 6.9 s | 24.4 s | 27.2 s | 0.3 s | 7 (0) | 21,632 | 9,992 | $0.00 | n/a (free-only model) |
| MiniMax M3.1 Flash | Gmail | 72.3 s | 10.2 s | 17.2 s | 43.5 s | 0.4 s | 7 (0) | 24,206 | 11,382 | $0.00 | n/a |
| MiniMax M3.1 Flash | Spotify | 50.8 s | 6.4 s | 16.1 s | 27.9 s | 0.2 s | 7 (0) | 22,300 | 10,741 | $0.00 | n/a |
| MiniMax M3.1 Flash | Notion | 78.1 s | 15.7 s | 18.7 s | 43.3 s | 0.1 s | 7 (0) | 24,717 | 9,973 | $0.00 | n/a |
| MiniMax M3.1 Flash | Zoom | 69.3 s | 15.7 s | 15.4 s | 38.0 s | 0.1 s | 7 (0) | 22,793 | 9,546 | $0.00 | n/a |
| MiniMax M3.1 Flash | Asana | **stream went silent twice** after the first research result (see below) | | | | | | | | $0.00 | |
| Nemotron 3 Ultra | GitHub | 95.7 s | | | 59.2 s | | 7 (0) | 22,835 | 8,535 | $0.00 | $0.034 |
| Nemotron 3 Ultra | Spotify | 64.5 s | | | 45.8 s | | 7 (0) | 20,025 | 6,755 | $0.00 | $0.028 |
| Nemotron 3 Ultra | Asana | 69.2 s | | | 39.7 s | | 6 (0) | 17,859 | 5,948 | $0.00 | $0.025 |

### Summary

| | MiniMax M3.1 Flash (default) | Nemotron 3 Ultra |
|---|---|---|
| Mean time per guide | **66 s** (5 runs: 51–78 s) | 77 s (3 runs: 65–96 s) |
| Mean tokens per guide (in / out) | 23.1k / 10.3k | 20.2k / 7.1k |
| Model calls per guide | 7 | 6–7 |
| Actual spend | **$0.00** (account usage change: $0) | **$0.00** |
| Same tokens on the paid model | n/a (no paid variant) | **about $0.03 per guide**, so about $3 for a 100-guide library |

- **Where the time goes:** writing the guide (`synthesize`, two parallel LLM calls) takes 45–60% of each run, and reading pages (`research`, one extraction per page in parallel) another 25–40%. Search, fetching, the console probe and quote verification together take about 10 seconds. The deterministic work is cheap; the model calls are the cost.
- **Ask this guide:** one LLM call. The first version took about 37 seconds; after moving `/ask` to the faster model with a 20-second cutoff and a deterministic fallback, answers come back in about 5 seconds.
- **Throughput on free models:** about 7 requests per guide against OpenRouter's free limit of 20 requests per minute, or 1,000 per day once 10 credits are bought (about 140 guides a day). That's fine for a demo, but a production library would use the paid variant at about 3 cents a guide.
- **Reliability finding (open):** Asana on MiniMax went silent twice on production, both times right after the first research result. The production logs show **the run kept going on the server** (it reached the guide-writing step minutes later), and the response headers rule out proxy buffering. So the event stream to the client stopped while the pipeline continued. We couldn't reproduce it locally: 3 Asana runs took 51–62 s with at most 0.67 s of event-loop lag. Mitigations: the stream is now exception-proof (any failure becomes a visible error and the stream ends cleanly), a 240-second run watchdog, and a run-status endpoint the page polls when the stream goes quiet, so it can still load the published guide.
