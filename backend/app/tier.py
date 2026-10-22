"""Deterministic tier signals from verified claim text. The model proposes a tier; strong rule signals win."""

from __future__ import annotations

import re
from dataclasses import dataclass

TIERS = ["instant", "verify_to_scale", "review_required", "partner_only"]  # least to most restrictive

RUBRIC = """Tier definitions (pick exactly one; the rules below beat your impression):
- partner_only: the provider only accepts applications from organizations, partners or invited companies, or \\
access needs a partner programme or an approval that individuals cannot get ("applications only from \\
organizations", "partner programme", "apply for access", "invitation only").
- review_required: a provider review, verification, audit or security assessment is REQUIRED before outside or \\
public users can use the app (app review, app verification, publisher or business verification, marketplace \\
listing review).
- verify_to_scale: the app works at once but usage is capped (users, connections, installs) until a plan upgrade, \\
certification or verification, with no review queue in the way of the first users.
- instant: no review and no meaningful cap; register the app and it works.
- unknown: only when fewer than 2 official pages were read or the claims do not describe registering an app. If the \
docs describe self-serve app registration and NO review, cap, partner or verification requirement appears anywhere, \
the tier is instant (confidence medium), not unknown."""

PARTNER = re.compile(
    r"(only|exclusively)\s+(accepts?|available|open)\b.{0,60}\b(organi[sz]ations?|companies|businesses)\b|"
    r"\b(accepts?|accepting)\s+(applications?|requests?)\s+(only\s+)?from\s+(organi[sz]ations?|companies|businesses|partners)\b|"
    r"\bpartner (program(me)?|application|approval)\b|\b(by|via) invitation\b|\binvitation[- ]only\b|"
    r"\bnot (open|available) to individuals\b|\(not individuals\)", re.I)
REVIEW = re.compile(
    r"\b(app|application|api|scope|publisher|business|brand)\s+(review|verification)\s+(is|are)?\s*(required|mandatory|needed)|"
    r"\b(review|verification|approval|audit|assessment)\s+(is|are)\s+(required|mandatory)|"
    r"\b(must|need to|required to|have to)\s+(pass|complete|submit|go through|undergo|get)\b.{0,50}\b(review|verification|audit|assessment|approval)\b|"
    r"\bsecurity assessment\b|\bsubmit\b.{0,40}\bfor (app )?(review|verification|approval)\b|"
    r"\bpublic (apps?|distribution)\b.{0,60}\b(review|approval)\b|\bmarketplace (listing|review)\b", re.I)
SCALE = re.compile(
    r"\b(until|unless)\b.{0,60}\b(verified|certified|upgrade|approved)\b|"
    r"\b(starter|free|development)\s+(tier|plan|mode)\b.{0,60}\b(limit|cap|up to|\d+)|"
    r"\b(limited|capped|restricted)\s+(to|at)\s+(up to\s+)?\d+\s+(users?|connections?|installs?|workspaces?|organi[sz]ations?)\b", re.I)


@dataclass
class TierSignal:
    tier: str
    quote: str | None
    strong: bool


def tier_from_texts(texts: list[str]) -> TierSignal:
    """The most restrictive tier any claim text clearly signals. Partner/review are strong; scale caps are weak."""
    for tier, pattern, strong in (("partner_only", PARTNER, True), ("review_required", REVIEW, True),
                                  ("verify_to_scale", SCALE, False)):
        for t in texts:
            m = pattern.search(t)
            if m:
                return TierSignal(tier, t if len(t) <= 200 else t[:197] + "...", strong)
    return TierSignal("instant", None, False)


def reconcile(model_tier: str, signal: TierSignal) -> tuple[str, str | None]:
    """Returns (tier, note). A strong rule signal beats a less restrictive (or unknown) model tier."""
    rank = {t: i for i, t in enumerate(TIERS)}
    if signal.strong and rank[signal.tier] > rank.get(model_tier, -1):
        return signal.tier, (f"Tier set to {signal.tier} by rule (model said {model_tier}) because the docs say: "
                             f'"{signal.quote}"')
    if signal.tier == "verify_to_scale" and model_tier in ("instant", "unknown"):
        return signal.tier, (f"Tier set to verify_to_scale by rule (model said {model_tier}) because the docs say: "
                             f'"{signal.quote}"')
    return model_tier, None


NO_REVIEW_NOTE = "No review step found in the provider's docs."


def infer_instant(model_tier: str, signal: TierSignal, official_sources: set[str], registration_sources: set[str]) -> bool:
    """Self-serve registration documented on 2+ official pages and no restricting signal: tier instant, not unknown."""
    return (model_tier == "unknown" and signal.tier == "instant" and len(official_sources) >= 2
            and bool(registration_sources & official_sources))
