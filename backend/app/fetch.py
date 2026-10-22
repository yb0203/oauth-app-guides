"""Page fetching: plain HTTP first, a shared headless Chromium as the fallback. GET only, never raises."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
MIN_VISIBLE_CHARS = 500


@dataclass
class Page:
    requested_url: str
    final_url: str
    redirect_chain: list[str]  # every URL visited in order, from the requested URL to the final one
    status: int | None
    title: str
    visible_text: str
    hidden_text: str  # ALL text including collapsed sections (like textContent)
    method: Literal["http", "browser"]
    error: str | None
    html: str = ""


# --- HTML to text -----------------------------------------------------------------------------

try:
    import lxml  # noqa: F401

    _PARSER = "lxml"
except ImportError:  # lxml is optional
    _PARSER = "html.parser"

_ALWAYS_DROP = ("script", "style")
_VISIBLE_DROP = ("noscript", "template")
_BLOCKS = [
    "p", "div", "li", "ul", "ol", "br", "tr", "td", "th", "table", "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "article", "header", "footer", "nav", "main", "aside", "pre", "blockquote", "form",
    "details", "summary", "dt", "dd", "dl", "hr", "figure", "figcaption",
]  # fmt: skip


def _hidden_nodes(root: Tag) -> list[Tag | NavigableString]:
    """Nodes whose text a browser would not show: hidden attributes, inline CSS, collapsed widgets."""
    hidden: list[Tag | NavigableString] = []
    for el in root.find_all(True):
        attrs = el.attrs
        style = re.sub(r"\s+", "", attrs.get("style") or "").lower()
        classes = attrs.get("class") or []
        if (
            "hidden" in attrs
            or str(attrs.get("aria-hidden", "")).lower() == "true"
            or "display:none" in style
            or "visibility:hidden" in style
            or ("collapse" in classes and "show" not in classes)  # Bootstrap collapsible
        ):
            hidden.append(el)
        if el.name == "details" and "open" not in attrs:
            hidden += [c for c in el.children if not (isinstance(c, Tag) and c.name == "summary")]
        if str(attrs.get("aria-expanded", "")).lower() == "false" and attrs.get("aria-controls"):
            target = root.find(id=str(attrs["aria-controls"]).split()[0])
            if target is not None:
                hidden.append(target)
        if "zippy" in classes:  # Google help accordions: the heading link is followed by its body
            sibling = el.find_next_sibling(True)
            if sibling is not None:
                hidden.append(sibling)
    return hidden


def _tidy(text: str) -> str:
    lines = (re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def _text(root: Tag) -> str:
    for block in root.find_all(_BLOCKS):
        block.insert_before("\n")
        block.insert_after("\n")
    return _tidy(root.get_text(""))


def _clean_root(soup: BeautifulSoup, drop: tuple[str, ...]) -> Tag:
    root = soup.body or soup
    for el in root.find_all(drop):
        el.decompose()
    return root


def html_to_texts(html: str) -> tuple[str, str, str]:
    """Return (visible_text, all_text, title). all_text keeps collapsed and hidden sections."""
    if not html.strip():
        return "", "", ""
    soup = BeautifulSoup(html, _PARSER)
    title = " ".join(soup.title.get_text().split()) if soup.title else ""
    everything = _text(_clean_root(soup, _ALWAYS_DROP))
    root = _clean_root(BeautifulSoup(html, _PARSER), _ALWAYS_DROP + _VISIBLE_DROP)
    for node in reversed(_hidden_nodes(root)):  # children before parents: decomposing a parent destroys its strings
        try:
            if isinstance(node, Tag):
                if not node.decomposed:
                    node.decompose()
            elif getattr(node, "parent", None) is not None:
                node.extract()
        except (AttributeError, ValueError):  # already detached by an earlier removal
            continue
    return _text(root), everything, title


def _crude_texts(html: str) -> tuple[str, str, str]:
    """Last resort when the HTML parser chokes: strip tags with a regex. Better a rough page than no run."""
    text = _tidy(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)))
    return text, text, ""


# --- decision rules ---------------------------------------------------------------------------

_SIGNIN_RE = re.compile(r"(?<![a-z])(login|signin|sign-in|sso|accounts|auth|oauth|identity)(?![a-z])")


def signin_tokens(url: str) -> set[str]:
    """Sign-in hints in a URL's host and path (not its query string)."""
    parts = urlsplit(url)
    return set(_SIGNIN_RE.findall(f"{parts.hostname or ''}{parts.path}".lower()))


def needs_browser(page: Page, *, console: bool = False) -> bool:
    # BROWSER_FALLBACK=off on hosts without Chromium (e.g. Vercel's Python runtime): stay HTTP-only.
    if os.getenv("BROWSER_FALLBACK", "on").lower() == "off":
        return False
    if page.error or page.status is None or 400 <= page.status < 500:
        return True
    if len(page.visible_text) < MIN_VISIBLE_CHARS:
        return True
    if console:  # a console that did not leave its own host or show a sign-in hint may redirect in JS
        same_host = urlsplit(page.final_url).hostname == urlsplit(page.requested_url).hostname
        return same_host and not (signin_tokens(page.final_url) - signin_tokens(page.requested_url))
    return False


# --- request observation (read-only audits) ---------------------------------------------------

_observers: list[Callable[[str, str], None]] = []


