# Shopify: Dev Dashboard app, per-shop OAuth, App Store review

- Researched: 2026-10-19
- Tier: **review-required**. Anything beyond your own dev stores needs public distribution review. Custom distribution reaches one store (or one Plus organization) only.
- Effort: roughly 12 to 25 active hours (our estimate): about 1 for sign-up and app creation, 4 to 10 for the OAuth flow, expiring-token refresh and compliance webhooks, 4 to 8 for listing, screencast, policies and protected-customer-data forms, 2 to 6 for review fixes.
- Calendar time: about 3 to 10 weeks including approval (our synthesis). Shopify states no official wait. Community reports run from days to over a month, with a spring 2026 slowdown.
- Confidence: medium-high on structure and token rules (many raw docs). Low-medium on review time (community anecdotes only).

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. DOCS quotes passed through a fetch-tool summarizer; see `_verification.md`.

## Directly observed (TESTED, 2026-10-19)

- `dev.shopify.com/dashboard` redirected to `accounts.shopify.com` login: email, password, passkey, Google/Apple/Facebook/WhatsApp. TESTED.
- `shopify.com/partners` marketing page ("Become a Shopify Partner"; "$1,300,000,000 USD paid to partners in 2025"). No fee mentioned on it. TESTED. It does not answer the registration-fee question.

## 1. Where and how the app is created

