"""L1: fetch_page, html_to_texts and the browser fallback decision. No network, no real Chromium."""

import pathlib

import httpx
import pytest

from app import fetch
from app.fetch import Page, fetch_page, html_to_texts, needs_browser

PAGES = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "pages"
LONG = "Lorem ipsum dolor sit amet. " * 40  # well over 500 characters


def make_page(**kw) -> Page:
    base = dict(requested_url="https://a.test/x", final_url="https://a.test/x", redirect_chain=["https://a.test/x"],
                status=200, title="t", visible_text=LONG, hidden_text=LONG, method="http", error=None)
    return Page(**{**base, **kw})


# html_to_texts


@pytest.fixture(scope="module")
def texts():
    return html_to_texts((PAGES / "hidden_sections.html").read_text())


def test_title_extracted(texts):
    assert texts[2] == "Configure OAuth consent | Example Docs"


def test_visible_text_keeps_shown_content(texts):
    visible = texts[0]
    for shown in ["You can enter up to 10 callback URLs", "Publishing status", "This section starts expanded",
                  "Read the docs, then click Continue."]:
        assert shown in visible


def test_collapsed_text_only_in_all_text(texts):
    visible, everything, _ = texts
    for hidden in ["up to 100 test users", "25 unverified redirect URIs", "Tokens expire after 8 hours",
                   "Hidden attribute paragraph", "Aria hidden paragraph", "Inline display none paragraph"]:
        assert hidden not in visible, hidden
        assert hidden in everything, hidden


def test_script_style_noscript_template_dropped(texts):
    for text in texts[:2]:
        assert "SCRIPT-ONLY-TOKEN" not in text
        assert "display: none" not in text and ".zippy" not in text
    assert "noscript text" not in texts[0]
    assert "Template only text" not in texts[0]


def test_empty_html():
    assert html_to_texts("") == ("", "", "")


# needs_browser


def test_needs_browser_rules():
    assert not needs_browser(make_page())
    assert needs_browser(make_page(visible_text="x" * 499))
    assert not needs_browser(make_page(visible_text="x" * 500))
    for status in (400, 403, 404, 406, 429):
        assert needs_browser(make_page(status=status))
    assert not needs_browser(make_page(status=500))
    assert needs_browser(make_page(status=None, error="boom", visible_text=""))
    assert needs_browser(make_page(error="boom"))


def test_needs_browser_console_mode():
    same_host = make_page(requested_url="https://dev.spotify.com/dashboard", final_url="https://dev.spotify.com/dashboard")
    assert needs_browser(same_host, console=True)
    assert not needs_browser(same_host)
    wall = make_page(requested_url="https://dev.spotify.com/dashboard", final_url="https://accounts.spotify.com/en/login")
    assert not needs_browser(wall, console=True)


# fetch_page over a mock transport


def mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


HTML = f"<html><head><title>Docs</title></head><body><p>{LONG}</p><details><summary>More</summary>secret detail</details></body></html>"


async def test_fetch_follows_redirects_and_records_chain():
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append((req.method, str(req.url), req.headers["user-agent"]))
        if req.url.path == "/old":
            return httpx.Response(301, headers={"location": "/mid"})
        if req.url.path == "/mid":
            return httpx.Response(302, headers={"location": "https://b.test/new"})
        return httpx.Response(200, text=HTML, headers={"content-type": "text/html"})

    async with mock_client(handler) as client:
        page = await fetch_page("https://a.test/old", allow_browser=False, client=client)
    assert page.redirect_chain == ["https://a.test/old", "https://a.test/mid", "https://b.test/new"]
    assert page.requested_url == "https://a.test/old" and page.final_url == "https://b.test/new"
    assert page.status == 200 and page.title == "Docs" and page.method == "http" and page.error is None
    assert "secret detail" in page.hidden_text and "secret detail" not in page.visible_text
    assert page.html.startswith("<html>")
    assert {m for m, _, _ in seen} == {"GET"}
    assert all("Mozilla/5.0" in ua for _, _, ua in seen)


async def test_fetch_network_error_returns_page_not_raise():
    def handler(req):
        raise httpx.ConnectError("boom", request=req)

    async with mock_client(handler) as client:
        page = await fetch_page("https://a.test/x", allow_browser=False, client=client)
    assert page.status is None and page.error and "ConnectError" in page.error
    assert page.requested_url == page.final_url == "https://a.test/x"
    assert page.redirect_chain == ["https://a.test/x"] and page.visible_text == ""


async def test_fetch_unexpected_exception_still_returns_page():
    def handler(req):
        raise RuntimeError("weird")

    async with mock_client(handler) as client:
        page = await fetch_page("https://a.test/x", allow_browser=False, client=client)
    assert page.status is None and "weird" in page.error


async def test_fetch_error_status_kept():
    async with mock_client(lambda r: httpx.Response(404, text="nope")) as client:
        page = await fetch_page("https://a.test/x", allow_browser=False, client=client)
    assert page.status == 404 and page.error is None


# browser fallback decision (browser function monkeypatched)


@pytest.fixture()
def browser_calls(monkeypatch):
    calls: list[str] = []

    async def fake_browser(url, *, timeout=20.0):
        calls.append(url)
        return make_page(requested_url=url, final_url=url, redirect_chain=[url], method="browser", title="Rendered")

    monkeypatch.setattr(fetch, "fetch_with_browser", fake_browser)
    return calls


async def test_no_browser_when_http_page_is_rich(browser_calls):
    async with mock_client(lambda r: httpx.Response(200, text=HTML)) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert browser_calls == [] and page.method == "http"


async def test_browser_when_text_is_thin(browser_calls):
    async with mock_client(lambda r: httpx.Response(200, text="<html><title>x</title><body>Loading</body></html>")) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert browser_calls == ["https://a.test/x"] and page.method == "browser" and page.title == "Rendered"


async def test_browser_when_4xx(browser_calls):
    async with mock_client(lambda r: httpx.Response(406, text=LONG)) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert browser_calls and page.method == "browser"


async def test_browser_when_network_error(browser_calls):
    def handler(req):
        raise httpx.ConnectError("boom", request=req)

    async with mock_client(handler) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert browser_calls and page.method == "browser"


async def test_allow_browser_false_never_calls_browser(browser_calls):
    async with mock_client(lambda r: httpx.Response(200, text="tiny")) as client:
        page = await fetch_page("https://a.test/x", allow_browser=False, client=client)
    assert browser_calls == [] and page.method == "http"


async def test_browser_failure_keeps_http_page_with_error_noted(monkeypatch):
    async def broken(url, *, timeout=20.0):
        return make_page(status=None, error="playwright not installed", method="browser", visible_text="")

    monkeypatch.setattr(fetch, "fetch_with_browser", broken)
    async with mock_client(lambda r: httpx.Response(200, text="<title>T</title>short")) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert page.method == "http" and page.status == 200 and page.title == "T"
    assert page.error and "playwright not installed" in page.error


async def test_browser_exception_never_raises(monkeypatch):
    async def exploding(url, *, timeout=20.0):
        raise RuntimeError("chromium crashed")

    monkeypatch.setattr(fetch, "fetch_with_browser", exploding)
    async with mock_client(lambda r: httpx.Response(200, text="short")) as client:
        page = await fetch_page("https://a.test/x", client=client)
    assert page.method == "http" and "chromium crashed" in page.error


async def test_close_browser_is_safe_when_never_started():
    await fetch.close_browser()