@contextmanager
def observe_requests() -> Iterator[list[tuple[str, str]]]:
    """Collect (method, url) of every request that actually went out, over HTTP or in the browser."""
    seen: list[tuple[str, str]] = []
    callback = lambda method, url: seen.append((method, url))  # noqa: E731
    _observers.append(callback)
    try:
        yield seen
    finally:
        _observers.remove(callback)


def _notify(method: str, url: str) -> None:
    for callback in list(_observers):
        callback(method, url)


# --- HTTP -------------------------------------------------------------------------------------


def _error_page(url: str, method: Literal["http", "browser"], exc: BaseException | str) -> Page:
    message = exc if isinstance(exc, str) else f"{type(exc).__name__}: {exc}"
    return Page(url, url, [url], None, "", "", "", method, message)


async def _fetch_http(url: str, timeout: float, client: httpx.AsyncClient | None) -> Page:
    own = client is None
    client = client or httpx.AsyncClient()
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=timeout)
    except Exception as exc:  # network errors become data, never exceptions
        return _error_page(url, "http", exc)
    finally:
        if own:
            await client.aclose()
    hops = [*resp.history, resp]
    for hop in hops:
        _notify(hop.request.method, str(hop.request.url))
    try:
        visible, everything, title = html_to_texts(resp.text)
    except Exception:  # one odd page must never take the run down
        visible, everything, title = _crude_texts(resp.text)
    chain = [str(hop.url) for hop in hops]
    return Page(url, str(resp.url), chain, resp.status_code, title, visible, everything, "http", None, resp.text)


# --- shared browser ---------------------------------------------------------------------------


@dataclass
class _Shared:
    loop: asyncio.AbstractEventLoop
    lock: asyncio.Lock
    playwright: object | None = None
    browser: object | None = None


_shared: _Shared | None = None


async def _get_browser():
    """Lazily start one Chromium and reuse it. Playwright objects are bound to their event loop."""
    global _shared
    loop = asyncio.get_running_loop()
    if _shared is None or _shared.loop is not loop:
        _shared = _Shared(loop, asyncio.Lock())
    async with _shared.lock:
        if _shared.browser is None or not _shared.browser.is_connected():
            from playwright.async_api import async_playwright

            _shared.playwright = await async_playwright().start()
            try:
                _shared.browser = await _shared.playwright.chromium.launch(headless=True)
            except Exception:
                await _shared.playwright.stop()
                _shared.playwright = None
                raise
        return _shared.browser


async def close_browser() -> None:
    global _shared
    shared, _shared = _shared, None
    if shared is None or shared.loop is not asyncio.get_running_loop():
        return
    for closer in (shared.browser and shared.browser.close, shared.playwright and shared.playwright.stop):
        if closer:
            try:
                await closer()
            except Exception:  # already gone
                pass


async def _only_reads(route) -> None:
    """Plain GET/HEAD only: anything else a page script tries is aborted before it leaves."""
    if route.request.method in ("GET", "HEAD"):
        await route.continue_()
    else:
        await route.abort()


_TEXT_JS = """() => {
  const body = document.body;
  if (!body) return ['', ''];
  const clone = body.cloneNode(true);
  clone.querySelectorAll('script, style, noscript, template').forEach(e => e.remove());
  return [body.innerText, clone.textContent];
}"""


async def fetch_with_browser(url: str, *, timeout: float = 20.0) -> Page:
    """Render the page in headless Chromium. Never raises; failures come back as Page.error."""
    from playwright.async_api import TimeoutError as PlaywrightTimeout

    context = None
    try:
        browser = await _get_browser()
        context = await browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 800}, locale="en-US")
        await context.route("**/*", _only_reads)
        page = await context.new_page()
        chain: list[str] = []
        status: list[int] = []

        def is_main_nav(request) -> bool:
            try:
                return request.is_navigation_request() and request.frame == page.main_frame
            except Exception:  # service-worker requests have no frame
                return False

        page.on("request", lambda r: chain.append(r.url) if is_main_nav(r) else None)
        page.on("response", lambda r: _notify(r.request.method, r.url))
        page.on("response", lambda r: status.append(r.status) if is_main_nav(r.request) and not 300 <= r.status < 400 else None)

        await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        try:
            await page.wait_for_load_state("networkidle", timeout=min(8000, timeout * 500))
        except PlaywrightTimeout:
            pass  # busy pages never go idle; the DOM is loaded anyway
        await page.wait_for_timeout(1000)  # let JavaScript redirects fire
        for attempt in range(2):
            try:
                inner, everything = await page.evaluate(_TEXT_JS)
                break
            except Exception:  # a late redirect destroyed the execution context
                if attempt:
                    raise
                await page.wait_for_timeout(1500)
        final = page.url
        visited = list(dict.fromkeys([url, *chain, final]))
        return Page(url, final, visited, status[-1] if status else None, await page.title(), _tidy(inner),
                    _tidy(everything), "browser", None, await page.content())  # fmt: skip
    except Exception as exc:
        return _error_page(url, "browser", exc)
    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass


async def fetch_page(
    url: str, *, allow_browser: bool = True, timeout: float = 20.0, client: httpx.AsyncClient | None = None
) -> Page:
    page = await _fetch_http(url, timeout, client)
    if not (allow_browser and needs_browser(page)):
        return page
    try:
        rendered = await fetch_with_browser(url, timeout=timeout)
    except Exception as exc:
        rendered = _error_page(url, "browser", exc)
    if rendered.error is None:
        return rendered
    note = f"browser fallback failed: {rendered.error}"
    page.error = f"{page.error}; {note}" if page.error else note
    return page
