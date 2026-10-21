# Google: OAuth client and verification for Gmail scopes

- Researched: 2026-10-19
- Tier: **review-required**. Gmail read and modify scopes are restricted, so verification also needs a paid third-party security assessment (CASA), renewed yearly. Still a public process, not a partner agreement.
- Effort and calendar by scenario (our estimates for effort, sources for waits):

| Scenario | Active developer hours | Calendar time |
|---|---|---|
| Testing mode only (up to 100 test users, 7-day tokens) | 1 to 2 | Same day |
| Non-sensitive scopes only (for example `gmail.labels`) | 3 to 6 | 1 to 3 days |
| Sensitive scopes (for example `gmail.send`) | 8 to 16 | about 1 to 3 weeks |
| Restricted scopes with CASA (for example `gmail.readonly`, `gmail.modify`) | 25 to 60 | about 6 to 14 weeks |
| Annual renewal | 6 to 20 | several weeks |

- Confidence: high on scope classes and caps (many DOCS agree). Medium on timing and cost (no official cost figure).

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. DOCS quotes passed through a fetch-tool summarizer; see `_verification.md`.

## Directly observed (TESTED, 2026-10-19)

`console.cloud.google.com/auth/overview` redirected to Google sign-in ("to continue to Google Cloud Platform", with "Create account"). The Auth Platform pages are behind sign-in. TESTED.

## 1. Where and how the app is created

