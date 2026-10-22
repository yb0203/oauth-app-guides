"""Sign-in wall probe (FR5): load a developer console URL once, read-only, and classify what we hit."""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlsplit

from . import fetch
from .models import WallProbe

KNOWN_CONSOLES: dict[str, str] = {
    "github": "https://github.com/settings/applications/new",
    "google": "https://console.cloud.google.com/auth/overview",
    "spotify": "https://developer.spotify.com/dashboard",
    "xero": "https://developer.xero.com/app/manage",
    "shopify": "https://dev.shopify.com/dashboard",
}  # same URLs as experiments/oauth-capture-poc/apps.json

_SIGNIN_TEXT = re.compile(r"(sign|log)[ -]?in (to|with) |you (must|need to) (sign|log)[ -]?in|enter your password", re.I)
_BOT_TEXT = re.compile(r"captcha|verify you are (a )?human|checking your browser|cloudflare challenge", re.I)
_DENIED_TEXT = re.compile(r"access denied|request blocked|forbidden", re.I)
_BLOCKED_STATUSES = {403, 406, 429}


def classify(
    console_url: str,
    final_url: str,
    status: int | None,
    redirect_chain: list[str],
    visible_text: str,
    error: str | None = None,
) -> WallProbe:
    host = urlsplit(final_url).hostname or ""
    bot = _BOT_TEXT.search(visible_text)
    bot_note = f" ({'reCAPTCHA' if 'recaptcha' in visible_text.lower() else 'bot check'} mentioned)" if bot else ""
    wall_host = None

    if error or status is None or status == 404 or status >= 500:
        outcome, asks = "error", "Couldn't reach the console" + (f" (HTTP {status})" if status else "")
    elif status in _BLOCKED_STATUSES:
        outcome, asks = "blocked", f"Blocked by {host} (HTTP {status}) before any sign-in page{bot_note}"
    elif fetch.signin_tokens(final_url) - fetch.signin_tokens(console_url) or _SIGNIN_TEXT.search(visible_text):
        outcome, wall_host, asks = "login_wall", host, f"Sign-in page at {host}{bot_note}"
    elif _DENIED_TEXT.search(visible_text):
        outcome, asks = "blocked", f"Blocked by {host} (access denied){bot_note}"
    else:
        outcome, asks = "console_reachable", f"Console page at {host} loaded without a sign-in prompt{bot_note}"

    return WallProbe(
        console_url=console_url,
        final_url=final_url,
        redirect_chain=list(redirect_chain),
        outcome=outcome,
        wall_host=wall_host,
        asks_for=asks,
        bot_check=bot is not None,
        method="http",
        observed_at=date.today().isoformat(),
    )


def _classify_page(console_url: str, page: fetch.Page) -> WallProbe:
    return classify(console_url, page.final_url, page.status, page.redirect_chain, page.visible_text, page.error)


async def probe_console(console_url: str) -> WallProbe:
    """GET the console once; retry in a browser if plain HTTP could not tell (JS redirects, 406s)."""
    page = await fetch.fetch_page(console_url, allow_browser=False)
    result = _classify_page(console_url, page)
    if result.outcome != "login_wall" and fetch.needs_browser(page, console=True):
        rendered = await fetch.fetch_with_browser(console_url)
        if rendered.error is None:
            result = _classify_page(console_url, rendered).model_copy(update={"method": "browser"})
    return result
