# GitHub: OAuth App and GitHub App

- Researched: 2026-10-19
- Tier: **instant**. No review to create or use either app type. Marketplace listing is optional and separate.
- Effort: OAuth App 0.25 to 0.5 hours, plus about 1 hour of end-to-end testing. GitHub App 1 to 2 hours.
- Calendar time: same day. The only waits are per-customer organization owner approvals, with no stated timeline.
- Confidence: high for creation and caps, medium for token behavior (docs changed in Aug 2026 and older pages are partly stale).

Evidence labels: TESTED (observed by us), DOCS, COMMUNITY, UNCERTAIN.

## Directly observed (TESTED, 2026-10-19)

`github.com/settings/developers` redirected to `github.com/login?return_to=...settings/developers` showing "Sign in to GitHub", username and password fields and "New to GitHub? Create an account". So the app form sits behind the normal login, with no separate developer program. TESTED.

## 1. Where and how the app is created

Two app types. Composio's own guide uses an OAuth App (COMMUNITY/vendor, https://composio.dev/auth/github, undated). GitHub recommends GitHub Apps (DOCS, differences page).

**Console:** `https://github.com/settings/developers`, then OAuth Apps, then New OAuth App. For an org-owned app use the organization's Settings, then Developer settings. The click path is from docs. The form itself was not seen.

**Prerequisites**
- Register under a personal account or an organization where you are admin. DOCS: "under any organization you have administrative access to". https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app
- Free account is enough. No payment or business verification mentioned (likely, not confirmed).
- 2FA is not a stated precondition, but "Publishing an app or action for others" triggers GitHub's mandatory 2FA. DOCS: https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/about-mandatory-two-factor-authentication
- Limit: DOCS: "A user or organization can own up to 100 OAuth apps". Same 100 cap for GitHub Apps (https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app).
- Whether a verified email is enforced: UNCERTAIN.

**Steps, OAuth App** (DOCS, creating-an-oauth-app page)
1. Profile picture, Settings.
2. Developer settings, OAuth apps.
3. New OAuth App (first time: "Register a new application").
4. Fill the fields. 5. Register application.
6. Generate a client secret. The secret screen is not described in docs. Composio's guide says it is shown once (COMMUNITY/vendor).
7. Optional logo, then Update application.

**OAuth App fields**
- Application name (required), Homepage URL, Application description (optional).
- Authorization callback URL: up to 10, via "Add callback URL".
- Enable Device Flow (checkbox).
- Expire user access tokens (checkbox, on by default; untick if your code cannot refresh). See section 4.
- Application logo and badge color (after creation; PNG/JPG/GIF under 1 MB, 200x200+ recommended; paraphrase, https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-a-custom-badge-for-your-oauth-app).
- No privacy policy URL, terms URL, or scope field on the OAuth App form. Scopes are sent at runtime in the `scope` parameter. Those documents exist only for a Marketplace listing.
- DOCS: "Only use information in your OAuth app that you consider public".

