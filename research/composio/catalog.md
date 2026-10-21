# Composio OAuth catalog and candidate guide library

Files: `catalog.csv` (proposed first 100, with tiers), `catalog_all_oauth_toolkits.csv` (all 334 OAuth toolkits). Data date: 2026-10-19.

## 1. Reachability: the full list IS public

No API key is needed. The complete toolkit table is public as raw markdown at https://docs.composio.dev/toolkits.md (rendered at https://docs.composio.dev/toolkits). It lists all 1,608 toolkits with slug, tool and trigger counts, auth schemes, and a "Managed App" column. The HTML version gets truncated by summarizing fetchers; the `.md` URL is complete. https://composio.dev/toolkits is JS-paginated and carries no auth data.

Counts, reproduced independently by the orchestrator with a script over the two pages (see `_verification.md`):

| Bucket | Count | Source |
|---|---|---|
| All toolkits | 1,608 | https://docs.composio.dev/toolkits.md |
| Toolkits with an OAuth scheme (OAUTH2, OAUTH1, DCR_OAUTH, S2S_OAUTH2) | 334 | same table; matches the managed-auth page total |
| Managed (Composio supplies the OAuth app) | 123 | https://docs.composio.dev/toolkits/managed-auth ; table "Managed App = Yes" gives the identical set |
| Bring-your-own (BYO) | 211 | same page; table "Managed App = No" |

The managed-auth page and the main table agree on every one of the 334 slugs. All tags in the catalog are "seen", none inferred.

### Caveats that change how to read "211 BYO"
- **99 of the 211 use DCR_OAUTH** (Dynamic Client Registration), nearly all `*_MCP` remote servers (98 pure DCR plus one DCR+API_KEY). INFERRED, UNCERTAIN: DCR means the client registers itself with the provider's server, so the developer creates no provider-side app and a guide adds little. That leaves about **112 BYO toolkits where a developer really registers an app**.
- **12 of those 112 are client-credentials only (S2S_OAUTH2)**: bitwarden, commerce_layer, cradl_ai, dev_cycle, gagelist, mongodb, mongodb_mcp, paypal, personio, reloadly, servicetitan, wild_apricot. No end-user consent screen; still provider-side registration.
- "Managed" means Composio supplies an app. Toolkits with several auth schemes may be managed for only one of them (check `composio_managed_auth_schemes` per toolkit; needs API key, not read). A managed toolkit can still have a custom auth config for branding, quota and scopes (see `composio-auth-model.md`), so managed apps with heavy provider-side review are legitimate guide topics.
- **Twitter/X** is BYO because Composio removed its managed credentials in February 2026 (per the Twitter toolkit page FAQ, as reported by the catalog subagent; orchestrator has not re-read that FAQ).

### Composio already publishes OAuth setup guides
https://composio.dev/auth lists 46 guides (slugs: airtable, apollo, asana, calendly, canva, confluence, daytona, docusign, dropbox, facebook, fathomai, github, gitlab, gong, googleapps, gorgias, hubspot, instantly, jira, linear, linkedin, monday, notion, outlook, pagerduty, pipedrive, posthog, ramp, rocketlane, salesforce, shopify, slack, slack_custom, snowflake, strava, stripe, supabase, telegram, ticktick, trello, twitter, workday, xero, zendesk, zoho, zoom). The slug list was taken from the page's link list. The guide content was not audited beyond Google, GitHub and Slack (see `composio-auth-model.md`).
Of our proposed 100, **18 overlap** (flagged in the last column). Several are BYO: twitter, pipedrive, shopify, xero, ramp, docusign, snowflake, workday. Implication: for those, compare against Composio's page (does it give time, approval, evidence?) rather than assume a blank field. Per `prior-art.md`, the pages we sampled lack time estimates and approval detail.

## 2. Proposed first 100 apps

Selection: the subagent prioritized BYO non-DCR toolkits that matter to agent builders, plus 17 managed apps whose provider-side review is the hard part (Google, Slack, Meta, LinkedIn and others). 83 are BYO, 17 managed. **Tags, auth schemes and categories are seen in Composio's docs. The difficulty tier, blocker and "(unsure)" notes come from model background knowledge; no provider docs were fetched. Treat every tier as a GUESS** to be verified in the per-provider research (`research/providers/`, handled by a sibling session).

