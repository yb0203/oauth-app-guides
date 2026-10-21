# Composio auth model (public docs only)

Method: subagent read public Composio docs (no API key); orchestrator spot-checked a sample (see `_verification.md`). Claims carry a source URL. Anything inferred is marked **UNCERTAIN**. The fetch tool summarizes pages, so quotes are paraphrase-grade and have not been checked against the raw page.

## 1. What a developer supplies when bringing their own OAuth app

**Fields** (custom auth config, `use_custom_auth`, scheme `OAUTH2`):
- `credentials.client_id`, `credentials.client_secret`, `credentials.oauth_redirect_uri`
- `credentials.scopes` is optional, a comma-separated string (example `"repo,read:org"`)
- The create call also needs `type`, `auth_scheme`, `name`
- Sources: https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md , https://docs.composio.dev/docs/authentication/controlling-scopes.md
- Required fields per toolkit can be discovered with `composio.toolkits.get_auth_config_creation_fields(toolkit, auth_scheme, required_only=True)` (programmatic-auth-configs page).
- The dashboard route is Create Auth Config, pick toolkit and scheme, enter credentials, copy the `ac_...` ID: https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app.md
- Scopes "must be approved in the provider's developer portal" (controlling-scopes page). They can be changed later with `auth_configs.update(...)`, which affects new connections only.

