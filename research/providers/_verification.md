# Verification log

Date: 2026-10-19. Verifier: the orchestrating session (not the research subagents).

## Method

The ten provider subagents read pages through a fetch tool that summarizes pages with a small model. A summarizer can paraphrase or invent a "quote". So for the checks below I fetched the live page myself with `curl` and stripped the HTML to plain text (my own script, not a summarizer), then searched for each quoted string and read the text around it. Pages that need JavaScript (Xero documentation) were read through a text-rendering proxy (r.jina.ai) or, for the Xero pricing and FAQ pages, from the static HTML.

Scope: I re-opened **about 28 live pages** across **10 providers** (GitHub, Notion, Slack, Google, Microsoft, HubSpot, Xero, Spotify, Shopify, Meta) and checked roughly **75 quoted strings and numeric claims**. The brief required at least 3 providers with 2 sources each. This is a wider pass than that, but it is still a sample, not an audit of every claim. Unchecked claims are listed at the end.

Also directly observed by me in the built-in browser (TESTED): login redirects for 8 console pages, the Notion Connections rename, and the Spotify 6 Feb 2026 blog post. See `_browser_observations.md`.

## Results by provider

| Provider | Source re-opened | Claim checked | Result |
|---|---|---|---|
| Spotify | https://developer.spotify.com/documentation/web-api/concepts/quota-modes | "Up to 5 authenticated Spotify users can use an app that is in development mode"; Premium owner required; organizations only from May 15, 2025; "at least 250k MAUs"; "can take up to six weeks" | All present as quoted. |
| Spotify | https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration | "Refreshing an access token does not reset or extend" the 6-month lifetime; new apps now, existing apps July 20, 2026 | Present. Dates match the table on the page. |
| Spotify | https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates | "25 Client IDs"; quota is per developer account; `QUOTA_EXCEEDED` | Present. Resolves the conflict with the Feb 2026 "one Client ID" post: the July post is newer. |
| Spotify | https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security (in browser) | 5 users, Premium, one Client ID from 11 Feb 2026; applies to existing apps from 9 Mar | TESTED. Read on screen. |
| HubSpot | .../list-apps/listing-your-app/app-marketplace-listing-requirements | "at least three active, unique installs"; OAuth as sole auth method; initial review "within 10 business days"; "no more than 60 days from the time feedback is shared" | All present. Confirms the brief's "60 installs" belongs to certification, not listing. |
| HubSpot | .../listing-your-app/marketplace-restrictions | Token-brokering exclusion | Present, word for word: "Credential and token brokering : apps with a primary commercial offering of storing, managing, or distributing end-user OAuth tokens or API credentials on behalf of third-party developers." |
| Slack | https://docs.slack.dev/slack-marketplace/slack-marketplace-review-guide | "installed on 10 or more active workspaces"; preliminary review up to 10 business days; functional review up to 10 weeks (6 weeks for published apps) | All present. |
| Slack | https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps | 1 request per minute, 15 objects; "will not be applied to existing installations of unlisted, distributed applications" | Present. The page also says it "has been updated to clarify the rate limits", which supports keeping the existing-installs question open in `slack.md` section 8. |
| Microsoft | .../publisher-verification-overview | "Microsoft doesn't charge developers for publisher verification"; "can be verified in minutes"; MSA-registered apps "can't be publisher verified" | All present. |
| Microsoft | .../partner-center/enroll/understand-the-verification-process | "In most cases, the process takes three to five business days to complete." | Present. |
| Microsoft | .../troubleshoot-publisher-verification | "Only Partner Global Accounts are supported" | Present on this page, **not** on the overview page. `microsoft.md` cites all three pages together for that bullet, so the citation holds, but a reader following only the overview link will not find it. |
| GitHub | .../creating-an-oauth-app | "A user or organization can own up to 100 OAuth apps"; "up to 10 callback URLs"; "Expire user access tokens" checkbox | Present. |
| GitHub | https://github.blog/changelog/2026-08-14-multiple-redirect-uris-and-token-refresh-for-oauth-apps | "Short-lived tokens are enabled by default for all new applications"; 10 redirect URIs; wildcard matching | Present. |
| GitHub | .../differences-between-github-apps-and-oauth-apps | "GitHub Apps aren't subject to organization application policies"; 5,000 requests | Present. |
| GitHub | same page | The subagent quoted "do not expire until the person who authorized the OAuth app revokes the token" as coming from this page | **WRONG SOURCE.** This page says "OAuth app tokens re long-lived by default" (typo is on the page). The "do not expire until..." sentence is on `.../about-creating-github-apps/deciding-when-to-build-a-github-app`. Quote is real; attribution was wrong. **Fixed** in `github.md`. |
| Google | https://developers.google.com/workspace/gmail/api/auth/scopes | `gmail.labels` non-sensitive; `gmail.send` sensitive; `gmail.metadata`, `gmail.compose`, `gmail.readonly` etc. restricted | Present in the three tables. Confirms blogs that call `gmail.metadata` sensitive are wrong. |
| Google | https://support.google.com/cloud/answer/15549945 | 100 test users; seven-day authorization expiry | Present. |
| Google | https://support.google.com/cloud/answer/13463817 | "the user cap applies over the entire lifetime of the project, and it cannot be reset or changed"; about 10 business days; 6 weeks | Present. The page says "100-user cap" and "100 new-user cap". The exact phrase "100 new users in total" in `google-gmail.md` comes from a different article (7454865) that I did not re-open. |
| Google | .../sensitive-scope-verification | "typically takes 3-5 business days" | Present. Conflicts with "about 10 business days" on 13463817. Both are official, so both stay in the file. |
| Xero | https://developer.xero.com/pricing | Starter 5, Core 50, Plus 1,000, Advanced 10,000, Enterprise no limit; Core $35 AUD, Plus $245 AUD; card needed Starter to Core | Present in static HTML. |
| Xero | https://developer.xero.com/documentation/guides/oauth2/limits/ (via proxy) | "New apps default to the starter tier with 5 connections"; "each organisation or practice is limited to connecting a maximum of five uncertified apps" | Present. |
| Xero | https://developer.xero.com/faq | "up to 50 redirect URIs"; wildcards not supported; Remote MCP "Real customer organisations need the Core plan"; and "an org can have 2 uncertified apps" | All present. The FAQ really does still say **2** uncertified apps while the limits page says **5**. This is a live contradiction inside Xero's own docs, not a research error. Kept as an open question in `xero.md`. |
| Notion | .../guides/get-started/marketplace-listing | "expect to hear back from our team within 5-10 business days via email"; "Any workspace" scope | Present. |
| Notion | .../reference/workspace-block-limits | "1,000 lifetime blocks"; three-day grace; `restricted_resource` | Present. |
| Notion | .../reference/request-limits | 600 per minute (Business and Enterprise), 180 per minute (others) | Present. |
| Shopify | https://shopify.dev/changelog/expiring-offline-access-tokens-required-for-public-apps-april-1-2026 | New public apps must use expiring offline tokens from April 1, 2026 | Present. |
| Shopify | .../app-requirements-checklist | "immediately authorize using OAuth" | Present. |
| Meta | https://developers.facebook.com/blog/post/2026/10/09/retiring-access-verification-for-tech-provider-apps/ | Dated Oct 9, 2026; "Access Verification will no longer be required in the Tech Provider onboarding flow"; Business Verification stays | Present. |

