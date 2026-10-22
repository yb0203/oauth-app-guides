# Quote checks (live, 2026-10-21)

Each row is a run of `capture.py quote URL "quote"` against the live page. Merged from the four per-app logs written by the guide authors. Main session re-checked two random quotes per guide (plus Gmail hidden-section, Xero pricing rerun after a transient 403).

---

## google-gmail

# Quote checks: google-gmail (2026-10-21)

Run with `experiments/oauth-capture-poc/.venv/bin/python capture.py quote URL "quote"`. All quotes below were re-checked live on 2026-10-21. Quotes Q1 to Q37 were first checked in batch 1 or 2; Q38 to Q52 were added in later batches. Exit code 0 means found. Earlier exploratory variants that FAILED before the wording was fixed are listed at the end.

| ID | App | URL | Quote | Result |
|---|---|---|---|---|
| Q1 | google-gmail | https://support.google.com/cloud/answer/15549945 | Projects configured with a publishing status of Testing are limited to up to 100 test users listed in the OAuth consent screen | found hidden_section |
| Q2 | google-gmail | https://support.google.com/cloud/answer/15549945 | Authorizations by a test user will expire seven days from the time of consent | found hidden_section |
| Q3 | google-gmail | https://support.google.com/cloud/answer/15549945 | 100 new users in total, after the app presents the unverified app screen | found visible |
| Q4 | google-gmail | https://support.google.com/cloud/answer/15549945 | The user cap applies over the entire lifetime of the project, and it cannot be reset or changed | found visible |
| Q5 | google-gmail | https://support.google.com/cloud/answer/13463817 | Failure to get your app verified for sensitive and/or restricted scopes might result in exhaustion of your project's 100-user cap and cause Google sign-in to be disabled. | found hidden_section |
| Q6 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | Under Audience, select the user type for your app. | found visible |
| Q7 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | use of restricted or sensitive scopes doesn't require further review by Google | found visible |
| Q8 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | Some scopes require additional reviews by Google. | found visible |
| Q9 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | Enter your email address and any other authorized test users, then click Save. | found visible |
| Q10 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | you can't remove the OAuth 2.0 consent screen after you've configured it | found visible |
| Q11 | google-gmail | https://developers.google.com/workspace/guides/create-credentials | Click Application type > Web application. | found visible |
| Q12 | google-gmail | https://developers.google.com/workspace/guides/create-credentials | Under Authorized redirect URIs, click Add URI. | found visible |
| Q13 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | https://www.googleapis.com/auth/gmail.send Send email on your behalf. Restricted scopes Scope code Description https://mail.google.com/ | found visible |
| Q14 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | https://www.googleapis.com/auth/gmail.readonly View your email messages and settings. | found visible |
| Q15 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | Sensitive: These scopes provide access to specific Google user data that users authorize for your app. They require additional OAuth App Verification. | found visible |
| Q16 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | Restricted: These scopes provide wide access to Google user data and require restricted scope OAuth App Verification. | found visible |
| Q17 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | If you store restricted scope data on servers (or transmit), then you must go through a security assessment. | found visible |
| Q18 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification | the sensitive scope verification process typically takes 3-5 business days to complete | found visible |
| Q19 | google-gmail | https://support.google.com/cloud/answer/13463817 | to protect user data per the Google API policy and the Additional Requirements for Specific API Scopes. 10 Business days | found hidden_section |
| Q20 | google-gmail | https://support.google.com/cloud/answer/13463817 | An additional Security assessment is required to demonstrate a minimum level of capability in handling data securely and deleting user data upon user request. 6 weeks | found hidden_section |
| Q21 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification | the restricted scopes verification process can potentially take several weeks to complete | found visible |
| Q22 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification | complete a security assessment at least every 12 months after your assessor's Letter of Assessment (LOA) approval date | found visible |
| Q23 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification | has the ability to access data from or through a third-party server must go through a security assessment from Google-empanelled security assessors | found visible |
| Q24 | google-gmail | https://support.google.com/cloud/answer/13465431 | Applications are assigned to either the AL1 or AL2 assurance level. | found visible |
| Q25 | google-gmail | https://support.google.com/cloud/answer/13465431 | the Google Trust and Safety team will contact you when it is time to initiate the security assessment process. | found visible |
| Q26 | google-gmail | https://support.google.com/cloud/answer/13465431 | the application will be awarded a "Letter of Validation" (LOV) from the security assessor | found visible |
| Q27 | google-gmail | https://developers.google.com/identity/protocols/oauth2 | There is currently a limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID. | found visible |
| Q28 | google-gmail | https://developers.google.com/identity/protocols/oauth2/web-server | Redirect URIs must use the HTTPS scheme, not plain HTTP | found visible |
| Q29 | google-gmail | https://support.google.com/cloud/answer/15549135 | When requesting sensitive or restricted scopes, you must provide justification for the request. Additionally, you must include a link to a demo video that demonstrates how these scopes will be used. | found visible |
| Q30 | google-gmail | https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md | set its authorized redirect URI to Composio's callback, then pass the client ID and secret | found visible |
| Q31 | google-gmail | https://knowledge.workspace.google.com/admin/apps/control-which-apps-access-google-workspace-data | Apps configured with an access setting (Trusted, Limited, Specific Google data, or Blocked). | found visible |
| Q32 | google-gmail | https://developers.google.com/workspace/workspace-api-user-data-developer-policy | create, train, or improve a machine learning or artificial intelligence model beyond that specific user's personalized model for the appropriate use case or user-facing feature | found visible |
| Q33 | google-gmail | https://developers.google.com/workspace/workspace-api-user-data-developer-policy | granularly require users to confirm the MCP, tool, skill, or other agentic behavior invocation | found visible |
| Q34 | google-gmail | https://developers.google.com/workspace/workspace-api-user-data-developer-policy | Protecting against prompt injection techniques by either using Google Cloud Platform's Model Armor or other prompt injection protection. | found visible |
| Q35 | google-gmail | https://cellcog.ai/blog/casa-security-assessment/ | CASA Tier 2 (Assurance Level 1), required by Google's notice of August 11, 2026 | found visible |
| Q36 | google-gmail | https://cellcog.ai/blog/casa-security-assessment/ | Google approved CellCog's OAuth app verification on September 13, 2026 | found visible |
| Q37 | google-gmail | https://meetorbis.com/blog/how-we-passed-google-casa-tier-2-with-claude | Why We Chose TAC Security ($540) | found visible |
| Q38 | google-gmail | https://developers.google.com/workspace/gmail/api/quickstart/python | Before using Google APIs, you need to turn them on in a Google Cloud project. | found visible |
| Q39 | google-gmail | https://developers.google.com/workspace/guides/configure-oauth-consent | select I agree to the Google API Services: User Data Policy | found visible |
| Q40 | google-gmail | https://support.google.com/cloud/answer/13461325 | Once your app is published to production, click “Prepare for Verification” to proceed to submit your app for verification. | found visible |
| Q41 | google-gmail | https://support.google.com/cloud/answer/13461325 | In the final step, click on “Submit for Verification” to begin the app review process. | found visible |
| Q42 | google-gmail | https://developers.google.com/workspace/gmail/api/quickstart/python | You can't change this setting after you create the client. | found visible |
| Q43 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | The Authorized domains section of the OAuth consent screen editor needs to contain the top private domains that are used in the URIs of the App domain section. | found visible |
| Q44 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | The Authorized domains section also needs to include the redirect URIs or JavaScript origins authorized in your "Web application" OAuth client types. | found visible |
| Q45 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | Verify the ownership of your authorized domains using the Google Search Console. | found visible |
| Q46 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | Your home page must be publicly accessible, and not just accessible to your site's logged-in users. | found visible |
| Q47 | google-gmail | https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | The privacy policy must disclose the manner in which your application accesses, uses, stores, or shares Google user data. | found visible |
| Q48 | google-gmail | https://support.google.com/cloud/answer/13461325 | Apps in development, testing or staging are not applicable for verification. | found visible |
| Q49 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | https://www.googleapis.com/auth/gmail.compose Manage drafts and send emails. | found visible |
| Q50 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | https://www.googleapis.com/auth/gmail.metadata View your email message metadata such as labels and headers, but not the email body. | found visible |
| Q51 | google-gmail | https://developers.google.com/workspace/gmail/api/auth/scopes | https://www.googleapis.com/auth/gmail.labels See and edit your email labels. | found visible |
| Q52 | google-gmail | https://support.google.com/cloud/answer/13463817 | If the app has been rejected for sensitive or restricted scopes, users’ access to the unapproved sensitive or restricted scopes in the app via OAuth will no longer work. | found hidden_section |

