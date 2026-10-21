# Xero: developer app, connection tiers, certification

- Researched: 2026-10-19
- Tier: **verify-to-scale**. The app works at once with 5 connections, free. A credit card unlocks 50 (no review found). Beyond 50 needs certification, which behaves like review-required. For a shared app serving hundreds of customer orgs, treat it as review-required.
- Effort: 1 to 2 hours to create an app and test on the demo company. Building to the 8 certification checkpoints is roughly 40 to 120 hours (our estimate, not official). The security self-assessment takes about 5 working days per Xero, probably 8 to 16 active hours.
- Calendar time: same day for Starter or Core. Certification and the Plus tier: about 2 to 6 months (our estimate from a vendor's "several months" and one 2024 to 2025 post). Xero states no overall wait.
- Confidence: medium-high on tiers and limits (Xero pricing and limits pages agree). Medium on certification timing.

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. Source IDs like [S5] map to section 7. Xero's documentation pages are JavaScript-rendered; the research tool read them through a text-rendering proxy, so quotes were not read from the original HTML. See `_verification.md`.

## Directly observed (TESTED, 2026-10-19)

`developer.xero.com/app/manage` redirected to `login.xero.com/identity/user/login` with email and password fields and "Don't have an account? Sign up". The first load showed a blank page, then the redirect. TESTED.

## 1. Where and how the app is created

**Console:** `https://developer.xero.com/app/manage` ("My Apps") [S1]. Sign-up link: `https://www.xero.com/signup/developers/` [S1].

**Prerequisites**
- DOCS [S1]: "Signup for a free Xero account"; then "Enable the Xero demo company" and add the OAuth 2.0 app.
- DOCS [S2]: the developer portal account "is not tied to a specific Xero payment plan".
- Starter-tier apps need no payment method; the tier table lists "Payment Method: Not Applicable" for Starter, "Required" from Core upward (DOCS [S3]).
- 2FA on the developer login: not stated anywhere read. UNCERTAIN.

**Steps**
1. Sign up for a free Xero account and verify the email.
2. `developer.xero.com/app/manage`, click **New app** (top right; COMMUNITY [S19] WorkOS; Xero's Postman guide calls it the "add a new app" modal [S12]).
3. Fill the form and accept the Developer Platform Terms and Conditions (COMMUNITY [S19], checkbox wording paraphrased).
4. **Create app**.
5. Configuration, **Generate a secret**, copy Client ID and secret (COMMUNITY [S19]).
6. Add more redirect URIs under App details, OAuth 2.0 credentials, "Add another URI" (COMMUNITY [S20], Paragon, undated).
7. Beyond 5 connections, add a card (sections 2 and 3).

**Fields confirmed**
- App name: "can't contain the word 'Xero'" (DOCS [S12], paraphrase); certification checkpoint 2: "cannot include the word Xero" [S6].
- Integration type: Web app / "Auth Code"; "Auth Code with PKCE" for native; "Custom connection" (client credentials) [S12, S9, S19]. DOCS [S5]: "make sure you select the 'Auth Code' grant type". DOCS [S11]: "Single Page Apps (SPAs) are not currently supported."
- Company or application URL: DOCS [S12]: "this needs to be an https address, but isn't used" (Postman context).
- Redirect URI: standard flow [S5]: "http://127.0.0.1 cannot be used"; localhost allowed for testing, everything else https. PKCE [S11]: "All redirect URIs must be https with the exception of localhost." and "Custom URL Schemes are not supported." FAQ [S10]: "You can use up to 50 redirect URIs for your app." and "The use of wildcards in redirect URI is not supported." COMMUNITY [S18] Composio's Xero guide says "No trailing slash"; not found in Xero docs.
- Scopes are not chosen in the app form for Web and PKCE apps; they go in the authorize URL `scope` parameter [S5]. Custom connections select scopes at creation [S9]. Always add `offline_access` and `openid profile email` [S4].
- "Login URL for launcher": a certification requirement set under Configuration [S6].
- Logo, privacy policy URL, terms URL: UNCERTAIN as form fields. None of the create-app guides read (Xero Postman, WorkOS, Apideck, Paragon, Composio) list them. The App Store listing form has its own fields [S7]. The developer terms require your own terms and privacy policy ("Your apps must include your own legally binding terms of use and privacy policy" [S14]): a legal duty, not a confirmed form field.

## 2. What works immediately vs what is gated

**Starter, no card:** DOCS [S4]: "New apps default to the starter tier with 5 connections." A "connection" is a tenant, not a user; DOCS [S8]: "only one of those connections will count towards your connection limit". The demo company is free; it resets "automatically reset 28 days after creation" and must be reconnected [S13]. Remote MCP on Starter works only with the demo org; "Real customer organisations need the Core plan or above." [S10]

**Tiers** (DOCS [S3], [S10])

| Tier | Max connections | Fee (AUD, ex tax) | Egress included | Prerequisite |
|---|---|---|---|---|
| Starter | 5 | free | n/a | none |
| Core | 50 | $35/month | 10 GB | card |
| Plus | 1,000 | $245/month | 50 GB | App Certification |
| Advanced | 10,000 | $1,445/month | 250 GB | Certification and security assessment |
| Enterprise | no limit | on application | on application | Certification and App Store listing |

Overage egress $2.40 AUD per GB; the Organisation endpoint is excluded. DOCS [S10]: "Your connections are capped at the tier maximums until you meet that tier's requirements." Starter to Core needs only a card; a 6th connection requires payment details (paraphrase [S10]); no review step found. "The only approved billing method is by credit card." [S10]

**Uncertified-app limit per customer organisation (separate):** DOCS [S4]: "each organisation or practice is limited to connecting a maximum of five uncertified apps"; "There is no limit on connecting certified apps." This belongs to the customer's org, not your app: a shared uncertified app consumes one of each customer's five slots. Custom Connections are exempt [S9].

**Rate limits** (same for all apps [S10]; DOCS [S4]): "5 calls in progress at one time"; "60 calls per minute"; "1,000 calls per day for starter, 5,000 calls per day for higher tiers" per tenant; "10,000 calls per minute" across all tenants. 429 carries `X-Rate-Limit-Problem` and `Retry-After`.

**Premium features:** Journals, the XPM API and Bulk Connections need the Advanced tier plus a security assessment and use-case approval [S3]. `accounting.journals.read` "is no longer granted by default" [S27]. Rapid Sync from Plus upward.

No unverified-app consent warning is documented. UNCERTAIN.

## 3. Approval / review path

**Triggers:** need for more than 50 connections; App Store listing requires Plus or above [S4]; Journals, XPM, Bulk Connections need security assessment and use-case approval [S10]; practice APIs (mail `api@xero.com`) and financial services apps (Google form) need prior approval before you can apply [S7].

**Apply:** developer portal, select the app, "Manage Plan", complete an application form; then upgrade to Plus and get certified as part of the upgrade (paraphrase [S7]).

**Reviewed:** prerequisites include "ten active customer connections" and Sign Up with Xero [S7]. You "may need to provision a test account for us" [S7]. Review is against 8 checkpoints [S6]: (1) connection (shows tenant name and status; connect and disconnect; calls DELETE on Connections; handles disconnect from Xero's side); (2) branding and naming; (3) App Launcher URL; (4) scopes ("Unexplained or ambiguous use of scopes will not be allowed."; "Using the offline_access scope is a requirement for certification."); (5) error handling; (6) data integrity; (7) account and payment mapping; (8) taxes. No demo video mentioned. The security self-assessment is annual; needed for 1,000+ connections and all practice API consumers [S15]; connections "capped at 999" until passed [S7].

**Reviewer:** Xero's API and developer team; Xero's security team reviews the assessment [S15].
**Cost:** no separate certification fee. The cost is the tier fee (Plus $245 AUD per month). Certified-app terms add a monthly Platform Fee and egress overages and make you responsible for removing stale connections ("You are responsible for removing Connections" [S16]).

- **Official wait:** security assessment only [S15]: "Typically the assessment takes around 5 working days to complete"; Xero then needs 5 to 10 working days to assess answers; on failure 30 days for a remediation plan and 60 days to implement. Text dates from the 2020 rollout, possibly stale. Overall certification and Plus-tier approval: no stated wait. UNCERTAIN.
- **Community-reported wait:** Codat: "It can take several months to become a Xero App Partner" (undated vendor doc [S22]). A developer's Medium post (2025-01-13 [S23]) says certification started February 2024; it does not say when approved.
- **Rejection reasons:** only generic: "If you do not meet the requirements above you will be required to make changes before proceeding with certification." [S8] No specific rejection cases found.
- **Re-review:** security assessment annual [S15]; commercial terms mention "the annual recertification process" [S16].

## 4. Gotchas

- **Tokens** (DOCS [S5]): id_token 5 minutes, "access_token: 30 minutes", "refresh_token: 60 days"; authorization code "expires 5 minutes after issuance"; every refresh returns a new refresh token (rotation), so save both; if the response is lost the old token can be retried for a "grace period of 30 minutes" (a 2026 vendor blog also says 30 minutes [S30]); then the user must re-authorize. DOCS [S10]: "Unused refresh tokens expire after 60 days." COMMUNITY [S24] (2026-04-16): concurrent refresh jobs can kill the connection (use a row lock); a missing `offline_access` means the connection dies after 30 minutes. A multi-tenant user shares one token pair across all tenants: store tokens per Xero user [S25].
- **Tenants and regions:** no per-tenant subdomains. Auth `login.xero.com`, tokens `identity.xero.com`, API `api.xero.com` with the `xero-tenant-id` header [S5]. DOCS [S8]: "You can only request scopes for a single tenant type at a time" (Accounting and Practice Manager need separate flows). Custom Connections work only in AU, NZ, UK, US orgs and cost the customer a monthly subscription (about AUD 10, NZD 10, GBP 5, USD 5; [S17]).
- **Roles:** the authorizing user picks which tenants to connect; cashbook and ledger orgs must be authorized by practice staff [S4]. Which org roles can authorize: UNCERTAIN.
- **Scope changes (a recent break):** DOCS [S27]: "Apps created on or after 2 March 2026 already use granular scopes."; "Existing apps have until 13 September 2027 to migrate." DOCS [S28]: `accounting.transactions` splits into `accounting.invoices`, `.payments`, `.banktransactions`, `.manualjournals`; `accounting.reports.read` splits per report; `accounting.settings`, `.contacts`, `.attachments` unchanged. A missing granular scope returns 401 with an insufficient-scope challenge [S10]. Scopes are additive on an existing token [S28]. COMMUNITY (search summary of GitHub PRs and Chift or Codat docs, not opened): requesting `accounting.transactions` on a new app returns `invalid_scope`. Composio's own Xero guide still lists `accounting.transactions` and `accounting.reports.read` [S18]: likely wrong for new apps.
- **Pricing timeline** (DOCS [S3], [S10]): 4 Dec 2025 new pricing announced (applies at once to developers registered on or after that date); 2 Mar 2026 new tiers effective and terms apply to earlier registrants; mid-March 2026 existing apps began migrating with at least 30 days' notice; 1 Jul 2026 deadline to move customers off XASS billing; pre-2026 revenue-share billing retired.
- **Terms relevant to an agent platform** (DOCS [S14]): clause 29 prohibits "Aggregate and supply user data" to another app or third party, and creating "multiple versions of your app" that do the same thing; clause 8 says you are "responsible for making sure your app's use cases have been approved by us"; API data may not be used to train or fine-tune AI models (paraphrase, [S14], [S3]).
- Deleting an app deletes its connections [S8]. Max request 10 MB, practical batch about 50 items [S4].

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research tiers, scopes, limits | Yes | No | Public docs |
| Draft app name, homepage URL, redirect list | Yes | No | Template text |
| Draft scope list and justification | Yes | Review | Must match real use and granular scopes |
| Draft privacy policy, terms, support docs | Yes | Legal review | Required by dev terms |
| Create Xero login and developer account | No | Yes | Account creation, credentials |
| MFA prompts | No | Yes | Human-only (whether required: UNCERTAIN) |
| New app and Create app | Possible with the human present | Yes, to accept Xero's terms | T&C acceptance |
| Generate and store client secret | No | Yes | Credentials |
| Add credit card for Core | No | Yes | Payment |
| Enable demo company and test the flow | No | Yes | Human's Xero login |
| Implement checkpoints (disconnect UI, mapping, errors) | Yes | Review | Engineering |
| Onboard 10 real customer connections | No | Yes | Real customers |
| Submit certification application and test account | Draft only | Yes | Owner's identity |
| Security self-assessment | Draft | Sign-off | Attests company facts |
| Waiting on Xero, annual re-assessment | No | Yes | Calendar time, annual duty |

## 6. Difficulty tier and estimate

**Tier: verify-to-scale** (see top of file for effort and time).

## 7. Sources

All accessed 2026-10-19.

| ID | URL | Supports | Label |
|---|---|---|---|
| S0 | developer.xero.com/app/manage (login redirect) | Login required | TESTED |
| S1 | https://developer.xero.com/documentation/getting-started-guide/ | Free account, demo company | DOCS |
| S2 | https://developer.xero.com/documentation/guides/collaborators/overview | Portal account not tied to a plan | DOCS |
| S3 | https://developer.xero.com/pricing | Tiers, fees, egress, dates | DOCS |
| S4 | https://developer.xero.com/documentation/guides/oauth2/limits/ | Starter 5, uncertified limit, rate limits | DOCS |
| S5 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | Redirects, tokens, connections | DOCS |
| S6 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | 8 checkpoints | DOCS |
| S7 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | Application steps, 10 connections, 999 cap | DOCS |
| S8 | https://developer.xero.com/documentation/best-practices/managing-connections/connections/ | Connection counting | DOCS |
| S9 | https://developer.xero.com/documentation/guides/oauth2/custom-connections/ | Custom Connection exemption | DOCS |
| S10 | https://developer.xero.com/faq | FAQs | DOCS (mixed; one answer says 2 uncertified apps) |
| S11 | https://developer.xero.com/documentation/guides/oauth2/pkce-flow | PKCE redirects | DOCS |
| S12 | https://developer.xero.com/documentation/sdks-and-tools/tools/postman | New-app form | DOCS (screenshots may be old) |
| S13 | https://developer.xero.com/documentation/development-accounts | Demo company | DOCS |
| S14 | https://developer.xero.com/xero-developer-platform-terms-conditions | Aggregation, AI training | DOCS (updated 4 Dec 2025) |
| S15 | https://developer.xero.com/faq/xero-ecosystem-security-requirements-update | Security assessment timelines | DOCS (2020 text) |
| S16 | https://developer.xero.com/xero-developer-platform-commercial-terms | Platform fee, recertification | DOCS |
| S17 | https://developer.xero.com/documentation/guides/oauth2/overview/ | Flow comparison, Custom Connection pricing | DOCS (says "maximum of 5 tenants", outdated) |
| S18 | https://composio.dev/auth/xero | Composio's guide | COMMUNITY/vendor (scope list stale) |
| S19 | https://workos.com/docs/integrations/xero-oauth | Form fields | COMMUNITY (undated) |
| S20 | https://docs.useparagon.com/resources/integrations/xero | Extra redirect URIs | COMMUNITY (undated) |
| S22 | https://docs.codat.io/integrations/accounting/xero/xero-app-partner-program/ | "Several months" | COMMUNITY (undated) |
| S23 | https://marco-susilo.medium.com/my-app-got-certified-on-xero-app-store-9f121958f426 | One certification timeline | COMMUNITY (2025-01-13) |
| S24 | https://nsinenko.com/api/integrations/fintech/2026/04/16/xero-api-integration/ | Rotation gotchas | COMMUNITY (2026-04-16) |
| S25 | https://developer.xero.com/documentation/best-practices/managing-connections/multi-tenancy | Token storage | DOCS |
| S27 | https://developer.xero.com/changelog | Granular scopes, 13 Sep 2027 | DOCS (updated 15 Oct 2026) |
| S28 | https://developer.xero.com/documentation/guides/oauth2/scopes/ | Scope mapping | DOCS |
| S29 | https://developers.apideck.com/connectors/xero/docs/application_owner+oauth_credentials | Create-app fields | COMMUNITY (undated) |
| S30 | https://www.maesn.com/blog/how-to-integrate-with-xero/ | Claims 2-app limit, 30-minute grace | COMMUNITY (2026-05-18; the "2" conflicts with Xero) |

## 8. Open questions

1. Uncertified apps per customer org: 2 or 5? Limits page [S4] and connections page [S8] say 5; the general FAQ [S10] and Maesn [S30] say 2. We treat 5 as current.
2. Third parties cite "25 tenants" as an older cap; current docs say 5 on Starter and 50 on Core.
3. Does Core really need no review? Docs say a card moves you to Core; no review step found. Check "Manage Plan" in the portal.
4. Is Sign Up with Xero required for certification? [S6] says no; [S10] says "still required" for listed apps; [S7] lists it as a prerequisite.
5. Connections needed to apply: docs say 10 [S7]; one search summary of Apideck said 3 in 30 days (not verified).
6. Security assessment trigger: Advanced and above [S3]; 1,000+ connections [S7, S15]. Exact trigger for a Plus app unclear.
7. Granular-scope timing: sources differ on when existing apps could request them; expect `accounting.transactions` to fail on apps created after 2 March 2026.
8. **Is Composio's shared-app model allowed?** The terms forbid aggregating and supplying user data to other apps or third parties and require pre-approved use cases [S14]. No Xero text addresses unified-API or agent platforms. Ask Xero developer support before committing.
9. Per-customer bring-your-own-app avoids a single shared cap but may conflict with the "multiple versions of your app" clause: UNCERTAIN.
10. Xero launched a Remote MCP server on 2026-10-15 for apps on Core or above [S27]; it may compete with or supersede an agent toolkit.
11. Assumption check: "Xero caps unapproved apps at a small number of connections" is **true but incomplete**. The cap is 5 on free Starter and 50 on Core with only a credit card, so an unapproved app can reach 50 without review. There is also a separate cap of 5 uncertified apps per customer organisation.
