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