Tier definitions (GUESS): instant (self-serve, works at once), verify-to-scale (works for own/test users, needs verification to go wider), review-required (outside users blocked until provider approves), partner-only (needs partner program or contract).

Tier mix of the 100 (GUESS): 45 verify-to-scale, 28 instant, 19 review-required, 8 partner-only.

Known weaknesses of the list for the orchestrator to decide on:
- 25 rows say "(unsure)" in the blocker; many of the BYO rows are niche (Disqus, Dribbble, Epic Games, Matterport, Kintone, WildApricot). There are only about 100 real BYO app-registration toolkits, so the list necessarily reaches into the long tail.
- Paypal, ServiceTitan, WildApricot are client-credentials only.
- Not in the 100: about 29 obscure BYO non-DCR toolkits (adroll, ahrefs, beeminder, bitwarden, clockify, egnyte, lodgify, neo4j, pinecone, resend, storyblok and others) and all DCR MCP toolkits. See `catalog_all_oauth_toolkits.csv`.
- Popular managed apps not selected (Box, Jira, Asana, Monday, Airtable, Mailchimp, Typeform, Zendesk, Intercom, Reddit, Pinterest, Notion, Linear, OneDrive, SharePoint, Sheets/Docs, Zoho family): managed and mostly low-friction, or already covered by a Composio guide.
- A few apps from the brief's mental list are managed, not BYO: Salesforce, HubSpot, Zoom, LinkedIn, Dropbox, Box, QuickBooks, Stripe, Zendesk, Intercom, Jira, Asana, Monday, Airtable, Mailchimp, Typeform, Facebook, Instagram, Pinterest, YouTube, Reddit, Teams, Outlook, OneDrive, SharePoint, standard Google apps, GitHub, Slack, Notion. Confirmed BYO from that list: Shopify, Xero, DocuSign, Twitter, TikTok, Meta Ads, LinkedIn Ads, Pipedrive, Klaviyo, SurveyMonkey.


## 3. Recommended demo apps (5 to 6)

Goal: cover all four tiers and different blockers, using BYO apps so Composio really requires the guide. Tiers are GUESSES.

1. **WordPress.com (`wordpress_com`, BYO) is the instant baseline.** Self-serve app creation, nothing to wait for. It shows the happy path and makes the other guides' friction visible. Composio has no existing guide for it. Alternative if a more recognisable name is wanted: Vercel or Salesforce Service Cloud (instant, but an org with admin rights is needed).
2. **Google Forms (`googleforms`, BYO) is verify-to-scale with Google OAuth verification as the blocker.** Works for up to 100 test users in Testing mode; sensitive scopes need verification to go beyond. It is the wall agent builders hit most, and the one where Nango's page is the only strong prior art (`prior-art.md`). The same guide covers Google Contacts, Chat, Admin and others.
3. **SharePoint Graph (`sharepoint_graph`, BYO) is verify-to-scale with a different blocker: Entra admin consent and publisher verification.** Works in the developer's own tenant; customers' tenants need admin approval. Shows delegated versus app-only (S2S) choices and carries over to OneNote, To Do, Power BI.
4. **TikTok (`tiktok`, BYO) is review-required.** Outside users are blocked until TikTok reviews the app; URL/domain verification is also needed and unaudited posts stay private. A long, confusing review cycle where a timeline and checklist help most. Alternative: Meta Ads (Marketing API advanced access, app review, business verification).
5. **LinkedIn Ads (`linkedin_ads`, BYO) is partner-only.** Advertising API access must be approved by LinkedIn, so a developer cannot self-serve. The guide is about application strategy and honest expectations, not clicks. Alternatives: Workday or ZoomInfo.
6. **DocuSign (`docusign`, BYO) is the sandbox-to-production blocker.** The developer sandbox works at once; production needs a Go-Live review. Composio already has a DocuSign guide, which makes it the best head-to-head demo of our guide versus an existing one (adds time, approval wait, evidence).

