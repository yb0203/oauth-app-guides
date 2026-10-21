# Spotify: developer app, Development Mode vs Extended Quota

- Researched: 2026-10-19
- Tier: **partner-only** for anything beyond 5 users. Development Mode alone is instant.
- Effort: 0.5 to 1 hour for a dev-mode app. 4 to 10 hours for an Extended Quota application.
- Calendar time: official "up to six weeks". Community reports 2 to 3+ months, or no reply. Approval needs a legal organization with at least 250k monthly active users, so for most developers the answer is "never".
- Confidence: medium-high on caps and token rules (several 2026 DOCS posts agree). Medium-low on real review times (community snippets only).

Evidence labels: TESTED (observed by us), DOCS, COMMUNITY, UNCERTAIN. Quotes in DOCS items passed through a summarizer in the research tool; see `_verification.md` for the ones re-checked.

## Directly observed (TESTED, 2026-10-19)

- `developer.spotify.com/dashboard` redirects to a Spotify login page (email, phone, Google, Facebook, Apple; "Don't have an account? Sign up"). TESTED.
- The developer.spotify.com home page shows a banner "Update on Developer Access and Platform Security". The linked post is dated February 6, 2026 and says, from 11 Feb 2026, new Development Mode Client IDs need "a Spotify Premium account", are limited to "one Development Mode Client ID", "up to five authorized users", and a "smaller set of supported endpoints". From March 9 the same rules apply to existing integrations. A March 9 update postponed endpoint-access changes for existing integrations only. TESTED (read on screen). https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security

## 1. Where and how the app is created

**Console:** https://developer.spotify.com/dashboard. Needs a Spotify login (TESTED). Field-level detail below comes from docs, not from seeing the dashboard.

