"""Find the provider's developer console (app management page) in the docs pages we already fetched."""

from __future__ import annotations

import re
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup

from .domains import is_official
from .fetch import Page

HINT = re.compile(
    r"app[-_ ]?(console|management|dashboard)|appconsole|developer[-_ ]?(portal|console|dashboard)|my[-_ ]?apps|"
    r"(create|register|new)[-_ ]?(an?[-_ ])?(new[-_ ])?(oauth[-_ ]?)?app|oauth[-_ ]?apps|apps/new|/apps\b", re.I)
NOT_A_CONSOLE = re.compile(r"/oauth/(authorize|token)|/authorize\b|/token\b|/callback|\.(png|jpg|svg|pdf)$", re.I)


def _score(text: str, href: str) -> int:
    score = 3 * bool(HINT.search(text)) + 2 * bool(HINT.search(href))
    return 0 if NOT_A_CONSOLE.search(href) else score


def console_candidates(page: Page, slug: str, name: str, domains: list[str] | None = None) -> list[str]:
    """Official https links on this page that look like the app console, best first."""
    scored: dict[str, int] = {}
    html = page.html or ""
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True) if html else []:
        url, _ = urldefrag(urljoin(page.final_url, a["href"]))
        url = url.split("?")[0]
        if not url.startswith("https://") or not is_official(url, slug, name, domains):
            continue
        s = _score(a.get_text(" ", strip=True), urlsplit(url).path)
        if s:
            scored[url] = max(scored.get(url, 0), s)
    for m in re.finditer(r"https://[^\s\"'<>)\],]+", page.visible_text or ""):
        url = m.group(0).rstrip(".").split("?")[0]
        if is_official(url, slug, name, domains) and _score("", urlsplit(url).path):
            scored[url] = max(scored.get(url, 0), 2)
    return [u for u, _ in sorted(scored.items(), key=lambda kv: -kv[1])]
