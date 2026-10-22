# Spec: OAuth App Setup Guides for Agent Builders

Status: **v2: approved and implemented** · Date: 2026-10-21 · Owner: Yashvi
Inputs: the Composio take-home brief; `research/providers/` (10 verified provider studies); `research/composio/` (auth model, 334-toolkit catalog, prior art); `experiments/oauth-capture-poc/` (setup-capture proof of concept on 5 apps).

**What changed from v1:** the agent no longer attempts setup. It runs a sign-in wall probe plus docs research with live quote verification instead (§6 FR5, §14). The quote checker reads hidden page text. Docs URLs are found fresh on every run. Screenshots are optional. Verification is a separate stage from research. The time budget reflects the hours already spent.

---

## 1. Problem

A developer building an AI agent on Composio wants their users to connect an app (Gmail, Xero, Shopify...). Every user connection depends on a **provider OAuth app**: the client registration the developer creates with the provider. Composio supplies one ("managed") for 123 toolkits. For 211 it does not, and even for managed toolkits developers often need their own (branding on the consent screen, dedicated rate limits, scopes Google won't allow on a shared app).

Creating that OAuth app, and getting it approved, is unpredictable. It can take five minutes (GitHub) or weeks with a paid security audit (Gmail read scopes), or it can be closed to anyone who isn't an established company (Spotify). Developers can't tell in advance how hard it will be, how long it will take, what they must prepare, or what will block them.

**Why a guide product and not "ask a chatbot":** answers from memory were wrong or out of date on several points (Spotify's dev-mode cap, GitHub's token default, the Xero vs Spotify tiers). Provider docs move and contradict themselves: in our proof of concept, both Shopify docs URLs we had saved now redirect to other pages, and a Xero form screenshot says 25 organisations where the text says 5. The value is a **research and verification process** that produces a structured, dated, sourced, shareable guide, not the prose itself.

**Why this is not generic research:** the answer depends on the developer's choices (audience, scopes, distribution). It includes a third party's review queue. Some choices are permanent. The work splits between agent and human. And there are gatekeepers on both sides: the provider's reviewers and the customer's admins.

## 2. Users and jobs

| User | Job |
|---|---|
| Developer / agent builder (primary) | "Tell me how hard it is to get an OAuth app for X ready, how long it takes including approval, what I need to prepare, what can block me, and what you can do for me versus what I must do myself." |
| Teammate or manager (secondary) | Reads a shared link to plan the timeline or approve the spend (for example, a security audit). |
| Evaluator (for this assignment) | Browses the demo guides, submits an unfamiliar app, watches it generate live, and judges usefulness, evidence and use of agents. |

## 3. Goals and non-goals

### Goals
- G1. A developer can find or generate a guide for an app and know **where to start, what to do next, how long it will take, and what to do when blocked**, without anyone explaining it.
- G2. Every claim is labeled with its evidence, and quotes are checked automatically against the live cited page.
- G3. Each guide is shaped by the developer's situation (audience and scopes), not one-size-fits-all.
- G4. Each guide clearly separates agent steps from human steps, and the agent produces drafts that move the developer forward.
- G5. The live generation is watchable: the evaluator sees what the agent is doing while it runs.

### Non-goals (this assignment)
- **Agent-driven setup:** creating accounts, signing in, filling console forms, or submitting for review. We tested this and it isn't viable (§14).
- Completing any provider approval, or using paid accounts.
- All 100 guides. We show a few varied, curated guides plus live generation.
- User accounts, auth for our own app, or team features.
- Production hardening beyond basic abuse limits.

## 4. Scope

### In scope
1. **Guide library:** 5 curated guides, checked by a human against our research.
2. **Catalog page:** the 100 proposed apps (from `research/composio/catalog.csv`), each either linked to its guide or offering "Generate".
3. **Live generation:** enter an app name or website and get a guide in about 5 minutes, with live progress.
4. **Shareable guides:** each guide has its own URL and can be exported as Markdown.
5. **Evidence pipeline:** a sign-in wall probe, docs research, and an independent quote-verification stage.
6. **Verification report:** what we checked, corrected and couldn't verify. It reuses the research `_verification.md` logs and the proof-of-concept results.
7. **Evals:** an answer key built from the 10 researched providers, plus edge-case runs.
8. **Submission:** a hosted link, the repo, and a README covering setup, key decisions (including the setup-attempt proof of concept) and limitations.

### Out of scope
See Non-goals. Also: guides for non-OAuth auth types. For those, the agent says the app doesn't use OAuth and stops.

### Optional, if time allows
- One human signed-in pass on GitHub with a test account. Yashvi signs in, and we capture the real form read-only. This gives one "tested by a human" curated guide.

## 5. Demo library

Picked from the 10 verified providers, and all 5 already have proof-of-concept captures in `experiments/oauth-capture-poc/runs/`. Together they cover all four tiers, both Composio statuses, and different kinds of blockers.

| App | Composio status | Tier | Why it's in the set |
|---|---|---|---|
| GitHub | managed | instant | The happy-path baseline; shows the customer-side gate (orgs restrict OAuth apps) and the new expiring-token default. |
| Gmail (Google) | managed, but often needs BYO | review-required | Shows the outcome changing with scopes (send-only means a short review; read means a review plus a paid audit), plus the 100-test-user and 100-new-user caps. |
| Xero | BYO | verify-to-scale | Connection caps unlocked by plan rather than review; 5 uncertified apps per organisation; a stale docs screenshot. |
| Shopify | BYO | review-required | A permanent distribution choice, a per-shop authorize URL, a mandatory app review, and docs URLs that moved. |
| Spotify | BYO | partner-only | A 5-user dev mode, a Premium owner, and extended access only for organizations with 250k MAU. An honest "you probably can't" guide. |

**Unseen set for live demo and evals** (not researched in advance): for example TikTok, LinkedIn, DocuSign, Zoom, WordPress.com. Final list fixed in the test plan.

## 6. Functional requirements

### FR1. App resolution
- Input: a free-text app name or URL.
- Resolve it to a canonical provider and match it to a Composio toolkit slug and status (managed or BYO) using `research/composio/catalog_all_oauth_toolkits.csv`. If there's no match, say "not in Composio's catalog".
- **Find the docs fresh on every run.** Search for the provider's current pages on creating the app, scopes, limits and review. Follow redirects, and confirm a page actually covers the topic before citing it. Never trust a hard-coded docs URL; it may have moved (seen with Shopify).
- If the name is ambiguous, pick the most likely match, say which one was picked, and let the user correct it.
- If the app doesn't support third-party OAuth, say which auth type it uses and stop.

### FR2. Situation questions (personalization)
Each guide starts with 2 or 3 questions that change the route:
- Who will connect? (Only my own company or workspace / outside users)
- What must the agent do? (A small checklist of capabilities, mapped to scopes and their review class)
- Optional, per provider: distribution or tenancy (single vs multi-tenant, public vs custom).
Answers re-render the verdict, steps and timeline. Variants are generated ahead of time inside the guide, not by a new agent run.

### FR3. Guide content (schema)
Fields come from the recurring patterns in `research/providers/_summary.md` and the `steps.json` shape used in the proof of concept. Every field carries an evidence label.

1. **Header:** app, Composio toolkit and status, guide type (curated / agent-generated), last verified date.
2. **Verdict:** tier, one-line summary, active effort (hours), calendar time (range, and whether it comes from official, community or our estimate), confidence.
3. **Should you bring your own app?** For managed apps: when the managed app is enough and when to bring your own.
4. **Before you start:** the account needed (from the wall probe), plans and costs, and eligibility rules (for example "organizations only", "owner needs Premium").
5. **Limits before approval:** the cap value, its unit (users, connections, installs, workspaces) and what it applies to (per app, per customer org, project lifetime).
6. **Steps (ordered):** each step has who does it (`agent` / `human` / `either`, with `human_reason`: credential, legal_acceptance, payment, identity, real_account, submit, wait), the action, exact values to paste (including Composio's callback URL, `https://backend.composio.dev/api/v3/toolkits/auth/callback`, with a note to copy it from the dashboard since some toolkits still use the legacy v1 URL), a flag if the step is irreversible, the evidence label and the source.
7. **Approval and review:** what triggers it, what to submit, who reviews, the official wait vs the community-reported wait, and the cost.
8. **Customer-side gates:** admin consent, org app restrictions, workspace approval.
9. **Gotchas:** token lifetimes and refresh rules, redirect URI rules (for example Spotify rejects `localhost`), per-tenant URLs, recent breaking changes (with dates).
10. **When you're blocked:** symptom, likely cause, fix (for example `redirect_uri_mismatch`, "This app is blocked", `invalid_client`).
11. **Prepared for you:** agent drafts, including the minimum scope list with a justification for each, a privacy policy outline, consent screen field values, and the review submission text.
12. **Open questions:** what we couldn't verify, and what to check on first sign-in.
13. **Sources:** URL, access date, quote, and verification result (`found_in`: visible / hidden_section / not found).

### FR4. Evidence model
- Labels: **TESTED** (observed by our tooling in this run, for example the sign-in wall), **DOCS** (official provider docs, quote verified on the live page), **COMMUNITY** (forums, blogs), **UNCERTAIN** (not verified).
- Every DOCS or COMMUNITY claim has its source URL, access date and a short exact quote.
- **An independent verification stage** re-opens each cited page in a real browser and checks the quote, separately from the researchers who made the claim. This is needed: in the proof of concept, a research worker wrongly reported a real limit as missing, and only an independent check caught it.
- **The quote checker searches both visible and hidden text** (collapsed sections, tabs). It normalizes whitespace, case and curly quotes, and records `found_in`. Google's help pages hide their limits in collapsed sections.
- A quote that isn't found is downgraded to UNCERTAIN, or re-researched once.
- **Conflicts are shown, not resolved silently** (for example "Xero docs say 5 on one page and 2 on another").
- The guide shows a summary such as "18 claims: 12 docs-verified, 3 community, 3 uncertain".

### FR5. Sign-in wall probe (our "attempt the setup")
- Load the provider's developer console URL once in a headless browser. Record the final URL, the redirect chain, and what the page asks for (account type, sign-in options, bot checks such as reCAPTCHA, cookie banners). This becomes TESTED evidence in "Before you start".
- Read-only: no typing, no clicks, no submits. The agent never creates accounts or signs in.
- Take one screenshot of the wall by default. Any other screenshots are optional, and the live pipeline doesn't need them.
- Why we stop there: on all 5 proof-of-concept apps the console redirected to sign-in after one hop, and everything after sign-in is human-only (terms, Register, payment, review). See §14.

### FR6. Live generation experience
- The user submits an app and sees a progress view: resolving the app, finding the docs, researching (with parallel workers listed), probing the sign-in wall, drafting, verifying quotes, done.
- Each stage shows a short status and a running count of sources found and verified.
- The finished guide gets a permalink. Failures show what succeeded and what didn't.
- Re-submitting an app that already has a guide opens the existing one, with a "regenerate" option.

### FR7. Sharing
- A permalink per guide, Markdown export, and a printable layout.
- Agent-generated guides are clearly badged as such, with their verification summary.

## 7. Agent design (behavioral; the stack is in §13)

Pipeline, each stage visible in the progress view:
1. **Resolve:** app → provider, Composio status, OAuth support, current docs pages (FR1).
2. **Research (parallel):** separate workers for (a) app registration and fields, (b) review and approval, (c) limits, tokens and redirect rules, (d) community-reported waits and blockers. Each worker gets the same three things that made the proof-of-concept subagents reliable: a **strict procedure**, a **worked example** of the output, and a **tool to check its own quotes**. Each returns claims in the schema's shape, with quotes and URLs.
3. **Probe:** the sign-in wall probe (FR5).
4. **Synthesize:** merge into the guide schema, build the situation variants, assign the tier and time estimates (with their basis), and write the "prepared for you" drafts.
5. **Verify (independent):** quote checks over visible and hidden text, conflict detection, downgrading (FR4).
6. **Publish:** save the guide and return the permalink.

Guardrails: fetched page content is treated as data, never as instructions. Every run has a time and cost cap. No credentials are used at any stage.

**Runtime models (decided 2026-10-21): free models on OpenRouter only.** Because free models are weaker and rate-limited, **code orchestrates the pipeline and the LLM does only narrow jobs**: extracting claims from page text (step 2) and writing the guide (step 4). Searching, fetching, the wall probe and quote verification are plain code. Every LLM output is validated against the Pydantic schema and retried on failure, with a fallback model if it keeps failing. **Claude Code (this session and its subagents) is used for building and testing only, never at runtime.**

**Baseline from the proof of concept:** one app per worker took about 4 to 6 minutes and about 100k to 115k tokens on Sonnet. 68 of 68 quotes were verified, plus 8 of 8 in an independent re-check.

## 8. Non-functional requirements
- **Time:** a live run aims for about 5 minutes. Curated guides load instantly.
- **Cost:** $0 in model spend (free OpenRouter models only). The real constraint is OpenRouter's free-model limits: **20 requests per minute, and 50 per day, or 1,000 per day once at least 10 credits have been bought (all time)**. A run should make about 15 LLM calls or fewer, with backoff on 429 errors. Requests per run are logged.
- **Safety:** no credentials in the repo. API keys come from environment variables. Basic rate limiting on public generation. Read-only browsing only.
- **Freshness:** every guide shows its last-verified date. Docs are found fresh on each run.
- **Clarity:** short sentences and scannable sections. A developer should get the verdict in 10 seconds.

## 9. Evaluation (outline; the full test plan is the next document)
- **Answer key:** the 10 researched providers. For each, the expected tier, user or connection cap, whether review is required, key blockers and key gotchas.
- **Metrics:** tier accuracy; key-fact recall; citation validity (share of quotes found on the live page, by `found_in`); honesty (unknowns marked UNCERTAIN rather than invented); schema validity; run time and cost.
- **Edge cases:** an app without OAuth, an ambiguous name, a Composio-managed app, an obscure app with thin docs, moved or redirected docs URLs, limits hidden in collapsed sections, a cookie banner covering content, and a fetched page containing prompt-injection text.
- **Deterministic tests (pytest):** schema validation, the quote matcher (including hidden text and curly quotes), catalog lookup, the evidence downgrade logic, and wall-probe parsing.
- **Unseen-app runs:** 3 to 5 apps that weren't researched, reviewed by hand for usefulness.

## 10. Deliverables
1. A hosted link to the working experience.
2. A source repository with no credentials.
3. A README covering setup, key decisions ("why not just a prompt", why this scope, why no agent-driven setup) and limitations.
4. A verification report: research verification logs, proof-of-concept results, and the sample re-checks.
5. 5 curated guides and the 100-app catalog page.

## 11. Acceptance criteria
- AC1. An evaluator can open any of the 5 curated guides and, within 10 seconds, see the tier, effort, calendar time and the first step.
- AC2. Changing the situation answers on the Gmail guide changes its verdict (internal: no review; send-only: short review; read: review plus audit).
- AC3. Submitting an unseen app produces a complete guide with live progress, within about 5 minutes, with a verification summary and a wall-probe result.
- AC4. At least 90% of DOCS quotes in curated guides are found on their live pages (visible or hidden). Every failure is downgraded and shown as such.
- AC5. An app without OAuth produces a clear "this app doesn't use OAuth" result, not a made-up guide.
- AC6. Every step is labeled agent, human or either (with a reason for human steps), and irreversible steps are flagged before the step.
- AC7. The README explains the setup-attempt proof of concept and why the product stops at the sign-in wall.

## 12. Time budget

The understanding, research and proof-of-concept phases have used a large share of the 6 to 8 hours, so the build stays lean:

| Block | Hours |
|---|---|
| Test plan | 0.5 |
| Agent pipeline + verifier (reusing `capture.py`) | 2.0 |
| Web UI (library, catalog, progress view, guide page) | 1.5 |
| Curated guides (from the proof-of-concept runs) + verification report | 0.75 |
| Deploy, README, demo rehearsal | 0.75 |

## 13. Decisions still open
| Decision | Recommendation | Why |
|---|---|---|
| Web UI | **Next.js on Vercel with AI SDK UI + AI Elements** (decided pending confirmation) | Streaming progress steps, inline source citations and message rendering come ready-made; guide pages get real permalinks (`/guides/<slug>`). Streamlit was rejected because it handles streaming and citations poorly. Vercel's "Chat SDK" was rejected because it's for Slack/Teams/Discord bots, not a web UI. The frontend talks to the Python backend over the AI SDK's streaming protocol (exact format to be confirmed from the installed AI SDK docs when building). |
| Backend language and framework | **Python + FastAPI + Pydantic AI** (decided pending confirmation) | Keeps the pipeline, quote verifier and wall probe in Python, where the proof-of-concept code already works. | `capture.py` (Playwright, Python) already works and becomes the wall probe and verifier. Pydantic AI talks to OpenRouter, validates every LLM output against our Pydantic guide schema with automatic retries, supports fallback models, and runs extractions in parallel with async. It's lighter than LangGraph or CrewAI, and we don't need their open-ended agent loops. |
| Runtime model | **Free OpenRouter models only** (decided). Shortlist from the live model list (free and tool-capable, 2026-10-21): `nvidia/nemotron-3-super-120b-a12b:free` (structured outputs), `nvidia/nemotron-3-ultra-550b-a55b:free`, `minimax/minimax-m3.1-flash:free`, `google/gemma-4-31b-it:free`. A 15-minute bake-off on one extraction task picks a primary and a fallback. | Free models vary in tool calling and JSON reliability, so we measure rather than guess. |
| Build and test | **Claude Code in this session** (decided), including subagents for parallel work and the manual eval rubric | No model spend for testing; the same pattern as the proof of concept. |
| Web search | **A free search library (`ddgs`, no key)**, with an optional Tavily free-tier key as a fallback | OpenRouter's built-in web search is paid. Search only finds candidate docs URLs; reading and verification use our Playwright code. |
| Web fetch and verification | **Plain HTTP first (httpx), headless browser (Playwright) only as a fallback** | Tested 2026-10-21. Plain HTTP found 4 of 5 quotes, including Google's collapsed-section limit, since hidden sections are still in the HTML, and saw the GitHub and Google sign-in redirects. It failed on Xero's JavaScript-rendered docs (39 characters of text), on Spotify's and Xero's JavaScript sign-in redirects, and on Shopify's dashboard (HTTP 406). Rule: fall back to the browser when the page text is under about 500 characters, the status is 4xx, or a console URL doesn't land on a sign-in host. |
| Hosting | **Frontend: Vercel. Backend: one Docker container with Chromium on Render or Fly** | The browser fallback needs Chromium on the server, and runs take minutes and must stream progress. |
| Storage | Curated guides as JSON in the repo; generated guides in a simple KV or blob store, or SQLite on the container | Minimal setup. |
| Demo apps | The 5 in §5 | Already captured in the proof of concept. |
| Human signed-in pass | Optional: GitHub only, if time allows | Cheapest real TESTED form evidence. |
| Managed Agents | Not for this submission; the code is parked | A good fit later, for hosted runs and scheduled re-verification. |

## 14. Approaches tested or considered and rejected
| Approach | Result | Decision |
|---|---|---|
| **Agent attempts the setup** (proof of concept, 5 apps, read-only Playwright) | All 5 consoles redirect to sign-in after 1 hop. Everything after that is human-only. | Replaced by the sign-in wall probe (FR5) plus docs research and verification. |
| **Docs screenshots as main evidence** | They show docs, not the console. Cookie banners and stale images get in the way. | Optional; text plus verified quotes carries the guide. |
| **Browser Use Cloud + disposable test accounts** | Would show the real form on easy providers. Doesn't solve account creation, new-device sign-in checks, approvals, or live demo apps. Would cost 1 to 2 hours to set up. | Future work for the curated library only. |
| **Claude Managed Agents for the capture run** | Written, not run (no API key in the environment). Moved the proof of concept into Claude Code instead. | Parked for later hosting. |
| **Single-prompt chatbot answer** | Memory-based answers were stale or wrong on several provider facts. | Rejected; this is why the verification process is the product. |

## 15. Risks
- **Live run too slow or flaky during the demo.** Mitigation: a time cap, partial results, and a pre-warmed example.
- **Docs blocked, moved or JavaScript-only.** Mitigation: find docs fresh, use a browser renderer, and mark claims UNCERTAIN instead of guessing.
- **A quote checker false negative** (hidden sections). Mitigation: check hidden text too, and record `found_in`.
- **Wrong tier on an unseen app.** Mitigation: the tier shows its basis and confidence; evals measure accuracy.
- **Rules change after we verify.** Mitigation: last-verified dates and an explicit freshness note.
- **Chromium on the host.** Mitigation: a Docker image with Playwright browsers; smoke-test the deployment early.
