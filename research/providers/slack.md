# Slack: app with OAuth v2, distribution and Marketplace

- Researched: 2026-10-19
- Tier: **review-required** for a commercial multi-tenant provider like Composio. Basic OAuth install is instant, with no review once Public Distribution is on. Full capability is gated by the Slack Marketplace.
- Effort: 1 to 2 hours to create and test in your own workspace. 2 to 4 hours to activate public distribution. Roughly 25 to 50 hours of Marketplace prep (our estimate, not sourced).
- Calendar time: same day for installs. Marketplace: unknown time to reach 10 active workspaces, then preliminary review up to 10 business days, then functional review up to 10 weeks. Plan 3 to 6 months end to end (our estimate from the sources).
- Confidence: medium-high on official process. Medium on real wait. Several dates conflict (section 8).

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. Quotes in DOCS items passed through a fetch-tool summarizer; see `_verification.md`.

## Directly observed (TESTED, 2026-10-19)

`api.slack.com/apps` showed "Your Apps" and "You'll need to sign in to your Slack account to create an application." with a "Sign in to another workspace" link. TESTED. So you need a Slack account in a workspace.

## 1. Where and how the app is created

**Console:** https://api.slack.com/apps. Quickstart: click Create an app, choose Blank app (DOCS, https://docs.slack.dev/app-management/quickstart-app-settings, paraphrase). A search snippet says "from scratch" or "from an app manifest" (https://docs.slack.dev/app-manifests/configuring-apps-with-app-manifests/, not fetched). Redirect URLs, scopes and token rotation sit under OAuth & Permissions; client credentials under Basic Information; distribution under Manage Distribution (DOCS, https://docs.slack.dev/authentication/installing-with-oauth and https://docs.slack.dev/app-management/distribution/).