## Failed attempts (before rewording)

| App | URL | Quote tried | Result | Action |
|---|---|---|---|---|
| google-gmail | https://support.google.com/cloud/answer/13463817 | about 10 business days | FAILED (not in the page text as worded) | Reworded to the table text 'to protect user data per the Google API policy and the Additional Requirements for Specific API Scopes. 10 Business days' (Q19, found hidden_section) |
| google-gmail | https://support.google.com/cloud/answer/15549135 | You must only request the narrowest scope(s) your app needs to function. | FAILED | Not found on this page; dropped. Replaced with the justification and demo video sentence (Q29, found visible). No guide claim relies on the narrowest-scope sentence. |

## Downgraded to UNCERTAIN

- Redirect URI mismatch error wording and propagation delay (blocker): not checked.

## Notes

- Q37 (Orbis) only matches a page heading, so it supports the $540 figure thinly; labelled COMMUNITY with that caveat.
- Q35 is a first-hand vendor report (COMMUNITY), not a Google statement. Checks not used as evidence objects in the JSON (still passed): Q10, Q13, Q14, Q26, Q28, Q36, Q43, Q48, Q50, Q51 (Q34 and Q50 appear only inside notes).
- Several tried-but-unused checks (e.g. 'Sensitive scopes', 'AL1' alone, '6 weeks' alone) passed but were too generic to use as evidence and are not in the guide.

