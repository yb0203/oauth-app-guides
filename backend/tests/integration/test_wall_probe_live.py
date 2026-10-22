"""L2: the sign-in wall probe against the 5 real consoles (pytest -m network). Read-only."""

from urllib.parse import urlsplit

import pytest
import pytest_asyncio

from app import fetch
from app.probe import KNOWN_CONSOLES, probe_console

pytestmark = [pytest.mark.network, pytest.mark.asyncio(loop_scope="module")]

WALL_HOSTS = {
    "github": "github.com",
    "google": "accounts.google.com",
    "spotify": "accounts.spotify.com",
    "xero": "login.xero.com",
    "shopify": "accounts.shopify.com",
}
READ_ONLY = {"GET", "HEAD"}


@pytest_asyncio.fixture(scope="module", loop_scope="module", autouse=True)
async def _close_browser():
    yield
    await fetch.close_browser()


@pytest.mark.parametrize("slug", sorted(KNOWN_CONSOLES))
async def test_console_ends_on_known_sign_in_host(slug):
    with fetch.observe_requests() as seen:
        result = await probe_console(KNOWN_CONSOLES[slug])
    assert result.outcome == "login_wall", result
    assert result.wall_host == WALL_HOSTS[slug] == urlsplit(result.final_url).hostname
    assert result.redirect_chain[0] == KNOWN_CONSOLES[slug]
    # 1-2 redirects for most; Spotify and Shopify add a third hop through their auth services
    assert 1 <= len(result.redirect_chain) - 1 <= 3, result.redirect_chain
    assert result.method in ("http", "browser")
    # read-only guarantee: nothing but GET/HEAD went out while probing
    assert seen and {method for method, _ in seen} <= READ_ONLY, seen


async def test_spotify_mentions_recaptcha():
    result = await probe_console(KNOWN_CONSOLES["spotify"])
    assert result.bot_check, result
