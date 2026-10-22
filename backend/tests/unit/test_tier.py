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