---

## xero

# Quote checks: Xero (2026-10-21)

Method: `experiments/oauth-capture-poc/.venv/bin/python capture.py quote URL "quote"` run live per quote (visible text first, then hidden text). 52 quotes checked; 52 found, 0 failed, 0 downgraded. All matches were in visible text.

Note: a first parallel batch returned HTTP 403 for 14 quotes (Xero rate-limits parallel headless requests); those 403s are not quote failures. They were re-run one at a time and all were found.

Quotes marked 'not used' were checked but are not in the final guide JSON. Source type COMMUNITY: q49 (Codat vendor docs).

| App | ID | URL | Quote | Result | Used in guide |
|---|---|---|---|---|---|
| Xero | q01 | https://developer.xero.com/documentation/getting-started-guide/ | Signup for a free Xero account | found visible | yes |
| Xero | q02 | https://developer.xero.com/documentation/getting-started-guide/ | Add your OAuth 2.0 application (you’ll be prompted to login to Xero first) | found visible | not used |
| Xero | q03 | https://developer.xero.com/documentation/development-accounts | data will be automatically reset 28 days after creation | found visible | yes |
| Xero | q04 | https://developer.xero.com/documentation/guides/oauth2/limits/ | New apps default to the starter tier with 5 connections. | found visible | yes |
| Xero | q05 | https://developer.xero.com/documentation/guides/oauth2/limits/ | Moving up to Core will give you up to 50 connections. | found visible | yes |
| Xero | q06 | https://developer.xero.com/documentation/guides/oauth2/limits/ | each organisation or practice is limited to connecting a maximum of five uncertified apps | found visible | yes |
| Xero | q07 | https://developer.xero.com/faq | So an org can have 2 uncertified apps plus as many custom connection apps as needed. | found visible | yes |
| Xero | q08 | https://developer.xero.com/documentation/best-practices/managing-connections/connections/ | Xero organisations are restricted to no more than 5 connections to uncertified apps. | found visible | yes |
| Xero | q09 | https://developer.xero.com/documentation/best-practices/managing-connections/connections/ | only one of those connections will count towards your connection limit | found visible | yes |
| Xero | q10 | https://developer.xero.com/pricing | Your card details will be required when moving from the Starter to the Core plan. | found visible | yes |
| Xero | q11 | https://developer.xero.com/faq | In order to add a 6th connection, you will need to first add your payment details. | found visible | yes |
| Xero | q12 | https://developer.xero.com/pricing | Monthly Tier Fee No charge $35 AUD $245 AUD $1445 AUD Price on Application | found visible | yes |
| Xero | q13 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | This must be an https address, however for testing you can use http://localhost/ | found visible | yes |
| Xero | q14 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | Please note that http://127.0.0.1 cannot be used | found visible | not used |
| Xero | q15 | https://developer.xero.com/faq | You can use up to 50 redirect URIs for your app. | found visible | yes |
| Xero | q16 | https://developer.xero.com/faq | The use of wildcards in redirect URI is not supported. | found visible | yes |
| Xero | q17 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | create an OAuth2 app and make sure you select the “Auth Code” grant type | found visible | yes |
| Xero | q18 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | Your app is assigned a unique Client ID and you can then generate a Client Secret | found visible | yes |
| Xero | q19 | https://developer.xero.com/documentation/guides/oauth2/auth-flow/ | a refresh token if you’ve requested the offline_access scope | found visible | not used |
| Xero | q20 | https://developer.xero.com/faq | Unused refresh tokens expire after 60 days. | found visible | yes |
| Xero | q21 | https://developer.xero.com/faq | you can retry refreshing your existing refresh token for a grace period of 30 minutes | found visible | yes |
| Xero | q22 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | Using the offline_access scope is a requirement for certification. | found visible | not used |
| Xero | q23 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | Unexplained or ambiguous use of scopes will not be allowed. | found visible | not used |
| Xero | q24 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | you’ve built Sign Up with Xero and have ten active customer connections | found visible | yes |
| Xero | q25 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | Once you’re on the Core Plan, you can then upgrade to the Plus Plan and get certified as part of the upgrade. | found visible | yes |
| Xero | q26 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | your connection numbers will be capped at 999 | found visible | yes |
| Xero | q27 | https://developer.xero.com/faq/xero-ecosystem-security-requirements-update | Typically the assessment takes around 5 working days to complete, followed by 5-10 working days for us to assess your answers. | found visible | yes |
| Xero | q28 | https://developer.xero.com/faq/xero-ecosystem-security-requirements-update | The security assessment will need to be undertaken annually. | found visible | not used |
| Xero | q29 | https://developer.xero.com/xero-developer-platform-terms-conditions | Aggregate and supply user data (or any other API Data accessed through the developer platform) to another app or any third party. | found visible | yes |
| Xero | q30 | https://developer.xero.com/xero-developer-platform-terms-conditions | You are responsible for making sure your app’s use cases have been approved by us | found visible | yes |
| Xero | q31 | https://developer.xero.com/xero-developer-platform-terms-conditions | You must not use API Data sourced from the Xero developer platform to train or fine tune any artificial intelligence models | found visible | yes |
| Xero | q32 | https://developer.xero.com/changelog | Apps created on or after 2 March 2026 already use granular scopes. Existing apps have until 13 September 2027 to migrate. | found visible | yes |
| Xero | q33 | https://developer.xero.com/faq | Real customer organisations need the Core plan or above. | found visible | not used |
| Xero | q34 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | cannot include the word Xero | found visible | yes |
| Xero | q35 | https://developer.xero.com/documentation/guides/oauth2/custom-connections/ | Custom Connection apps do not count toward the five uncertified app limit | found visible | yes |
| Xero | q36 | https://developer.xero.com/faq | Your connections are capped at the tier maximums until you meet that tier's requirements. | found visible | yes |
| Xero | q37 | https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md | set its authorized redirect URI to Composio's callback, then pass the client ID and secret | found visible | yes |
| Xero | q38 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | Once certified you'll be upgraded to the Plus Tier. | found visible | not used |
| Xero | q39 | https://developer.xero.com/documentation/guides/oauth2/custom-connections/ | Log in to My Apps and click “New App”. | found visible | not used |
| Xero | q40 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | Select your app, then click ‘Manage Plan’ | found visible | not used |
| Xero | q41 | https://developer.xero.com/documentation/guides/oauth2/limits/ | 1,000 calls per day for starter, 5,000 calls per day for higher tiers | found visible | yes |
| Xero | q42 | https://developer.xero.com/documentation/guides/oauth2/scopes/ | Each subsequent time your app sends a user through the flow, any new scopes will be added to previously consented scopes. | found visible | not used |
| Xero | q43 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/building-and-growing-your-app | you’ll need prior approval from us and additional permissions before you can apply | found visible | yes |
| Xero | q44 | https://developer.xero.com/pricing | Connections (maximum) 5 50 1000 10,000 No Limit | found visible | yes |
| Xero | q45 | https://developer.xero.com/documentation/getting-started-guide/ | Enable the Xero demo company | found visible | yes |
| Xero | q46 | https://developer.xero.com/faq/xero-ecosystem-security-requirements-update | which will be reviewed by Xero’s security team | found visible | yes |
| Xero | q47 | https://developer.xero.com/documentation/guides/oauth2/custom-connections/ | require an additional monthly subscription | found visible | yes |
| Xero | q48 | https://developer.xero.com/xero-developer-platform-terms-conditions | Your apps must include your own legally binding terms of use and privacy policy | found visible | yes |
| Xero | q49 | https://docs.codat.io/integrations/accounting/xero/xero-app-partner-program/ | It can take several months to become a Xero App Partner | found visible | yes |
| Xero | q50 | https://developer.xero.com/documentation/guides/oauth2/scopes/ | To get a refresh token, you must request the offline_access scope. | found visible | yes |
| Xero | q51 | https://developer.xero.com/documentation/guides/oauth2/scopes/ | Web and PKCE apps – Since March 2026, all new and existing Web and PKCE apps have been assigned granular scopes. | found visible | not used |
| Xero | q52 | https://developer.xero.com/documentation/xero-app-store/app-partner-guides/certification-checkpoints | Apps created on or after 2 March 2026 will use the new granular scopes | found visible | not used |

