# HubSpot: OAuth app (new project-based platform) and App Marketplace

- Researched: 2026-10-19
- Tier: **review-required**. A working app is instant but capped at 25 installs with warning banners. Unlimited installs need a Marketplace listing.
- Effort: about 6 to 10 active hours (1 to 2 CLI and config, 1 Composio wiring, 2 to 4 listing form, docs, policies and demo video, 1 to 2 feedback rounds).
- Calendar time: under an hour to a capped app. About 3 to 8 weeks to a listed app. Official: initial review within 10 business days, full feedback cycle no more than 60 days. You also need 3 real, unaffiliated installs first. Certification (optional) adds 6+ months.
- Confidence: medium-high on structure (many raw DOCS reads). Medium on timings (vendor blogs only). A Composio-specific policy risk is flagged as UNCERTAIN.

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN.

## Headline: the old "create a public app" path is closed

- DOCS: "As of June 23, 2026, legacy public apps can no longer be created." https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview
- Accounts created on or after May 26, 2026 lost creation on May 26. Older accounts on June 23, 2026. Existing legacy public apps keep working (DOCS, changelog https://developers.hubspot.com/changelog/legacy-public-app-creation-sunset, read through a summarizer).
- Composio's own HubSpot guide (https://composio.dev/auth/hubspot, COMMUNITY/vendor, undated) still says "Create a public app". For a developer with no existing legacy app, that is stale.
- Separate developer accounts were folded into standard accounts on March 9, 2026 (DOCS, https://developers.hubspot.com/docs/getting-started/developer-overview).
- TESTED (consistent): `developers.hubspot.com` leads with an animated terminal typing `hs`, not a console form. `app.hubspot.com/signup-hubspot/developers` redirected to the generic CRM signup `...signup-hubspot/crm?intent=developer`. Only a cookie dialog was visible; fields were not seen.

## 1. Where and how the app is created

**There is no web form.** Apps are created and deployed with the HubSpot CLI (`hs project create`, choose App, then `hs project upload`). DOCS: https://developers.hubspot.com/docs/apps/developer-platform/overview ("created and deployed via the HubSpot CLI", partial quote); https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app (summarizer).

After upload the project appears in the HubSpot account under Development, Projects. Client ID, secret and redirect URLs are on the **Auth** tab. The install URL is on the **Distribution** tab (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/build-apps/manage-apps-in-hubspot). Platform versions (DOCS, https://developers.hubspot.com/docs/developer-tooling/platform/versioning): 2026.09 is Current (from Sept 8, 2026); 2026.03 and 2025.2 supported; 2025.1 sunset Aug 1, 2026.

**Prerequisites**
- A normal HubSpot account, free or paid (DOCS, https://developers.hubspot.com/docs/getting-started/account-types).
- Access to Development: super admin, partner admin, or a user with a developer seat or "Developer tools access" (DOCS, developer-overview).
- No payment to create an app. 2FA: UNCERTAIN. Node.js: 2025.2 requires v22 (DOCS, versioning).

**Steps**
1. Sign up or log in to a HubSpot account (human).
2. `npm install -g @hubspot/cli`, then `hs account auth` (personal access key).
3. `hs project create`; choose App, distribution marketplace, auth oauth.
4. Edit `app-hsmeta.json`: uid, name, description, logo, redirectUrls, scopes, support fields.
5. `hs project upload`, `hs project open`. Copy client ID and secret from the Auth tab.
6. Distribution tab, **Begin publishing**; review and sign the Acceptable Use Policy. Until signed, the app installs only in developer test accounts (DOCS, manage-apps).
7. Install into a developer test account, then real accounts via the install URL.

**`app-hsmeta.json` fields** (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration)

| Field | Rule |
|---|---|
| `uid` | required, up to 64 chars |
| `name` | required, up to 200 chars |
| `description` | required, up to 8192 chars |
| `logo` | optional png, jpeg, gif or bmp |
| `distribution` | `marketplace` or `private` |
| `isUserLevel` | optional, default false |
| `supportEmail`, `documentationUrl`, `supportUrl`, `supportPhone` | optional; URLs HTTPS; phone starts with `+` |
| `permittedUrls` | optional fetch, iframe, img arrays, HTTPS |
| `auth.type` | `oauth` or `static` |
| `auth.redirectUrls` | required, at least one. DOCS: "it must use HTTPS. The only exception is that `http://localhost` is allowed". No maximum stated (UNCERTAIN). No IP addresses (paraphrase). |
| `requiredScopes` | at least one |
| `optionalScopes`, `conditionallyRequiredScopes` | OAuth only |

Marketplace distribution must use OAuth. Auth type and distribution cannot change after first upload (paraphrase via a search result, UNCERTAIN on wording).

Privacy policy and terms URLs are **not** in `app-hsmeta.json`. They are in the listing form (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/listing-your-app): Listing info tab (public app name, company name, tagline, install experience, install button URL, 800x800 icon, up to two categories), App details tab (demo video, up to 8 screenshots, overview), Support tab (support email required; privacy and terms links). Listing URL fields are limited to 250 characters.

## 2. What works immediately vs what is gated

**Install caps** (DOCS, manage-apps). Quote: "Marketplace OAuth app prior to listing: can be installed in up to 25 accounts".

| Distribution | Cap |
|---|---|
| Marketplace OAuth, unlisted | 25 accounts, not counting developer test accounts. Unlimited once listed. |
| Private OAuth | 10 allowlisted accounts (100 for apps in a Solutions Partner portal) |
| Static token | 1 standard account plus up to 10 developer test accounts |

The caps apply to apps created or migrated to platform 2025.2 from Sept 22, 2025 (DOCS, changelog https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits, summarizer). Unlisted marketplace OAuth apps have no allowlist: anyone with the install URL can install until the cap.

**Warnings at install:** unverified apps show a banner and the installer must type "I accept the risk". A TXT-record domain verification removes the "unverified" banner but leaves "not reviewed or approved by HubSpot". One verified domain per account, shared by all apps; changing it takes "a couple hours". Listed apps show neither (DOCS, manage-apps and legacy overview).

**Installer permissions:** Super Admin or Marketplace Access permission plus the permissions for requested scope groups (DOCS). Consequence: a non-admin end user cannot connect HubSpot.

**Scopes:** many are tier-gated; sensitive-data scopes are Enterprise-only (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/scopes). Optional scopes are silently dropped if the tier is missing; required scopes fail the install.

**Rate limits** (DOCS, https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines): public marketplace OAuth apps get 110 requests per 10 seconds per installing account (excluding CRM Search); no daily cap listed for public apps. Private apps: 100 per 10 seconds on Free and Starter, 190 on Professional and Enterprise; daily caps 250k, 625k, 1M. Certification docs say "100 inbound requests every 10 seconds" (paraphrase), so throttle at 100 client-side.

**Test accounts** (DOCS, account-types): free, up to 10 per standard account, expire after 90 days without API calls, not counted against install caps.

## 3. Approval / review path

**Trigger:** the 25-install cap. A Marketplace listing is the route to unlimited installs; the alternative is private distribution (10 or 100 accounts).

**Listing minimums** (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/app-marketplace-listing-requirements, read raw): "your app must have at least three active, unique installs" (production accounts unaffiliated with you, successful activity in the past 30 days); "your app must use OAuth as its sole authorization method"; one app ID; only scopes actually used; Technology Partner Program Agreement; not a restricted industry; no classic CRM cards (unsupported since June 16, 2025); supported platform version; AI connectors need user-level permissions or HubSpot's MCP server; live Terms and Privacy URLs; public setup docs; a support contact; install button URL; a Shared data table matching the scopes; allowlist the "HubSpot Crawler" user agent.

**Submission:** a Super Admin goes to Development, App Listings, Create listing, completes seven tabs, clicks Validate & submit. A demo video field exists; the listing page does not make it mandatory. Reviewer: the HubSpot Ecosystem Quality team. Only one app can be submitted at a time; extras are "automatically rejected".

**Cost:** DOCS: "No, we do not charge you a fee to list or certify your apps" (https://developers.hubspot.com/docs/apps/developer-platform/list-apps/apply-for-certification/certification-requirements). No revenue share.

- **Official wait:** initial review "within 10 business days"; the full review and feedback cycle "should take no more than 60 days from the time feedback is shared". HubSpot "reserves the right to unpublish or refuse" a listing (paraphrase).
- **Community-reported wait:** a vendor blog (https://appnigma.ai/blogs/hubspot-marketplace-complete-guide/, June 24, 2026, unsourced) says 2 to 4 weeks, with one case at 9 weeks and one feedback round. A HubSpot Community thread (https://community.hubspot.com/t5/APIs-Integrations/App-not-Publised-in-Marketplace-ever-after-resubmission/td-p/1166746) was seen only in search results (403 on fetch): UNCERTAIN.
- **Rejection reasons** (COMMUNITY/vendor, not HubSpot; appnigma and https://hs-x.dev/docs/guides/marketplace-listing/, undated): unused scopes, dead or uncrawlable setup or privacy URLs, demo video not matching the listing, Shared data table not matching scopes, OAuth install loop from not returning to `returnUrl`, no reviewer test credentials.
- **Certification** (separate, optional; DOCS, certification-requirements): needs 60 active unique installs, a demo video, a verified domain and a security questionnaire; the app must have been listed 6 months. Same 10 business day and 60 day windows. After rejection, reapply in 6 months. Valid 2 years. Not needed for unlimited installs.
- **Blocker for Composio-style apps** (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/marketplace-restrictions): not eligible, "Credential and token brokering: apps with a primary commercial offering of storing, managing, or distributing end-user OAuth tokens or API credentials on behalf of third-party developers." White-label and developer-only infrastructure are also excluded. A Composio-owned shared HubSpot app could be rejected under this clause. Whether Composio counts is UNCERTAIN. This is why Composio may want customers to bring their own app, which stays at 25 installs unless they list it.
- **Re-review:** after Oct 26, 2026, any listed app editing its listing must choose an install experience (DOCS, https://developers.hubspot.com/docs/apps/developer-platform/list-apps/understand-app-install-flow). Apps not installed in 180 days are delisted (paraphrase). Certification renews every 2 years.

## 4. Gotchas

- **Tokens:** DOCS: "Access tokens are short-lived (30 minutes)" with `expires_in: 1800` (https://developers.hubspot.com/docs/api-reference/auth-oauth-v3/guide). The refresh token is described only as "long-term"; no expiry is given. COMMUNITY (search snippet, not fetched): a staffer says refresh tokens should not expire unless uninstalled. UNCERTAIN.
- Refresh failures: the error says "refresh token is invalid, expired or revoked" (DOCS). Nango (https://www.nango.dev/blog/hubspot-oauth-bad-refresh-token, April 1, 2026, COMMUNITY/vendor) lists uninstall, scope changes, parallel refresh races and undocumented security heuristics; its "~1% per month" figure is anecdotal. A revoke endpoint exists (DOCS).
- **Scope changes force re-authorization;** static-token apps need the Reinstall URL (DOCS, manage-apps).
- **EU:** Fivetran (https://fivetran.com/docs/connectors/applications/hubspot/troubleshooting/hub-unknown-error, third-party, snippet only) says EU accounts authorize via `app-eu1.hubspot.com`, otherwise "Hub is unknown to this Hublet". No official doc confirmed. UNCERTAIN. The OAuth page says `app.hubspot.com/oauth/authorize` can target one portal by inserting the account ID.
- **Composio callback URL** differs between its HubSpot guide (`/api/v3/toolkits/auth/callback`) and general docs (`/api/v3.1/...`). Verify which the project expects.
- **Date-based API versions:** legacy v1 to v4 still supported; platform versions sunset after 18 months (DOCS, versioning).
- **Migration:** legacy public apps over 25 installs may hit the cap when migrated; a community error `UNLISTED_APP_OVER_PRIVATE_INSTALL_LIMIT` (snippet only). Legacy private app creation also being sunset; dates seen in a search result were Sept 28 and Oct 26, 2026 (UNCERTAIN).

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research current docs and caps | Yes | No | Public docs |
| HubSpot sign-up, 2FA, email verification | No | Yes | Account and credentials |
| Install CLI, `hs account auth` | Commands only | Browser auth consent | Personal access key belongs to a logged-in human |
| Scaffold project, edit `app-hsmeta.json`, upload | Yes, once authed | Review | Template-able |
| Copy client ID and secret | Partly | Yes | Secrets |
| Sign the Acceptable Use Policy | No | Yes | Legal acceptance |
| Domain verification TXT record | Draft instructions | Yes | Needs DNS access |
| Draft privacy policy, terms, scope justification, listing copy | Yes | Legal review | Writing |
| Record demo video | No | Yes | Needs a real account |
| Find 3 unaffiliated customers who install and use it | No | Yes | Business relationships |
| Submit listing (Super Admin) | No | Yes | Irreversible, terms |
| Answer reviewer feedback | Draft | Send | Owner |
| Wait for review | No | Yes | Elapsed time |

## 6. Difficulty tier and estimate

**Tier: review-required.** Not instant (25-install cap and banners until listed). Not partner-only (no fee, no partner-program gate for the OAuth Marketplace path). The token-brokering clause could push a shared Composio app toward partner-only. Estimates at the top of this file.

## 7. Sources

All accessed 2026-10-19.

| URL | Supports | Label | Notes |
|---|---|---|---|
| developers.hubspot.com, app.hubspot.com/signup-hubspot/developers | Landing page leads with CLI; signup redirect | TESTED | Fields not seen |
| https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview | Creation closed June 23, 2026 | DOCS | |
| https://developers.hubspot.com/changelog/legacy-public-app-creation-sunset | Sunset dates | DOCS (summarizer) | Raw 404 |
| https://developers.hubspot.com/docs/apps/developer-platform/overview | CLI creation | DOCS | |
| https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app | CLI steps | DOCS (summarizer) | |
| https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration | Fields, redirect rules | DOCS (raw) | |
| https://developers.hubspot.com/docs/apps/developer-platform/build-apps/manage-apps-in-hubspot | Caps, AUP, domain | DOCS (raw) | |
| https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits | Cap introduction | DOCS (summarizer) | |
| https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/app-marketplace-listing-requirements | 3 installs, wait times | DOCS (raw) | |
| https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/listing-your-app | Listing wizard | DOCS | |
| https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/marketplace-restrictions | Token-brokering ban | DOCS (raw) | Undated |
| https://developers.hubspot.com/docs/apps/developer-platform/list-apps/apply-for-certification/certification-requirements | Certification, no fee | DOCS (raw) | |
| https://developers.hubspot.com/docs/api-reference/auth-oauth-v3/guide | 30-minute token | DOCS (raw) | |
| https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines | Rate limits | DOCS (raw) | |
| https://developers.hubspot.com/docs/developer-tooling/platform/versioning | Versions | DOCS (raw) | |
| https://developers.hubspot.com/docs/getting-started/account-types | Test accounts | DOCS (raw) | |
| https://developers.hubspot.com/docs/getting-started/developer-overview | Account merge | DOCS | |
| https://developers.hubspot.com/docs/apps/developer-platform/list-apps/understand-app-install-flow | Install experience change | DOCS (raw) | |
| https://developers.hubspot.com/docs/apps/developer-platform/build-apps/migrate-an-app/overview | Migration rules | DOCS (raw) | Internally confusing |
| https://www.nango.dev/blog/hubspot-oauth-bad-refresh-token | Refresh failures | COMMUNITY (vendor, 2026-04-01) | Anecdotal |
| https://appnigma.ai/blogs/hubspot-marketplace-complete-guide/ | Review time | COMMUNITY (vendor, 2026-06-24) | Unsourced |
| https://hs-x.dev/docs/guides/marketplace-listing/ | Rejection reasons | COMMUNITY (vendor, undated) | |
| https://composio.dev/auth/hubspot | Composio guide | COMMUNITY/vendor | Likely stale |
| community.hubspot.com thread 1166746; fivetran EU doc | Review delay; EU host | COMMUNITY (snippets only) | Not read |

## 8. Open questions

- "60 installs" is the certification threshold, not the listing threshold (3). The certification page measures installs over six months; the listing page uses 30 days. Both official.
- Appnigma says sandboxes and beta installs count towards the 3; HubSpot says production accounts unaffiliated with you. Trust the docs.
- Migration doc is internally inconsistent about the 10-install rule.
- Is a Composio-owned shared HubSpot app allowed on the Marketplace? The token-brokering clause says maybe not. Unconfirmed.
- Refresh-token lifetime is not stated officially.
- Can the new platform be used without the CLI? The overview says CLI; the Projects UI was not checked.
- Redirect URI count limit, 2FA and signup friction: unknown without logging in.
- Our assumption "HubSpot public app via the developer account" is outdated: it is now CLI-based projects, in a normal HubSpot account.
