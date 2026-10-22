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