---

## shopify

# Quote checks: Shopify guide (2026-10-21)

Tool: `experiments/oauth-capture-poc/.venv/bin/python capture.py quote URL "quote"` (checks visible text, then collapsed/hidden text). Each DOCS and COMMUNITY quote in `data/guides/shopify.json` was run live by the guide author on 2026-10-21; `found_in` in the JSON comes straight from these results. Several Shopify docs URLs redirect; the tool followed the redirect, and the guide's `sources` use the final URL.

Summary: 80 checks run, 78 found, 2 failed (both failures were quotes tried on the wrong page and were not used). No DOCS quote was downgraded to UNCERTAIN. COMMUNITY quotes are from community.shopify.dev threads (some by Shopify Staff); the pages show month and day but no year, research dates them 2026.

| id | URL | quote | result | note |
|---|---|---|---|---|
| a1 | https://shopify.dev/docs/apps/launch/distribution/select-distribution-method | Before you can share your app, select a distribution method | found visible | checked; not an evidence quote (may be referenced in a note) |
| a2 | https://shopify.dev/docs/apps/launch/distribution/select-distribution-method | A custom app can be installed on multiple stores when those stores belong to the same Plus organization | found visible | checked; not an evidence quote (may be referenced in a note) |
| a3 | https://shopify.dev/docs/apps/launch/distribution/select-distribution-method | find the Distribution card and click Select distribution method | found visible | checked; not an evidence quote (may be referenced in a note) |
| a4 | https://shopify.dev/docs/apps/launch/distribution | Building for many merchants: You'll use public distribution | found visible | checked; not an evidence quote (may be referenced in a note) |
| a5 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | Applying for protected customer data isn't possible while the app is under review | found visible | used in guide |
| a6 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | Apps that are distributed through the Shopify App Store must subscribe to compliance webhooks | found visible | checked; not an evidence quote (may be referenced in a note) |
| a7 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | If they don't redirect merchants to the OAuth grant screen, then your app won't be approved | FAILED | Wrong page (text is on pass-app-review); rechecked as a7b |
| a7b | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | If they don't redirect merchants to the OAuth grant screen, then your app won't be approved | found visible | used in guide |
| a8 | https://shopify.dev/docs/apps/launch/protected-customer-data | You don't need to submit a request for review for apps that are installed only on development stores | found visible | used in guide |
| a9 | https://shopify.dev/docs/apps/launch/protected-customer-data | you need to select a distribution method for your app | found visible | checked; not an evidence quote (may be referenced in a note) |
| a10 | https://community.shopify.dev/t/longer-app-store-review-times-what-you-need-to-know/31728 | review times are longer than usual right now | found visible | used in guide |
| a11 | https://community.shopify.dev/t/longer-app-store-review-times-what-you-need-to-know/31728 | doing so will move you to the back of the queue | found visible | used in guide |
| a12 | https://community.shopify.dev/t/does-shopifyqlquery-require-level-2-pcd-access-how-long-to-get-that-access/33439 | we are unable to provide any estimated timeframes | found visible | used in guide |
| a13 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | Merchants can modify requested scopes during authorization, so always verify before storing the token | found visible | checked; not an evidence quote (may be referenced in a note) |
| a14 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | Anchor the pattern at both ends | found visible | checked; not an evidence quote (may be referenced in a note) |
| a15 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | Partners may be temporarily suspended from submitting their app | found visible | checked; not an evidence quote (may be referenced in a note) |
| a16 | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | The app review team will only review production-ready apps | found visible | checked; not an evidence quote (may be referenced in a note) |
| a17 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | Creating an app for the app store? Build using Shopify CLI instead. | found visible | used in guide |
| a18 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | You're a user with app development permissions | found visible | used in guide |
| a19 | https://shopify.dev/docs/apps/launch/app-store-review/review-process | your app moves to the Paused status | found visible | checked; not an evidence quote (may be referenced in a note) |
| a20 | https://shopify.dev/docs/apps/launch/app-store-review/review-process | During the review process your app changes status: Draft, Submitted, Reviewed, and Published | found visible | used in guide |
| a21 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | compute an HMAC-SHA256 hash using your client secret | found visible | checked; not an evidence quote (may be referenced in a note) |
| a22 | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | Your app should re-install for merchants who've previously installed it | found visible | checked; not an evidence quote (may be referenced in a note) |
| a23 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | Must exactly match a redirect URI you've configured in the Dev Dashboard or your app's configuration TOML file | found visible | checked; not an evidence quote (may be referenced in a note) |
| a24 | https://shopify.dev/docs/apps/launch/distribution | Installed on a single Shopify store, on multiple stores that belong to the same Plus organization, or on development stores | found visible | used in guide |
| a25 | https://shopify.dev/docs/apps/launch/distribution | Can be installed on multiple Shopify stores | found visible | checked; not an evidence quote (may be referenced in a note) |
| b1 | https://shopify.dev/docs/apps/launch/protected-customer-data | you must meet all of the level 1 and 2 requirements | found visible | used in guide |
| b2 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Your app must not request the manual entry of a myshopify.com URL or a shop's domain during the installation or configuration flow | found hidden_section | used in guide |
| b3 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Apps must be installed and initiated only on Shopify services | found hidden_section | used in guide |
| b4 | https://shopify.dev/docs/apps/launch/distribution/select-distribution-method | The Distribution card appears only for apps that belong to a Partner organization | found visible | used in guide |
| b5 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens#offline-access-tokens) | 1 hour (expires_in is 3600) | found visible | used in guide |
| b6 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens#offline-access-tokens) | 90 days (refresh_token_expires_in is 7776000) when issued | found visible | used in guide |
| b7 | https://shopify.dev/docs/apps/build/privacy-law-compliance (redirected to https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance) | Every app that's distributed through the Shopify App Store must subscribe to the following compliance webhook topics | found visible | used in guide |
| b8 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | The app icon must be 1200 x 1200 pixels in size and in either JPEG or PNG format | found visible | used in guide |
| b10 | https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant?lang=node) | The access token from this grant is valid for 24 hours (expires_in is 86399) | FAILED | Wrong page (sentence is on the access-tokens page); dropped, not used |
| b11 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/offline-access-tokens (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens#offline-access-tokens) | Shopify keeps one current expiring offline token per app and store | found visible | used in guide |
| b12 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Your app must immediately authenticate using OAuth before any other steps occur | found hidden_section | checked; not an evidence quote (may be referenced in a note) |
| c1 | https://community.shopify.dev/t/unlisted-shopify-app-review-required-before-installation/33101 | I can confirm that this is expected and an app review is required | found visible | used in guide |
| c2 | https://community.shopify.dev/t/unlisted-shopify-app-review-required-before-installation/33101 | you are not able to workaround these limitations by creating a new Custom distribution app for each merchant | found visible | used in guide |
| c3 | https://community.shopify.dev/t/unlisted-shopify-app-review-required-before-installation/33101 | we are unable to provide any specific estimated timeframes for how long a review may take | found visible | used in guide |
| c4 | https://community.shopify.dev/t/shopify-app-review-taking-more-than-2-weeks-is-this-normal/29646 | the review process can take up to 2 weeks | found visible | used in guide |
| c5 | https://community.shopify.dev/t/how-many-days-does-it-take-to-approve-an-shopify-app/32984 | Right now it takes min of 4 weeks to get a response | found visible | used in guide |
| c6 | https://community.shopify.dev/t/shopify-app-review-still-assigning-a-reviewer-after-5-days-how-long-does-it-take/36879 | for us it has usually taken between 1 and 3 weeks | found visible | used in guide |
| c7 | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | When the app is installed, it doesn't immediately redirect to the OAuth grant screen | found visible | checked; not an evidence quote (may be referenced in a note) |
| d1 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | If your app isn't embedded in the Shopify admin, you can use the default https://shopify.dev/apps/default-app-home | found visible | checked; not an evidence quote (may be referenced in a note) |
| d2 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | After the merchant approves your app, Shopify redirects to your redirect_uri with an authorization code | found visible | used in guide |
| d3 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | Shopify prompts them to approve the added permissions | found visible | used in guide |
| d4 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | submit your app for review by the Shopify App Store Review team | found visible | used in guide |
| d5 | https://shopify.dev/docs/apps/launch/distribution/select-distribution-method | generate an install link and send it to the store owner | found visible | used in guide |
| d6 | https://shopify.dev/docs/api/usage/access-scopes | Shopify has to approve your app for the scope before you can declare it | found visible | used in guide |
| d7 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | Access to protected customer data or other sensitive information requires approval | found visible | checked; not an evidence quote (may be referenced in a note) |
| d8 | https://shopify.dev/docs/api/usage/access-scopes | For older orders, add read_all_orders, which you must request access to | found visible | used in guide |
| d9 | https://community.shopify.dev/t/longer-app-store-review-times-what-you-need-to-know/31728 | Double-checking your app listing, privacy policy, and test credentials are complete and accurate | found visible | checked; not an evidence quote (may be referenced in a note) |
| d10 | https://shopify.dev/docs/apps/launch/app-store-review/submit-app-for-review | Every app submission must specify a primary language and create at least one Shopify App Store listing | found visible | checked; not an evidence quote (may be referenced in a note) |
| d11 | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | Test that your app successfully obtains an access token | found visible | checked; not an evidence quote (may be referenced in a note) |
| e1 | https://shopify.dev/docs/apps/launch/app-store-review/review-process | You can withdraw from the review process at any time by clicking Withdraw in the status banner | found visible | used in guide |
| q1 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | Select Start from Dev Dashboard | found visible | used in guide |
| q2 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | Your app must have at least one version before it can be installed on a store | found visible | used in guide |
| q3 | https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard | Copy your Client ID and Client secret | found visible | used in guide |
| q4 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | Must exactly match a redirect URI you've configured in the Dev Dashboard | found visible | used in guide |
| q5 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | https://{shop}/admin/oauth/authorize?client_id={client_id} | found visible | used in guide |
| q6 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/authenticate-standalone-apps?lang=node) | New public apps must use expiring offline access tokens | found visible | used in guide |
| q7 | https://shopify.dev/docs/apps/build/cli-for-apps/app-configuration | You must include at least one redirect URL before making your app public | found visible | used in guide |
| q8 | https://shopify.dev/docs/apps/launch/distribution | You can't change the distribution method after you select it | found visible | used in guide |
| q9 | https://shopify.dev/docs/apps/launch/app-store-review/review-process | it goes through an app review process | found visible | checked; not an evidence quote (may be referenced in a note) |
| q10 | https://shopify.dev/docs/apps/launch/app-store-review/review-process | are the same for both fully visible and limited visibility public apps | found visible | used in guide |
| q11 | https://shopify.dev/docs/apps/launch/app-requirements-checklist (redirected to https://shopify.dev/docs/apps/launch/shopify-app-store/best-practices) | Your app should immediately authorize using OAuth before any other steps occur | found visible | used in guide |
| q12 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Include a screencast to demonstrate your app's onboarding and features | found hidden_section | used in guide |
| q13 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Include account credentials in your testing instructions | found hidden_section | used in guide |
| q14 | https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements | Apps that use off-platform billing cannot be distributed through the Shopify App store | found visible | used in guide |
| q15 | https://shopify.dev/docs/apps/build/privacy-law-compliance (redirected to https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance) | Complete the action within 30 days of receiving the request | found visible | used in guide |
| q16 | https://help.shopify.com/en/partners/partner-program/glossary | A one-time $19 USD fee to join the app revenue share program | found visible | used in guide |
| q17 | https://shopify.dev/changelog/expiring-offline-access-tokens-required-for-public-apps-april-1-2026 (redirected to https://shopify.dev/changelog/posts/expiring-offline-access-tokens-required-for-public-apps-april-1-2026) | all new public apps must request and use expiring offline access tokens | found visible | used in guide |
| q18 | https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/client-credentials-grant (redirected to https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant?lang=node) | when the app and the store belong to the same Shopify organization | found hidden_section | used in guide |
| q19 | https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md | set its authorized redirect URI to Composio's callback, then pass the client ID and secret | found visible | used in guide |
| q20 | https://shopify.dev/docs/apps/launch/protected-customer-data | Always available | found visible | checked; not an evidence quote (may be referenced in a note) |
| q21 | https://shopify.dev/docs/apps/launch/distribution | Approval required | found visible | checked; not an evidence quote (may be referenced in a note) |
| q22 | https://community.shopify.dev/t/does-shopifyqlquery-require-level-2-pcd-access-how-long-to-get-that-access/33439 | we are unable to provide any estimated timeframes | found visible | used in guide |
| q23 | https://community.shopify.dev/t/longer-app-store-review-times-what-you-need-to-know/31728 | longer than usual | found visible | used in guide |
| q24 | https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review | redirect | found visible | used in guide |

