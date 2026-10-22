"""Composio catalog lookup: free-text app name, slug or URL to a catalog entry."""

from __future__ import annotations

import csv
import difflib
import re
from dataclasses import dataclass, field
from functools import cache
from typing import Literal
from urllib.parse import urlparse

from . import config, store

Status = Literal["managed", "byo", "not_in_catalog"]

# Common alternative names and hosts that don't match a catalog name or slug by themselves.
ALIASES = {
    "google mail": "gmail", "googlemail": "gmail", "gcal": "googlecalendar", "gdrive": "googledrive",
    "google sheets": "googlesheets", "ms teams": "microsoft_teams", "msteams": "microsoft_teams",
    "office 365 outlook": "outlook", "x": "twitter", "x twitter": "twitter",
}
HOST_ALIASES = {
    "mail.google.com": "gmail", "calendar.google.com": "googlecalendar", "drive.google.com": "googledrive",
    "docs.google.com": "googledocs", "sheets.google.com": "googlesheets", "teams.microsoft.com": "microsoft_teams",
    "outlook.com": "outlook", "outlook.office.com": "outlook", "x.com": "twitter",
}
TIERS = {"instant", "verify_to_scale", "review_required", "partner_only"}
FUZZY_CUTOFF = 0.85
MAX_ALTERNATIVES = 5


@dataclass
class Resolution:
    query: str
    slug: str | None
    name: str | None
    toolkit_slug: str | None
    status: Status
    alternatives: list[dict] = field(default_factory=list)
    not_in_catalog: bool = False
    matched_via: str = "none"
    auth_scheme: str | None = None
    website: str | None = None


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _tokens(text: str) -> set[str]:
    """Lowercase words with a trailing plural 's' removed ('Teams' -> 'team')."""
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", text.lower())}


@cache
def _entries() -> list[dict]:
    """All 334 OAuth toolkits, with proposed-top-100 rank and tier guess merged in."""
    with open(config.CATALOG_ALL_CSV, newline="") as f:
        rows = {r["slug"]: dict(r, rank=None, tier_guess="unknown") for r in csv.DictReader(f)}
    with open(config.CATALOG_CSV, newline="") as f:
        for r in csv.DictReader(f):
            tier = r["difficulty_tier_GUESS"].replace("-", "_")
            row = rows.setdefault(r["slug"], dict(r))
            row.update(rank=int(r["rank"]), tier_guess=tier if tier in TIERS else "unknown")
    return list(rows.values())


def _summary(e: dict) -> dict:
    return {"slug": e["slug"], "name": e["name"], "status": e["managed_or_byo"]}


def _host_labels(query: str) -> tuple[str | None, list[str]]:
    """(host, candidate name labels) when the query looks like a URL or domain, else (None, [])."""
    q = query.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", q, re.I) and not re.match(r"^[\w-]+(\.[\w-]+)+(/|$)", q):
        return None, []
    host = (urlparse(q if "://" in q else f"//{q}").hostname or "").removeprefix("www.")
    labels = host.split(".")[:-1]  # drop the TLD
    return host, [*labels[-1:], *labels[:-1][::-1]]  # registrable label first


def _rank(e: dict, extra_tokens: int = 0) -> tuple:
    return (e["rank"] is None, e["managed_or_byo"] != "managed", extra_tokens, e["name"])


def _find(query: str) -> tuple[dict | None, str, list[dict]]:
    """(best entry, matched_via, other candidates)."""
    entries = _entries()
    by_slug = {e["slug"]: e for e in entries}
    by_key: dict[str, dict] = {}
    for e in entries:
        by_key.setdefault(_key(e["slug"]), e)
        by_key.setdefault(_key(e["name"]), e)

    host, labels = _host_labels(query)
    if host in HOST_ALIASES:
        return by_slug[HOST_ALIASES[host]], "alias", []
    for label in labels:
        if _key(label) in by_key:
            return by_key[_key(label)], "url", []
    if host:
        return None, "none", []

    qkey = _key(query)
    if not qkey:
        return None, "none", []
    spaced = " ".join(re.findall(r"[a-z0-9]+", query.lower()))
    if spaced in ALIASES:
        return by_slug[ALIASES[spaced]], "alias", []
    if qkey in by_key:
        return by_key[qkey], "exact", []

    # Query words all appear in the name or slug, e.g. "teams" -> Microsoft Teams, Zoom Team Chat.
    q_tokens = _tokens(query)
    hits = [(e, len(_tokens(f"{e['name']} {e['slug']}") - q_tokens)) for e in entries if q_tokens <= _tokens(f"{e['name']} {e['slug']}")]
    if hits:
        hits.sort(key=lambda h: _rank(*h))
        return hits[0][0], "token", [e for e, _ in hits[1:]]

    close = difflib.get_close_matches(qkey, by_key, n=MAX_ALTERNATIVES + 1, cutoff=FUZZY_CUTOFF)
    if close:
        return by_key[close[0]], "fuzzy", [by_key[k] for k in close[1:]]
    return None, "none", []


def resolve(query: str) -> Resolution:
    entry, via, others = _find(query)
    if entry is None:
        _, labels = _host_labels(query)
        return Resolution(query=query, slug=store.slugify(labels[0] if labels else query) or "app", name=None,
                          toolkit_slug=None, status="not_in_catalog", not_in_catalog=True)
    host, _ = _host_labels(query)
    return Resolution(
        query=query, slug=entry["slug"], name=entry["name"], toolkit_slug=entry["slug"], status=entry["managed_or_byo"],
        alternatives=[_summary(e) for e in others[:MAX_ALTERNATIVES] if e is not entry], matched_via=via,
        auth_scheme=entry.get("auth_scheme") or entry.get("composio_auth_scheme"), website=f"https://{host}" if host else None,
    )


def list_catalog() -> list[dict]:
    """The 100 proposed apps for GET /api/catalog, joined with the guides that exist.

    `tier` (the guide's verified tier) and `guide_slug` are null unless a guide exists. The guide is found by
    catalog slug or by its Composio toolkit slug, since they can differ (catalog `gmail`, guide `google-gmail`).
    """
    items = sorted((e for e in _entries() if e["rank"] is not None), key=lambda e: e["rank"])
    out = []
    for e in items:
        guide = store.find_by_toolkit(e["slug"])
        out.append({"slug": e["slug"], "name": e["name"], "composio_status": e["managed_or_byo"],
                    "tier_guess": e["tier_guess"], "has_guide": guide is not None,
                    "tier": guide["verdict"]["tier"] if guide else None,
                    "guide_slug": guide["slug"] if guide else None})
    return out
