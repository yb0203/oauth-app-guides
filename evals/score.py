"""Score a generated guide (from a saved SSE stream) against the answer key in docs/TEST_PLAN.md §4.1.

Usage: python3 evals/score.py <provider> <stream.sse> [more <provider> <stream.sse> pairs]
Scores: tier (exact 1 / adjacent 0.5), key-fact recall (regex over the guide text),
honesty (no DOCS claim without a verified quote), BYO path present, and the evidence summary.
"""

import json
import re
import sys

TIERS = ["instant", "verify_to_scale", "review_required", "partner_only"]

ANSWER_KEY = {
    "github": {"tier": "instant", "facts": {
        "10 callback URLs": r"\b10\b.{0,40}callback|callback.{0,40}\b10\b",
        "expiring user tokens on by default": r"expir\w*.{0,60}(default|enabled)|(default|enabled).{0,60}expir",
        "orgs can restrict OAuth apps": r"organi[sz]ation.{0,80}(restrict|approv)|(restrict|approv).{0,80}organi[sz]ation"}},
    "google-gmail": {"tier": "review_required", "facts": {
        "100 test users in Testing": r"100 test users|test users.{0,40}100",
        "100 new-user cap while unverified": r"100.{0,30}(new[- ]user|user cap)|user cap.{0,40}100",
        "restricted scopes need a security assessment": r"(security assessment|CASA)",
        "internal apps skip verification": r"internal.{0,120}(no|not|without|skip|exempt).{0,40}(review|verif)"}},
    "spotify": {"tier": "partner_only", "facts": {
        "5 users in development mode": r"\b5\b.{0,40}(users|user)|(up to|max\w*) (5|five)",
        "owner needs Premium": r"premium",
        "extended quota for organizations only (250k MAU)": r"organi[sz]ation|250k|250,?000"}},
    "xero": {"tier": "verify_to_scale", "facts": {
        "Starter tier 5 connections": r"\b5\b.{0,40}connection",
        "5 uncertified apps per organisation": r"uncertified",
        "offline_access for refresh": r"offline_access"}},
    "shopify": {"tier": "review_required", "facts": {
        "public apps need app review": r"(app )?review",
        "per-shop authorize URL": r"(myshopify|per[- ]shop|\{shop\})",
        "distribution choice is permanent": r"(permanent|can(no|')t be changed)"}},
}


def load_guide(path):
    for line in open(path):
        if line.startswith("data:") and '"type":"data-guide"' in line:
            return json.loads(line[5:])["data"]["guide"]
    return None


def walk_evidence(o):
    if isinstance(o, dict):
        if {"label", "source_id", "quote", "found_in", "note"} <= set(o):
            yield o
        for v in o.values():
            yield from walk_evidence(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_evidence(v)


def score(provider, path):
    key = ANSWER_KEY[provider]
    g = load_guide(path)
    if g is None:
        return {"provider": provider, "error": "no data-guide in stream"}
    text = json.dumps(g).lower()
    tier = g["verdict"]["tier"]
    if tier == key["tier"]:
        tier_score = 1.0
    elif tier in TIERS and abs(TIERS.index(tier) - TIERS.index(key["tier"])) == 1:
        tier_score = 0.5
    else:
        tier_score = 0.0
    facts = {name: bool(re.search(rx, text, re.I | re.S)) for name, rx in key["facts"].items()}
    ev = list(walk_evidence(g))
    dishonest = [e for e in ev if e["label"] == "DOCS" and not (e.get("quote") and e.get("found_in"))]
    official = {s["id"] for s in g["sources"] if s["kind"] in ("official_docs", "composio_docs")}
    docs_on_non_official = [e for e in ev if e["label"] == "DOCS" and e.get("source_id") not in official]
    byo = any(re.search(r"(register|create|new).{0,40}(oauth )?app", s["title"], re.I) for s in g["steps"])
    callback = "backend.composio.dev" in text
    return {
        "provider": provider, "tier": tier, "expected": key["tier"], "tier_score": tier_score,
        "facts": facts, "recall": round(sum(facts.values()) / len(facts), 2),
        "docs_without_verified_quote": len(dishonest), "docs_label_on_non_official": len(docs_on_non_official),
        "byo_step": byo, "composio_callback": callback, "summary": g["verification_summary"],
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    for provider, path in zip(args[::2], args[1::2]):
        print(json.dumps(score(provider, path), indent=1))