---

## spotify

# Quote checks: Spotify

Run 2026-10-21 with `experiments/oauth-capture-poc/.venv/bin/python capture.py quote URL "quote"` (checks visible text, then hidden text). Every quote below was found on the first try; none failed and none were downgraded. All matches were in visible text (`found_in: visible`).

| App | URL | Quote | Result | In guide |
|---|---|---|---|---|
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | You can create up to 25 apps per developer account | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | put a tick in the Developer Terms of Service checkbox | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | they will be displayed to the user on the grant screen | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | Client Secret, the key you will use to authorize your Web API or SDK calls | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | regenerate it immediately by clicking the ROTATE button on the app overview page | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/apps | In Redirect URIs enter one or more addresses that you want to allowlist with Spotify | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | The app owner must have a Spotify Premium account for apps in development mode to function | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Up to 5 authenticated Spotify users can use an app that is in development mode | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Each Spotify user who installs your app will need to be added to your app's allowlist before they can use it | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Newly-created apps begin in development mode | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Spotify only accepts applications from organizations (not individuals) | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Maintaining a minimum of active users (at least 250k MAUs) | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Application must be sent through a company email | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | This review process can take up to six weeks | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Tap on the Quota extension Request tab | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Tap on the Add new user button and enter the name and Spotify email address of the user | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Tell us about your app by filling out the provided questionnaire (4 steps) | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Spotify's app review team will take a look at your app and evaluate it for compliance with our Developer Policy | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | API requests with an access token associated to that user and app will receive a 403 status code error | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Apps in this category can be installed by an unlimited number of users | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | The specific groupings and limits are subject to change | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/redirect_uri | Use HTTPS for your redirect URI, unless you are using a loopback address, when HTTP is permitted | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/redirect_uri | localhost is not allowed as redirect URI | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/redirect_uri | must exactly match the redirect URI you provide when you create your app | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/redirect_uri | register your redirect URI with a loopback IP literal, but without any port number | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | Refreshing an access token does not reset or extend the refresh token's 6-month lifetime | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates | You can now create up to 25 Client IDs per developer account | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | up to five authorized users | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | a Spotify Premium account | found visible | no (checked, not used) |
| spotify | https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md | set its authorized redirect URI to Composio's callback, then pass the client ID and secret | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | Development Mode use will require a Spotify Premium account | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | Each Client ID will be limited to up to five authorized users | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | Developers will be limited to one Development Mode Client ID | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | should not be relied on as a foundation for building or scaling a business on Spotify | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | personal projects for non-commercial use by individual developers | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | the authorized user cap and one Client ID per developer limit will take effect as planned for existing Development Mode integrations | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | Refresh tokens issued to apps registered on Spotify for Developers will now require reauthentication after 6 months | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | Refresh tokens do not expose an issuance timestamp | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | If the user re-authorizes your app, a fresh 6-month lifetime begins | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | This only applies to tokens issued on behalf of a user (Authorization Code and Authorization Code with PKCE flows) | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates | Quota counting is now per developer account, not per Client ID | found visible | yes |
| spotify | https://developer.spotify.com/terms | delete the applicable Spotify Personal Data in your possession or control within five (5) days | found visible | yes |
| spotify | https://developer.spotify.com/terms | You must display a privacy policy to end users before they install or signup to your SDA | found visible | yes |
| spotify | https://developer.spotify.com/policy | Do not use the Spotify Platform or any Spotify Content to train a machine learning or AI model | found visible | yes |
| spotify | https://developer.spotify.com/terms | You must provide all users with a working and easily accessible mechanism to disconnect their Spotify Service account from your SDA at any time | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/scopes | user-read-private | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide | If the owner's Premium subscription lapses, the app will stop working | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide | If you already have multiple Client IDs or more than 5 users, you will retain them | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide | Apps in extended quota mode are not affected by any of the changes described in this guide | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | these same requirements will also apply to all existing Development Mode integrations | found visible | yes |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | the Web API returns a 429 Too Many Requests response | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | will return a 400 Bad Request response with an invalid_grant error | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | Your app must handle this case by discarding the token and sending the user through the authorization code flow | found visible | no (checked, not used) |
| spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Extended quota mode apps also have access to a higher rate limit than development mode apps do | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | API access will be limited to a smaller set of supported endpoints | found visible | yes |
| spotify | https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates | Client ID limit increased from 1 to 25 | found visible | yes |

Checked but not used (extra context for gotchas or discarded): see the `no` rows.

## Other checks

- Wall probe re-observed with the same tool on 2026-10-21 (`capture.py quote https://developer.spotify.com/dashboard "Continue with Google"`): one redirect to accounts.spotify.com/en/login; page text includes continue with Google, Facebook, Apple, phone number, and Sign up. In the guide the `state` and `flow_ctx` query values were dropped from the stored URL.
- Community thread https://community.spotify.com/t5/Spotify-for-Developers/Quota-Extension-Request-tab-not-visible-in-Developer-Dashboard/td-p/7401540 returned HTTP 403 ("This site has been temporarily disabled") to curl; not opened, so all community waits are marked UNCERTAIN.
- Scopes page https://developer.spotify.com/documentation/web-api/concepts/scopes: checked only that `user-read-private` appears (found visible); scope names used in `prepared.scopes` were also seen in that page's text via curl. Not an evidence object.