**Redirect URI: the answer.**
- By default the developer registers a **Composio-hosted callback** with the provider, not their own domain: `https://backend.composio.dev/api/v3/toolkits/auth/callback`. Sources: programmatic-auth-configs page and https://composio.dev/auth/github
- **Legacy value still in use:** `https://backend.composio.dev/api/v1/auth-apps/add`. The Google guide (https://composio.dev/auth/googleapps) still tells developers to use it, and the programmatic page says "some toolkits" still use it. The docs do not say which ones. The GitHub guide says its screenshot shows the older URL.
- The value registered with the provider must match exactly. The Google guide and https://docs.composio.dev/kb/guide/platform-google-oauth.md both say this.
- The dashboard shows the redirect URI for each auth config, and Composio says to use the exact value it shows, not old examples: https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app.md , https://docs.composio.dev/kb/guide/dashboard-auth-configs-navigation.md
- **Own domain is possible (white-labeling):** register `https://yourdomain.com/api/composio-redirect` with the provider. Your endpoint must return a 302 to `https://backend.composio.dev/api/v3/toolkits/auth/callback` with the query string forwarded, and the auth config's custom redirect URI must be set to match: https://docs.composio.dev/docs/authentication/white-labeling-authentication.md
- Programmatic access to the URI: the `POST /api/v3.1/auth_configs` reference documents no redirect field in the request or the response (it documents `toolkit.slug`, `auth_config.id`, `auth_config.auth_scheme`, `auth_config.is_composio_managed`): https://docs.composio.dev/reference/api-reference/auth-configs/postAuthConfigs.md . **UNCERTAIN:** whether the live API returns it undocumented. The documented source is the dashboard.
- **UNCERTAIN:** whether the URI varies per environment, project, or self-hosted deployment. The docs are silent.
- Provider-specific note: Slack's fix for a mismatch is under OAuth & Permissions → Redirect URLs (https://docs.composio.dev/toolkits/slack).

**Takeaway for our guides:** every BYO guide should tell the developer to copy the redirect URI from the Composio dashboard for that auth config, with the v3 URL as the expected value, and warn that some toolkits still show the legacy v1 URL.

## 2. When to bring your own app even if a managed one exists

Source for the table: https://docs.composio.dev/docs/authentication/custom-app-vs-managed-app.md

| Factor | Explicit in docs? | What the docs say |
|---|---|---|
| Consent-screen branding | Yes | Managed shows "Composio wants to access your account"; production users should see your app name. The Connect Link page can be branded even with managed apps. |
| Rate limits | Yes | Managed apps share quota across all Composio users; your own app gets dedicated quota. No numbers are given. The Gmail toolkit page repeats this. |
| Scopes | Yes | Managed uses Composio's defaults; custom is your choice. The scopes page says managed apps can also set scopes in credentials, and lists no caps. |
| Polling | Yes | Managed auth has a 15-minute minimum polling interval. |
| Custom instances | Yes | Self-hosted or regional variants (for example a private Salesforce subdomain) need their own app. |
| Enterprise requirements | Yes | Customers may require your branding end to end. |
| Verification status | Partly | Gmail toolkit page: scopes Google has not verified for the client cause "App is blocked"; fix is your own OAuth app verified for that scope (https://docs.composio.dev/toolkits/gmail , Google KB above). |
| Slack approval | Yes | Composio says it is working on Slack Marketplace review for its managed app with no timeline; suggests your own app or admin approval meanwhile (https://docs.composio.dev/toolkits/slack). |
| Token isolation | Yes (Notion) | "strongly recommend using your own Notion app" (https://docs.composio.dev/toolkits/notion). |
| Security and compliance | Not stated | Pointer only to https://docs.composio.dev/docs/security/token-custody (not read). **UNCERTAIN.** |
| Production use | Not as a rule | Managed is described as suited to internal tools, prototypes and development. |

Some toolkits have no managed app at all; the fallback is to "register your own OAuth app" (https://docs.composio.dev/toolkits/managed-auth).

## 3. How auth configs and connected accounts relate

Sources: https://docs.composio.dev/docs/authentication.md , https://docs.composio.dev/docs/authentication/programmatic-auth-configs.md
- **Auth config** = the blueprint for one toolkit in one project: auth scheme, scopes, credentials, managed or custom. ID looks like `ac_xxxxxxxx`. API flag: `is_composio_managed`. Types: `use_composio_managed_auth` or `use_custom_auth`.
- **Connected account** = one end user's authorized connection (`ca_...`) created against an auth config. Legacy terms: entity ID is now `user_id`, integration ID is now `auth_config_id`.
- In session mode `composio.create(user_id, auth_configs={"github": "ac_..."})` selects a custom config per toolkit. Unlisted toolkits keep managed auth, and managed toolkits need no pre-created config.
- Flow: optionally create the auth config, create a session, `session.authorize("gmail", callback_url=...)` returns a connection request with `redirect_url`, the user consents at the provider, Composio redirects back, `wait_for_connection(timeout)` returns the account (default 60 s). Source: https://docs.composio.dev/docs/authentication/manually-authenticating.md
- The `callback_url` passed here is the **end-user's post-auth return URL in the developer's app**, which is different from the provider-side redirect URI. Composio appends `status=success|failed` and `connected_account_id` and warns that these are not proof of ownership. Keep these two URLs distinct in guides.
- Statuses: `INITIATED` when the user abandons the flow; the API page mentions `ACTIVE` and `FAILED` with `status_reason`. No full status model is documented.
- REST: `POST /api/v3.1/connected_accounts/link` takes `auth_config_id`, `user_id`, optional `callback_url`, `alias`; returns `link_token`, `redirect_url`, `expires_at`, `connected_account_id`: https://docs.composio.dev/reference/api-reference/connected-accounts/postConnectedAccountsLink.md
- Existing connections stay tied to their original auth config; to switch, delete and re-authenticate (white-labeling page).

## 4. The managed vs bring-your-own split

Source: https://docs.composio.dev/toolkits/managed-auth
- Two sections: "Composio-managed OAuth available (123)" and "Bring your own OAuth app (211)", 334 OAuth toolkits in total. Each is a two-column markdown table (Toolkit, Slug).
- Only OAuth toolkits are covered. A toolkit is listed as managed if Composio manages at least one of its OAuth methods, so multi-method toolkits need a check on their own page. Programmatic check: the `composio_managed_auth_schemes` field on the toolkit endpoint.
- Counts come from the section headings; the orchestrator also counted the table rows (123 and 211), see `_verification.md`.

## 5. Provider-side approval: who does it?

Composio documents none of the approval process and leaves it to the developer.
- Google: KB says to complete Google's required verification for sensitive or restricted scopes, then reconnect. It states it does not cover CASA, publishing status, or who performs verification (https://docs.composio.dev/kb/guide/platform-google-oauth.md).
- Slack: for your own app, the docs only cover workspace-admin settings ("Require apps from Slack Marketplace", "Require approved apps").
- GitHub: user must install the GitHub App; Composio provides no installation link.
- Nothing found on privacy policy, domain verification, scope justification, or submission steps.

This is the gap our guides fill.

## Composio's own per-provider guides exist
`https://composio.dev/auth/<slug>` pages (for example `/auth/github`, `/auth/googleapps`, `/auth/slack`) hold step-by-step provider setup guides. They matter for prior art (see `prior-art.md`) and may be a source for the library. **UNCERTAIN:** how many exist.

## Open questions
- Does the live API return the redirect URI on auth config creation? (Not documented.)
- Which toolkits still use the legacy v1 callback?
- Does the URI vary by environment or self-hosted deployment?
- Are managed-app scope sets fixed? (Docs say only "defaults".)
- Token-custody and compliance pages were not read.