**Prerequisites**
- A Spotify account (DOCS, https://developer.spotify.com/documentation/web-api, paraphrase).
- The app owner needs Premium. DOCS: "The app owner must have a Spotify Premium account for apps in development mode to function." https://developer.spotify.com/documentation/web-api/concepts/quota-modes. If Premium lapses the app stops until resubscribed (DOCS, https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide, paraphrase).
- No organization, domain or business needed for Development Mode (none found). A company is required only for Extended Quota.
- Whether the dashboard requires 2FA: UNCERTAIN.

**Steps** (DOCS, https://developer.spotify.com/documentation/web-api/concepts/apps, paraphrase)
1. Open the Dashboard, click "Create an App". Limit: 25 apps per developer account.
2. Fill in App Name, App Description, tick the Developer Terms of Service.
3. Click CREATE. The overview page shows Client ID and Client Secret.
4. Edit Settings: Website, Redirect URIs, Android Package or iOS Bundle IDs. Save.
5. For users other than the owner: Settings, Users Management, Add new user (name and Spotify email).

| Field | Notes | Evidence |
|---|---|---|
| App Name, App Description | Shown on the grant screen | DOCS |
| Developer Terms of Service | Checkbox | DOCS |
| Website | Optional | DOCS (paraphrase) |
| Redirect URIs | Rules below | DOCS |
| Android Package / iOS Bundle IDs | Mobile apps only | DOCS |
| Logo, privacy policy URL, terms URL | Not documented. Probably absent. | UNCERTAIN |
| "Which API/SDK" selector | Web API landing page says select "Web API". Apps page lists no such field. | UNCERTAIN |

**Redirect URI rules** (DOCS, https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- "Use HTTPS for your redirect URI, unless you are using a loopback address".
- Loopback must be `http://127.0.0.1:PORT` or `http://[::1]:PORT`. "`localhost` is not allowed as redirect URI."
- Exact match, except loopback may use a dynamic port.
- New validation applied to newly created apps from April 9, 2025. All clients were expected to migrate by November 2025 (paraphrase).
- Wildcards and maximum URI count: not documented (UNCERTAIN).

**Scopes** are requested at authorization time, not set on the app (DOCS, https://developer.spotify.com/documentation/web-api/concepts/scopes). `streaming` needs Premium and the Web Playback SDK. `app-remote-control` is mobile SDKs only.

**Flows** (DOCS, https://developer.spotify.com/documentation/web-api/concepts/authorization): Authorization Code, Authorization Code with PKCE, Client Credentials. Implicit Grant is labelled deprecated.

## 2. What works immediately vs what is gated

Every new app starts in Development Mode (DOCS, quota-modes page).

- **Users:** "Up to 5 authenticated Spotify users can use an app that is in development mode." Users must be on the allowlist. It was 25 until February 2026 (COMMUNITY/press, https://techcrunch.com/2026/02/06/spotify-changes-developer-mode-api-to-require-premium-accounts-limits-test-users/).
- **Client IDs per developer:** 1 from Feb 11, 2026 (DOCS, Feb 6 blog). On July 23, 2026: "You can now create up to 25 Client IDs per developer account." (DOCS, https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates).
- **Quota is per developer account**, shared across dev-mode apps. Exceeding it returns 429 with `"reason": "QUOTA_EXCEEDED"`. No number is published (DOCS, July 2026 blog).
- **Rate limit:** a rolling 30-second window, with `Retry-After` on 429. No numbers published (DOCS, https://developer.spotify.com/documentation/web-api/concepts/rate-limits).
- **Endpoints:** a smaller set for dev-mode apps. See section 4.
- **Test users:** the allowlist is the mechanism, capped at 5.
- No consent-screen warning for dev-mode apps was found. UNCERTAIN.
- An owner with Premium can create an app and call the API immediately, with no review.

## 3. Approval / review path (Extended Quota Mode)

- **Trigger:** you need more than 5 users or more than the dev-mode quota.
- **Who may apply:** DOCS: since May 15, 2025, "Spotify only accepts applications from organizations (not individuals)." Company email required. (quota-modes page)
- **Criteria** (DOCS, quota-modes page, paraphrase): legal business entity, active launched service, at least 250k MAUs, availability in key markets, commercial viability, adherence to the Terms.
- **Process** (DOCS, paraphrase): submit the Partner Application form with a company email; if approved, open Settings, "Quota extension Request" tab; complete a 4-step questionnaire; submit; Spotify reviews policy compliance and tests the app, then emails feedback. A community post says the tab moved and is now a form (COMMUNITY, search snippet only, https://community.spotify.com/t5/Spotify-for-Developers/Quota-Extension-Request-tab-not-visible-in-Developer-Dashboard/td-p/7401540).
- **Submitted:** questionnaire content is not published. No demo video or security assessment requirement found (UNCERTAIN).
- **Reviewer:** Spotify's app review team. **Cost:** none stated.
- **Official wait:** DOCS: "This review process can take up to six weeks."
- **Community-reported wait** (snippets only, pages did not render): pinned post says peak periods "may take longer than six weeks" (undated); one request filed March 21 had no answer after 2+ months (probably 2023); one report of a December 19, 2025 request still not in review after 3+ months, URL not pinned down. Treat as anecdotal. UNCERTAIN.
- **Rejection reasons** (COMMUNITY, snippets): commercial use, Remote Playback SDK use, changing reasons between attempts, not meeting post-May-2025 criteria. Spotify said over 95% of earlier applications fell short of security, privacy and licensing standards (DOCS, https://developer.spotify.com/blog/2025-04-15-updating-the-criteria-for-web-api-extended-access, paraphrase).
- **Re-review:** not stated. New use cases must be notified to Spotify (DOCS, https://developer.spotify.com/policy, paraphrase).

## 4. Gotchas

- **Refresh tokens now expire after 6 months** (DOCS, https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration). Quote: "Refreshing an access token does not reset or extend the refresh token's 6-month lifetime." New apps from June 18, 2026. Existing apps from July 20, 2026. Expiry returns `400 invalid_grant`. Applies to Authorization Code and PKCE. Spotify gives no issue timestamp, so store your own authorization time. Extended Quota exemption: unstated (UNCERTAIN). **Implication for Composio: every Spotify connection needs a re-auth prompt at about 6 months.**
- Access tokens last 1 hour (DOCS, https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens). A refresh response may omit a new refresh token; keep the old one then (paraphrase).
- **Dev-mode endpoint cuts** (DOCS, migration guide): removed or renamed batch multi-get endpoints, `GET /browse/new-releases`, `/browse/categories`, `GET /artists/{id}/top-tracks`, `GET /users/{id}`, user playlists, `GET /markets`, `/playlists/{id}/tracks` (now `/items`), per-type library endpoints (now `/me/library`). Fields removed include `popularity`, `available_markets`, artist `followers`, and on `GET /me`: `country`, `email`, `explicit_content`, `followers`, `product`. Search `limit` max fell from 50 to 10. Playlist contents are returned only for playlists the user owns or collaborates on.
- **Nov 27, 2024 cuts** (DOCS, https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api): new and unreviewed apps lost Related Artists, Recommendations, Audio Features, Audio Analysis, Featured and Category Playlists, and 30-second previews in multi-get.
- **Terms** (DOCS, https://developer.spotify.com/terms, paraphrase): AI/ML training on Spotify content is banned; delete a user's data within 5 days of disconnect; privacy policy must be shown before sign-up.
- The Web API landing page says "You need a Spotify Premium account to use the Web API."
- Policy changed in Nov 2024, Apr/May 2025, Feb/Mar 2026, Jun/Jul 2026. Re-check before publishing.

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research current limits and endpoints | Yes | No | Public docs |
| Create Spotify account, subscribe to Premium | No | Yes | Credentials and payment |
| Log in to dashboard | No | Yes | Credentials |
| Create app, fill name and description | Draft | Yes | Submission under the human's session |
| Accept Developer Terms | No | Yes | Needs human consent |
| Register redirect URIs | Draft the list | Yes | Dashboard action |
| Add allowlist users (max 5) | Draft | Yes | Needs each user's email and consent |
| Copy Client ID and Secret into Composio | No | Yes | Secrets |
| Draft privacy policy, terms, use-case text | Yes | Review and publish | Writing |
| Partner Application and quota questionnaire | Draft answers | Yes (submit) | Needs a legal entity and company email |
| Wait for review | No | Yes | Up to 6 weeks officially |
| Build 6-month re-auth flow | Yes | Review | Code |

## 6. Difficulty tier and estimate

**Tier: partner-only** (dev mode alone is instant but capped at 5 users).
- Dev mode: 0.5 to 1 active hour, same day.
- Extended Quota: 4 to 10 active hours, then 6 weeks to 4+ months or never.

## 7. Sources

| URL | Supports | Label | Accessed |
|---|---|---|---|
| developer.spotify.com/dashboard (login wall) | Login required | TESTED | 2026-10-19 |
| https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security | 5 users, Premium, 1 Client ID | TESTED + DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/quota-modes | Caps, org-only, 250k MAU, 6 weeks | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide | Endpoint cuts, Premium lapse | DOCS | 2026-10-19 |
| https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates | 25 Client IDs, per-account quota | DOCS | 2026-10-19 |
| https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | 6-month refresh | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens | 1h access token | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/redirect_uri | Redirect rules | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/apps | Create-app steps | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/rate-limits | 30s window | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/authorization | Flows | DOCS | 2026-10-19 |
| https://developer.spotify.com/documentation/web-api/concepts/scopes | Scopes | DOCS | 2026-10-19 |
| https://developer.spotify.com/blog/2025-04-15-updating-the-criteria-for-web-api-extended-access | 2025 criteria | DOCS | 2026-10-19 |
| https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api | 2024 cuts | DOCS | 2026-10-19 |
| https://developer.spotify.com/terms, https://developer.spotify.com/policy | Terms, policy | DOCS | 2026-10-19 |
| https://techcrunch.com/2026/02/06/spotify-changes-developer-mode-api-to-require-premium-accounts-limits-test-users/ | Old 25-user cap | COMMUNITY (press) | 2026-10-19 |
| community.spotify.com threads (waits, rejections, tab moved) | Wait anecdotes | COMMUNITY (snippets only) | 2026-10-19 |

## 8. Open questions

1. Existing-app grandfathering: the Feb blog says the 5-user and 1-Client-ID rules reach existing apps from March 9; the migration guide says "If you already have multiple Client IDs or more than 5 users, you will retain them." Unresolved.
2. Client-ID limit: 1 (Feb) vs 25 (July 23). The July post is newest.
3. Does Extended Quota exempt apps from the 6-month refresh expiry?
4. Does rotation reset the 6-month window?
5. Real review time: official 6 weeks vs community 2 to 3+ months. Community threads were seen as snippets only.
6. Live create-app form fields (logo, privacy policy, "Web API" selector) need a logged-in check.
7. Contradicts our assumption: "Spotify caps unapproved apps at a small number of users" is true, and the number is **5** (not 25), plus a Premium requirement for the owner.
