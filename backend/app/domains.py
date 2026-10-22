"""Which hosts count as the provider's own (official) sources, decided by domain, not by the model."""

from __future__ import annotations

import re
from urllib.parse import urlparse

# Vendor-owned domains that don't contain the app's name (the vendor's org, docs hosts, SDK pages).
ORG_DOMAINS: dict[str, list[str]] = {
    "todoist": ["todoist.com", "doist.com", "doist.github.io"],
    "github": ["github.com", "githubusercontent.com"],
    "gmail": ["google.com", "googleapis.com"],
    "google": ["google.com", "googleapis.com"],
    "outlook": ["microsoft.com", "microsoftonline.com"],
    "slack": ["slack.com"],
    "shopify": ["shopify.com", "shopify.dev"],
    "spotify": ["spotify.com"],
    "xero": ["xero.com"],
}
COMPOSIO_DOMAINS = ("composio.dev",)
TWO_LEVEL_TLDS = {"co.uk", "com.au", "co.jp", "co.in", "com.br", "co.nz"}
GITHUB_PAGES = "github.io"


def host_of(url: str) -> str:
    return (urlparse(url if "//" in url else "//" + url).hostname or "").lower().removeprefix("www.")


def registrable(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_LEVEL_TLDS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def provider_tokens(slug: str, name: str) -> set[str]:
    """Words that identify the provider inside its domain names: 'todoist', 'google', 'googlecalendar'."""
    toks = {_squash(slug.split("_")[0]), _squash(slug), _squash(name)}
    toks |= {_squash(w) for w in re.split(r"[\s_\-]+", name) if len(_squash(w)) >= 4}
    return {t for t in toks if len(t) >= 4}


def official_domains(slug: str, name: str, extra: list[str] | None = None) -> list[str]:
    """Known org domains for the provider, plus any the caller learned (e.g. from the user's own URL)."""
    out = list(ORG_DOMAINS.get(slug, [])) + list(ORG_DOMAINS.get(slug.split("_")[0], []))
    out += [registrable(host_of(d)) if not host_of(d).endswith(GITHUB_PAGES) else host_of(d) for d in extra or []]
    return list(dict.fromkeys(out))


def is_official(url: str, slug: str, name: str, domains: list[str] | None = None) -> bool:
    """True if the host belongs to the provider: a listed org domain, or its registrable domain's name contains
    a provider token (todoist.com, developer.todoist.com). Other people's github.io pages never match by token."""
    host = host_of(url)
    if not host:
        return False
    listed = domains if domains is not None else official_domains(slug, name)
    if any(host == d or host.endswith("." + d) for d in listed):
        return True
    reg = registrable(host)
    if reg == GITHUB_PAGES or host.endswith("." + GITHUB_PAGES):
        return False
    label = _squash(reg.split(".")[0])
    return any(t in label for t in provider_tokens(slug, name))


def source_kind(url: str, slug: str, name: str, domains: list[str] | None = None) -> str:
    host = host_of(url)
    if any(host == d or host.endswith("." + d) for d in COMPOSIO_DOMAINS):
        return "composio_docs"
    return "official_docs" if is_official(url, slug, name, domains) else "community"
