import glob
import json

import pytest

from app import config
from app.tier import reconcile, tier_from_texts


def quotes_of(path) -> list[str]:
    out: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("label") in ("DOCS", "COMMUNITY") and o.get("quote"):
                out.append(o["quote"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.load(open(path)))
    return out


@pytest.mark.parametrize("slug,expected", [("github", "instant"), ("google-gmail", "review_required"),
                                           ("shopify", "review_required"), ("spotify", "partner_only"),
                                           ("xero", "verify_to_scale")])
def test_rule_agrees_with_the_curated_guides_from_their_own_verified_quotes(slug, expected):
    sig = tier_from_texts(quotes_of(config.CURATED_DIR / f"{slug}.json"))
    assert sig.tier == expected, (sig.tier, sig.quote)


@pytest.mark.parametrize("text,tier", [
    ("Spotify only accepts applications from organizations (not individuals)", "partner_only"),
    ("Apply to the Partner Program to get access", "partner_only"),
    ("Access is by invitation only.", "partner_only"),
    ("Apps must go through app review before they can be used by people outside your org", "review_required"),
    ("Restricted scopes require an annual security assessment", "review_required"),
    ("Verification is required for apps with more than 100 users", "review_required"),
    ("New apps default to the starter tier with 5 connections.", "verify_to_scale"),
    ("Apps are limited to 25 users until verified", "verify_to_scale"),
    ("You can enter up to 10 callback URLs", "instant"),
    ("Organization owners can restrict OAuth apps", "instant"),
])
def test_signals(text, tier):
    assert tier_from_texts([text]).tier == tier


def test_strong_signal_overrides_a_less_restrictive_model_tier_with_a_note():
    sig = tier_from_texts(["Spotify only accepts applications from organizations (not individuals)"])
    tier, note = reconcile("review_required", sig)
    assert tier == "partner_only" and "by rule" in note and "organizations" in note
    assert reconcile("unknown", sig)[0] == "partner_only"
    assert reconcile("partner_only", sig) == ("partner_only", None)


def test_rule_never_loosens_a_model_tier_and_weak_signals_do_not_override_review():
    weak = tier_from_texts(["New apps default to the starter tier with 5 connections."])
    assert reconcile("review_required", weak) == ("review_required", None)
    assert reconcile("instant", weak)[0] == "verify_to_scale"
    assert reconcile("partner_only", tier_from_texts(["nothing"])) == ("partner_only", None)


# --- the round-2 GitHub run: tier "unknown" although registration is self-serve and nothing restricts it -------

FIXTURES = config.REPO_ROOT / "backend" / "tests" / "fixtures" / "guides"


def r2_github():
    from app.models import Guide, GuideContent
    from app.research import Claim, VerifiedClaim

    raw = json.loads((FIXTURES / "r2_github.json").read_text())
    g = Guide.model_validate(raw)
    content = GuideContent.model_validate({k: raw[k] for k in GuideContent.model_fields})
    official = {s.id for s in g.sources if s.kind == "official_docs"}
    claims = [VerifiedClaim(f"c{i}", e["source_id"], Claim(category="registration" if i % 2 else "other", text=e["quote"], quote=e["quote"]), "visible")
              for i, e in enumerate(_docs_evidence(raw)) if e["source_id"] in official]
    return content, claims, official


def _docs_evidence(raw):
    out = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("label") == "DOCS" and o.get("quote"):
                out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(raw)
    return out


def test_r2_github_documents_no_restricting_signal():
    content, claims, official = r2_github()
    assert content.verdict.tier == "unknown" and len(official) >= 2
    assert tier_from_texts([c.claim.quote for c in claims]).tier == "instant"


def test_unknown_becomes_instant_with_medium_confidence_when_registration_is_self_serve():
    from app.synthesize import apply_tier_rule

    content, claims, official = r2_github()
    apply_tier_rule(content, claims, official, infer_instant_ok=True)
    assert content.verdict.tier == "instant" and content.verdict.confidence == "medium"
    assert "No review step found in the provider's docs." in content.open_questions


def test_unknown_stays_unknown_for_degraded_drafts_and_thin_evidence():
    from app.synthesize import apply_tier_rule

    content, claims, official = r2_github()
    apply_tier_rule(content, claims, official, infer_instant_ok=False)  # degraded verdict part
    assert content.verdict.tier == "unknown"
    content, claims, official = r2_github()
    one = {sorted(official)[0]}
    apply_tier_rule(content, [c for c in claims if c.source_id in one], one, infer_instant_ok=True)  # fewer than 2 pages
    assert content.verdict.tier == "unknown"
    content, claims, official = r2_github()
    apply_tier_rule(content, [c for c in claims if c.claim.category != "registration"], official, infer_instant_ok=True)
    assert content.verdict.tier == "unknown"  # no registration claim at all


def test_restricting_signal_blocks_the_instant_inference():
    from app.research import Claim, VerifiedClaim
    from app.synthesize import apply_tier_rule

    content, claims, official = r2_github()
    claims.append(VerifiedClaim("cx", sorted(official)[0], Claim(category="review", text="x",
                  quote="Apps must go through app review before they can be used by people outside your org"), "visible"))
    apply_tier_rule(content, claims, official, infer_instant_ok=True)
    assert content.verdict.tier == "review_required"
