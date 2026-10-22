"""L1: wall probe classification (FR5) using fixtures saved from the proof of concept."""

import json
import pathlib
from datetime import date

import pytest

from app import fetch, probe
from app.fetch import Page
from app.probe import KNOWN_CONSOLES, classify

WALL = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "wall"
SLUGS = ["github", "google", "spotify", "xero", "shopify"]


def load(name: str) -> dict:
    return json.loads((WALL / f"{name}.json").read_text())


def classify_fixture(fx: dict):
    return classify(fx["console_url"], fx["final_url"], fx["status"], fx["redirect_chain"], fx["visible_text"])


@pytest.mark.parametrize("slug", SLUGS)
def test_poc_consoles_are_login_walls(slug):
    fx = load(slug)
    r = classify_fixture(fx)
    assert r.outcome == "login_wall"
    assert r.wall_host == fx["expect"]["wall_host"]
    assert r.bot_check is fx["expect"]["bot_check"]
    assert r.final_url == fx["final_url"] and r.console_url == fx["console_url"]
    assert r.redirect_chain == fx["redirect_chain"]
    assert r.method == "http" and r.observed_at == date.today().isoformat()
    assert r.wall_host in r.asks_for


def test_spotify_recaptcha_is_reported():
    r = classify_fixture(load("spotify"))
    assert r.bot_check and "recaptcha" in r.asks_for.lower()
    assert not classify_fixture(load("github")).bot_check


def test_known_consoles_cover_the_five_apps():
    assert set(KNOWN_CONSOLES) == set(SLUGS)
    assert KNOWN_CONSOLES["github"] == "https://github.com/settings/applications/new"
    assert KNOWN_CONSOLES["shopify"] == "https://dev.shopify.com/dashboard"


def test_google_console_path_containing_auth_is_not_a_wall():
    url = "https://console.cloud.google.com/auth/overview"
    r = classify(url, url, 200, [url], "OAuth overview. Create OAuth client. Configure consent screen.")
    assert r.outcome == "console_reachable"


def test_console_with_create_form_is_reachable():
    fx = load("console_reachable")
    r = classify_fixture(fx)
    assert r.outcome == "console_reachable" and r.wall_host is None and not r.bot_check


def test_in_place_sign_in_prompt_is_a_wall():
    url = "https://dev.example.com/apps"
    r = classify(url, url, 200, [url], "You need to sign in to continue. Enter your password.")
    assert r.outcome == "login_wall" and r.wall_host == "dev.example.com"


@pytest.mark.parametrize("status", [404, 500, 502, 503])
def test_not_found_and_server_errors(status):
    url = "https://dev.example.com/apps"
    r = classify(url, url, status, [url], "Not found")
    assert r.outcome == "error" and r.wall_host is None
    assert "couldn't reach the console" in r.asks_for.lower()


def test_network_error_is_error():
    url = "https://dev.example.com/apps"
    r = classify(url, url, None, [url], "", error="ConnectError: boom")
    assert r.outcome == "error" and "couldn't reach the console" in r.asks_for.lower()


@pytest.mark.parametrize("status", [403, 406, 429])
def test_blocked_statuses(status):
    url = "https://dev.shopify.com/dashboard"
    r = classify(url, url, status, [url], "")
    assert r.outcome == "blocked"


def test_access_denied_text_is_blocked():
    url = "https://dev.example.com/apps"
    assert classify(url, url, 200, [url], "Access Denied. Reference #18.2d").outcome == "blocked"


def test_cloudflare_challenge_sets_bot_check():
    url = "https://dev.example.com/apps"
    r = classify(url, url, 200, [url], "Verify you are human by completing the action below.")
    assert r.bot_check


# probe_console: http first, browser retry when the http result is not a wall


def page(url: str, final: str, status: int | None, text: str, method="http", error=None) -> Page:
    return Page(url, final, [url, final] if final != url else [url], status, "t", text, text, method, error)


async def test_probe_console_http_login_wall_skips_browser(monkeypatch):
    fx = load("github")
    calls = []

    async def fake_fetch(url, **kw):
        calls.append(kw)
        return Page(url, fx["final_url"], fx["redirect_chain"], 200, "Sign in", fx["visible_text"] * 30, fx["visible_text"] * 30, "http", None)

    async def no_browser(*a, **k):
        raise AssertionError("browser should not run")

    monkeypatch.setattr(fetch, "fetch_page", fake_fetch)
    monkeypatch.setattr(fetch, "fetch_with_browser", no_browser)
    r = await probe.probe_console(fx["console_url"])
    assert r.outcome == "login_wall" and r.method == "http"
    assert calls[0].get("allow_browser") is False


async def test_probe_console_retries_with_browser(monkeypatch):
    fx = load("shopify")

    async def fake_fetch(url, **kw):
        return page(url, url, 406, "")

    async def fake_browser(url, **kw):
        return Page(url, fx["final_url"], fx["redirect_chain"], 200, "Log in", fx["visible_text"], fx["visible_text"], "browser", None)

    monkeypatch.setattr(fetch, "fetch_page", fake_fetch)
    monkeypatch.setattr(fetch, "fetch_with_browser", fake_browser)
    r = await probe.probe_console(fx["console_url"])
    assert r.outcome == "login_wall" and r.method == "browser" and r.wall_host == "accounts.shopify.com"


async def test_probe_console_keeps_http_result_if_browser_unavailable(monkeypatch):
    url = "https://dev.shopify.com/dashboard"

    async def fake_fetch(u, **kw):
        return page(u, u, 406, "")

    async def broken_browser(u, **kw):
        return page(u, u, None, "", method="browser", error="playwright missing")

    monkeypatch.setattr(fetch, "fetch_page", fake_fetch)
    monkeypatch.setattr(fetch, "fetch_with_browser", broken_browser)
    r = await probe.probe_console(url)
    assert r.outcome == "blocked" and r.method == "http"


async def test_probe_console_network_error_is_error(monkeypatch):
    url = "https://dev.example.com/apps"

    async def fake_fetch(u, **kw):
        return page(u, u, None, "", error="ConnectError")

    async def broken_browser(u, **kw):
        return page(u, u, None, "", method="browser", error="ConnectError")

    monkeypatch.setattr(fetch, "fetch_page", fake_fetch)
    monkeypatch.setattr(fetch, "fetch_with_browser", broken_browser)
    r = await probe.probe_console(url)
    assert r.outcome == "error" and "couldn't reach the console" in r.asks_for.lower()


def test_js_shell_console_is_not_reported_as_open_without_a_caveat():
    from app.probe import classify

    r = classify("https://app.todoist.com/app/settings/integrations/app-management",
                 "https://app.todoist.com/app/settings/integrations/app-management", 200, [], "Todoist")
    assert r.outcome == "console_reachable" and "JavaScript" in r.asks_for and "could not be observed" in r.asks_for
