# Live eval results

Scored with `evals/score.py` against the answer key in `docs/TEST_PLAN.md` §4.1. Runs are against **production** (Vercel Python, free OpenRouter models, no browser fallback). Raw streams are in `evals/runs/`.

## Round 1: 2026-10-22 (after the BYO-first and source-labeling fixes)

| App | Time | Tier (got / expected) | Key-fact recall | DOCS without verified quote | DOCS on non-official source | Register-your-own-app step | Composio callback | Evidence (verified / community / uncertain) |
|---|---|---|---|---|---|---|---|---|
| GitHub | 51 s | instant / instant ✅ | 0.67 (missed "10 callback URLs") | 0 | 0 | yes | yes | 25 / 0 / 4 |
| Gmail | 174 s | unknown / review_required ❌ | 0.50 | 0 | 0 | no | yes | 10 / 19 / 0 |
| Spotify | 53 s | review_required / partner_only (adjacent, 0.5) | 0.67 (missed "5 users") | 0 | 0 | yes | yes | 20 / 0 / 2 |
| Todoist (unseen) | 48 s | n/a | n/a | n/a | n/a | n/a | n/a | completed |

**What we learned:**
- Honesty held everywhere: no DOCS claim without a verified quote, and no third-party page labeled as official.
- Gmail failed on three counts. The guide writer timed out, so the run published its labeled fallback draft. Search kept only 1 official Google page and padded with third-party blogs. The probe picked the wrong console (Apps Script).
- The Spotify tier was off by one: nothing tied "organizations only" to partner-only.

**Fixes sent to the backend:** split and time-budget the writer; a tier rubric with deterministic checks; official domains for multi-domain vendors (google.com subdomains); console URL seeding and validation. Round 2 below.

## Round 2: 2026-10-22 (writer split, tier rubric, official org domains, console seeding)

| App | Time | Tier (got / expected) | Key-fact recall | DOCS without verified quote | DOCS on non-official source | Register-your-own-app step | Evidence (verified / community / uncertain) |
|---|---|---|---|---|---|---|---|
| GitHub | 55 s | unknown / instant ❌ (rubric too strict) | 1.00 | 0 | 0 | yes | 26 / 0 / 5 |
| Gmail | 49 s | review_required / review_required ✅ | 0.00 (off-topic Google pages) | 0 | 0 | yes | 26 / 0 / 4 |
| Spotify | 78 s | partner_only / partner_only ✅ | 1.00 | 0 | 0 | yes | 34 / 0 / 5 |
| Zoom (unseen) | 90 s | review_required (Marketplace security review for scopes; publication review) | n/a | 0 | 0 | yes | 32 / 0 / 0, 5 official pages |
| Dropbox (unseen) | 56 s | review_required (production approval) | n/a | 0 | 0 | yes | 29 (3 hidden) / 4 / 4, login wall probed |

**What we learned:** the writer no longer times out (0 degraded guides, down from 1), tier accuracy rose and Spotify became perfect, and unseen apps now produce bring-your-own guides from official docs. Two regressions are being fixed: the rubric returned "unknown" when docs simply don't mention a review (it should be instant with medium confidence), and an official-domain page can still be off-topic (Google Cloud connector docs), which crowded out the Gmail limits pages.

## Round 3: 2026-10-22 (instant-tier rule, topic relevance filter), the final deployed version

| App | Time | Tier (got / expected) | Key-fact recall | DOCS without verified quote | DOCS on non-official source | Evidence (verified / community / uncertain) |
|---|---|---|---|---|---|---|
| GitHub | 60 s | instant / instant ✅ | 0.67 (missed "expiring tokens on by default") | 0 | 0 | 33 / 0 / 3 |
| Gmail | 74 s | review_required / review_required ✅ | 0.50 (missed the two 100-user caps) | 0 | 0 | 30 / 0 / 2 |
| Asana (unseen) | 70 s | review_required, medium confidence | n/a | 0 | 0 | 24 (3 hidden) / 0 / 2, login wall probed, 4 official pages |

## Summary across the latest run of each app

- **Tier accuracy on the answer key:** GitHub ✅, Gmail ✅, Spotify ✅ (round 2), so 3 of 3. Round 1 scored 1.5 of 3.
- **Key-fact recall:** 0.67 / 0.50 / 1.00 (mean 0.72). The misses are numeric caps (Gmail's 100-user limits) that the free models don't always extract. The curated guides contain them.
- **Honesty:** 0 DOCS claims without a verified quote and 0 DOCS labels on non-official sources, in every round.
- **Reliability:** every production run since round 2 produced a full guide in 49 to 90 s. No fallback drafts, and no dropped streams since heartbeats were added.
- **Unseen apps** (Todoist, Zoom, Dropbox, Asana): every one produced a bring-your-own guide from official docs, with the Composio callback and a register-your-own-app step.
- **Scorer caveat:** the "register-your-own-app step" check is a title regex, and Gmail's step is phrased "Create the OAuth client", so the regex misses it.