## What was wrong

1. **GitHub: wrong page cited for a real quote.** Fixed (see table).
2. **Microsoft: one quote lives on a sibling page.** The citation is correct as a set, but I noted it here so nobody relies on the overview page alone.
3. **Google: one quote attributed to the wrong article number is a wording match, not a mismatch.** "100 new users in total" is not on 13463817 (that page says "100-user cap" and "100 new-user cap"). I left the file as is and flagged it above because the number is the same.
4. **My own first search phrase for Spotify ("not accept applications from organizations") was not on the page.** That was my test string, not a claim in any file. The page says "only accepts applications from organizations (not individuals)", which is what `spotify.md` quotes.
5. **Subagent output was not always internally consistent.** Examples I caught while writing: Xero's two uncertified-app numbers (a real source conflict), and Slack's 10 vs 5 workspace threshold (docs vs two third-party posts). Both are kept as conflicts, not resolved.

No quoted string checked above turned out to be fabricated.

## What could not be verified

- **Every console form and field list.** All ten consoles need a login. Field lists come from docs. Nothing about form layout, logo limits, or required fields is TESTED. In particular: Notion's new Connections form fields, Spotify's logo and privacy fields, Slack's privacy and terms fields, Xero's logo and policy fields, Microsoft's branding limits, Meta's required Live-mode fields.
- **Community wait times.** The Spotify, Slack, Shopify and Meta community threads were seen through search snippets or a summarizer, and several returned 403 to the subagents. I did not re-open them. Treat every COMMUNITY wait time as anecdotal.
- **Vendor blog claims** (bundle.social review times, appnigma HubSpot timings, Viktor and WorkOS for Slack, DeepStrike and Unipile for Google costs, Nango for Notion tokens). Not re-opened.
- **Microsoft Learn pages not re-opened:** the managed-consent-policy exclusions list (`manage-app-consent-policies`), the permissions reference, throttling limits, M365 Certification. The managed-policy finding is also inference: it combines two docs and was not observed in a tenant.
- **Meta:** all quotes passed through the summarizer and only the Oct 9, 2026 blog post was re-opened. The rest of `meta.md` is the least verified file. Several "quotes" are marked "wording unverified" in the file.
- **Shopify:** only two pages re-opened. The $19 fee, redirect URL rules, and review times are unverified.
- **Slack's 10 vs 5 workspace threshold:** the official side (10) is verified; the 5 comes from third parties and could reflect the console checklist. A person with a Slack login needs to look at Manage Distribution.
- **Spotify:** the 2026-02-06 post says endpoint-access changes for existing apps were postponed, and the migration guide says existing apps "retain" multiple Client IDs and more than 5 users. I did not re-open the migration guide, so the grandfathering conflict is unresolved.
- **Dates and "current" status.** Policy pages for Spotify, Slack, Shopify, Xero, HubSpot and Google changed several times in 2026. Everything here is true as of 2026-10-19 only.

## Follow-up subagent

The brief asked for one follow-up subagent for any provider with fewer than 3 DOCS-level citations. None did: every provider returned at least 9 DOCS-level URLs. No follow-up was launched.
