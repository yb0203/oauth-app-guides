"""Find current docs pages for a provider: free web search (ddgs), then fetch and topic-check each page."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

from .fetch import Page, fetch_page

# Docs domains for the apps researched by hand; everything else is found by search and ranked.
DOC_DOMAINS: dict[str, list[str]] = {
    "github": ["docs.github.com"],
    "gmail": ["developers.google.com", "support.google.com"],
    "google": ["developers.google.com", "support.google.com"],
    "spotify": ["developer.spotify.com"],
    "xero": ["developer.xero.com"],
    "shopify": ["shopify.dev"],
}
COMMUNITY_HOSTS = ("reddit.com", "stackoverflow.com", "stackexchange.com", "medium.com", "dev.to", "quora.com")
NOISE_HOSTS = ("github.com", "gist.github.com", "youtube.com", "linkedin.com", "facebook.com", "x.com", "twitter.com")
TOPIC_PATH = re.compile(r"creat|regist|review|verif|approv|limit|quota|oauth|authori[sz]|app-?(setup|config)", re.I)
VERSIONED = re.compile(r"enterprise-(server|cloud)@")
TOPIC_WORDS = re.compile(r"oauth|client[ _-]?id|redirect uri|redirect url|authoriz|access token|scopes?\b", re.I)

Searcher = Callable[[str, int], list[dict]]


def ddgs_search(query: str, max_results: int = 8) -> list[dict]:
    from ddgs import DDGS

    try:
        return [r for r in DDGS().text(query, max_results=max_results) if r.get("href")]
    except Exception:  # rate limits and network errors: the caller handles "no results"
        return []


def queries_for(name: str, domains: list[str]) -> list[str]:
    sites = " OR ".join(f"site:{d}" for d in domains)
    suffix = f" ({sites})" if sites else ""
    return [
        f"{name} create OAuth app register application client id redirect URI{suffix}",
        f"{name} OAuth app review verification approval scopes{suffix}",
        f"{name} API app limits users quota development mode{suffix}",
    ]


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def score_url(url: str, slug: str, name: str, domains: list[str]) -> int:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    token = re.sub(r"[^a-z0-9]", "", slug.split("_")[0].lower())
    score = 0
    if any(host == d or host.endswith("." + d) for d in domains):
        score += 6
    if token and token in re.sub(r"[^a-z0-9]", "", host):
        score += 3
    if re.search(r"(^|\.)(docs|developers?|dev|api|support|help)\.", host) or "/docs" in parsed.path:
        score += 1
    if any(host.endswith(c) for c in COMMUNITY_HOSTS):
        score -= 2
    if token != "github" and any(host == n or host.endswith("." + n) for n in NOISE_HOSTS):
        score -= 5
    if VERSIONED.search(url):
        score -= 5
    score += min(2, len(TOPIC_PATH.findall(parsed.path)))
    return score


def covers_topic(page: Page, name: str) -> bool:
    text = page.visible_text or page.hidden_text
    first = re.sub(r"[^a-z0-9]", "", name.lower().split()[0]) if name.split() else ""
    return (
        page.status is not None and page.status < 400 and len(text) >= 500 and bool(TOPIC_WORDS.search(text))
        and (not first or first in re.sub(r"[^a-z0-9]", "", (text[:20000] + page.final_url).lower()))
    )


async def find_docs(
    name: str, slug: str, *, search: Searcher = ddgs_search, fetch: Callable[[str], Awaitable[Page]] = fetch_page,
    max_pages: int = 5, domains: list[str] | None = None,
) -> tuple[list[Page], list[str]]:
    """Returns (pages that cover the topic, urls that were tried and rejected)."""
    domains = DOC_DOMAINS.get(slug, []) if domains is None else domains
    found: dict[str, dict] = {}
    for q in queries_for(name, domains):
        for r in await asyncio.to_thread(search, q, 8):
            found.setdefault(r["href"].split("#")[0], r)
        if len(found) >= 12:
            break
    token = re.sub(r"[^a-z0-9]", "", slug.split("_")[0].lower())
    def official(u: str) -> bool:
        h = _host(u)
        return token in re.sub(r"[^a-z0-9]", "", h) and bool(re.match(r"(docs|developers?|dev|api)\.", h)) or any(
            h == d or h.endswith("." + d) for d in domains)

    if token and not any(official(u) for u in found):
        # nothing from the provider itself: retry restricted to its likely developer domains
        guess = [f"developers.{token}.com", f"developer.{token}.com", f"docs.{token}.com", f"{token}.com"]
        for q in queries_for(name, guess)[:2]:
            for r in await asyncio.to_thread(search, q, 8):
                found.setdefault(r["href"].split("#")[0], r)
        domains = [*domains, *guess]
    ranked = sorted((u for u in found if not VERSIONED.search(u)), key=lambda u: -score_url(u, slug, name, domains))[
        : max_pages + 3]
    sem = asyncio.Semaphore(4)

    async def one(url: str) -> Page:
        async with sem:
            return await fetch(url)

    pages = await asyncio.gather(*(one(u) for u in ranked))
    good: list[Page] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for page in pages:
        key = page.final_url.split("#")[0]
        if key in seen:
            continue
        seen.add(key)
        if len(good) < max_pages and covers_topic(page, name):
            good.append(page)
        else:
            rejected.append(page.requested_url)
    return good, rejected
