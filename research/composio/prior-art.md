# Prior art: how integration platforms document provider OAuth app setup

Method: a web-research subagent opened each cited URL via a summarizing fetch tool, so "no screenshots" or "no troubleshooting" are strong signals, not pixel-verified. Anything marked UNVERIFIED could not be confirmed. Research date: 2026-10-19.

## Summary table

| Platform | Guide shape | Screenshots | Time estimate | Approval blockers | Dates / freshness | Troubleshooting |
|---|---|---|---|---|---|---|
| Nango | Hub page + separate "register your own X OAuth app" page per provider, numbered steps | No | Only "2 minutes" for the test app; Google review page gives weeks | **Best in set (Google only)** | None (inline hints only) | Little |
| Merge | Agent Handler: one generic page + 3 inline walkthroughs. Unified: one help-center article per partner | Help-center yes, docs no | No | Partial (SharePoint publisher verification) | Relative label ("8 months ago") | Scattered prose |
| Pipedream | Generic 3-4 step flow, no per-provider pages | One | No | No | No | No |
| Paragon | Uniform template per provider (credential fields, redirect URL, 3-4 steps) | **Heaviest: animated GIFs per click path** | No | No | No | No |
| Unified.to | Blog-style guide per vendor (about 25-30, approximate) | Yes (poorly named files) | "Wait for approval" with no duration | Mentions Google CNAME for restricted scopes | **Published and updated dates** | No |
| Composio | Generic custom-auth page (flagged legacy) + generated toolkit reference pages + `composio.dev/auth/<slug>` guides | Screenshot-only sections | No | Gmail "App is blocked" FAQ only | `last_updated: null` on pages opened | One redirect_uri_mismatch callout |

