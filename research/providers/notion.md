# Notion: OAuth ("public connection") setup and approval

- Researched: 2026-10-19
- Tier: **instant** for a working OAuth app. The optional Marketplace listing is **review-required**.
- Effort: about 0.5 to 1.5 active hours. Same-day calendar time. Add 2 to 4 hours of prep and a 5 to 10 business day wait if you also want a Marketplace listing.
- Confidence: medium. Official docs are current (2026). Form fields and token lifetimes are not stated in them.

Evidence labels: TESTED (observed by us in a browser), DOCS (official docs), COMMUNITY (third party), UNCERTAIN. Quotes from DOCS pages came through a summarizer tool, so see `_verification.md` for which were re-checked.

## Naming change (TESTED + DOCS)

- TESTED: on 2026-10-19 `notion.so/my-integrations` redirected to `app.notion.com/login?redirectURL=/developers/connections`. The page was titled "Connections | Notion Developers". The sidebar showed Get started, Workers, Connections, Personal access tokens, MCP tokens. The table had columns Connection, Installable in, Auth type, Owner, Created and a "New connection" button.
- DOCS: the changelog (May 12, 2026) says the Developer portal launched as one place for connections, Workers and personal access tokens. https://developers.notion.com/page/changelog
- A guide that says "integration" means "connection". Old URLs still redirect.

## 1. Where and how the app is created

**Console:** https://app.notion.com/developers/connections (DOCS, https://developers.notion.com/guides/get-started/authorization, 2026-10-19). Old URL `notion.so/my-integrations` redirects there (TESTED).

**Prerequisites**
- DOCS: for internal connections, "You must be a Workspace Owner to create a connection." https://developers.notion.com/guides/get-started/internal-connections
- Public connection: the docs say you choose a "development workspace" (paraphrase). Whether a non-owner can create one is UNCERTAIN.
- No payment, 2FA or organization requirement found for a public connection. UNCERTAIN, because it needs a login to confirm.

