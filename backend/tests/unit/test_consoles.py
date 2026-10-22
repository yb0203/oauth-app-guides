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
