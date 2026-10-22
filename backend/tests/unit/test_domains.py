import pytest

from app.domains import host_of, is_official, official_domains, registrable, source_kind


@pytest.mark.parametrize("url,expected", [
    ("https://developer.todoist.com/api/v1/", "official_docs"),
    ("https://todoist.com/help", "official_docs"),
    ("https://doist.github.io/todoist-sdk-typescript/authorization/", "official_docs"),  # the vendor's own org
    ("https://doist.com/blog", "official_docs"),
    ("https://automatisch.io/docs/apps/todoist/connection", "community"),
    ("https://developer.transmitsecurity.com/guides/integrations/todoist", "community"),
    ("https://docs.n8n.io/integrations/todoist/", "community"),
    ("https://someone.github.io/todoist-notes/", "community"),  # other people's github.io pages
    ("https://docs.composio.dev/toolkits/todoist", "composio_docs"),
    ("https://notatodoist.example.com/x", "community"),
])
def test_todoist_source_kinds(url, expected):
    assert source_kind(url, "todoist", "Todoist") == expected


def test_other_providers():
    assert source_kind("https://docs.github.com/en/apps", "github", "GitHub") == "official_docs"
    assert source_kind("https://developers.google.com/gmail/api", "gmail", "Gmail") == "official_docs"
    assert source_kind("https://developers.google.com/calendar", "googlecalendar", "Google Calendar") == "official_docs"
    assert source_kind("https://support.google.com/cloud/answer/1", "google_drive", "Google Drive") == "official_docs"
    assert source_kind("https://dev.shopify.com/dashboard", "shopify", "Shopify") == "official_docs"
    assert source_kind("https://medium.com/@x/xero-oauth", "xero", "Xero") == "community"
    assert source_kind("https://developer.xero.com/documentation", "xero", "Xero") == "official_docs"


def test_helpers():
    assert host_of("https://www.Xero.com/path") == "xero.com" and host_of("todoist.com") == "todoist.com"
    assert registrable("developer.todoist.com") == "todoist.com" and registrable("a.b.co.uk") == "b.co.uk"
    assert "doist.github.io" in official_domains("todoist", "Todoist")
    assert is_official("https://learn.acme.dev/x", "acme", "Acme", official_domains("acme", "Acme", ["https://acme.dev"]))
