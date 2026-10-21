# Meta: Facebook Login / Instagram API (Instagram Login and Facebook Login)

- Researched: 2026-10-19
- Tier: **review-required**. Serving other businesses needs Advanced Access, which needs App Review and Business Verification. Own accounts only (Standard Access) is effectively instant.
- Effort: about 8 to 16 active hours (our estimate): app and settings 1 to 2, policies and data-deletion endpoint 2 to 4, Business Verification paperwork 1 to 2, test accounts and calls 1 to 2, screencast and submission 3 to 6 per feature set, plus 2 to 4 per rejection cycle.
- Calendar time: about 1 to 6 weeks, up to 8 with one rejection. Official: "within about a week" (undated page). Community: 10 to 20+ days in 2026.
- Confidence: medium. All docs were read through a summarizer. Review times rest on vendor blog and forum anecdotes.

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. DOCS quotes passed through a fetch-tool summarizer; see `_verification.md`.

## Directly observed (TESTED, 2026-10-19)

`developers.facebook.com/apps/` redirected to `business.facebook.com/business/loginpage/?next=...developers.facebook.com/apps/`. Visible text: "Create apps with use cases that can connect your app with Facebook, Instagram, WhatsApp, Threads and more"; "Request access to permissions and features in app review"; "Complete all verification and data access requirements to keep your apps secure and trusted". Buttons: Continue with Facebook, Create new account, Log in with a Managed Meta Account. TESTED. Confirms use-case-based creation and that review and verification live in the same dashboard.

## 1. Where and how the app is created

