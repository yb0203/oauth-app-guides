"""Find current docs pages for a provider: free web search (ddgs), then fetch and topic-check each page."""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

from .domains import host_of, is_official, official_domains, registrable
from .fetch import Page, fetch_page

# Docs domains for the apps researched by hand; everything else is found by search and ranked.
DOC_DOMAINS: dict[str, list[str]] = {
    "github": ["docs.github.com"],
    "gmail": ["developers.google.com", "support.google.com", "cloud.google.com"],
    "google": ["developers.google.com", "support.google.com", "cloud.google.com"],
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
    """DuckDuckGo via ddgs. It rate-limits quietly (empty results or an exception), so retry once after a pause."""
    from ddgs import DDGS

    for attempt in range(2):
        try:
            results = [r for r in DDGS().text(query, max_results=max_results) if r.get("href")]
            if results:
                return results
        except Exception:  # rate limits and network errors
            pass
        if attempt == 0:
            time.sleep(2.0)
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
    if any(host == d or host.endswith("." + d) for d in domains) or is_official(url, slug, name, domains):
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


SNIPPET_WORDS = re.compile(r"verif|review|approv|limit|quota|\bcaps?\b|test users|unverified|restricted|sensitive|"
                           r"register|client id|redirect|consent|extended|development mode", re.I)


def snippet_score(result: dict) -> int:
    """Search-result title and snippet that talk about approval, caps and registration point at the right page."""
    text = f"{result.get('title', '')} {result.get('body', '')}"
    return min(3, len({m.group(0).lower() for m in SNIPPET_WORDS.finditer(text)}))


def covers_topic(page: Page, name: str, need_name: bool = True) -> bool:
    """Official pages need not say the app's name (Google's consent-screen pages never say "Gmail")."""
    text = page.visible_text or page.hidden_text
    first = re.sub(r"[^a-z0-9]", "", name.lower().split()[0]) if need_name and name.split() else ""
    return (
        page.status is not None and page.status < 400 and len(text) >= 500 and bool(TOPIC_WORDS.search(text))
        and (not first or first in re.sub(r"[^a-z0-9]", "", (text[:20000] + page.final_url).lower()))
    )


MIN_OFFICIAL = 3


def official_queries(name: str, domains: list[str]) -> list[str]:
    """Queries restricted to the provider's own domains: registration, the app console, authorization, review."""
    sites = " OR ".join(f"site:{d}" for d in domains[:4])
    return [f"{name} {topic} ({sites})" for topic in (
        "OAuth app register client id redirect URI", "OAuth consent screen app verification scopes",
        "developer app console create app", "API authorization scopes", "app review approval limits users quota",
        "unverified app user cap test users development mode")]


async def _collect(search: Searcher, queries: list[str], found: dict[str, dict], enough: int = 14) -> None:
    results = await asyncio.gather(*(asyncio.to_thread(search, q, 8) for q in queries))  # queries run in parallel
    for rs in results:  # merged in query order so the first query's hits rank first
        for r in rs:
            found.setdefault(r["href"].split("#")[0], r)


async def discover_official(name: str, slug: str, search: Searcher) -> list[str]:
    """For a provider we have no domains for: the registrable domains of search results whose name contains the
    provider token (todoist.com for "Todoist"). Cheap and deterministic; the model has no say."""
    found: dict[str, dict] = {}
    await _collect(search, [f"{name} API developer documentation", f"{name} OAuth developer app"], found, enough=16)
    counts: dict[str, int] = {}
    for url in found:
        if is_official(url, slug, name, []):
            counts[registrable(host_of(url))] = counts.get(registrable(host_of(url)), 0) + 1
    return [d for d, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:2]]


async def find_docs(
    name: str, slug: str, *, search: Searcher = ddgs_search, fetch: Callable[[str], Awaitable[Page]] = fetch_page,
    max_pages: int = 5, domains: list[str] | None = None, extra_domains: list[str] | None = None,
) -> tuple[list[Page], list[str]]:
    """Official developer docs first; third-party pages only when fewer than MIN_OFFICIAL official ones cover the
    topic. Returns (pages that cover the topic, urls that were tried and rejected)."""
    official = list(domains) if domains is not None else official_domains(slug, name, extra_domains)
    if not official:
        official = await discover_official(name, slug, search)
    sem = asyncio.Semaphore(4)

    async def fetch_all(urls: list[str]) -> list[Page]:
        async def one(url: str) -> Page:
            async with sem:
                return await fetch(url)

        return list(await asyncio.gather(*(one(u) for u in urls)))

    def ranked(found: dict[str, dict], keep) -> list[str]:
        urls = [u for u in found if not VERSIONED.search(u) and keep(u)]
        return sorted(urls, key=lambda u: -(score_url(u, slug, name, official) + snippet_score(found[u])))[: max_pages + 4]

    good: list[Page] = []
    rejected: list[str] = []
    seen: set[str] = set()

    def triage(pages: list[Page], want_official: bool, limit: int) -> None:
        for page in pages:
            key = page.final_url.split("#")[0]
            if key in seen:
                continue
            seen.add(key)
            is_off = is_official(page.final_url, slug, name, official)
            ok = covers_topic(page, name, need_name=not is_off) and is_off == want_official
            if ok and limit > 0:
                good.append(page)
                limit -= 1
            else:
                rejected.append(page.requested_url)

    if official:
        found: dict[str, dict] = {}
        await _collect(search, official_queries(name, DOC_DOMAINS.get(slug) or official), found)
        triage(await fetch_all(ranked(found, lambda u: True)), True, max_pages)
    n_official = len(good)
    if n_official < MIN_OFFICIAL:  # top up with third-party pages, but never more than three of them
        found = {}
        await _collect(search, queries_for(name, []), found)
        pool = ranked(found, lambda u: is_official(u, slug, name, official) == False and u.split("#")[0] not in seen)  # noqa: E712
        triage(await fetch_all(pool), False, min(3, max_pages - n_official))
    return good, rejected
