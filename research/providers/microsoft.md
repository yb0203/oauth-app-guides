# Microsoft Entra ID / Microsoft Graph (Outlook)

- Researched: 2026-10-19
- Tier: **verify-to-scale**. Registering and using an app in your own tenant is instant. Reaching other organizations is gated by each customer tenant's consent policy, and publisher verification helps.
- Effort: about 6 to 12 active hours including publisher verification. 1 to 3 more hours if you start with no tenant. Attestation adds 1 to 3 hours. M365 Certification adds weeks and cost.
- Calendar time: same day for your own tenant. About 1 to 3 weeks for a verified publisher (official 3 to 5 business days for Partner Center vetting, plus reply cycles; the slippage allowance is our estimate). Per customer: 0 to several days waiting on that customer's admin.
- Confidence: medium. Docs are rich and dated. Key interactions (verification vs managed consent policy) are inference, not observed.

Evidence labels: TESTED, DOCS, COMMUNITY, UNCERTAIN. The research tool read some pages through a summarizer; those are flagged.

## Directly observed (TESTED, 2026-10-19)

`entra.microsoft.com` App registrations URL redirected to `login.microsoftonline.com/organizations/oauth2/v2.0/authorize?...` showing "Sign in to continue to Microsoft Azure" and "No account? Create one!". The `/organizations` endpoint in the URL means a work or school account is expected. TESTED.

## 1. Where and how the app is created

**Console:** https://entra.microsoft.com, Entra ID, App registrations, New registration. DOCS: "Browse to **Entra ID** > **App registrations** and select **New registration**" (https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app). Also reachable from portal.azure.com (paraphrase).