**Consoles**
- Dev Dashboard: `https://dev.shopify.com/dashboard/`. App creation, dev stores, logs and org permissions moved here from the Partner Dashboard (DOCS, https://shopify.dev/docs/apps/build/dev-dashboard/migrate-from-partners).
- Partner Dashboard `partners.shopify.com` is "no longer the home for partner stores" (DOCS). The App Store submission flow still lives under App, Distribution there (COMMUNITY, https://community.shopify.dev/t/app-store-review-updates-new-tools-to-speed-up-submissions/33472, 2026-04-20).
- Next-Gen Dev Platform went GA 2025-09-03; dev stores allowed on any plan (DOCS, https://shopify.dev/changelog/next-gen-dev-platform-ga).

**Prerequisites**
- The "App store registration fee": "A one-time $19 USD fee to join the app revenue share program." Waived for accounts created before 2021-08-01 and for partners who "only build private/custom apps" (DOCS, https://help.shopify.com/en/partners/partner-program/glossary; page undated). When or where it is charged: UNCERTAIN. A third-party guide (qualimero.com) says registration is free: conflicts with the glossary.
- Account type, business info, 2FA: UNCERTAIN. Help pages say only "follow the sign-up link". A community thread shows Partner login can force 2FA (https://community.shopify.com/t/trying-to-signup-but-getting-error/550785, date not visible).
- The migration guide does not say a Partner account is required for the Dev Dashboard.

**Steps** (DOCS, https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard)
1. Apps, Create app, "Start from Dev Dashboard". Name it.
2. Versions page: App URL, Webhooks API version, Scopes, then Release. Quote: "must have at least one version before it can be installed".
3. Install via the Installs card (opens OAuth in a new tab).
4. App settings holds Client ID and Client secret.
5. For public distribution use Shopify CLI (`shopify.app.toml`). The dashboard route is "Best for automation or API-only apps" (https://shopify.dev/docs/apps/build/dev-dashboard).
6. Choose a distribution method. DOCS: "You can't change the method after you select it." (https://shopify.dev/docs/apps/launch/distribution/select-distribution-method)

**Fields:** version form (App URL, webhooks API version, scopes, `redirect_urls`); app settings (Client ID, secret, icon and contact email merchants see, automation tokens, EventBridge destination). toml `[auth] redirect_urls` is required, at least one before going public; also `application_url`, `embedded`, `scopes`, `optional_scopes`, `use_legacy_install_flow` (default false = Shopify managed installation) (DOCS, https://shopify.dev/docs/apps/build/cli-for-apps/app-configuration).

**Redirect rules:** `redirect_uri` "Must exactly match a redirect URI you've configured" (DOCS, https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant). HTTPS-only, localhost, wildcards, maximum count: UNCERTAIN (not stated). COMMUNITY: an old complaint that wildcards and localhost are not accepted (https://community.shopify.dev/t/customer-account-api-auth-limitations/8691, date not visible, different API, possibly stale); an unanswered 2026-04-03 thread on 127.0.0.1 (https://community.shopify.dev/t/question-about-using-localhost-redirect-urls-for-shopify-oauth/32946). A human should test the form.

**Distribution types** (DOCS, https://shopify.dev/docs/apps/launch/distribution)
- Public: many merchants, requires Shopify approval; the app must "sync certain data with Shopify".
- Custom: one merchant, or several stores in the same Plus organization, or dev stores. No approval. Cannot use Shopify billing.
- Legacy admin-created custom apps can no longer be created; COMMUNITY puts the cutoff at 2026-01-01 (https://community.shopify.dev/t/starting-january-1-2026-you-will-not-be-able-to-create-new-legacy-custom-apps-this-will-not-impact-any-existing-apps/26798).
- "Unlisted" now means a public app with limited visibility (section 3).

**Per-shop OAuth** (DOCS, authorization-code-grant page)
- Authorize: `https://{shop}/admin/oauth/authorize` with `client_id`, `scope` (comma-separated), `redirect_uri`, `state`.
- Callback params: `code`, `hmac`, `shop`, `state`, `timestamp`. Verify HMAC-SHA256 with the client secret, check `state`, validate `shop` against an anchored `myshopify.com` regex.
- Exchange: `POST https://{shop}/admin/oauth/access_token` with `client_id`, `client_secret`, `code`, `expiring=1`. Response: `access_token`, `scope`, `expires_in`, `refresh_token`, `refresh_token_expires_in`. Online tokens: `grant_options[]=per-user`; no refresh token.

**Install flows** (DOCS, https://shopify.dev/docs/apps/build/authentication-authorization/app-installation): managed installation (Shopify handles install and scopes; embedded apps) vs legacy flow (you implement the authorization code grant; this is the path for standalone, non-embedded connectors like Composio's hosted-redirect model).

## 2. What works immediately vs what is gated

- Dev stores are free. A public-distribution app that is not yet approved installs only on dev stores of your Partner org (COMMUNITY, reply dated 2026-04-08, https://community.shopify.dev/t/unlisted-shopify-app-review-required-before-installation/33101/2; replier not marked as staff). A numeric dev-store install cap: not found.
- Custom distribution works with no review: Distribution card, Custom distribution, enter the store domain, optionally untick "Allow multi-store installs for one Plus organization", Generate link, send to the merchant. Multi-store only within the same Plus organization. Apps created before 2023-07-26 need Support to enable multi-store (DOCS, select-distribution-method). Not a path to arbitrary merchants.
- **Client credentials grant** works only "when the app and the store belong to the same Shopify organization"; tokens last 24 hours (`expires_in` 86399) (DOCS, https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant).
- **Protected customer data** (DOCS, https://shopify.dev/docs/apps/launch/protected-customer-data): Level 1 is customer data without name, address, phone, email; Level 2 includes those. Public apps must request access in the Partner Dashboard; both levels need review. Custom apps: "Always available". Dev-store-only apps need none. PCD scopes can be declared before approval, but the API returns no data from non-development stores until approved (DOCS, https://shopify.dev/docs/api/usage/access-scopes).
- Scopes labelled "Shopify approval required" cannot be declared until approved (version creation fails with an `app_access` error). `read_all_orders` is gated; without it orders are limited to the last 60 days (paraphrase).
- **Rate limits:** no evidence unapproved apps get lower limits. Per app-and-store pair, set by plan. GraphQL restore rate (DOCS, https://shopify.dev/docs/apps/build/apis/graphql-admin/rate-limits): Standard 100 points per second, Advanced 200, Plus 1000, Enterprise 2000. A single query "may not exceed a cost of 1,000 points, regardless of plan limits." Bucket sizes: UNCERTAIN. REST is a leaky bucket (https://shopify.dev/docs/api/usage/rate-limits); per-plan numbers not retrieved. Also: array inputs max 250, pagination capped at 25,000 objects, 10,000 new variants per day for stores past 500,000 variants (Plus exempt).

## 3. Approval / review path

- **Trigger:** public distribution and wanting installs beyond your dev stores. Unlisted does not escape review: requirements "are the same for both fully visible and limited visibility public apps" (DOCS, https://shopify.dev/docs/apps/launch/app-store-review/review-process).
- **Submitted** (DOCS, https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review and https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements): app configuration (app URLs, compliance webhooks, icon, API contact, emergency contact), at least one listing with a primary language, the PCD request, automated checks you must pass. Requirement 4.5.3: "Include a screencast to demonstrate your app's onboarding and features." Requirement 4.5.4: "Include account credentials in your testing instructions" (valid, full access, 4.5.5). A privacy policy is required. A demo-store link is on the checklist page.
- **Listing specs** (DOCS, https://shopify.dev/docs/apps/launch/app-requirements-checklist): name 30 characters or fewer; icon 1200x1200 JPEG or PNG; feature media 1600x900; 3 to 6 desktop screenshots with alt text; intro up to 100 characters; details up to 500; up to five search terms.
- **Hard requirements:**
  - OAuth first. Quote: "Your app should immediately authorize using OAuth before any other steps occur." Requirement 2.3.1: no manual entry of a myshopify.com URL.
  - Billing 1.2: "Apps that use off-platform billing cannot be distributed through the Shopify App store." Whether a free connector is exempt: UNCERTAIN.
  - Compliance webhooks: all three topics (`customers/data_request`, `customers/redact`, `shop/redact`) for every App Store app, even with no personal data. "Complete the action within 30 days of receiving the request." Configure them in the toml before publishing (DOCS, https://shopify.dev/docs/apps/build/privacy-law-compliance).
  - GraphQL only for new public apps: REST Admin API legacy since 2024-10-01; since 2025-04-01 new public apps must use GraphQL exclusively (paraphrase, https://shopify.dev/docs/api/admin-rest). No stated deadline for existing apps in what was read.
  - Performance: Lighthouse must not drop by more than 10 points (paraphrase, checklist page; may be softer in practice). Online-store changes must use theme app extensions.
- **Stages** (DOCS, review-process): Draft, Submitted, Paused (core requirements fail), Reviewed (reply to reviewer), Published. Withdraw any time. Since 2026-04-20 requirement-level feedback is in the Partner Dashboard and resubmission is blocked until all flagged items are resolved. An optional AI self-review is advisory and "uses model token costs" (COMMUNITY, post 33472).
- **Reviewer:** Shopify's App Store Review team, assigned after core requirements are met.
- **Cost:** no review fee found. The $19 registration fee is covered in section 1. Revenue share not researched.
- **Official wait:** none stated. Staff on 2026-04-20: "we are unable to provide any estimated timeframes" (COMMUNITY, https://community.shopify.dev/t/does-shopifyqlquery-require-level-2-pcd-access-how-long-to-get-that-access/33439). The confirmation email reportedly says "can take up to 2 weeks" (second-hand, user quote dated 2026-02-16, https://community.shopify.dev/t/shopify-app-review-taking-more-than-2-weeks-is-this-normal/29646).
- **Community-reported wait:** announcement 2026-02-26 that reviews were slower than usual, no estimate; replies report about 1 to 2 months or more; do not resubmit (back of queue) (https://community.shopify.dev/t/longer-app-store-review-times-what-you-need-to-know/31728). 2026-04-06: one poster says Shopify quotes 2 to 4 weeks, others report 4+ weeks with no reviewer assigned (https://community.shopify.dev/t/how-many-days-does-it-take-to-approve-an-shopify-app/32984). 2026-08-18: one user says 1 to 3 weeks (https://community.shopify.dev/t/shopify-app-review-still-assigning-a-reviewer-after-5-days-how-long-does-it-take/36879): may have eased, one anecdote. Planning range 1 to 6 weeks for first review (our synthesis).
- **PCD timing:** no figure. Staff on 2026-03-16: the Level 2 review "happens during app review", so submit the form complete beforehand (https://community.shopify.dev/t/level-2-access-to-customer-data-versus-public-app-approval/32233). Partial approvals and revocations after resubmission were reported (https://community.shopify.dev/t/pcd-request-partially-approved-clarification-submitted-but-no-response-yet/32215).
- **Rejection reasons** (DOCS, https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review): billing, installation (no redirect to the OAuth grant screen, fatal error after install, failed reinstall), embedding, UI errors (404/500), no testing instructions or credentials, not using theme app extensions.
- **Repeated failure:** the 2026-02-26 announcement warns of temporary suspension (COMMUNITY); the review-process page does not.
- **Re-review:** not documented. Shopify may select an app for a data protection review later (paraphrase, PCD page). New scopes need merchant approval in a later version.

## 4. Gotchas

- **Token lifetimes (key change).** Changelog 2026-04-01: "all new public apps must request and use expiring offline access tokens." Custom, merchant-built and pre-2026-04-01 public apps were exempt at that point (DOCS, https://shopify.dev/changelog/expiring-offline-access-tokens-required-for-public-apps-april-1-2026). The offline-tokens page adds existing public apps must switch for GraphQL Admin API requests by 2027-01-01 (paraphrase, https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens). Expiring offline access token: 1 hour (`expires_in` 3600). Refresh token: 90 days (7776000 s). Non-expiring tokens last until uninstall or secret revocation. Each refresh returns new access and refresh tokens; store both. Acquiring a new token via token exchange or the authorization code grant retires older expiring tokens for that app and store; do not refresh and acquire at the same time. Rotating the client secret invalidates tokens tied to the old secret. Changelog 2026-08-28: the previous refresh token now stays valid until you use its replacement, up to 30 days from first use and never past 90 days (paraphrase; previously a 60-minute retry window) (https://shopify.dev/changelog/more-resilient-refreshes-for-expiring-offline-access-tokens.md). Refresh request format: UNCERTAIN (not on pages fetched).
- **Token exchange is embedded-only** (needs an App Bridge ID token; DOCS, https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/token-exchange). A headless integration platform must use the authorization code grant.
- **Per-tenant subdomain:** authorize and token URLs are per shop, so the user must supply their shop domain before redirect. This conflicts with requirement 2.3.1 ("must not request the manual entry of a myshopify.com URL"). How review treats a connector-initiated flow: UNCERTAIN.
- **Scopes:** write implies read; merchants can change requested scopes, so check the granted `scope`. With `optional_scopes`, installed scopes can differ from config; query `currentAppInstallation`.
- **Custom distribution is permanent;** making one custom app per merchant to avoid review may violate the Partner Program Agreement (COMMUNITY, 2026-04-08 reply).
- **Reviewer testing:** reviews stalled when the reviewer could not exercise a Level 2-gated call (COMMUNITY, 2026-03-13 thread). Supply credentials that reach real functionality.
- **Webhooks:** `customers/redact` payloads arrive 10 days after the request if the customer has not ordered in six months; `shop/redact` 48 hours after uninstall. HTTPS webhooks: 1-second connect timeout, 5-second total, 8 retries over 4 hours (DOCS, privacy-law-compliance and https://shopify.dev/docs/apps/build/webhooks/subscribe/https).
- Dev Dashboard client credentials are not a drop-in for legacy static tokens (expire in 24 hours; COMMUNITY, not opened).

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research requirements, limits, token model | Yes | No | Public docs |
| Draft privacy policy, terms, PCD justification | Yes | Legal review, publish at a public URL | Accountable owner |
| Fill toml (`scopes`, `redirect_urls`, compliance webhooks) | Yes | Run CLI deploy in their account | Logged-in CLI and org |
| Partner sign-up | No | Yes | Account, possible 2FA, business info |
| Pay the $19 fee if charged | No | Yes | Payment |
| Create app, copy Client ID and secret | No | Yes | Login |
| Select distribution (public) | No | Yes | Irreversible |
| Build OAuth endpoint, HMAC check, refresh handling, compliance webhooks | Yes | Review and deploy | Code |
| Create dev store, test install and reinstall | Partly | Yes | Console login |
| Listing assets | Draft copy | Capture real screenshots, approve branding | Must reflect the real product |
| Record screencast | Script | Yes | Own account |
| Reviewer test credentials | Draft instructions | Create and own accounts | Credentials |
| Submit PCD request and the review | Draft answers | Submit | Irreversible |
| Wait, reply to reviewer | Draft | Send | Messages on user's behalf |

## 6. Difficulty tier and estimate

**Tier: review-required.** A multi-tenant OAuth connector cannot use custom distribution. Usable on day one: dev stores, plus custom-distribution links to single shops. Estimates at the top.

## 7. Sources

All accessed 2026-10-19.

| URL | Supports | Label |
|---|---|---|
| dev.shopify.com/dashboard, shopify.com/partners | Login wall, marketing page | TESTED |
| https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant | Auth flow, redirect rule | DOCS |
| https://shopify.dev/docs/apps/launch/distribution ; .../select-distribution-method | Distribution types | DOCS |
| https://shopify.dev/docs/apps/build/dev-dashboard ; .../create-apps-using-dev-dashboard ; .../migrate-from-partners | Dev Dashboard | DOCS |
| https://shopify.dev/changelog/next-gen-dev-platform-ga | GA, dev stores | DOCS |
| https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant ; .../token-exchange ; .../app-installation | Grants and install flows | DOCS |
| https://shopify.dev/docs/apps/build/cli-for-apps/app-configuration | toml fields | DOCS |
| https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens | Expiring tokens | DOCS |
| https://shopify.dev/changelog/expiring-offline-access-tokens-required-for-public-apps-april-1-2026 ; https://shopify.dev/changelog/more-resilient-refreshes-for-expiring-offline-access-tokens.md | Token changes | DOCS |
| https://shopify.dev/docs/api/usage/access-scopes ; https://shopify.dev/docs/apps/launch/protected-customer-data | Scopes, PCD | DOCS |
| https://shopify.dev/docs/apps/launch/app-requirements-checklist ; .../shopify-app-store/app-store-requirements ; .../app-store-review/submit-app-for-review ; .../review-process ; .../pass-app-review | Review | DOCS |
| https://shopify.dev/docs/apps/build/privacy-law-compliance | Compliance webhooks | DOCS |
| https://shopify.dev/docs/apps/build/apis/graphql-admin/rate-limits ; https://shopify.dev/docs/api/usage/rate-limits ; https://shopify.dev/docs/api/admin-rest | Limits, REST status | DOCS |
| https://help.shopify.com/en/partners/partner-program/glossary | $19 fee | DOCS (undated) |
| community.shopify.dev threads listed above (31728, 33472, 29646, 32984, 36879, 33101, 32233, 33439, 26798, 32946, 8691, 32215) | Review waits, behavior | COMMUNITY (2026-02 to 2026-08) |
| https://community.shopify.com/t/trying-to-signup-but-getting-error/550785 | Partner 2FA | COMMUNITY (undated) |

## 8. Open questions

1. Expiring-token deadline: the 2026-04-01 changelog says only new public apps; the offline-tokens page adds existing public apps by 2027-01-01. Trust the docs page; re-check.
2. $19 fee: glossary says it exists; one third-party guide says free; when it is charged is unknown.
3. Redirect URL rules (HTTPS, localhost, wildcards, count): not stated. Matters for a shared Composio callback.
4. Manual shop entry (requirement 2.3.1) vs per-shop OAuth for a connector-initiated flow: unknown.
5. Off-platform billing ban vs a free connector app: unverified.
6. Review wait: Shopify says up to 2 weeks (second-hand), no SLA, community days to over a month.
7. Sign-up prerequisites, bucket sizes, REST limits: need a logged-in or logged-out walk-through.
8. Assumption check: "custom distribution works for arbitrary merchants" is wrong (single store or one Plus org, permanent). Dev Dashboard client credentials do not reach stores outside your org.