## 1. Nango
- **Pages:** https://nango.dev/docs/api-integrations/google , `.../google/how-to-register-your-own-google-api-oauth-app` , `.../google-shared/google-security-review` , `.../slack/how-to-register-your-own-slack-api-oauth-app` , `.../airtable/how-to-register-your-own-airtable-api-oauth-app`. Old `docs.nango.dev/integrations/all/...` URLs redirect or 404; the live pattern is `/docs/api-integrations/<slug>`. Catalog lists up to 1,058 provider slugs (https://nango.dev/docs/llms.txt); how many have a "register your own" page is UNVERIFIED.
- **Structure:** hub page (Quickstart, guides list, syncs/actions table) plus a hand-written setup page: intro then numbered steps (Google 8, Slack 6, Airtable 5). Text only. Some hubs say Nango has no test app (for example Google).
- **Gets right:** the Google security review page is the most concrete approval documentation anywhere. It gives timing (under 1 week if well prepared; Google's own estimate 4-6 weeks for restricted scopes; first reply 24-48 h; CASA Tier 2 5-20 days; letter of validation up to 1 week), CASA vendor prices "as of August 2025" ($540-720 to $3,000+), demo video, scope justification, domain verification, annual renewal, and the 7-day refresh-token expiry in Testing mode.
- **Missing:** no total-time figure; its two Google pages disagree ("several weeks" versus "under 1 week"); a "Step 7" cross-reference should be Step 8; no difficulty, agent/human split, or redirect_uri_mismatch help; Slack guide ignores directory review; no last-updated date.
- **Borrow:** a "Do I need a review?" decision gate at the top (app verification versus verification plus CASA).

## 2. Merge
- **Pages:** https://docs.merge.dev/merge-agent-handler/admin-setup/add-oauth-credentials , https://help.merge.dev/articles/5683609-lever-how-do-i-enable-my-partner-credentials-for-oauth , https://help.merge.dev/articles/2543780893-sharepoint-onedrive-partnership , https://docs.merge.dev/merge-unified/merge-link/overview (no custom OAuth content). Partner article count UNVERIFIED.
- **Structure:** Agent Handler has one page with a 5-step dashboard flow, a custom-callback flow, and inline walkthroughs for Google (7 steps), Microsoft (6) and Salesforce (5); no screenshots. Unified's help center has one hand-written article per partner with 2-3 screenshots and a relative "last updated" label.
- **Gets right:** different callback URL per product; own-domain note so the consent screen stops showing "merge.dev"; a Lever scope table (about 27 scopes, with purpose); SharePoint publisher verification and the ban on `*.onmicrosoft.com` domains; operational notes (existing connections keep working, Salesforce provisioning about 10 minutes, wrong secret-rotation order breaks refresh).
- **Missing:** no time estimates (Google verification "unspecified"); no difficulty or agent/human split; troubleshooting is prose; Lever gives no partnership wait time.
- **Borrow:** the "what stays working when you swap credentials" before/after note.

## 3. Pipedream
- **Pages:** https://pipedream.com/docs/connect/managed-auth/oauth-clients , https://pipedream.com/docs/apps/oauth-clients , https://pipedream.com/blog/bring-your-own-oauth-clients/ . No per-app setup pages found (absence UNVERIFIED).
- **Structure:** generic 3-step (Connect) and 4-step flows, GitHub as the only example, API reference with TS/Python/cURL tabs, one screenshot.
- **Gets right:** a table of which capabilities need a custom client; API parity with the dashboard; write-only secret; limitations list (no custom-client triggers for Discord, Dropbox, Slack, Zoom); warning that scope changes force reconnect.
- **Missing:** everything else on our checklist.
- **Borrow:** the "official client versus custom client" capability matrix as a decision aid.

## 4. Paragon
- **Pages:** https://docs.useparagon.com/automate/resources/oauth/salesforce , `.../slack` , `.../hubspot` , https://docs.useparagon.com/resources . About 125 integration pages in llms.txt; OAuth page count UNVERIFIED.
- **Structure:** uniform template: "Setup Guide", four credential fields (App Name, Client ID/Key, Secret, Scopes), then 3-4 steps (redirect URL into provider, app into Paragon, credentials in). Short callouts (Salesforce needs REST API access and admin permission; HubSpot legacy versus project apps; Slack needs a per-workflow redirect URL).
- **Gets right:** the best step-level visuals, with animated GIFs on each click path (Salesforce has 5 GIFs).
- **Missing:** time, approval, dates, difficulty, troubleshooting, agent/human split; Slack lacks directory review.
- **Borrow:** a GIF per click path, especially "copy redirect URL then find where to paste it".

## 5. Unified.to
- **Pages:** https://docs.unified.to/guides/how_to_obtain_your_github_oauth2_credentials.md , https://unified.to/blog/how_to_register_a_google_developer_app_and_get_oauth_2_credentials.md (HTML URL 404; `.md` works). About 25-30 guides (approximate, from a summary).
- **Structure:** blog-style per-vendor guides; GitHub 4 steps/4 screenshots, Google 7 steps/3 screenshots (files named "image.png"). Published and updated metadata (Google guide: published 2025-05-29, updated 2026-08-23).
- **Gets right:** dated guides (best freshness signal); Google restricted/sensitive scopes need a CNAME setup via support; consent screen shows "unified.to" until verification finishes; secret shown once; test in Testing status before publishing.
- **Missing:** "Wait for approval and verification" with no duration; no troubleshooting or difficulty; the GitHub guide's visible callback text (`api.unified.to/oauth/code`) disagrees with its hyperlink target (a localhost URL), which is a freshness defect.
- **Borrow:** visible published/updated pair on every guide, plus a before/after of the consent screen branding.

## 6. Composio's own pages
- **Pages:** https://docs.composio.dev/docs/custom-auth-configs , https://docs.composio.dev/docs/using-custom-auth-configuration , https://docs.composio.dev/toolkits/github , https://docs.composio.dev/toolkits/gmail ; plus the `composio.dev/auth/<slug>` guides (github, googleapps, slack) from the auth-model research.
- **Structure:** a generic custom-auth page flagged as legacy, with Google and GitHub subsections that are screenshot-only, a callout on `redirect_uri_mismatch`, and a 5-step auth-config list. Toolkit pages are generated tool references (metadata block, per-tool tables, `last_updated: null`, version string like `20261014_00`). The GitHub toolkit page has no OAuth app setup, only a GitHub Apps FAQ.
- **Gets right:** the Gmail FAQ is the only explanation of "App is blocked" in the set (unverified scopes for your client; fix is remove scopes or get your own app verified; names `gmail.settings.basic`). White-labeling docs describe the 302 proxy.
- **Missing:** no Google verification walkthrough, no time, difficulty, agent/human split; `last_updated` null; Google setup defers to an external guide.
- **Borrow:** surface error-based diagnostics ("App is blocked") inline at the failing step.

## Others (brief)
- **Arcade:** https://docs.arcade.dev/en/references/auth-providers/google shows "Last updated on October 16, 2026" and about 33 provider pages; inline error cases (400 unsupported scopes, 401 `invalid_client`); no time estimates or verification process.
- **Ampersand:** https://docs.ampersand.ai/provider-guides/hubspot , about 200 provider guides, many GIFs and callouts, hard limits spelled out (HubSpot Acceptable Use Policy gate, 25-install cap until Marketplace listing, Super Admin requirement); no time estimates or dates.

## Gaps none of them fill (our product opportunity)
1. **Time-to-approval per provider and scope tier.** Only Nango's Google page gives numbers, and its own pages disagree. Nothing on Meta, Zoom, LinkedIn, Slack directory or HubSpot Marketplace timing.
2. **Total time to first production user.** Every "2 minutes" claim is the test app. No page sums setup, review wait and any paid security assessment.
3. **Evidence and freshness on every claim.** Composio `last_updated` is null, Merge is relative, Nango has none; Unified.to and Arcade are the exceptions, and Unified.to has a contradicting link. No page links claims to provider docs with a verified-on date.
4. **Agent versus human split.** No one marks which steps an agent can do (create project, enable APIs, paste credentials) and which need a human (sign-up, CAPTCHA, demo video, legal contact, CASA vendor).
5. **Difficulty rating.** None rates difficulty, though steps run from 5 (Airtable) to 12 (Ampersand HubSpot) before any review.
6. **Symptom-first troubleshooting.** Only Composio has one redirect_uri_mismatch callout and one "App is blocked" FAQ; none link a symptom to the approval or config cause.
7. **Gating requirements as a checklist.** Privacy policy language, verified domain, demo video, monitored contact email, scope justification appear as prose on Nango's Google page only, nowhere as a checkable list.
8. **Live-state awareness.** Merge and Composio mention what happens to live connections when credentials change; no tool shows it.