**Prerequisites**
- Role: at least Application Developer in the tenant (DOCS, paraphrase).
- Tenant and subscription: the quickstart lists "An Azure account that has an active subscription." See section 8 for doubt.
- A tenant is mandatory (DOCS, https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant, paraphrase).
- DOCS: "Only paid customers can create a new Workforce tenant in Microsoft Entra ID." (https://learn.microsoft.com/en-us/entra/fundamentals/create-new-tenant)
- **Microsoft 365 Developer Program sandbox is no longer open to everyone** (DOCS, https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-faq, dated 2026-09-04). Eligibility paths: Visual Studio Professional or Enterprise subscribers; ISV Success or eligible Cloud Partner Program tiers; Premier or Unified Support customers. It gives 25 licenses (24 test users plus an admin) with sample mail and calendar data. DOCS: "Linking a valid billing account is mandatory during sandbox setup and can't be bypassed." It needs a Microsoft Customer Agreement billing account with an Azure subscription. DOCS: "Microsoft may require tenants to be recreated every 90 days."
- 2FA for registration: not found. MFA is required for publisher verification.

**Steps** (DOCS, quickstart-register-app)
1. Sign in at entra.microsoft.com as Application Developer or higher; switch tenants if needed.
2. Entra ID, App registrations, New registration.
3. Name (user-visible, duplicates allowed).
4. Supported account types.
5. Optional redirect URI by platform; can be added later under Authentication (https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-redirect-uri).
6. Register, then record the Application (client) ID and Directory (tenant) ID.
7. API permissions: add Microsoft Graph delegated permissions (Mail.Read, Mail.Send, Calendars.ReadWrite, offline_access). Add all of them to the registration so admin consent and `/.default` work.
8. Certificates and secrets: create a secret or certificate.
9. Branding and properties: logo, home page URL, terms URL, privacy URL, publisher domain. The field list comes from search snippets and third-party guides; the official branding how-to returned 404. Logo size limits: UNCERTAIN.
10. Optional publisher verification.

**Supported account types** (exact labels): "Single tenant only - <your tenant>"; "Multiple Entra ID tenants"; "Any Entra ID Tenant + Personal Microsoft accounts"; "Personal accounts only." DOCS: "New app registrations are hidden to users by default." (My Apps page only.)

**Redirect URI rules** (DOCS, https://learn.microsoft.com/en-us/entra/identity-platform/reply-url)

| Rule | Detail |
|---|---|
| Scheme | `https` required; `http` only for localhost |
| Max count | 256 for work/school only, 100 if personal accounts included. DOCS: "The maximum number of redirect URIs can't be raised for security reasons." |
| Length | maximum 256 characters each |
| Case | case-sensitive (paraphrase) |
| Special characters | `! $ ' ( ) , ;` unsupported; no internationalized domains |
| Wildcards | work/school-only apps, manifest editor only; not with personal accounts; discouraged |
| Query strings | work/school-only apps only |
| Localhost | port ignored when matching. DOCS: "The IPv6 loopback address (`[::1]`) isn't currently supported." |
| 127.0.0.1 over http | portal text box rejects; edit `replyUrlsWithType` in the manifest |
| Multitenant root domain | if publisher domain is null, all redirect URIs must share one root domain, with exceptions for localhost, custom schemes, single-tenant (DOCS, https://learn.microsoft.com/en-us/entra/identity-platform/howto-configure-publisher-domain) |
| Platform types | Web, SPA, iOS/macOS, Android, Mobile and desktop. A `spa` redirect gives 24-hour refresh tokens |

Requested-permission limits: 400 for work/school audiences, 30 if personal accounts are included (DOCS, https://learn.microsoft.com/en-us/graph/permissions-overview).

## 2. What works immediately vs what is gated

- No review gate to create or use the app (absence of any review step in the quickstart). No documented dev-mode user cap. Hidden or undocumented abuse blocking: UNCERTAIN.
- Your own tenant works fully.
- **Other tenants are gated by their consent policy:**
  1. "Unverified" label on the consent prompt if the publisher is not verified (DOCS, https://learn.microsoft.com/en-us/entra/identity-platform/application-consent-experience).
  2. Risk-based step-up consent: users cannot consent to most unverified multitenant apps registered after Nov 8, 2020 that ask for more than basic sign-in (paraphrase, https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview).
  3. Application permissions for Mail and Calendars need admin consent. Delegated Mail.Read, Mail.ReadWrite, Mail.Send, Calendars.Read, Calendars.ReadWrite are listed as not needing admin consent (DOCS, https://learn.microsoft.com/en-us/graph/permissions-reference, read through a summarizer; verify in the live table).
  4. **Microsoft-managed default consent policy** (default for new tenants) blocks end-user consent for many delegated permissions. DOCS: "This is also the default for a new tenant." Excluded scopes include Mail.Read, Mail.ReadWrite, Mail.ReadBasic, the shared variants, Calendars.Read/ReadWrite and shared variants, MailboxSettings, Contacts.ReadWrite, Tasks.*, People.Read, Files and Sites .All, Chat, OnlineMeetings, and Exchange EAS/EWS/IMAP/POP AccessAsUser. Mail.Send is not in the exclusions listed. A built-in "Mail client policy" exempts a fixed list of mail clients (Apple Mail, Spark, eM Client, Thunderbird, Android mail), not you. https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-app-consent-policies (ms.date 2026-01-22, updated 2026-08-28). COMMUNITY (search snippet only, fetch 403): the list grew in late 2025 and Message Center MC1304287 (Jun/Jul 2026) reportedly added Contacts, Tasks, People. Unverified.
- Admin consent workflow: if enabled, users can request approval (DOCS, https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview, paraphrase).
- Rate limits are not tiered by approval. Outlook limits are per app ID and mailbox pair (section 4).
- Test users: the Developer Program sandbox gives 24 (DOCS, FAQ).

## 3. Approval / review path

Nothing is mandatory to call Graph mail APIs. Practical triggers are customer tenants restricting consent and enterprise security reviews. Publisher verification does not lift the Mail.Read exclusion in the managed policy (paraphrase of the manage-app-consent-policies page); the "Allow user consent for apps from verified publishers" setting does depend on it.

**1. Publisher verification (free)**
- The org needs a verified Microsoft AI Cloud Partner Program (CPP) account. Enter the Partner One ID of its Partner Global Account in Branding and properties, "Add Partner ID to verify publisher".
- Requirements: app registered with a work or school account (DOCS: "Apps that are registered by using a Microsoft account can't be publisher verified."); tenant associated with the Partner Global Account; publisher domain set and not `*.onmicrosoft.com`; CPP verification email domain matches the publisher domain; Application Admin or Cloud Application Admin plus CPP Partner Admin or Accounts Admin; MFA in the same session.
- Not supported: national clouds, B2C tenants, location-level Partner One IDs ("Only Partner Global Accounts are supported.").
- DOCS: "Microsoft doesn't charge developers for publisher verification." DOCS: "Developers who have already met these requirements can be verified in minutes."
- Sources: https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview, .../mark-app-as-publisher-verified, .../troubleshoot-publisher-verification.

**2. Microsoft 365 Publisher Attestation:** a self-assessment of 80+ factors in Partner Center; Microsoft does not independently verify answers. DOCS: "Most attestations can be completed in one hour or less"; "Approved attestations remain valid for one year from the submission date." No review SLA stated. https://learn.microsoft.com/en-us/microsoft-365-app-certification/docs/attestation

**3. Microsoft 365 Certification:** third-party audit through Claranet at ISV expense (amount not stated; UNCERTAIN). Needs publisher verification and attestation first. 14-day documentation stage, 60 days for evidence (extension up to 60 more days; developer deadlines, not a Microsoft SLA). Annual recertification. Pen test mandatory for apps connecting to non-Microsoft-hosted services. Graph least-privilege validation is part of review. https://learn.microsoft.com/en-us/microsoft-365-app-certification/docs/certification (updated 2026-09-22)

- **Official wait:** DOCS: "In most cases, the process takes three to five business days to complete." (Partner Center vetting; checks email, identity via government ID, employment, business formation documents; https://learn.microsoft.com/en-us/partner-center/enroll/understand-the-verification-process, ms.date 2026-07-27). Verification step itself takes "a few minutes" (paraphrase). Attestation and certification: no Microsoft turnaround stated.
- **Community wait:** no reliable timings found. Threads describe blockers (empty Legal Info tab, wrong role, tenant not associated with CPP account; sole traders reportedly unsupported, from a snippet). COMMUNITY: https://learn.microsoft.com/en-us/answers/questions/1643712/assistance-needed-with-adding-program-and-obtainin (2024-04-04/05, unresolved).
- **Cost:** verification free. Basic CPP enrollment fee not stated in fetched docs (UNCERTAIN). Paid CPP packages $350 to $4,875 exist and are not required, as far as determined. ISV Success free the first year, $1,550 from the second (DOCS, https://learn.microsoft.com/en-us/partner-center/membership/mpn-overview, updated 2026-06-25).
- **Error causes** (DOCS, troubleshoot page): MPNAccountNotFoundOrNoAccess, MPNGlobalAccountNotFound (location ID used), MPNAccountNotVetted, PublisherDomainMismatch, NoPublisherDomainOnApplication, MSANotSupported, InteractionRequired (no MFA), UserUnableToAddPublisher, UnableToAddPublisher.
- **Re-review:** attestation and certification annual. Publisher verification has no documented renewal (UNCERTAIN).

## 4. Gotchas

- **Refresh tokens:** DOCS: 90 days "for all other scenarios", 24 hours for single-page apps. They roll on use; discard the old one. Lifetimes have not been configurable since Jan 30, 2021. Returned only if `offline_access` was requested. Revocation by admin reset; confidential-client tokens survive a user password change. https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens (ms.date 2025-11-05), .../configurable-token-lifetimes, .../v2-oauth2-auth-code-flow.
- **Access tokens:** "a random value ranging between 60-90 minutes"; up to 28 hours with Continuous Access Evaluation. Token-lifetime policies unsupported for audiences including personal accounts.
- **Endpoints:** `/common`, `/organizations`, `/consumers` and tenant IDs. For admin consent, DOCS: "Do not use 'common'". Endpoint `https://login.microsoftonline.com/{tenant}/v2.0/adminconsent?client_id=...&scope=...&redirect_uri=...`; application permissions need `/.default` (https://learn.microsoft.com/en-us/entra/identity-platform/v2-admin-consent).
- **Per tenant:** the app becomes a service principal in each customer tenant. If "user assignment required" is on, an admin must consent (paraphrase, configure-user-consent).
- **Credentials:** DOCS: "Client secret lifetime is limited to two years (24 months) or less." Microsoft recommends under 12 months and certificates in production. The secret value is shown once. An expired secret is a silent outage (https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials).
- **Unverified multitenant:** COMMUNITY (Chatwoot vendor doc, undated, https://developers.chatwoot.com/self-hosted/configuration/features/email-channel/azure-app-setup.md): the integration will not work for other tenants until publisher verification. An admin in the other org can still consent while end users cannot (Tech Community, snippet only).
- **Throttling (Outlook)** (DOCS, https://learn.microsoft.com/en-us/graph/throttling-limits, updated 2026-09-17): per app ID and mailbox pair, "10,000 API requests in a 10-minute period", "Four concurrent requests", "150 megabytes (MB) upload (PATCH, POST, PUT) in a 5-minute period". A global 130,000 per 10 seconds figure came from a summarizer: verify. Throttled calls return 429.
- Application permissions are all-mailbox by default; scoping with Exchange RBAC for Applications was not researched (UNCERTAIN).
- Portal quirks: never add redirect URIs to the service principal. DOCS: "Once created, you can't move the application object between different tenants."
- Personal-account audience trade-offs: 100 redirect URIs, 30 permissions, no wildcards or query strings, no token-lifetime policy.
- Recent changes: Developer Program restricted in 2024; FAQ (2026-09-04) says commerce-enabled sandboxes shipped from July 2026; managed consent policy now excludes Mail and Calendar delegated permissions; Partner Center benefits restructured 2025-01-22.

## 5. Agent vs human split

| Step | Agent can do? | Human must do? | Why |
|---|---|---|---|
| Research rules and choose permissions | Yes | Approve | Public docs; risk decision |
| Get a tenant (Azure free account or Developer Program) | No | Yes | Sign-up, card or billing, identity, eligibility |
| Fill registration fields | Yes, in a supervised signed-in session | Sign in and consent | Needs the user's session |
| Draft privacy policy, terms, scope justification | Yes | Review and publish | Legal accuracy, hosting |
| Host `.well-known/microsoft-identity-association.json` | Generate the file | Domain DNS or hosting access | Domain control |
| CPP enrollment and business verification | No | Yes | Legal entity, government ID, domain documents |
| Run publisher verification with MFA | No | Yes | MFA and role |
| Create secret and store it | Partly | Yes | Value shown once |
| Admin consent at a customer tenant | No | Customer's tenant admin | Only that admin can grant |
| Attestation questionnaire | Draft answers | Sign and submit | Legal representation |
| M365 Certification evidence, audit payment, pen test | Prepare docs | Yes | Auditor, payment, production access |
| Waiting on vetting | No | Yes | Calendar time |

## 6. Difficulty tier and estimate

**Tier: verify-to-scale.** Estimates at the top of this file.

## 7. Sources

All accessed 2026-10-19. Label DOCS unless noted.

| URL | Supports | Notes |
|---|---|---|
| entra.microsoft.com (redirect) | Login required | TESTED |
| https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app | Steps, account types, roles | ms.date 2026-05-14 |
| https://learn.microsoft.com/en-us/entra/identity-platform/reply-url | Redirect rules | ms.date 2025-05-14 |
| https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-redirect-uri | Redirect steps | |
| https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials | Secret lifetimes | |
| https://learn.microsoft.com/en-us/entra/fundamentals/create-new-tenant | Paid customers only | ms.date 2026-07-29 |
| https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant | Tenant required | |
| https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-faq | Sandbox eligibility | dated 2026-09-04, fast-changing |
| https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview | Verification | ms.date 2024-08-13 |
| https://learn.microsoft.com/en-us/entra/identity-platform/mark-app-as-publisher-verified | Steps | |
| https://learn.microsoft.com/en-us/entra/identity-platform/troubleshoot-publisher-verification | Errors | |
| https://learn.microsoft.com/en-us/entra/identity-platform/howto-configure-publisher-domain | Publisher domain | ms.date 2023-04-27 |
| https://learn.microsoft.com/en-us/partner-center/enroll/understand-the-verification-process | 3 to 5 business days | ms.date 2026-07-27 |
| https://learn.microsoft.com/en-us/partner-center/membership/mpn-overview | CPP prices | prices change |
| https://learn.microsoft.com/en-us/microsoft-365-app-certification/docs/attestation | Attestation | |
| https://learn.microsoft.com/en-us/microsoft-365-app-certification/docs/certification | Certification | updated 2026-09-22 |
| https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview | Consent settings | |
| https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/configure-user-consent | Consent config | |
| https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-app-consent-policies | Managed policy exclusions | re-check before publishing |
| https://learn.microsoft.com/en-us/entra/identity-platform/application-consent-experience | "Unverified" | |
| https://learn.microsoft.com/en-us/graph/permissions-overview | Permission limits | |
| https://learn.microsoft.com/en-us/graph/permissions-reference | Admin-consent flags | summarizer-read |
| https://learn.microsoft.com/en-us/entra/identity-platform/v2-admin-consent | Admin consent endpoint | |
| https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow | Endpoints, offline_access | |
| https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens | Refresh lifetimes | |
| https://learn.microsoft.com/en-us/entra/identity-platform/configurable-token-lifetimes | Access tokens | |
| https://learn.microsoft.com/en-us/graph/throttling-limits | Outlook limits | updated 2026-09-17 |
| https://learn.microsoft.com/en-us/answers/questions/1643712/assistance-needed-with-adding-program-and-obtainin | MPN ID confusion | COMMUNITY, 2024-04 |
| https://learn.microsoft.com/en-us/answers/a/1936787 | Dev Program ineligibility reports | COMMUNITY, 2025-02 to 2026-01 |
| https://developers.chatwoot.com/self-hosted/configuration/features/email-channel/azure-app-setup.md | Unverified publisher limits | COMMUNITY (vendor, undated) |
| https://blog-en.topedia.com/2025/11/microsoft-managed-default-app-consent-policy-now-blocks-20-additional-permissions/ | Consent policy timeline | COMMUNITY, snippet only, 403 on fetch |

## 8. Open questions

1. Is an Azure subscription required to register an app? Quickstarts say so; tenant creation is paid-only. A personal Microsoft account may or may not yield a usable tenant. Needs a sign-in to test. UNCERTAIN.
2. Developer Program eligibility: FAQ (2026-09-04) says Visual Studio Professional or Enterprise; older sources say Enterprise only. FAQ adds a mandatory MCA billing account. Q&A threads show people hitting "not qualified" through January 2026.
3. Does publisher verification solve the end-user consent problem? Probably not for Mail.Read and Calendars.* in tenants on the managed default policy. This is inference from two docs, not a test.
4. Mail.Send is not in the exclusion list. An app requesting only Mail.Send may stay user-consentable. Needs a live test.
5. Late-2025 and 2026 policy changes rest on third-party snippets.
6. Basic CPP enrollment cost, and whether sole traders can complete business verification.
7. Not researched: app-registration limits, Exchange RBAC for Applications, national clouds, AppSource listing.