**Steps for a public connection** (DOCS, https://developers.notion.com/guides/get-started/public-connections)
1. In the Developer portal, select **Public connections** under **Build**.
2. Click **Create new connection**. Fill in the required fields.
3. Open the **Configuration** tab to get the OAuth client ID and client secret.
4. Set **Capabilities** (read, update, insert content; the internal-connections page also lists read user information).

**Form fields**

| Field | Evidence |
|---|---|
| Connection name | DOCS |
| Development workspace | DOCS |
| Redirect URI(s) | DOCS (in the OAuth configuration section of the authorization guide). Maximum count not stated: UNCERTAIN. |
| Installation scope: **Any workspace** or **Selected workspaces only** | DOCS: "This can't be changed after creation." Only "Any workspace" is Marketplace-eligible. |
| Capabilities | DOCS |
| Company name, website, tagline, privacy policy URL, terms URL, support email, icon | COMMUNITY only (norahsakal.com, Oct 1, 2022; docs.ampersand.ai, undated). The current official guide does not list them. UNCERTAIN whether the new form still asks. |

**Redirect URI rules**
- COMMUNITY (Oct 2022): no fragments, relative paths or wildcards; protocol required; not a public IP. https://norahsakal.com/blog/create-public-notion-integration/
- COMMUNITY (undated): "Notion only allows using 'http' for 'localhost'" and not 127.0.0.1. https://docs.allauth.org/en/latest/socialaccount/providers/notion.html. Another source says HTTPS only. See section 8.
- DOCS: `redirect_uri` is required at token exchange if the authorization URL had one or the app has more than one URI, and forbidden if exactly one URI and none was sent. https://developers.notion.com/reference/create-a-token

**Scopes:** Notion has no OAuth scope strings. Permissions are the capabilities above (COMMUNITY, Nango, undated). The user also picks which pages to share during consent (DOCS).

## 2. What works immediately vs what is gated

- Public connection OAuth: no prior review found in the docs (DOCS). Marketplace listing is optional (DOCS, https://developers.notion.com/guides/get-started/marketplace-listing).
- Caveat (DOCS): an image caption on the authorization page says "The Authorization URL field populates after a public connection is submitted for review." What that submit step does is UNCERTAIN.
- No user or workspace cap for public connections was found. UNCERTAIN, because absence of a stated limit is not proof.
- Each user completes the OAuth flow individually (DOCS, public-connections page).
- **Free-workspace block cap** (DOCS, https://developers.notion.com/reference/workspace-block-limits): "Free workspaces with more than one member have a limit of 1,000 lifetime blocks." It applies to internal connections and to OAuth connections limited to "Selected workspaces only". It does not apply to "Any workspace" connections or personal access tokens. After the limit, block creation returns HTTP 403 `restricted_resource`. The changelog dates enforcement to Sep 1, 2026.
- **Rate limits** (DOCS, https://developers.notion.com/reference/request-limits): "600 requests per minute (an average of 10 per second)" on Business and Enterprise; "180 requests per minute" on other plans. There is also a shared workspace-level limit with no number. No lower limit for unlisted apps was found.
- **Enterprise customer-side gate** (DOCS, https://www.notion.com/help/enterprise-connection-settings): an Enterprise owner can set "Approved only", so members cannot install a connection until an owner approves it. This is the customer's gate, not Notion's review.
- No unverified-app warning or test-user list was found. UNCERTAIN.

## 3. Approval / review path

- **For OAuth use:** no review is documented.
- **For Marketplace listing** (DOCS, marketplace-listing page): only public connections with "Any workspace" scope are eligible. You submit listing name and description, category and tags, images and logo. "The Notion team reviews every listing submission." The page mentions no fee, no demo video, no security assessment, and no business or domain verification (paraphrase). Rejection reasons: brand or trademark issues, quality, or failing unspecified "baseline connection criteria".
- **Official wait:** DOCS: "expect to hear back from our team within 5-10 business days via email."
- **Community-reported wait:** none found. UNCERTAIN.
- **Re-review cadence:** not stated. UNCERTAIN.
- The Best Practices guide with the real approval criteria was not fetched. UNCERTAIN.

## 4. Gotchas

**Tokens (most conflicting information)**
- DOCS: a refresh token comes with the access token. Call `https://api.notion.com/v1/oauth/token` with `grant_type=refresh_token`. It returns a new access token and a new refresh token (paraphrase; endpoint requires `Notion-Version: 2026-03-11` and Basic auth with client ID and secret). https://developers.notion.com/reference/refresh-a-token
- DOCS: no fetched page gives an access or refresh token lifetime. UNCERTAIN on lifetime.
- DOCS (changelog, Jun 8, 2026): new public connections issue a fresh access token and refresh token on each successful authorization. Existing connections keep earlier behavior (paraphrase). So an app created before that date may behave differently.
- COMMUNITY (Nango docs, undated): Notion has no refresh tokens and tokens never expire. This looks stale and contradicts current docs.
- COMMUNITY (Nango blog, Apr 1, 2026, vendor): refresh tokens rotate, so the old one stops working after use. Serialize refreshes per connection and save the new refresh token atomically. https://nango.dev/blog/notion-oauth-refresh-token-invalid-grant
- The `refresh_token` field is typed "string or null" (DOCS). Handle null.

**Consent and access**
- DOCS: users pick which pages to share. Only pages they have full access to appear. Abandoning the flow early leaves the connection with no access to the chosen pages.
- DOCS: always use `owner=user` in the authorization URL.
- DOCS: public connections act on behalf of the authorizing user. Access to a parent page covers its children.
- COMMUNITY (2022): the client secret may be shown only once. Save it at creation.

**Recent changes** (DOCS, changelog): Jun 16, 2026 workspace-level rate limit added. Sep 9, 2026 per-connection limit uses a fixed 60-second window. Sep 24, 2026 429 and 529 responses repeat the wait in `additional_data.retry_after`. Sep 1, 2026 block cap enforced over REST. Jul 2, 2026 personal access tokens got expiry options of 7, 30, 90, 180 days or 1 year.

No per-tenant subdomains or regions found for Notion OAuth. UNCERTAIN.

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research requirements | Yes | No | Public docs |
| Draft privacy policy, terms, tagline, scope text | Yes | Review and host on their domain | Needs owner sign-off |
| Notion sign-up, login, 2FA | No | Yes | Credentials |
| Workspace owner role | No | Yes | Required for internal connections |
| Create the connection, choose installation scope | No (needs login) | Yes | Scope is permanent |
| Copy client ID and secret to a secrets store | No | Yes | Sensitive, may be shown once |
| Add the Composio redirect URI | Draft the value | Paste in portal | Needs login |
| Marketplace copy, logo, images | Draft text | Upload and submit | Needs login |
| Wait for 5 to 10 business day review | No | Yes | Waiting on Notion |
| Test OAuth end to end | Yes, with a human-prepared test account | Approve the consent screen | Needs a real user and page selection |
| Handle refresh-token rotation in code | Yes | No | Code only |

## 6. Difficulty tier and estimate

**Tier: instant** (OAuth). Marketplace is review-required but optional.
- Active effort: 0.5 to 1.5 hours. Add 2 to 4 hours for a Marketplace listing.
- Calendar: same day. With a listing, roughly 1 to 3 weeks including a possible resubmission.
- Risk: the "submitted for review" caption may mean a human review gates the Authorization URL. Unverified.

## 7. Sources

| URL | Supports | Label | Accessed | Staleness |
|---|---|---|---|---|
| https://developers.notion.com/guides/get-started/authorization | Public vs internal, install scope, refresh, review caption | DOCS | 2026-10-19 | Current; no lifetimes |
| https://developers.notion.com/guides/get-started/public-connections | Create steps, fields | DOCS | 2026-10-19 | Omits company, privacy, terms fields |
| https://developers.notion.com/guides/get-started/internal-connections | Owner requirement | DOCS | 2026-10-19 | Current |
| https://developers.notion.com/guides/get-started/marketplace-listing | Review, 5-10 business days | DOCS | 2026-10-19 | Current |
| https://developers.notion.com/reference/request-limits | Rate limits | DOCS | 2026-10-19 | Current |
| https://developers.notion.com/reference/refresh-a-token | Refresh endpoint | DOCS | 2026-10-19 | Current |
| https://developers.notion.com/reference/create-a-token | redirect_uri rules | DOCS | 2026-10-19 | Current |
| https://developers.notion.com/reference/workspace-block-limits | Block cap | DOCS | 2026-10-19 | New in Sep 2026 |
| https://developers.notion.com/page/changelog | Dated 2026 changes | DOCS | 2026-10-19 | Fetched via summarizer |
| https://www.notion.com/help/enterprise-connection-settings | Enterprise approved-only | DOCS | 2026-10-19 | Current |
| https://norahsakal.com/blog/create-public-notion-integration/ | Form fields, URI rules | COMMUNITY (2022-10-01) | 2026-10-19 | 4 years old |
| https://docs.ampersand.ai/provider-guides/notion | Form fields | COMMUNITY (undated) | 2026-10-19 | Undated |
| https://docs.allauth.org/en/latest/socialaccount/providers/notion.html | http only for localhost | COMMUNITY (undated) | 2026-10-19 | Undated |
| https://nango.dev/blog/notion-oauth-refresh-token-invalid-grant | Token rotation | COMMUNITY (2026-04-01) | 2026-10-19 | Vendor blog |
| https://app.notion.com/developers/connections (via redirect) | Console renamed | TESTED | 2026-10-19 | Login wall only |

## 8. Open questions

1. Do tokens expire? Old community docs say never; current docs describe rotation but give no lifetime. Build for rotation.
2. What does the "submitted for review" step do on a new public connection?
3. Which fields does the live form require? A person with a login must look.
4. Localhost redirects: `http://localhost` allowed, or HTTPS only? Sources disagree.
5. Maximum number of redirect URIs.
6. The brief's assumption "Notion is instant" holds for OAuth use. The review gate applies only to the optional Marketplace.
