"""L2: the quote verifier against live pages (pytest -m network). Re-run once before trusting a failure."""

import json

import pytest
import pytest_asyncio

from app import fetch
from app.fetch import fetch_page
from app.verify import check_quote_on_page

pytestmark = [pytest.mark.network, pytest.mark.asyncio(loop_scope="module")]

GITHUB_DOCS = "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app"
GOOGLE_SUPPORT = "https://support.google.com/cloud/answer/15549945"


@pytest_asyncio.fixture(scope="module", loop_scope="module", autouse=True)
async def _close_browser():
    yield
    await fetch.close_browser()


async def test_visible_quote_on_github_docs():
    page = await fetch_page(GITHUB_DOCS)
    assert page.status == 200, page.error
    result = check_quote_on_page(page, "You can enter up to 10 callback URLs")
    assert result.found_in == "visible", result


async def test_hidden_quote_on_google_support_page():
    page = await fetch_page(GOOGLE_SUPPORT)
    assert page.status == 200, page.error
    quote = "limited to up to 100 test users listed in the OAuth consent screen"
    result = check_quote_on_page(page, quote)
    assert result.found_in == "hidden_section", (result, page.method)


async def test_made_up_sentence_is_not_found():
    page = await fetch_page(GITHUB_DOCS)
    result = check_quote_on_page(page, "GitHub grants every OAuth app unlimited callback URLs for free forever")
    assert not result.found and result.found_in is None


async def test_moved_shopify_docs_url_is_followed_and_recorded(root):
    apps = json.loads((root / "experiments/oauth-capture-poc/apps.json").read_text())
    old = next(a for a in apps if a["slug"] == "shopify")["docs_urls"][0]
    page = await fetch_page(old)
    assert page.status == 200, page.error
    assert page.final_url != old and len(page.redirect_chain) >= 2
    assert page.redirect_chain[0] == old and page.redirect_chain[-1] == page.final_url
    assert page.title
