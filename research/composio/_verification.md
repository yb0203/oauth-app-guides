# Verification log (2026-10-19)

Method: the orchestrator re-fetched Composio pages directly with `curl` (raw markdown, no summarizer in the loop) and compared against what the subagents reported. Scratch parsing scripts and downloads live in `/tmp/orch`, outside the project.

## Part 1. Full-catalog check (beyond the 5 spot-checks asked)

| Check | Result |
|---|---|
| `https://docs.composio.dev/toolkits/managed-auth.md` row counts per section | 123 managed, 211 BYO, matching the headings |
| `https://docs.composio.dev/toolkits.md` table rows | 1,608 toolkits |
| Rows whose Auth column has OAUTH or DCR | 334 |
| "Managed App" column among those 334 | 123 Yes, 211 No |
| Set difference between managed-auth page "managed" slugs and table "Yes" | empty (the two pages agree on all 334) |
| Subagent's 100 proposed rows vs table: slug exists, managed/BYO tag, auth scheme | 100 of 100 match, 0 mismatches, 100 unique slugs |
| DCR_OAUTH toolkits among BYO | 98 pure DCR (agent said 99 including one DCR+API_KEY, vidiq_mcp). Both are consistent. |

## Part 2. Five managed/BYO tag spot-checks on live toolkit pages

Fetched `https://docs.composio.dev/toolkits/<slug>.md` and read the "Composio-managed OAuth available?" line.

| Toolkit | Catalog tag | Live page | Match |
|---|---|---|---|
| shopify | BYO | "Composio-managed OAuth available? No"; page links to composio.dev/auth/shopify | yes |
| tiktok | BYO | No | yes |
| googleforms | BYO | No | yes |
| slack | managed | Yes | yes |
| hubspot | managed | Yes | yes |

Bonus: twitter tagged BYO; live page says No and its FAQ states that as of February 2026 Composio managed credentials for Twitter were removed. Matches the catalog note.

## Part 3. Claims from `composio-auth-model.md` checked against cited URLs

| Claim | Cited URL | Result |
|---|---|---|
| Default redirect URI is `https://backend.composio.dev/api/v3/toolkits/auth/callback`; some toolkits still use legacy `.../api/v1/auth-apps/add` | programmatic-auth-configs.md ; composio.dev/auth/github | **Confirmed.** The programmatic page shows the v3 URL and the example `oauth_redirect_uri`, and its note says "some toolkit defaults still use the supported legacy endpoint" v1. The GitHub guide contains both URLs (4 mentions each). |
| Own-domain route: register `https://yourdomain.com/api/composio-redirect`; it must 302 to the Composio callback; do not follow server-side | white-labeling-authentication.md | **Confirmed**, including the explicit "must return a 302 redirect" warning. The page also says to set the custom URL in both places (provider and auth config). |
| Managed auth has a 15-minute minimum polling interval; managed apps share quota across all Composio users | custom-app-vs-managed-app.md | **Confirmed**, both statements verbatim in substance. Extra: the page says a custom auth config can also be created for branding, scopes, rate limits, polling intervals, or custom instances. |
| Slack: Composio is working on Marketplace review for its managed Slack app, and suggests own app or admin approval meanwhile | docs.composio.dev/toolkits/slack | **Confirmed** (line 86 of the .md page). |
| Gmail: managed auth hits "app is blocked" when `gmail.settings.basic` is added; fix is your own verified Google OAuth app; managed apps share quota | docs.composio.dev/toolkits/gmail | **Confirmed.** |

## Part 4. Corrections and notes
- **Orchestrator error fixed:** `catalog.md` first said about 35 rows carry "(unsure)"; the real count is 25. Corrected.
- **New finding, verified:** the HubSpot toolkit page says the managed HubSpot OAuth app is still awaiting HubSpot approval and shows users a warning; Composio gives no ETA and tells developers to use their own app for control over "review status" and the consent screen. Also, the Shopify page says its default app "may be under review or expired". This supports adding managed apps to the guide library and is the clearest evidence that approval is a live problem even for Composio itself.
- **Not independently verified:** all difficulty tiers and blockers (model background knowledge; no provider docs fetched); the Composio guide contents at composio.dev/auth beyond the GitHub page URL check; the 46-guide count came from the page's link list (46 slugs found by `grep`, 9 of those slugs (apollo, fathomai, googleapps, instantly, posthog, rocketlane, slack_custom, strava, telegram) do not match a slug in the 334 set, either because the guide covers a non-OAuth or differently-named toolkit); token-custody and compliance pages; API-reference claim that no redirect field is documented on `POST /auth_configs` (taken from the subagent).
- **Prior art** (`prior-art.md`) was not re-verified by the orchestrator beyond the Composio-side facts; its claims are subagent-opened pages through a summarizing fetcher. Spot-check candidates before quoting externally: Nango's timing figures and CASA prices, and Unified.to's mismatched GitHub link.
