import pathlib

from app.consoles import console_candidates
from app.fetch import Page

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "pages"


def page(html: str, url="https://developer.todoist.com/api/v1/", text="") -> Page:
    return Page(url, url, [], 200, "t", text, text, "http", None, html)


def test_todoist_docs_page_yields_the_app_management_console():
    html = (FIXTURES / "todoist_api_excerpt.html").read_text()
    got = console_candidates(page(html), "todoist", "Todoist")
    assert got[0] == "https://app.todoist.com/app/settings/integrations/app-management"
    assert not any("oauth/authorize" in u or "example.com" in u or "github.com" in u for u in got)


def test_no_console_link_gives_empty_list():
    assert console_candidates(page("<a href='https://todoist.com/help'>Help</a>"), "todoist", "Todoist") == []


def test_console_url_in_plain_text_counts():
    text = "Create your app at https://developer.acme.com/apps/new before continuing."
    assert console_candidates(page("", "https://docs.acme.com/x", text), "acme", "Acme") == ["https://developer.acme.com/apps/new"]


def test_third_party_console_lookalikes_are_ignored():
    html = "<a href='https://other.example.org/app-management'>App Management Console</a>"
    assert console_candidates(page(html), "todoist", "Todoist") == []


import pytest  # noqa: E402

from app import store  # noqa: E402
from app.consoles import looks_like_console  # noqa: E402


@pytest.mark.parametrize("url,ok", [
    ("https://console.cloud.google.com/auth/overview", True),
    ("https://app.todoist.com/app/settings/integrations/app-management", True),
    ("https://developer.spotify.com/dashboard", True),
    ("https://dev.shopify.com/dashboard", True),
    ("https://developer.xero.com/app/manage", True),
    ("https://developers.google.com/apps-script", False),  # the wrong console the Gmail smoke run probed
    ("https://developers.google.com/gmail/api/guides", False),
    ("https://app.todoist.com/oauth/authorize", False),
    ("http://insecure.example.com/console", False),
    ("https://developers.zoom.us/docs/integrations/create/", False),  # a docs page, the Zoom smoke run probed it
    ("https://marketplace.zoom.us/develop/create", True),
    ("https://developer.spotify.com/documentation/web-api/concepts/apps", False),
])
def test_looks_like_console(url, ok):
    assert looks_like_console(url) is ok


def test_curated_guides_seed_the_console_url_by_guide_or_toolkit_slug():
    assert store.curated_console("gmail") == "https://console.cloud.google.com/auth/overview"
    assert store.curated_console("google-gmail") == "https://console.cloud.google.com/auth/overview"
    assert store.curated_console("github") == "https://github.com/settings/applications/new"
    assert store.curated_console("some-unknown-app") is None


def test_docs_page_linking_to_itself_is_not_a_console():
    html = "<a href='/docs/integrations/create/'>Create an OAuth app</a>"
    p = page(html, "https://developers.zoom.us/docs/integrations/create/")
    assert console_candidates(p, "zoom", "Zoom") == []
