# POC: can an agent record OAuth app setup with screenshots?

Run on 2026-10-21 inside Claude Code: the main session plus 4 parallel Sonnet subagents. It's a warm-up before building the product. (The Managed Agents version is parked in `../managed-agent-oauth-capture/`.)

## What we ran

- `capture.py` is a read-only Playwright tool. It can `shot` (screenshot, optionally cropped around matching text), save a page as `text`, and check a `quote` (does this exact quote appear on the live page?). It never types, clicks or submits.
- `PROCEDURE.md` is the per-app recipe. `runs/github/` is the worked example, which the main session did by hand as the pilot.
- Five apps were run, one per approval tier from our research: GitHub, Google (Gmail), Spotify, Xero and Shopify. Results are in `runs/<slug>/`: screenshots, `steps.json`, `guide.md` and `findings.md`.

## Results

| App | Console wall | Screenshots | Quotes verified | Notable |
|---|---|---|---|---|
| GitHub | `github.com/login`, 1 redirect | 3 | 3 / 3 | Mouse-wheel scrolling bug found and fixed (switched to cropping) |
| Google | `accounts.google.com`, 1 redirect | 6 | 16 / 16 | Missed the 100-test-user cap because it's inside a collapsed section; caught in the spot-check and fixed in `capture.py` |
| Spotify | `accounts.spotify.com`, 1 redirect (mentions reCAPTCHA) | 6 | 15 / 15 | A fixed cookie banner hides part of the docs in screenshots |
| Xero | `login.xero.com`, 1 redirect | 6 | 20 / 20 | The docs image of the form says 25 organisations; the docs text says 5 (stale screenshot) |
| Shopify | `accounts.shopify.com`, 1 redirect | 8 | 14 / 14 | Both docs URLs in `apps.json` now redirect to pages that don't cover app creation; the agent found the right ones |

The main session also re-checked 8 randomly sampled quotes (2 per subagent app) independently: 8 of 8 were found. Each subagent took about 4 to 6 minutes and about 100k to 115k tokens.

## What we learned

1. **The agent can't create the OAuth app.** Every console stops at sign-in after one redirect. Without a human-provided login, an agent never sees the real form. Even with one, the next steps (accepting terms, Register, payment, review) are human-only by nature. So "the agent attempts the setup" isn't a viable product feature, and the assignment's "as practical" covers that.
2. **The wall itself is cheap, real evidence.** One request gives a TESTED fact: which account you need and which sign-in options exist. It's worth keeping as a probe in the live pipeline.
3. **Verifying quotes against the live page is the high-value part.** 68 of 68 subagent quotes and 8 of 8 re-checked quotes held up, and the process caught stale material: moved docs URLs, an out-of-date docs screenshot, and a self-contradicting docs page. That's the evidence story the product needs.
4. **The verifier must read hidden text.** Providers put limits inside collapsed sections, so a visible-text-only checker gives false "not found" results. `capture.py` now checks both and reports `found_in`.
5. **Docs screenshots add little.** They show the docs, not the console, and cookie banners and stale images get in the way. Keep screenshots optional in the product; text plus verified quotes carries the guide.
6. **Getting real form screenshots needs a human once.** For the curated library, a person can sign in once (free accounts: GitHub, Xero, Spotify) and capture the form. That's a "human-tested" upgrade, not an agent feature.

## Considered and not pursued: Browser Use Cloud with disposable test accounts

We looked at whether a hosted browser agent ([Browser Use Cloud](https://docs.browser-use.com/cloud/quickstart): managed browsers, saved profiles, site-bound secrets, proxies), paired with test accounts we own, would get past the walls.

**What it would solve:** signing in to a test account, seeing the real create-app form, and creating throwaway OAuth apps on easy providers (GitHub, Xero, Google in Testing mode). That would give genuine TESTED evidence of the form fields.

**What it would not solve:**
- **Creating the accounts.** Email or phone verification and CAPTCHAs still need a human. Automating account creation would also break most providers' terms.
- **New-device sign-in checks.** A cloud browser signs in from an unfamiliar IP, which triggers emailed device codes (GitHub), suspicious-login checks (Google) and 2FA prompts. A human has to answer them at least once.
- **Approvals.** Google verification, Shopify app review and Spotify's extended quota are decided by human reviewers over days or weeks. That's the hard part of the problem, and no browser shortens it.
- **The live demo.** No test account exists for an app the evaluator submits on the spot.

**Decision:** not now. Its value is limited to a few easy, curated guides, which need guides the least, and setting it up would cost about 1 to 2 hours of the remaining budget. The cheaper equivalent is one human signed-in pass (for example GitHub, about 10 minutes, read-only capture). It's listed as future work for the curated library.

## Implications for the spec

- Drop "agent attempts setup" from the live pipeline. Keep a **wall probe** (TESTED) plus **docs research and live quote verification** (DOCS).
- The quote checker must search hidden text, normalize quotes, and record `found_in`.
- Treat provider doc URLs as moving targets: re-resolve them per run instead of hard-coding them.
- Screenshots are optional, and only where they clearly help (for example the login wall, or a key limits table).
- Optional, for the curated guides only: one human signed-in pass on a free provider to show what "TESTED by a human" looks like.