**Console:** the "Google Auth platform" has three pages: Branding `https://console.developers.google.com/auth/branding`, Audience `.../auth/audience`, Data Access `.../auth/scopes` (DOCS, https://developers.google.com/workspace/guides/configure-oauth-consent). Clients page creates OAuth clients; registering the app is "required before creating a client" (DOCS, https://support.google.com/cloud/answer/15549257). The older "APIs & Services, OAuth consent screen" path: UNCERTAIN whether it still exists.

**Prerequisites:** a Google account and a Google Cloud project (DOCS, https://developers.google.com/workspace/gmail/api/quickstart/python). Billing, 2FA and org requirements: UNCERTAIN. Internal user type needs a Cloud Organization (Workspace or Cloud Identity); outsiders get `org_internal` (DOCS, https://support.google.com/cloud/answer/15549945).

**Steps**
1. Create or select a Cloud project. 2. Enable the Gmail API. 3. Google Auth platform, Get Started: App name, User support email, Audience (Internal or External), contact email, tick "I agree to the Google API Services: User Data Policy", Create. 4. Audience: add test users if External. 5. Data Access: Add or Remove Scopes (choose the minimum; replacing sensitive or restricted scopes with non-sensitive ones avoids extra review). 6. Branding fields below. 7. Clients, Create Client, Web application, redirect URIs, download `client_secret.json`. 8. To go live: publish to production, "Prepare for Verification", "Submit for Verification" (DOCS, https://support.google.com/cloud/answer/13461325). Publish branding first (DOCS, https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).

**Branding fields** (DOCS, https://support.google.com/cloud/answer/15549049)

| Field | Rules |
|---|---|
| App name | Must distinctly represent your business; shown on the consent screen only after verification |
| User support email | A Google Group managed by you, or your own Google account email |
| Logo | JPG, PNG or BMP, 1MB max, 120x120 recommended; hidden for External production apps until verified; changing it requires re-verification |
| Home page | On a verified domain you own; not only a login page; must link to the privacy policy |
| Privacy policy | Same domain as the home page; linked from home page and consent screen, and the links must match |
| Terms of service | In App Domain section; required for external production apps (paraphrase) |
| Authorized domains | Every domain used in the project must be pre-registered (DOCS, https://support.google.com/cloud/answer/10311615); add them before redirect URIs |
| Developer contact | Google sends project notifications here |

Domain ownership must be proven through Google Search Console (DOCS, https://support.google.com/cloud/answer/13464321). Once configured, the consent screen cannot be removed (paraphrase).

**Client types** (DOCS, 15549257): Web (authorized JavaScript origins and redirect URIs); Native (Android, iOS, Chrome extension, desktop, TV). A checkbox "Use this client for an AI-powered agent" cannot be changed after creation ("You can't change this setting after you create the client", Gmail Python quickstart) and does not grant extra scopes (paraphrase).

**Redirect URI rules** (DOCS, https://developers.google.com/identity/protocols/oauth2/web-server and 15549257): "Redirect URIs must use the HTTPS scheme, not plain HTTP" (localhost exempt); "Hosts cannot be raw IP addresses" (localhost exempt); no userinfo, path traversal, fragments or non-printable characters; no wildcards (`*` prohibited). No maximum count stated. Changes take time: "It may take 5 minutes to a few hours".

**Client secrets** (DOCS, 15549257): at most two per client; shown in full only at creation. Clients inactive for six months are auto-deleted (restorable for 30 days); the policy dates to Oct 27, 2025 (DOCS, https://developers.google.com/identity/protocols/oauth2/policies).

## 2. What works immediately vs what is gated

- **Testing status (External):** DOCS: "limited to up to 100 test users"; "Authorizations by a test user will expire seven days from the time of consent." This includes refresh tokens. Exception: apps requesting only `openid`, `userinfo.email` and `userinfo.profile` get no test-user list, warning or 7-day expiry (DOCS, https://support.google.com/cloud/answer/15549945). Test users still see a tester warning screen. Verification is not required in dev, test or staging (paraphrase).
- **In production but unverified (sensitive or restricted scopes):** capped at 100 new users, for the life of the project: "the user cap applies over the entire lifetime of the project, and it cannot be reset or changed" (DOCS, https://support.google.com/cloud/answer/13463817); "100 new users in total, after the app presents the unverified app screen" (DOCS, https://support.google.com/cloud/answer/7454865). Users see the "unverified app" screen (when scopes in code differ from the consent screen, or verification is requested but unfinished). The cap does not apply if the app requests only already-approved scopes.
- **Gmail scope classes** (DOCS, https://developers.google.com/workspace/gmail/api/auth/scopes):

| Class | Scopes |
|---|---|
| Non-sensitive | `gmail.addons.current.action.compose`, `gmail.addons.current.message.action`, `gmail.labels` |
| Sensitive | `gmail.addons.current.message.metadata`, `gmail.addons.current.message.readonly`, `gmail.send` |
| Restricted | `https://mail.google.com/`, `gmail.readonly`, `gmail.compose`, `gmail.insert`, `gmail.modify`, `gmail.metadata`, `gmail.settings.basic`, `gmail.settings.sharing` |

`gmail.metadata` and `gmail.compose` are restricted, not sensitive; some blogs say otherwise.
- **Exceptions that skip verification** (DOCS, https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification): personal use (you or only a few users), internal use (your Workspace or Cloud Identity org), domain-wide installation (no brand verification, but sensitive or restricted scopes still need app verification), dev/test/staging. Internal apps "don't list scopes on the consent screen, and their restricted or sensitive scopes don't need Google review" (paraphrase).
- **Rate limits for unverified apps:** no official quota difference found. UNCERTAIN. The verification form itself rate-limits: "too many verification requests... wait 24 hours" (paraphrase; COMMUNITY, https://discuss.google.dev/t/oauth-verification-stuck-in-too-many-requests-loop-verification-centre-wipes-scope-fields-pii-removed-by-staff/390554, about Aug 2026, no staff reply).

## 3. Approval / review path

**Trigger:** sensitive or restricted scopes need verification (DOCS, https://support.google.com/cloud/answer/13463073). Brand verification is needed to show the app name and logo for External published apps (DOCS, https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification).

**Submitted**
- Brand: homepage on a verified domain, privacy policy (identical on homepage and consent screen), Search Console domain verification, branding that follows Google guidelines, current project contacts.
- Sensitive and restricted (DOCS, https://support.google.com/cloud/answer/15549135 and 13464321): scope justification ("Explain how you'll use the data, and why narrower scopes won't work", paraphrase); a YouTube demo video (unlisted OK) showing the OAuth grant flow, the consent screen with exact scopes in English, the features using each scope, the same app name and branding, and the client ID in the address bar; an appropriate use case; "You must only request the narrowest scope(s) your app needs to function."; compliance with the Google API Services User Data Policy and Limited Use rules.

**Policy content that matters** (DOCS, https://developers.google.com/workspace/gmail/api/policy and https://developers.google.com/workspace/workspace-api-user-data-developer-policy, "Last updated 2026-09-03"): use limited to "providing or improving your appropriate use case"; human reading of data prohibited with narrow exceptions; using data to "create, train, or improve a machine learning or artificial intelligence model" is barred beyond a single user's personalized model (paraphrase); approved Gmail use cases include email clients, backup, CRM, mail merge, tracking reports. The 2026-09-03 page says agentic tool invocations should be granularly confirmed and lists "Protecting against prompt injection techniques" (paraphrase of tool output). COMMUNITY: https://www.agenticfabriq.com/blog/google-oauth-verification-casa (2026-09-21) calls this new; when it was added is unconfirmed. For an AI-agent product, ask whether reviewers test this.

**Reviewer:** Google's OAuth review team emails owners and editors; for restricted scopes, Trust and Safety tells you when to start the assessment (DOCS, https://support.google.com/cloud/answer/13465431).

**Security assessment (CASA)**
- Required for restricted-scope apps that access data "from or through a third-party server" (DOCS, restricted-scope page). Based on the App Defense Alliance (ADA) CASA framework and OWASP ASVS.
- DOCS (13465431): apps are assigned **AL1 or AL2** from user count, scopes and other signals; the level can rise. Older "Tier 1/2/3" wording persists in third-party content; DeepStrike (https://deepstrike.io/blog/google-casa-security-assessment-2025, updated 2026-09-02) maps Tier 2 to AL1 and Tier 3 to AL2.
- DOCS (https://appdefensealliance.dev/casa/tier-2/tier2-overview, updated 2024-11-07): "The CASA self scanning process is deprecated."
- Output: Letter of Validation (13465431; Google's developer page calls it a Letter of Assessment).
- Authorized labs (DOCS, https://www.appdefensealliance.org/certification/authorized-labs; names inferred from link URLs): Bishop Fox, DEKRA, Eydle, Leviathan, NCC Group, NetSentries, NowSecure, Prescient Security, TAC Security, Valuementor. Not all offer CASA.

**Cost:** Google charges nothing for verification. No official figure for the assessment exists on any Google or ADA page. COMMUNITY: DeepStrike roughly $500 to $4,500 (TAC Security Tier 2 plans $540 to $1,800, Tier 3 $4,500); Orbis (https://meetorbis.com/blog/how-we-passed-google-casa-tier-2-with-claude, 2026-02-10, first-hand) $540 with TAC including a DAST scan and revalidation; Unipile marketing (https://www.unipile.com/integrating-google-oauth-2-0-user-authentication-into-your-app/, undated) $540 to $1,000 self-serve and a "legacy" $15,000 to $75,000 (unattributed, unverified).

**Official wait** (DOCS): brand verification a few minutes automated, 2 to 3 business days if manual; sensitive scopes "typically takes 3-5 business days" (sensitive-scope page) vs about 10 business days (FAQ 13463817); restricted scopes about 6 weeks plus the assessment (FAQ), "can potentially take several weeks to complete" (restricted-scope page). Estimates, not guarantees.

**Community-reported wait:** CellCog (https://cellcog.ai/blog/casa-security-assessment/, 2026-09-16, first-hand): CASA notice Aug 11, evidence Aug 14, Google approval Sep 13 (about 33 days from notice). Orbis: about 2 days of lab work. GMass (https://www.gmass.co/blog/live-updates-google-oauth-verification-security/, 2020, STALE): about 8 months. Vendor estimates 4 to 12+ weeks. Forum reports of a stuck verification loop (Aug 2026, one post).

**Rejection reasons:** Google lists none. On rejection, scope access "will no longer work" and "All required materials need to be resubmitted" (paraphrase). COMMUNITY (search excerpts, not fetched): vague justification, demo-video gaps, over-broad scopes, missing or broken privacy policy, mismatched authorized domains.

**Re-review:** reassessment "at least every 12 months after your assessor's Letter of Assessment (LOA) approval date" (paraphrase); annual re-verification for restricted-data apps (13463073); adding a new restricted scope may force reassessment.

**Local-only storage exemption:** not on any official list. The trigger wording "from or through a third-party server" suggests device-only apps might be outside CASA, but there is no official confirmation. COMMUNITY: https://discuss.google.dev/t/does-a-client-only-android-app-with-no-server-need-the-casa-security-assessment-for-drive-readonly/393638 (2026-08-31) asks exactly this, with no answers. UNCERTAIN. Do not tell developers it is exempt.

## 4. Gotchas

- **Refresh tokens:** DOCS: "There is currently a limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID." New ones past the limit silently invalidate the oldest (service accounts exempt). Other expiry causes: unused six months, password change for tokens with Gmail scopes, user revocation, admin restriction (`admin_policy_enforced`), Cloud session control (`invalid_grant`, `invalid_rapt`) (https://developers.google.com/identity/protocols/oauth2). Testing-status apps get 7-day tokens. `access_type=offline` returns a refresh token only on first authorization; repeat consent needs `prompt=consent` (web-server page). For Composio-style multi-tenant platforms: the 100-token limit is per account per client, and 7-day expiry hits every Testing-mode connection.
- **Scopes:** do not add a new sensitive or restricted scope to authorization requests until verified (DOCS, 15549135); requesting an unregistered scope also triggers the warning. Nylas guide (COMMUNITY, https://developer.nylas.com/docs/provider-guides/google/google-verification-security-assessment-guide/, updated 2026-10-07): `gmail.send` and `gmail.labels` avoid CASA, matching Google's classification.
- **Brand verification results** are valid for 7 days (DOCS): publish within that window or re-verify.
- **Workspace admin controls:** admins can set apps to Trusted, Limited, Specific Google data or Blocked under Security, Access and data control, API controls (DOCS, https://knowledge.workspace.google.com/admin/apps/control-which-apps-access-google-workspace-data). Unverified apps can be blocked. A verified app can still fail in a customer's Workspace until the admin trusts it.
- **Form bugs** (COMMUNITY, discuss.google.dev, May to Aug 2026, no staff answers): Data Access submissions can wipe scope justification and demo video fields; "too many requests" lockouts. Screenshot submissions.
- **Policy changes** (DOCS, policies page): Aug 5, 2026 security-signals handling; Dec 15, 2025 continuous improvements; Oct 27, 2025 unused client deletion; Workspace API user data policy updated 2026-09-03.
- Verified status can be lost if code requests scopes outside the approved set (13463817). Failure to act on notifications "could result in the loss of access to Google APIs" (paraphrase). Approval is per Cloud project and client, not per developer (CellCog notes other connectors on a partner's app are outside its assessment).

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Classify scopes, choose minimum set | Yes | Approve | Public docs |
| Write scope justification text | Yes (draft) | Review and attest | Must be honest and specific |
| Draft privacy policy, terms, homepage copy | Yes (draft) | Approve and publish on own domain | Must match real data handling and Limited Use |
| Create Google account or Cloud project | No | Yes | Account creation, sign-in |
| Accept the User Data Policy checkbox | No | Yes | Legal agreement |
| Fill Branding, Audience, Data Access | Template ready | Yes | Signed-in session |
| Search Console domain verification | Instructions | Yes | DNS or tag access |
| Create OAuth client, store secret | Prepare values | Yes | Secret shown once |
| Record demo video | Script and shot list | Yes | Real app, real consent screen, client ID visible |
| Submit for verification | No | Yes | Submission and attestations |
| Answer reviewer emails | Draft | Send from owner or editor account | Email goes to owner |
| CASA lab choice, quote, payment | Compare quotes | Yes | Payment, contract |
| CASA scan and remediation | Triage findings, fix code | Lab portal submissions | Evidence goes through the lab |
| Wait | No | Yes | Calendar time |
| Annual re-verification | Reminders, evidence refresh | Yes | Google emails owners and editors |

## 6. Difficulty tier and estimate

**Tier: review-required** (heavier than usual for restricted Gmail scopes). Estimates at the top. Active-effort numbers are ours.

## 7. Sources

All accessed 2026-10-19.

| URL | Supports | Label |
|---|---|---|
| console.cloud.google.com/auth/overview (redirect) | Sign-in required | TESTED |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification | CASA trigger, exceptions, 12-month reassessment | DOCS |
| https://developers.google.com/workspace/gmail/api/auth/scopes | Scope classes | DOCS |
| https://support.google.com/cloud/answer/13463073 | Verification required | DOCS |
| https://support.google.com/cloud/answer/13461325 | Submission steps | DOCS |
| https://support.google.com/cloud/answer/13463817 | User cap, timelines | DOCS |
| https://support.google.com/cloud/answer/13464321 | Brand and scope requirements | DOCS |
| https://support.google.com/cloud/answer/13465431 | AL1 and AL2, LOV | DOCS |
| https://support.google.com/cloud/answer/15549945 | Audience, 100 test users, 7 days | DOCS |
| https://support.google.com/cloud/answer/15549135 | Data Access, justification, video | DOCS |
| https://support.google.com/cloud/answer/15549049 | Branding fields | DOCS |
| https://support.google.com/cloud/answer/15549257 | Clients, secrets | DOCS |
| https://support.google.com/cloud/answer/10311615 | Authorized domains | DOCS |
| https://support.google.com/cloud/answer/7454865 | Unverified screen, 100 new users | DOCS |
| https://developers.google.com/identity/protocols/oauth2 | Refresh token rules | DOCS |
| https://developers.google.com/identity/protocols/oauth2/web-server | Redirect rules | DOCS |
| https://developers.google.com/identity/protocols/oauth2/policies | Policy change dates | DOCS |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | Brand verification | DOCS |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification | 3 to 5 days | DOCS |
| https://developers.google.com/workspace/gmail/api/policy | Limited Use, AI/ML ban | DOCS |
| https://developers.google.com/workspace/workspace-api-user-data-developer-policy | Agent language, 2026-09-03 | DOCS |
| https://developers.google.com/workspace/guides/configure-oauth-consent | Console URLs, setup | DOCS |
| https://developers.google.com/workspace/gmail/api/quickstart/python | Prerequisites, AI-agent checkbox | DOCS |
| https://knowledge.workspace.google.com/admin/apps/control-which-apps-access-google-workspace-data | Admin controls | DOCS |
| https://appdefensealliance.dev/casa ; .../casa/tier-2/tier2-overview ; https://www.appdefensealliance.org/certification/authorized-labs | CASA | DOCS (ADA) |
| cellcog, meetorbis, deepstrike, agenticfabriq, nylas, unipile, gmass, discuss.google.dev threads (URLs above) | Waits, costs, bugs | COMMUNITY |

## 8. Open questions

- Sensitive-scope timing: 3 to 5 business days (developer page) vs about 10 (FAQ). Plan 1 to 3 weeks.
- Restricted timing: Google about 6 weeks; vendors 4 to 12+ weeks; CellCog about 33 days from CASA notice but after earlier rounds.
- CASA cost: no official figure; community $540 to $4,500; a $15k to $75k vendor claim unverified. Get quotes.
- CASA self-scan: ADA says deprecated; blogs still describe a self-serve $540 route. Verify with the lab.
- Tier vs AL naming and what AL1 means: unresolved.
- Blogs misclassify `gmail.readonly` and `gmail.modify` as sensitive. Google's page says restricted.
- `gmail.labels`: Google's page says non-sensitive; the console label was not checked.
- Local-only exemption: unconfirmed (section 3).
- The lifetime 100-user cap vs a stale GMass anecdote of 200: do not rely on it.
- Billing for project creation: UNCERTAIN. Old "OAuth consent screen" menu: UNCERTAIN.
- Whether reviewers enforce the new prompt-injection and agent-confirmation language for Gmail restricted scopes: unknown.
- Our assumption "restricted Gmail scopes need a yearly third-party assessment" is confirmed (12-month reassessment, DOCS), with the caveat that the trigger is "from or through a third-party server".