Coverage: instant (1), verify-to-scale (2, 3, 6 depending on how DocuSign is judged), review-required (4), partner-only (5). Blockers: none, Google verification, admin consent, app review, partner approval, go-live review.
All tier assignments need confirming against provider docs before the demo is built.

## 4. Method and what could not be confirmed
- Counts and tags: subagent fetched the table and every one of the 334 OAuth toolkit pages (`https://docs.composio.dev/toolkits/<slug>.md`) and found no mismatch with the table; the orchestrator re-derived the counts independently.
- Not confirmed: scopes per toolkit; which DCR toolkits need no manual app (INFERRED none); the gap between 1,608 toolkits on docs.composio.dev and "1621" on composio.dev/toolkits; the per-scheme managed flag (needs an API key).

## 5. Proposed 100 (also in `catalog.csv`)

| # | App (slug) | Tag | Tier (GUESS) | Likely blocker (GUESS) | Why agent builders care | Composio guide? |
|---|---|---|---|---|---|---|
| 1 | Twitter (`twitter`) | byo | instant | paid API plan or credits required; plan-based access tiers (Composio FAQ) | Post, search and DM on X; core of social/outreach agents | yes |
| 2 | Tiktok (`tiktok`) | byo | review-required | app review for Content Posting/Login Kit; domain/URL verification; unaudited posts private | Publish video/photo posts and read creator data | no |
| 3 | Meta Ads (`metaads`) | byo | review-required | Marketing API advanced access, app review, business verification | Create and report on Facebook/Instagram ad campaigns | no |
| 4 | Linkedin Ads (`linkedin_ads`) | byo | partner-only | Advertising API product access approval by LinkedIn | Campaign management and reporting for B2B advertisers | no |
| 5 | Snapchat (`snapchat`) | byo | instant | Snap Business account needed; ads scopes (unsure) | Snap Ads and Marketing API access | no |
| 6 | Spotify (`spotify`) | byo | verify-to-scale | dev mode user cap (allowlisted users) until extended quota review | Playlist/library control and music agents | no |
| 7 | SoundCloud (`soundcloud`) | byo | review-required | API access must be requested/approved (unsure) | Track/playlist access for audio and creator agents | no |
| 8 | Vimeo (`vimeo`) | byo | verify-to-scale | upload scope needs Vimeo approval | Video upload and management for media agents | no |
| 9 | Dribbble (`dribbble`) | byo | instant | upload scope may need approval (unsure) | Read/post design shots | no |
| 10 | Buffer (`buffer`) | byo | review-required | developer access by request (unsure) | Schedule social posts through Buffer | no |
| 11 | Disqus (`disqus`) | byo | instant | none (unsure) | Comment moderation and community agents | no |
| 12 | Google Admin (`google_admin`) | byo | verify-to-scale | Google OAuth verification for sensitive scopes plus Workspace super-admin consent | Workspace user/group/device admin automation | no |
| 13 | Google Chat (`google_chat`) | byo | verify-to-scale | Google OAuth verification; Chat app configuration; Workspace only | Send messages and manage spaces in Google Chat | no |
| 14 | Googleforms (`googleforms`) | byo | verify-to-scale | Google OAuth verification (sensitive scopes) and 100-user testing cap | Read forms and responses for survey/intake agents | no |
| 15 | Googlecontacts (`googlecontacts`) | byo | verify-to-scale | Google OAuth verification (sensitive scopes) and 100-user testing cap | Read/write contacts for CRM-style agents | no |
| 16 | Google AdSense (`google_adsense`) | byo | verify-to-scale | Google OAuth verification; AdSense account required | Publisher revenue reporting | no |
| 17 | Google Data Studio (`google_data_studio`) | byo | verify-to-scale | Google OAuth verification (sensitive scopes) | Looker Studio report and data source automation | no |
| 18 | Microsoft OneNote (`onenote`) | byo | verify-to-scale | Entra app registration; admin consent and publisher verification for multi-tenant use | Read/write notes via Microsoft Graph | no |
| 19 | Microsoft To Do (`microsoft_todo`) | byo | verify-to-scale | Entra app registration; admin consent for org tenants | Task automation via Microsoft Graph | no |
| 20 | Microsoft Power Bi (`microsoft_power_bi`) | byo | verify-to-scale | Entra app registration; tenant admin consent; Power BI license | Query datasets and reports in Power BI | no |
| 21 | SharePoint Graph (`sharepoint_graph`) | byo | verify-to-scale | admin consent for Sites.* scopes; publisher verification | Site/list/file access via Graph (delegated and app-only) | no |
| 22 | Azure Monitor Activity Log (`azure_monitor_activity_log`) | byo | verify-to-scale | Entra admin consent; Azure subscription RBAC | Azure audit/activity log queries for ops agents | no |
| 23 | Pipedrive (`pipedrive`) | byo | verify-to-scale | OAuth app needs developer sandbox account; Marketplace review to publish publicly | Sales pipeline CRUD for sales agents | yes |
| 24 | Salesforce Service Cloud (`salesforce_service_cloud`) | byo | instant | Salesforce org with External Client App/Connected App creation rights; sandbox/dev org free | Cases and support data in Salesforce | no |
| 25 | Kommo (`kommo`) | byo | verify-to-scale | private integration instant; public integration needs Kommo review | Messenger-centric CRM for SMB sales | no |
| 26 | Follow Up Boss (`follow_up_boss`) | byo | review-required | system/integration registration with Follow Up Boss (unsure) | Real-estate CRM leads and tasks | no |
| 27 | HighLevel Agency (`highlevel_agency`) | byo | verify-to-scale | marketplace app review to list publicly; agency plan needed | GoHighLevel agency-level automation | no |
| 28 | HighLevel Location (`highlevel_location`) | byo | verify-to-scale | marketplace app review to list publicly; agency plan needed | GoHighLevel sub-account automation | no |
| 29 | Zoominfo (`zoominfo`) | byo | partner-only | paid ZoomInfo contract for API access | B2B contact and company enrichment | no |
| 30 | Shopify (`shopify`) | byo | verify-to-scale | public apps need Shopify app review; protected customer data approval; per-store install | Orders, products and customers for commerce agents | yes |
| 31 | Wix (`wix`) | byo | instant | Wix Dev Center app; app listing review only for marketplace (unsure) | Site, store and CRM data for Wix merchants | no |
| 32 | Webflow (`webflow`) | byo | verify-to-scale | workspace-scoped app instant; Marketplace review to distribute | CMS and e-commerce updates for site agents | no |
| 33 | WordPress.com (`wordpress_com`) | byo | instant | none | Publish posts and manage WordPress.com sites | no |
| 34 | Lightspeed Retail X-Series (`lightspeed`) | byo | review-required | developer program registration (unsure) | Retail POS, inventory and sales | no |
| 35 | Clover (`clover`) | byo | verify-to-scale | sandbox instant; production app needs Clover review | Merchant POS orders and payments | no |
| 36 | Xero (`xero`) | byo | verify-to-scale | free tier capped at 25 connected orgs until app certification; paid API tiers | Accounting automation for SMBs | yes |
| 37 | Ramp (`ramp`) | byo | verify-to-scale | developer app approval for third-party access (unsure) | Spend management, cards and bills | yes |
| 38 | Brex (`brex`) | byo | partner-only | Brex partner/API OAuth enablement (unsure) | Corporate cards and expense data | no |
| 39 | Razorpay (`razorpay`) | byo | review-required | partner program approval and live-mode KYC | Indian payments, partner OAuth for merchants | no |
| 40 | Netsuite (`netsuite`) | byo | instant | NetSuite account with integration-record admin rights; paid ERP | ERP records and SuiteQL for finance agents | no |
| 41 | Coupa (`coupa`) | byo | instant | requires customer Coupa instance admin to create OAuth client; enterprise license | Procurement and spend data | no |
| 42 | Alpaca (`alpaca`) | byo | instant | funded or paper account; trading disclosures | Brokerage/trading API OAuth for fintech agents | no |
| 43 | Paypal (`paypal`) | byo | partner-only | PayPal Partner/third-party permissions needs approval; live app review | Payments and invoicing (client-credentials) | no |
| 44 | DocuSign (`docusign`) | byo | verify-to-scale | Go-Live review (successful sandbox API calls) before production | Send and track eSignature envelopes | yes |
| 45 | Dropbox Sign (`dropbox_sign`) | byo | verify-to-scale | test mode instant; production app approval and paid plan | E-signature requests | no |
| 46 | SignNow (`sign_now`) | byo | instant | developer account; paid plan for production (unsure) | E-signature workflows | no |
| 47 | Klaviyo (`klaviyo`) | byo | verify-to-scale | public OAuth apps require Klaviyo app review (unsure) | Email/SMS marketing and customer profiles | no |
| 48 | Constant Contact (`constant_contact`) | byo | instant | none (free V3 API app) | Email marketing lists and campaigns | no |
| 49 | Brevo (`brevo`) | byo | review-required | OAuth available to partner integrations (unsure) | Email/SMS marketing and CRM | no |
| 50 | AWeber (`aweber`) | byo | verify-to-scale | apps start in dev; production needs AWeber approval (unsure) | Newsletter lists and subscribers | no |
| 51 | GetResponse (`getresponse`) | byo | instant | paid plan for API; marketplace review optional | Email marketing automation | no |
| 52 | SurveyMonkey (`survey_monkey`) | byo | verify-to-scale | draft apps limited to developer's own account until review | Survey creation and responses | no |
| 53 | Tally (`tally`) | byo | instant | none (unsure) | Form builder submissions | no |
| 54 | Bitly (`bitly`) | byo | instant | none | Link shortening and analytics | no |
| 55 | Help Scout (`help_scout`) | byo | instant | Marketplace review only to publish | Support mailbox conversations | no |
| 56 | ServiceNow (`servicenow`) | byo | instant | instance admin to create OAuth endpoint; free PDI instance | ITSM tickets and workflows | no |
| 57 | Aircall (`aircall`) | byo | verify-to-scale | public apps reviewed by Aircall (unsure) | Cloud phone call data and actions | no |
| 58 | Datadog (`datadog`) | byo | review-required | OAuth client registration with Datadog (unsure) | Metrics, monitors and incidents | no |
| 59 | Snowflake (`snowflake`) | byo | instant | ACCOUNTADMIN to create security integration | Warehouse SQL for data agents | yes |
| 60 | Databricks (`databricks`) | byo | instant | account admin to create OAuth app connection | Lakehouse jobs and SQL | no |
| 61 | Vercel (`vercel`) | byo | instant | none; marketplace integrations require review | Deployments and projects for devops agents | no |
| 62 | DigitalOcean (`digital_ocean`) | byo | instant | none | Droplets and apps management | no |
| 63 | Railway (`railway`) | byo | instant | workspace-level OAuth app; none | Deploy and manage services | no |
| 64 | PlanetScale (`planetscale`) | byo | instant | org-level OAuth app (unsure) | Database branches and deploys | no |
| 65 | LaunchDarkly (`launch_darkly`) | byo | verify-to-scale | OAuth client creation via API/partner onboarding (unsure) | Feature flag management | no |
| 66 | Gusto (`gusto`) | byo | review-required | production access requires Gusto app review/partner approval | Payroll and HR data | no |
| 67 | BambooHR (`bamboohr`) | byo | review-required | partner application to get OAuth app (unsure) | HR employee data | no |
| 68 | Workday (`workday`) | byo | partner-only | tenant admin registers API client; enterprise contract | HRIS and finance tenant data | yes |
| 69 | Lever (`lever`) | byo | partner-only | OAuth via Lever partner program (unsure) | Recruiting pipeline | no |
| 70 | Workable (`workable`) | byo | review-required | partner access (unsure) | Recruiting pipeline | no |
| 71 | Recruitee (`recruitee`) | byo | review-required | partner/OAuth app approval (unsure) | Applicant tracking | no |
| 72 | Canvas (`canvas`) | byo | review-required | institution admin must issue developer key; no global app | LMS courses and assignments | no |
| 73 | Blackboard (`blackboard`) | byo | partner-only | Anthology developer registration plus admin allow-listing | LMS courses and grades | no |
| 74 | D2L Brightspace (`d2lbrightspace`) | byo | review-required | per-institution admin registers OAuth app | LMS courses and grades | no |
| 75 | Zoom Team Chat (`zoom_chat`) | byo | verify-to-scale | Zoom Marketplace review for publishing; admin-managed scopes | Team Chat messaging | no |
| 76 | Clio Manage (`clio_manage`) | byo | verify-to-scale | developer app; production review (unsure) | Legal practice matters and billing | no |
| 77 | Jobber (`jobber`) | byo | verify-to-scale | test developer account; app review for production | Field service jobs and clients | no |
| 78 | ServiceTitan (`servicetitan`) | byo | partner-only | developer portal onboarding with ServiceTitan; tenant integration setup | Field-service data | no |
| 79 | Whop (`whop`) | byo | instant | none | Digital product communities | no |
| 80 | Epic Games (`epic_games`) | byo | review-required | Epic Developer Portal product approval | Game account/entitlement data | no |
| 81 | Matterport (`matterport`) | byo | verify-to-scale | developer account; approval for production (unsure) | 3D space data | no |
| 82 | Kintone REST (`kintone_rest`) | byo | instant | Kintone admin creates OAuth client | Low-code business apps records | no |
| 83 | WildApricot (`wild_apricot`) | byo | instant | admin creates authorized application | Membership management | no |
| 84 | Gmail (`gmail`) | managed | verify-to-scale | Google OAuth verification plus CASA security assessment for restricted scopes | Email read/send agent core; restricted scopes | no |
| 85 | Google Drive (`googledrive`) | managed | verify-to-scale | Google OAuth verification; restricted scopes need security assessment | Files and docs access for RAG agents | no |
| 86 | Google Calendar (`googlecalendar`) | managed | verify-to-scale | Google OAuth verification (sensitive scopes); testing cap 100 users | Scheduling agents | no |
| 87 | Slack (`slack`) | managed | verify-to-scale | public distribution / Marketplace directory review; rate limits for non-Marketplace apps | Messaging agents and bots | yes |
| 88 | GitHub (`github`) | managed | instant | none (GitHub App vs OAuth App choice) | Repo and PR automation | yes |
| 89 | LinkedIn (`linkedin`) | managed | review-required | products (Share on LinkedIn, Marketing) require approval; company page verification | Profile, share and Pages posting | yes |
| 90 | Facebook (`facebook`) | managed | review-required | Meta App Review for permissions, business verification | Pages and Graph API for social agents | yes |
| 91 | Instagram (`instagram`) | managed | review-required | Meta App Review, business verification, professional account | Instagram professional account publishing/insights | no |
| 92 | YouTube (`youtube`) | managed | verify-to-scale | Google OAuth verification; API quota audit | Upload and manage channel content | no |
| 93 | Zoom (`zoom`) | managed | verify-to-scale | Zoom Marketplace review to go beyond own account | Meetings and recordings | yes |
| 94 | Salesforce (`salesforce`) | managed | instant | Connected/External Client App in org; none for own org | CRM objects for sales agents | yes |
| 95 | HubSpot (`hubspot`) | managed | verify-to-scale | public app listing review (private apps instant) | CRM, marketing and CMS | yes |
| 96 | Microsoft Teams (`microsoft_teams`) | managed | verify-to-scale | admin consent for tenant-wide scopes; publisher verification | Chat and channel messaging via Graph | no |
| 97 | Outlook (`outlook`) | managed | verify-to-scale | admin consent; publisher verification | Mail and calendar via Graph | yes |
| 98 | QuickBooks (`quickbooks`) | managed | verify-to-scale | dev sandbox instant; production keys require app assessment | Accounting for SMBs | no |
| 99 | Stripe (`stripe`) | managed | verify-to-scale | Connect platform profile; live mode activation; Connect review | Payments and Connect platform OAuth | yes |
| 100 | Dropbox (`dropbox`) | managed | verify-to-scale | dev apps capped at 500 users until production approval | File storage | yes |