**Prerequisites**
- A Slack account in a workspace (you pick a development workspace). No payment mentioned (DOCS, paraphrase).
- A free workspace works. DOCS: "You can add up to ten third-party or custom apps." https://slack.com/help/articles/115002422943-Usage-limits-for-free-workspaces (line undated; older pages say 3).
- A free Slack Developer Program sandbox exists (basic: up to 2 workspaces, 8 users). DOCS: sandboxes "Cannot be used to distribute third-party apps and workflows." https://docs.slack.dev/tools/developer-sandboxes/
- 2FA for app creation: not found. UNCERTAIN.
- Workspace owners can restrict members to Marketplace apps; "This will not prevent members from creating and installing internal apps." (DOCS, https://slack.com/help/articles/1500009181142-Manage-app-settings-and-permissions)

**Steps**
1. api.slack.com/apps, Create New App (scratch or manifest). 2. Name and development workspace. 3. Basic Information: display info. 4. OAuth & Permissions: HTTPS redirect URLs, bot and user scopes, optional token rotation. 5. Read Client ID and Client Secret. 6. Install to your own workspace (single-workspace token). 7. For other workspaces, implement OAuth v2: authorize at `https://slack.com/oauth/v2/authorize`, exchange at `oauth.v2.access`; the code expires after ten minutes (paraphrase). 8. Manage Distribution, complete the checklist, **Activate Public Distribution**.

**Fields and limits** (DOCS, https://docs.slack.dev/reference/app-manifest, from a table)
- App name max 35 chars. Short description max 140. Long description max 4,000 (manifest editor requires at least 174). Background colour 3- or 6-digit hex; can be changed, not removed.
- Privacy policy and terms URL fields in the console: UNCERTAIN. The Marketplace guidelines require a privacy policy on your landing page.

**Redirect URL rules**
- DOCS: "The `redirect_uri` must use HTTPS." (https://docs.slack.dev/authentication/installing-with-oauth)
- A runtime `redirect_uri` must match or be a subdirectory of a configured URL (quote: "must match or be a subdirectory of a Redirect URL"). No anchors ("A Redirect URL can _not_ contain an anchor"). With several configured, send the same `redirect_uri` in both steps or get `bad_redirect_uri`; with none sent, the first is used (paraphrase).
- Manifest allows at most 1,000 redirect URLs. No wildcard syntax documented.
- Localhost: not mentioned in docs. COMMUNITY reports of `http://localhost` being rejected (post dates not seen): https://community.n8n.io/t/slack-oauth-redirect-uri-did-not-match-any-configured-uris-self-hosted-on-windows/271936, https://forum.cursor.com/t/slack-mcp-cli-login-fails-redirect-uri-mismatch-localhost-8787/158400. Use an HTTPS tunnel in dev. "Localhost always fails" is not documented: UNCERTAIN.

**Scopes:** bot scopes in `scope=`, user scopes in `user_scope=`. DOCS: "It is not possible to downgrade an access token's scopes." Manifest allows up to 255 bot and 255 user scopes; optional scopes via `bot_optional` and `user_optional`. Sign in with Slack (OpenID Connect) scopes cannot be combined with other scopes: "Each set of scopes must be requested in separate OAuth flows." (https://docs.slack.dev/authentication/sign-in-with-slack)

**App types:** internal (one workspace), unlisted/public, Marketplace (paraphrase). Classic apps can no longer be created (section 4).

## 2. What works immediately vs what is gated

- No review for internal apps or for unlisted public distribution (DOCS, distribution page, paraphrase). Before activating, every URL (redirect, events, interactivity, options load, slash command) must be HTTPS.
- DOCS: "Your app can only be installed on the workspace that owns it" until distributed; elsewhere `invalid_team_for_non_distributed_app`.
- No documented per-app cap on installs or users for unlisted apps. UNCERTAIN beyond that.
- **History limits (important).** `conversations.history` and `conversations.replies` drop from Tier 3 to Tier 1 (1 request per minute) for commercially distributed apps not approved for the Marketplace. `limit` max and default fall to 15 objects. Applies to new unlisted apps and net-new installs of existing unlisted apps from May 29, 2025. Marketplace apps unaffected. Internal customer-built apps keep Tier 3 (50+ per minute, up to 1,000 objects). Quote: "The new rate limits will not be applied to existing installations". Sources: https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps, https://docs.slack.dev/apis/web-api/rate-limits. A conflicting later rollout date exists (section 8).
- **MCP:** DOCS: "unlisted apps are prohibited from using MCP". https://docs.slack.dev/ai/slack-mcp-server/
- Other tiers per method, workspace, app, minute: Tier 1 1+, Tier 2 20+, Tier 3 50+, Tier 4 100+. `chat.postMessage` about 1 per second per channel. 429 carries `Retry-After` (paraphrase).
- Workspace admins can require app approval; members can request installs (paraphrase, https://slack.com/help/articles/222386767-Manage-app-approval-for-your-workspace). Adding scopes later forces reinstall in every workspace.
- Unverified-app warning on consent screens: not documented. UNCERTAIN. Whether the free-plan 10-app cap blocks a small customer from installing an unlisted app: plausible by plain reading, untested.

## 3. Approval / review path

**Trigger:** none is mandatory to distribute. But DOCS: the Marketplace is "the only appropriate channel for commercially distributing apps built with Slack APIs" (https://docs.slack.dev/changelog/2025/05/29/tos-updates; effective May 29, 2025 for new apps, June 30, 2025 for existing). Together with the history limits and the MCP rule, a commercial integration vendor is pushed toward the Marketplace.

**Preconditions to submit** (DOCS, https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide): "Your app has been installed on 10 or more active workspaces" (active = used in the last 28 days; Discovery API partners exempt). Changelog Sept 1, 2026 (effective July 2026): apps must "stay at 10 or more installed workspaces" during review (https://docs.slack.dev/changelog/2026/09/01/slack-marketplace-install-requirement/). Reviewers need test accounts and credentials. A demo video is recommended (paraphrase).

**Reviewed:** preliminary review (listing info, docs, a reason for each scope, working OAuth install) then functional review (every scope tested). "We will return submissions that are not ready for review." Guidelines require a public landing page, a privacy policy covering collection, use, retention and deletion, a public support page ("We expect support requests to receive a response within 2 business days."), request-signature verification, TLS 1.2+, least-privilege scopes, no scopes for future features, generally no legacy or restricted scopes (`admin.*`, `identity.*`, `search:read`, `workflow.steps:execute`). Quote: Slack "may also perform an advanced security review at any point". Training LLMs on Slack data is prohibited (paraphrase). Source: https://docs.slack.dev/slack-marketplace/slack-marketplace-app-guidelines-and-requirements. Business or domain verification: not mentioned (UNCERTAIN). A standalone security checklist is not on that page; a community issue lists an architecture diagram (https://github.com/tolgee/tolgee-platform/issues/3928, Sep 18, 2026).

**Reviewer:** Slack (Salesforce). A vendor blog says automated scans, architecture review and OAuth audit (COMMUNITY, https://viktor.com/blog/slack-marketplace-ai-agent, Feb 24, 2026, marketing).
**Cost:** none found.

- **Official wait:** preliminary review up to 10 business days; functional review up to 10 weeks for new submissions, 6 weeks for published apps resubmitting changes; Slack cannot speed up review for launch dates (review guide).
- **Community-reported wait:** Viktor: "typically 2 to 3 months", own app approved in two weeks (2026-02-24, vendor). A Medium/gitconnected post reportedly says four months (https://levelup.gitconnected.com/how-i-published-my-own-app-in-the-slack-marketplace-and-what-the-docs-didnt-tell-me-776e365d0426): 403 on fetch, undated, UNCERTAIN. A 2018 dev.to post says 7 days (https://dev.to/yvoschaap/the-slack-app-directory-developer-review-34go): stale.
- **Rejection reasons** (DOCS, paraphrase): bugs or poor UX, missing test accounts or install instructions, scopes for non-existent features, legacy or broad or restricted scopes, incomplete guideline compliance.
- **Re-review:** published apps are locked; config, feature or scope changes need resubmission. Resubmitting during preliminary review resets queue place; in functional review it is kept (official wording). COMMUNITY (tolgee, WorkOS) says every resubmission resets: partial conflict. Upgrading to granular permissions cannot be undone.

## 4. Gotchas

- **Tokens:** DOCS: "OAuth tokens do not expire" by default. Token rotation is opt-in (granular permissions only), set in OAuth & Permissions or `settings.token_rotation_enabled`. "Token rotation may not be turned off once it's turned on." With rotation: 12-hour tokens (`expires_in` 43,200), refresh via `oauth.v2.access` with `grant_type=refresh_token`. "Refresh tokens are designed to be used once." The old one is revoked after a short grace period; persist the newest and serialise refreshes per connection. Only 2 active access tokens are kept if you refresh repeatedly (paraphrase). https://docs.slack.dev/authentication/using-token-rotation. A snippet suggests `oauth.v2.exchange` converts existing tokens once, and that user tokens rotate as `xoxe.xoxp-` (UNCERTAIN). COMMUNITY: a CLI v4.9.0 release adds `settings.app_level_token_rotation_enabled` (https://releasebot.io/updates/slack/slack-developer, Oct 2, 2026).
- **Bot vs user tokens:** bot acts as the app; user tokens come under `authed_user`. Treat the `team` parameter as a hint: "The `oauth.v2.access` response is the source of truth."
- **Scope granularity:** 120+ granular scopes by action and conversation type (paraphrase, https://docs.slack.dev/reference/scopes). Bots read only channels they belong to.
- **Admin approval and Grid:** owners can require approval; adding scopes means reinstall; subscribe to `app_uninstalled`. Org-ready apps use `org_deploy_enabled: true`; org installs return `team: null` and an `enterprise` object and `is_enterprise_install`; one token covers many workspaces so some methods need `team_id` (DOCS, https://docs.slack.dev/enterprise/developing-for-enterprise-orgs/).
- **Policy changes:** May 29, 2025 history limits; June 30, 2025 ToS for existing apps; July 2026 Marketplace threshold to 10; classic apps (section 8).
- **OIDC:** authorize `https://slack.com/openid/connect/authorize`; scopes `openid`, `email`, `profile`; separate flow.
- Unfurl domains: up to 5, reinstall on change (snippet only). GovSlack uses `slack-gov.com`.

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research docs, scopes, limits | Yes | No | Public |
| Draft app manifest (name, descriptions, scopes, redirect, rotation flag) | Yes | Review | Text/JSON with known limits |
| Sign in to Slack, Create New App, paste manifest | No | Yes | Authenticated account |
| Copy client ID and secret into Composio | Template | Yes | Secrets |
| Draft privacy policy, support page, landing page, per-scope justification | Yes | Review and publish | Human owns legal accuracy |
| Host those pages | Generate files | Yes | Deploy and domain access |
| Test OAuth install and redirect URLs | Code | Click consent | Slack consent screen |
| Activate Public Distribution | No | Yes | Console action |
| Recruit 10 active workspaces | Draft outreach | Yes | Real customers |
| Record 30 to 90 s demo video | Script | Yes | Needs own account and screen |
| Reviewer test account and credentials | No | Yes | Credentials |
| Submit Marketplace form | Draft | Yes | Irreversible |
| Wait, answer feedback | Draft replies | Yes | Calendar time, account access |
| Org-level install on Grid | No | Org Admin | Admin approval |

## 6. Difficulty tier and estimate

**Tier: review-required** (commercial vendor). Escape hatch (inference only): if each customer registers their own Slack app, "internal customer-built" apps keep Tier 3 limits. Whether a customer's app used through a vendor counts as internal is not stated: UNCERTAIN. Estimates at the top.

## 7. Sources

All accessed 2026-10-19.

| URL | Supports | Label |
|---|---|---|
| api.slack.com/apps | Sign-in required | TESTED |
| https://docs.slack.dev/authentication/installing-with-oauth | Redirect rules, tokens, install limits | DOCS |
| https://docs.slack.dev/authentication/using-token-rotation | Rotation | DOCS |
| https://docs.slack.dev/app-management/distribution/ | Distribution | DOCS |
| https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps | History limits | DOCS |
| https://docs.slack.dev/apis/web-api/rate-limits | Tiers | DOCS |
| https://docs.slack.dev/reference/methods/conversations.history | Non-Marketplace limits | DOCS |
| https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide | 10 workspaces, timelines | DOCS |
| https://docs.slack.dev/changelog/2026/09/01/slack-marketplace-install-requirement/ | Threshold 10 | DOCS |
| https://docs.slack.dev/slack-marketplace/slack-marketplace-app-guidelines-and-requirements | Guidelines | DOCS |
| https://docs.slack.dev/changelog/2025/05/29/tos-updates | Marketplace as commercial channel | DOCS |
| https://docs.slack.dev/reference/app-manifest | Field limits | DOCS |
| https://docs.slack.dev/app-management/quickstart-app-settings | Create steps | DOCS |
| https://docs.slack.dev/reference/scopes | Scopes | DOCS |
| https://docs.slack.dev/authentication/sign-in-with-slack | OIDC | DOCS |
| https://docs.slack.dev/enterprise/developing-for-enterprise-orgs/ | Org installs | DOCS |
| https://docs.slack.dev/ai/slack-mcp-server/ | MCP restriction | DOCS |
| https://docs.slack.dev/tools/developer-sandboxes/ | Sandbox | DOCS |
| https://docs.slack.dev/changelog/2024-09-legacy-custom-bots-classic-apps-deprecation/ ; https://docs.slack.dev/changelog/2025/07/29/classic-apps-extension/ | Classic app date and pause | DOCS |
| https://slack.com/help/articles/115002422943-Usage-limits-for-free-workspaces | Free-plan 10 apps | DOCS (help center) |
| https://slack.com/help/articles/222386767-Manage-app-approval-for-your-workspace ; https://slack.com/help/articles/1500009181142-Manage-app-settings-and-permissions | Admin approval | DOCS (help center) |
| https://workos.com/blog/oauth-app-approval-slack-microsoft-atlassian | "5 or more" workspaces, Aug 27, 2026 | COMMUNITY (contradicts docs) |
| https://github.com/tolgee/tolgee-platform/issues/3928 | Prep checklist, Sep 18, 2026 | COMMUNITY |
| https://viktor.com/blog/slack-marketplace-ai-agent | 2 to 3 months, 2026-02-24 | COMMUNITY (vendor) |
| https://releasebot.io/updates/slack/slack-developer | Aggregated updates | COMMUNITY |
| gitconnected, n8n, cursor forum URLs above | Wait, localhost | COMMUNITY (snippets or 403) |

## 8. Open questions

1. Marketplace minimum: 10 active workspaces (official, Sept 1, 2026 changelog) vs "5" (WorkOS Aug 27, 2026; tolgee issue Sep 18, 2026, quoting the console checklist). Check Manage Distribution in the console.
2. When do history limits hit existing unlisted installs? Official pages say existing installs are not affected; secondary sources report rollout to existing installs from Sept 2, 2025 to March 3, 2026 with no official page found. Do not assume existing installs are safe.
3. Does a shared Composio-style unlisted app count as "commercially distributed"? ToS says the Marketplace is the only appropriate channel; the distribution doc presents unlisted distribution with no review. Enforcement risk UNCERTAIN.
4. Customer-built apps as escape hatch: inference only.
5. Resubmission queue reset: official vs community differ.
6. Classic apps: page body says Nov 16, 2026 (under a month from today) but a top notice says changes are paused. Check before depending on either.
7. Localhost redirects: docs silent, community says rejected.
8. Free-plan app limit 10 vs older 3.
9. Not verifiable without login: console privacy and terms fields, unverified-app warning, 2FA, Manage Distribution checklist.
10. Our assumption check: none of the brief's named assumptions concern Slack. The notable surprise is that review is not about OAuth install at all; it is about rate limits and MCP access for commercial apps.