**Console:** `https://developers.facebook.com/apps`. Creation wizard `developers.facebook.com/apps/creation/` (DOCS, https://developers.facebook.com/docs/development/create-an-app/, paraphrase).

**Prerequisites**
- A Meta developer account: logged into a Facebook account, verify a phone number and email by code, accept platform terms and developer policies, pick an occupation. No fees mentioned (DOCS, https://developers.facebook.com/docs/development/register, paraphrase).
- 2FA: not mentioned; UNCERTAIN.
- A person can hold a role on up to 15 apps not connected to a Meta Verified Business Account; archived apps count (DOCS, create-an-app, paraphrase).
- A business portfolio is optional at creation but needed to publish; the Instagram page says the business must complete Business Verification (paraphrase, summarizer; https://developers.facebook.com/documentation/instagram-platform/create-an-instagram-app.md).

**Generic wizard** (DOCS, paraphrase): name and contact email; choose use cases ("Use cases cannot be removed" after creation; you can skip them); connect or create a business portfolio, or skip; review requirements; Go to dashboard.

**Instagram-specific** (DOCS, create-an-instagram-app.md, paraphrase): Create App; connect a business; "Other" use case; Business app type (must be a business-type app to add Instagram; exact wording unverified); name and email; add the Instagram product, Set up, which adds "API setup with Instagram login" (use "API setup with Facebook login" instead if the professional account is linked to a Page); add Instagram accounts as testers (each must be public per the page, one summarized source, unsure); webhooks (Callback URL and Verify token); Business login (Redirect URL, Embed URL, extra OAuth Redirect URIs, Deauthorize callback URL, Data deletion request URL); complete App Review.

**Facebook Login for Business** (DOCS, https://developers.facebook.com/docs/facebook-login/facebook-login-for-business, paraphrase): new Business-type apps use it automatically; Configurations replace `scope` with a `config_id` (token type, expiration, assets, permissions); users must grant all requested permissions or the app gets none; switching can be rolled back only within 30 days; Advanced Access to `public_profile` is required before going live.

**App types:** Consumer and Business; "App types cannot be changed" (DOCS, https://developers.facebook.com/docs/development/create-an-app/app-dashboard/app-types, paraphrase). Business apps use access levels instead of app modes.

**Settings, Basic** (DOCS, https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings, paraphrase): Display Name, Contact Email, Terms of Service URL, App Icon, Category and App Purpose are required for Live. The Privacy Policy URL and User Data Deletion are not listed as required for Live there, but the Instagram App Review page requires a privacy policy URL, 1024x1024 icon, category and business email (conflict, section 8). Treat the privacy policy as required.

**Redirect URI rules** (DOCS, https://developers.facebook.com/docs/facebook-login/security/, paraphrase): "Enforce HTTPS" requires HTTPS for OAuth redirects (all apps since October 6, 2018). Strict Mode requires an exact match including all parameters (`state` ignored; extra query parameters not allowed). No maximum stated. Wildcards for the redirect list not addressed. Localhost: COMMUNITY (Auth0, 2021-06-18, https://community.auth0.com/t/problems-with-facebook-login-when-testing-connection/64718) quotes dashboard text "http://localhost redirects are automatically allowed while in development mode only"; five years old, possibly stale. Business Login for Instagram: `redirect_uri` must match a base URI in the valid OAuth URI list; the dashboard may append a trailing slash; the token exchange must reuse the identical URI (DOCS, https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login). Authorization URL `https://www.instagram.com/oauth/authorize`.

**Scopes**
- Instagram Login: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_messages`, `instagram_business_manage_comments`, `instagram_business_manage_insights` (DOCS, https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login).
- Facebook Login (Instagram Graph API): `instagram_basic`, `instagram_manage_comments`, `instagram_manage_messages`, `instagram_content_publish`, `pages_show_list` and others (DOCS, https://developers.facebook.com/documentation/instagram-platform/app-review.md).
- An app uses Facebook Login or Instagram Login, not both (paraphrase).

## 2. What works immediately vs what is gated

- Standard Access is the default for all apps (DOCS, https://developers.facebook.com/documentation/instagram-platform/overview: "Standard Access is the default access level for all apps."). It suits role holders and accounts you own or manage. Advanced Access is needed for professional accounts you do not own or manage, and requires App Review and Business Verification (paraphrase).
- New apps start in Development mode; only role users can use them; in Live mode only permissions "approved through App Review" can be requested from anyone (DOCS, https://developers.facebook.com/docs/development/build-and-test/app-modes, paraphrase). Caveat: Business apps use access levels instead of app modes.
- **Roles** (DOCS, https://developers.facebook.com/docs/development/build-and-test/app-roles, paraphrase): Administrator, Developer, Tester, Analytics User; up to 500 administrators; up to 50 testers on most apps (up to 500 combined analytics users and testers for apps linked to a verified Business Manager). Testers must accept the invite (Facebook Settings, Apps and Websites; Instagram testers accept on instagram.com; the Instagram detail is from a vendor doc seen only in search, https://www.sourcecoast.com/jfbconnect/docs/social-network-applications/instagram-application-setup). Messaging testers need a role on the app and on the Instagram professional account.
- Works without review (own accounts): "Generate token" in the dashboard for added Instagram accounts gives a 60-day token (paraphrase, .../instagram-api-with-instagram-login/get-started).
- App Review does not apply to apps used only by role holders; others need per-permission approval (DOCS, https://developers.facebook.com/docs/app-review/, paraphrase).
- Until Business Verification is complete, users from other Businesses cannot grant permissions (DOCS, https://developers.facebook.com/docs/development/release/business-verification, paraphrase). This is the key block for Composio end users.
- Private apps that reviewers cannot test can request only `instagram_basic` and `instagram_manage_comments` (paraphrase).
- Users need an Instagram professional (Business or Creator) account; Facebook Login setups also need a linked Page (DOCS, overview).
- No per-app user-count cap other than role limits found. Some messaging features may not work until Advanced Access.
- **Rate limits** (DOCS, https://developers.facebook.com/docs/graph-api/overview/rate-limiting, paraphrase): Instagram non-messaging 4,800 x impressions per 24 hours per app and app-user pair; Business Discovery and Hashtag Search use Platform limits (200 x users per hour); Conversations API 2 calls per second per account; Send API 100 per second (text), 10 per second (audio or video); Private Replies 750 per hour; error code 80002; check `X-Business-Use-Case-Usage`. No separate published limit for unapproved apps (UNCERTAIN).

## 3. Approval / review path

**Triggers:** serving any user without a role requires App Review (DOCS, app-review). Tech Providers serving multiple businesses need Advanced Access ("Your app must complete App Review before it can request permissions with Advanced Access", wording unverified). Business Verification is required for Advanced Access (DOCS, business-verification page; "you might need to complete", effective February 1, 2023).

**Business Verification** (DOCS, paraphrase): an app admin links the app to a Business at Settings, Basic, Verification; a Business Admin starts verification in Business Manager; confirm the app shows a verified Business. Docs list no required documents (defer to the Business Help Center, whose body did not load). COMMUNITY/vendor (search summary, not opened): business registration or licence plus proof of address or phone; sole proprietors may be asked for government ID. UNCERTAIN.

**Submitted** (DOCS, https://developers.facebook.com/documentation/instagram-platform/app-review.md and https://developers.facebook.com/docs/resp-plat-initiatives/app-review/submission-guide, paraphrase): 1024x1024 icon, privacy policy URL, category, business email; step-by-step instructions with test credentials if needed (web is the only platform for Instagram Login); per permission a use description, a screencast and agreement to Allowed Usage; at least one successful API call per permission; a visible login button. Screencast: 1080p or better, no audio, show a user granting each permission and the app using it; "Any requested permission or feature missing a screen recording will not be approved." (unverified wording). Reviewers use their own test accounts; do not share personal Meta credentials. API calls must fall within 30 days of submission and call data logs within 2 days. Answer data-handling questions. Messaging: screencast covers login, granting permissions, setting up the automation or inbox and testing; the automation must respond within 30 seconds (DOCS, https://developers.facebook.com/documentation/business-messaging/instagram-messaging/app-review/apps-for-other-businesses, paraphrase).

**Path:** Instagram, API setup with Instagram login, "Complete app review", Continue to app review, App Review, Requests, Edit (paraphrase).

**Reviewer and cost:** Meta reviews and tests the app; if Meta cannot access the app, the whole submission is rejected (paraphrase). No fee mentioned in any fetched doc; not confirmed absent.

- **Official wait:** "Decisions are expected within about a week" (submission guide, paraphrase of summarizer; page undated, may be stale). The dashboard reportedly states a figure; could not check (UNCERTAIN). Business Verification: no timeline in the docs.
- **Community-reported wait:** a vendor blog (https://bundle.social/blog/meta-app-review-20-days, self-dated 2026-08-04, snippet showed 2026-07-05) claims the dashboard now says "expect a 20-day wait for most submissions", with history of 1 to 3 days until 2025, 4 to 6 days Jan to Mar 2026, 9 to 12 days April, 17 to 19 days May, up to 20 days mid-2026; promotional, unverified. Forum thread (https://developers.facebook.com/community/threads/3459359287566790/): a submission for `instagram_business_basic` and `instagram_business_manage_messages` had no update at 13 days; another submitted April 29 still waiting May 13; one resolved "after a few more weeks"; one blocker was an incomplete Data Use Checkup; post year not shown. Business Verification: submitted March 31, 2026, "In review" for 6 business days against a stated 2-day SLA (https://developers.facebook.com/community/threads/3091343734393360/, single case). Vendor reports of minutes to about 30 days for Business Verification (search summaries, not opened): weak.
- **Rejection reasons** (DOCS, paraphrase): missing screencasts, failing Allowed Usage, copy-pasted usage descriptions, changing app settings after submission. COMMUNITY (bundle.social): vague review notes, unused permissions, recordings that skip functionality, test accounts that fail (2FA, email verification, empty workspace), unreachable test environments, Business Verification name mismatches. https://singhamandeep.com/instagram-dm-screencast-case/ (undated consultant marketing): the recording showed sending but not receipt. A forum snippet says Instagram blocks screen capture of its own Android app (undated, https://communityforums.atmeta.com/android-apps-143/black-screen-on-screencast-due-to-instagram-business-manage-messages-permission-on-android-172197).
- **Re-review and recertification:** Data Use Checkup is annual for live apps with a use case or Advanced Access ("to maintain API access", unverified wording); Standard Access apps exempt; Dev-mode apps need it before Live (DOCS, https://developers.facebook.com/docs/resp-plat-initiatives/individual-processes/data-use-checkup). No fixed calendar date stated. Data Protection Assessment: annual, 60 calendar days from first notification; non-response deactivates the app (paraphrase, .../data-protection-assessment/faq).

## 4. Gotchas

- **Tokens, Instagram Login** (DOCS, overview): code valid 1 hour; short-lived token 1 hour; long-lived 60 days, refreshable. Business Login (paraphrase): code single-use; long-lived exchange `GET graph.instagram.com/access_token` with `grant_type=ig_exchange_token`, server-side only; refresh `ig_refresh_token`; the token must be at least 24 hours old, still valid and carry `instagram_business_basic`; tokens not refreshed within 60 days expire for good.
- **Tokens, Facebook Login** (DOCS, https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived): "A long-lived token generally lasts about 60 days."; long-lived Page tokens have no expiration date; an expired token cannot be exchanged. Login for Business system-user tokens default to never expire (paraphrase).
- **Instagram Login vs Facebook Login:** Instagram Login lacks hashtag search, product tagging and partnership ads, and needs no Facebook Page; it uses the Instagram app ID (Facebook Login for Business uses the Meta app ID). Migration swaps `graph.facebook.com` for `graph.instagram.com` (DOCS, .../migration-guide.md). A non-Business app cannot be converted.
- **Policy changes** (DOCS, https://developers.facebook.com/documentation/instagram-platform/changelog.md, paraphrase): old `business_*` scopes stopped 2025-01-27; some metrics removed in 2025; `instagram_manage_contents` added 2025-12-03; `instagram_manage_engagement` added 2026-04-22; `media_url` omitted for some videos from 2026-07-30; `enable_fb_login` deprecated 2025-06-14 then re-added 2026-02-06 (the changelog flags the conflict). Graph API v20.0 removed 2026-09-24, v21.0 2027-01-21; v26.0 published 2026-07-29 (DOCS, https://developers.facebook.com/blog/post/2026/07/29/introducing-graph-api-v26-and-marketing-api-v26/). **Access Verification retired** (DOCS, https://developers.facebook.com/blog/post/2026/10/09/retiring-access-verification-for-tech-provider-apps/, dated 2026-10-09, paraphrase): Business Verification and App Review remain required; older Access Verification guidance is stale. Basic Display API shut down 2024-12-04 (COMMUNITY, TechCrunch via search snippet only, https://techcrunch.com/2024/12/06/instagram-locks-out-developers-of-third-party-consumer-apps; no official Meta page found: UNCERTAIN at DOCS level).
- **Messaging:** you can message only after the user messages first; usually a 24-hour window, with a 7-day human-agent window (DOCS, .../messaging-api, paraphrase).
- Permissions only cover data created by the app user who granted them (paraphrase).
- **Composio specifics** (DOCS, vendor's own, https://docs.composio.dev/toolkits/instagram, paraphrase): the managed app currently lacks the comment permission; use your own Meta app with it approved; webhooks need the app Live with Advanced Access and Business Verification; only Business or Creator accounts work. Callback `https://backend.composio.dev/api/v3.1/toolkits/auth/callback` (search snippet of https://docs.composio.dev/docs/custom-auth-configs; older pages show another path; verify in your dashboard).

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research docs and requirements | Yes | No | Public |
| Create Meta developer account | No | Yes | Phone and email verification |
| Create app, choose use case | Template values | Yes | Logged-in Facebook identity |
| Draft privacy policy, ToS, data-deletion page | Yes | Review and host | Legal accuracy, live URL |
| Host those pages | Generate files | Deploy to company domain | Must be on company domain |
| Fill Basic Settings | Field template | Enter after login | Console |
| Add redirect URIs and callbacks | Supply exact values | Enter them | Console |
| Business portfolio and Business Verification | Document checklist | Yes | Government documents, Business Admin |
| Add Instagram testers, accept invites | No | Yes | Needs those accounts' logins |
| Test API call per permission | Scripts with human's token | Provide tokens | Calls logged within 30 days |
| Per-permission use-case text | Draft | Review | Must be accurate, unique per permission |
| Record screencast | Script and shot list | Yes | Their accounts, must match live app |
| Test credentials | Draft instructions | Create the account | Sensitive |
| Submit App Review | Prepare | Click submit | Irreversible |
| Wait, respond to feedback | Draft | Yes | Waiting, account access |
| Annual Data Use Checkup and Data Protection Assessment | Draft answers | Admin certifies | Legal certification |

## 6. Difficulty tier and estimate

**Tier: review-required.** Own-accounts-only is effectively instant. Review is the bottleneck; 2026 slowdown reports are all secondary. Access Verification no longer adds a step as of October 2026 (removes roughly 5 business days from the old path). Estimates at the top.

## 7. Sources

All accessed 2026-10-19.

| URL | Supports | Label |
|---|---|---|
| developers.facebook.com/apps/ (login redirect) | Use-case creation, review and verification in same dashboard | TESTED |
| https://developers.facebook.com/docs/development/create-an-app/ ; .../register ; .../app-dashboard/app-types ; .../app-dashboard/basic-settings | Creation, prerequisites, types, fields | DOCS (summarizer) |
| https://developers.facebook.com/documentation/instagram-platform/create-an-instagram-app.md ; .../app-review.md ; .../overview ; .../changelog.md | Instagram setup, submission, access levels, changes | DOCS (summarizer) |
| https://developers.facebook.com/docs/resp-plat-initiatives/app-review/submission-guide ; https://developers.facebook.com/docs/app-review/ | Submission rules, "about a week" | DOCS (summarizer) |
| https://developers.facebook.com/docs/development/release/business-verification | Business Verification | DOCS |
| https://developers.facebook.com/blog/post/2026/10/09/retiring-access-verification-for-tech-provider-apps/ ; .../2026/07/29/introducing-graph-api-v26-and-marketing-api-v26/ | Recent changes | DOCS |
| https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login (and /business-login, /messaging-api, /get-started, /migration-guide.md) | Scopes, tokens, messaging | DOCS (summarizer) |
| https://developers.facebook.com/docs/graph-api/overview/rate-limiting | Rate limits | DOCS |
| https://developers.facebook.com/docs/facebook-login/security/ ; .../guides/access-tokens/get-long-lived ; .../facebook-login-for-business | Redirects, tokens, Login for Business | DOCS |
| https://developers.facebook.com/docs/development/build-and-test/app-modes ; .../app-roles | Modes, roles | DOCS |
| https://developers.facebook.com/docs/resp-plat-initiatives/individual-processes/data-use-checkup ; .../data-protection-assessment/faq | Annual processes | DOCS |
| https://developers.facebook.com/documentation/business-messaging/instagram-messaging/app-review/apps-for-other-businesses | Messaging review | DOCS |
| https://docs.composio.dev/toolkits/instagram | Composio requirements | DOCS (vendor) |
| https://bundle.social/blog/meta-app-review-20-days | 2026 slowdown | COMMUNITY (vendor; date inconsistent) |
| https://developers.facebook.com/community/threads/3459359287566790/ ; .../3091343734393360/ | Waits | COMMUNITY (year not shown) |
| https://community.auth0.com/t/problems-with-facebook-login-when-testing-connection/64718 | Localhost | COMMUNITY (2021-06-18) |
| https://techcrunch.com/2024/12/06/instagram-locks-out-developers-of-third-party-consumer-apps | Basic Display shutdown | COMMUNITY (snippet only) |

## 8. Open questions

1. Privacy policy: basic-settings page does not require it for Live; the Instagram review page does. Treat as required.
2. Do Business apps have a Live toggle at all, or only access levels? Check the dashboard.
3. Review wait: docs say about a week; community 10 to 20+ days; the dashboard's own figure unverified. bundle.social's date is inconsistent.
4. Business Verification documents and timing: not in developer docs.
5. Cost: none found, not confirmed absent.
6. Localhost redirect in dev mode: only a 2021 community quote.
7. 2FA requirement: unknown.
8. `enable_fb_login` conflict in the changelog.
9. Is Business Verification required for every Advanced Access request? Docs say "might"; the Instagram overview says Advanced Access requires it. Assume yes for multi-tenant use.
10. Instagram testers must be public accounts: one summarized page, unsure.
11. App Review per permission: inferred from a table column, not stated.
12. All quotes came through a summarizer; re-check against live pages before publishing.