**Redirect URI rules**
- Up to 10 callback URLs (DOCS, creating page and changelog https://github.blog/changelog/2026-08-14-multiple-redirect-uris-and-token-refresh-for-oauth-apps, Aug 14, 2026).
- HTTPS-only is not stated in the pages read. Do not assume.
- Loopback: prefer `127.0.0.1` or `::1`. A loopback `redirect_uri` may use any port: "does not need to match the port specified" (DOCS, https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).
- Without wildcard matching the `redirect_uri` must exactly match a registered URL. If omitted, GitHub uses the first one.
- With wildcard matching (per URL): host and port must match exactly, path must equal or be below the registered path (paraphrase).
- Mismatch returns `redirect_uri_mismatch` (DOCS, troubleshooting-authorization-request-errors).

**GitHub App path** (DOCS, registering-a-github-app): Developer settings, GitHub Apps, New GitHub App. Fields: name (max 34 characters, globally unique), description, homepage URL (a repo URL is accepted), callback URL (up to 10, optional), Expire user authorization tokens (default on), Request user authorization during installation, Device Flow, Setup URL, webhook settings, per-permission access (No access, Read-only, Read & write), events, and "Where can this GitHub App be installed?" (Only on this account / Any account). For GitHub Apps the `scope` parameter does not carry permissions; only `offline_access` is supported (paraphrase, generating-a-user-access-token page).

## 2. What works immediately vs what is gated

- Both app types work as soon as they are saved. Public GitHub App: "any user on GitHub can install it and authorize it" (DOCS, making-a-github-app-public-or-private).
- No user cap, test-user list or unverified-app warning found for either type. The only count thresholds are for paid Marketplace listings: "minimum of 100 installations" (GitHub Apps) and "minimum of 200 users" (OAuth apps) (DOCS, requirements-for-listing-an-app).
- **The real gate is the customer's organization.** With OAuth App access restrictions on, members "cannot authorize OAuth app access to organization resources" until an owner approves (Third-party Access, OAuth app policy, Review, Grant access). DOCS: https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/about-oauth-app-access-restrictions. "OAuth app access restrictions are enabled by default" for new organizations. Older orgs may have no restriction. Unapproved apps lose private-resource API access.
- GitHub Apps are "not subject to organization application policies", but an org owner must install or approve them (DOCS, differences page).
- No restricted-scope review exists. All OAuth scopes are open to any new app (DOCS, scopes page, read through a summarizer: paraphrase only). `repo` also covers org-owned resources.
- **Rate limits:** no separate tier for unapproved apps. OAuth tokens use the user's 5,000 requests per hour (DOCS, differences page). Apps owned by a GitHub Enterprise Cloud org get 15,000 per hour; installation tokens scale to a 12,500 per hour cap (paraphrase, rate limits page). Device-flow code submission is capped at 50 per hour per app (paraphrase).
- An app can be suspended for "reported abuse, spam, or a mis-use of the API" (paraphrase). Fix: contact GitHub Support.

## 3. Approval / review path

Creating and using an app needs **no GitHub review**. Review applies only to two optional programs.

- **A. Marketplace listing** (not needed to connect users). Submit: draft listing, pricing plan, contact info, description, privacy policy link ("Listings must have a valid link to a privacy policy"), support link, logo, screenshots, Marketplace Developer Agreement, plan-change webhooks. Reviewer: an "onboarding expert" ("An onboarding expert will reach out to you"). Must "integrate with the platform in some way beyond authentication", so a pure login connector may not qualify. Org-owned apps: only org owners can list. DOCS: https://docs.github.com/en/apps/github-marketplace/creating-apps-for-github-marketplace/requirements-for-listing-an-app and https://docs.github.com/en/apps/github-marketplace/listing-an-app-on-github-marketplace/submitting-your-listing-for-publication.
- **B. Publisher verification** (needed for paid plans or a badge): accurate profile and support email, 2FA enforced for the org, verified domain, then Request Verification. App must be org-owned. DOCS: https://docs.github.com/en/apps/github-marketplace/github-marketplace-overview/applying-for-publisher-verification-for-your-organization. Paid apps also go through "a financial onboarding process" (paraphrase).
- **Cost:** no listing fee stated. Revenue share: UNCERTAIN, not checked.
- **Official wait:** none stated.
- **Community wait:** none found. UNCERTAIN.
- Rejection reasons and re-review cadence: not published. UNCERTAIN.

## 4. Gotchas

**Tokens**
- OAuth App tokens are long-lived unless expiration is on. DOCS: "OAuth app tokens re long-lived by default" (sic) on the differences page (https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps), and "OAuth app tokens do not expire until the person who authorized the OAuth app revokes the token" on https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app (both partly stale after Aug 2026; quote re-checked live, see `_verification.md`).
- With expiration: 8-hour access token (`expires_in=28800`), refresh token valid 6 months without use (`refresh_token_expires_in=15897600`), single use. DOCS: "the refresh token expires after six months without use" (authorizing-oauth-apps page).
- Enabling expiry "does not cause existing tokens to expire". Requesting `offline_access` returns an expiring token for that sign-in.
- GitHub revokes an OAuth token "not used in one year" (DOCS, token-expiration-and-revocation).
- **Token cap:** 10 tokens per user, app and scope combination; a limit of ten per hour. Over the cap GitHub revokes an older token ("limit of ten tokens"). Re-running auth often with identical scopes can silently kill older connections.
- GitHub App user tokens: 8 hours, 6-month refresh. Response `scope` is always empty.
- Refresh tokens rotate; parallel refreshes cause `bad_refresh_token` (COMMUNITY: https://nango.dev/blog/github-app-oauth-refresh-token-bad-refresh-token, post date not confirmed; https://github.com/orgs/community/discussions/24745, Aug 2020, may be fixed).

**Recent changes (changelog, Aug 14, 2026):** OAuth Apps can opt in to expiring tokens, hold 10 redirect URIs, and enable per-URI wildcard matching. Quote: "Short-lived tokens are enabled by default for all new applications." A new OAuth App created now issues 8-hour tokens unless unticked, so integrations must store and rotate refresh tokens. Apps with one callback URL before Aug 3, 2026 had wildcard matching switched on. Wildcard matching suits per-tenant subdomains but is a security risk.

**Other traps**
- SAML SSO orgs: the user needs an active SSO session when authorizing, and must re-authorize after SSO is enforced (paraphrase).
- GitHub App user tokens only reach repositories where the app is also installed ("only has permissions that both the user and the app have"). "Act as the user everywhere" needs an OAuth App.
- Enterprise-level resources: only OAuth Apps ("a GitHub App cannot yet be given permissions against an enterprise").
- Revoking an OAuth App's access deletes SSH keys it created (paraphrase).
- Composio's callback URL: `https://backend.composio.dev/api/v3/toolkits/auth/callback`; some toolkit defaults still use `/api/v1/auth-apps/add`. The OAuth app's callback must match `oauth_redirect_uri` in the auth config. COMMUNITY/vendor: https://docs.composio.dev/docs/auth-configuration/custom-auth-configs (undated). A `/api/v3.1/...` form appeared in a snippet and is UNCERTAIN.

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Choose OAuth App vs GitHub App | Yes | Confirm | Judgment |
| Draft name, description, homepage text, logo spec | Yes | Approve | Public copy |
| Draft privacy policy, terms, scope justification | Yes | Approve and publish | Marketplace and customer security reviews |
| Sign in, 2FA | No | Yes | Credentials |
| Submit New OAuth App form | No | Yes | Human session |
| Generate and store client secret | No | Yes | Secret, shown once |
| Callback URL value | Prepare exact value | Enter it | Must match Composio config |
| Create Composio auth config | Prepare fields | Enter secrets | Secrets |
| Test an authorization | No | Yes | Real GitHub login |
| Org owner approval at customer org | No | Customer's owner | Third-party admin |
| Marketplace, publisher and domain verification | Draft text | Yes | Org ownership, DNS, waiting |

## 6. Difficulty tier and estimate

**Tier: instant.** Effort and calendar time are at the top of this file. Marketplace would be review-required but is not needed.

## 7. Sources

| URL | Supports | Label | Accessed |
|---|---|---|---|
| github.com/settings/developers (login redirect) | Login required | TESTED | 2026-10-19 |
| https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app | Fields, 100-app cap, 10 callbacks | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps | Redirect and wildcard rules, token lifetimes, token cap | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps | Scopes | DOCS (summarizer only) | 2026-10-19 |
| https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps | Comparison, org policy | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app | GitHub App fields | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app | User tokens | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens | Refresh | DOCS | 2026-10-19 |
| https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/about-oauth-app-access-restrictions | Org restrictions | DOCS | 2026-10-19 |
| https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/approving-oauth-apps-for-your-organization | Owner approval | DOCS | 2026-10-19 |
| https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | Rate limits | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/github-marketplace/creating-apps-for-github-marketplace/requirements-for-listing-an-app | Marketplace requirements | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/github-marketplace/listing-an-app-on-github-marketplace/submitting-your-listing-for-publication | Review by onboarding expert | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/github-marketplace/github-marketplace-overview/applying-for-publisher-verification-for-your-organization | Publisher verification | DOCS | 2026-10-19 |
| https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation | Inactivity revoke | DOCS | 2026-10-19 |
| https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/about-mandatory-two-factor-authentication | 2FA trigger | DOCS | 2026-10-19 |
| https://docs.github.com/en/apps/oauth-apps/maintaining-oauth-apps/troubleshooting-authorization-request-errors | Suspension, mismatch | DOCS | 2026-10-19 |
| https://github.blog/changelog/2026-08-14-multiple-redirect-uris-and-token-refresh-for-oauth-apps | Aug 2026 changes | DOCS (changelog) | 2026-10-19 |
| https://docs.composio.dev/docs/auth-configuration/custom-auth-configs | Composio callback URL | COMMUNITY/vendor | 2026-10-19 |
| https://composio.dev/auth/github | Composio uses OAuth App | COMMUNITY/vendor | 2026-10-19 |
| https://www.nango.dev/blog/github-app-vs-github-oauth | Comparison | COMMUNITY (2026-04-01) | 2026-10-19 |
| https://nango.dev/blog/github-app-oauth-refresh-token-bad-refresh-token | Refresh races | COMMUNITY | 2026-10-19 |
| https://github.com/orgs/community/discussions/24745 | bad_refresh_token | COMMUNITY (2020-08-09) | 2026-10-19 |

## 8. Open questions

- Token lifetime: older page says long-lived by default; the Aug 2026 changelog says expiry is on by default for new apps. Probably both true for different app ages.
- Wildcard date: docs say Aug 3, 2026, changelog is Aug 14, 2026.
- Nango says OAuth Apps need no admin approval; GitHub docs say that holds only for orgs without restrictions, and new orgs have them on by default. Trust the docs.
- GitHub recommends GitHub Apps, but "act as the user across all repos and orgs" favors an OAuth App. Not tested either way.
- Not verified: secret screen, GitHub App logo rules, any hidden review for large apps, Marketplace review time.
- Our assumption "GitHub is instant" holds, with the caveat that customer orgs commonly gate third-party OAuth apps by default.
