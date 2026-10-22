from app.docsearch import covers_topic, find_docs, score_url
from app.fetch import Page

TEXT = "Creating a TikTok app with OAuth. Register your client id and redirect URI. " + "word " * 200


def page(url, text=TEXT, status=200):
    return Page(url, url, [], status, "t", text, text, "http", None)


def test_official_docs_outrank_blogs_repos_and_versioned_pages():
    official = score_url("https://developers.tiktok.com/docs/en/getting-started-create-an-app", "tiktok", "TikTok", [])
    blog = score_url("https://medium.com/x/tiktok-oauth", "tiktok", "TikTok", [])
    repo = score_url("https://github.com/someone/TikTok-API", "tiktok", "TikTok", [])
    old = score_url("https://docs.github.com/en/enterprise-server@3.2/apps/x", "github", "GitHub", ["docs.github.com"])
    current = score_url("https://docs.github.com/en/apps/x", "github", "GitHub", ["docs.github.com"])
    assert official > blog and official > repo and old < current


def test_covers_topic_rejects_short_errors_and_off_topic_pages():
    assert covers_topic(page("https://x"), "TikTok")
    assert not covers_topic(page("https://x", text="TikTok OAuth"), "TikTok")  # too short
    assert not covers_topic(page("https://x", status=404), "TikTok")
    assert not covers_topic(page("https://x", text="Pasta recipes. " * 100), "TikTok")


async def test_find_docs_filters_and_dedupes():
    urls = ["https://developers.tiktok.com/docs/a", "https://developers.tiktok.com/docs/a#frag",
            "https://developers.tiktok.com/docs/b", "https://developers.tiktok.com/docs/c"]

    async def fetch(url):
        return page(url, text="nothing here" if url.endswith("/c") else TEXT)

    good, rejected = await find_docs("TikTok", "tiktok", search=lambda q, n: [{"href": u} for u in urls], fetch=fetch)
    assert [p.final_url for p in good] == ["https://developers.tiktok.com/docs/a", "https://developers.tiktok.com/docs/b"]
    assert rejected == ["https://developers.tiktok.com/docs/c"]


def test_official_pages_need_not_name_the_app():
    consent = Page("https://developers.google.com/workspace/guides/configure-oauth-consent", "https://developers.google.com/workspace/guides/configure-oauth-consent",
                   [], 200, "t", "Configure the OAuth consent screen and choose scopes. " + "word " * 200, "", "http", None)
    assert not covers_topic(consent, "Gmail")  # third-party rule: must mention the app
    assert covers_topic(consent, "Gmail", need_name=False)


async def test_gmail_gets_three_official_google_pages_before_any_third_party():
    official = [f"https://developers.google.com/gmail/{i}" for i in range(3)] + ["https://support.google.com/cloud/answer/1"]
    third = ["https://nylas.com/gmail-oauth"]
    text = "Set up the OAuth consent screen, scopes and a client id for your app. " + "word " * 200

    def searcher(q, n):
        return [{"href": u} for u in (official if "site:" in q else third)]

    seen: list[str] = []

    async def fetch(url):
        seen.append(url)
        return Page(url, url, [], 200, "t", text, "", "http", None)

    good, _ = await find_docs("Gmail", "gmail", search=searcher, fetch=fetch)
    assert len(good) >= 3 and all("google.com" in p.final_url for p in good)
    assert "https://nylas.com/gmail-oauth" not in seen


# --- Gmail relevance (round 2): off-topic Google products and junk limits ------------------------------------------

from app.docsearch import OFF_TOPIC_PATH, official_queries, vendor_for  # noqa: E402

OFF_TOPIC = ["https://docs.cloud.google.com/integration-connectors/docs/connectors/gsc_gmail/configure",
             "https://docs.cloud.google.com/contact-center/ccai-platform/docs/oauth-email-google",
             "https://developers.google.com/apps-script/guides/services"]
ON_TOPIC = ["https://support.google.com/cloud/answer/15549945", "https://support.google.com/cloud/answer/13464325",
            "https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification",
            "https://developers.google.com/workspace/guides/configure-oauth-consent"]


def test_off_topic_google_products_are_recognised_by_url():
    assert all(OFF_TOPIC_PATH.search(u) for u in OFF_TOPIC)
    assert not any(OFF_TOPIC_PATH.search(u) for u in ON_TOPIC)


async def test_find_docs_drops_off_topic_urls_even_when_search_returns_them_first():
    text = "Configure OAuth: create a client id, set the redirect URI and choose scopes. " + "word " * 200
    fetched: list[str] = []

    async def fetch(url):
        fetched.append(url)
        return Page(url, url, [], 200, "t", text, "", "http", None)

    good, _ = await find_docs("Gmail", "gmail", search=lambda q, n: [{"href": u} for u in OFF_TOPIC + ON_TOPIC], fetch=fetch)
    assert not any(OFF_TOPIC_PATH.search(p.final_url) for p in good) and not any(OFF_TOPIC_PATH.search(u) for u in fetched)
    assert {p.final_url for p in good} == set(ON_TOPIC)


def test_vendor_family_queries_are_added_for_gmail_but_not_for_a_standalone_app():
    assert vendor_for("gmail", "Gmail") == "Google" and vendor_for("googlecalendar", "Google Calendar") == "Google"
    qs = official_queries("Gmail", ["support.google.com"], "Google")
    assert any(q.startswith("Google OAuth consent screen user cap") for q in qs)
    assert any(q.startswith("Google restricted scope verification") for q in qs)
    assert any(q.startswith("Google OAuth app verification") for q in qs)
    assert not any(q.startswith("Todoist restricted scope") for q in official_queries("Todoist", ["todoist.com"], "Todoist"))
    assert len(official_queries("Todoist", ["todoist.com"], "Todoist")) == len(qs) - 3


def test_a_page_about_only_one_setup_word_does_not_cover_the_topic():
    thin = Page("https://x.com/a", "https://x.com/a", [], 200, "t", "Pasta with OAuth sauce. " + "word " * 200, "", "http", None)
    assert not covers_topic(thin, "Pasta")


async def test_one_page_that_raises_or_is_malformed_is_skipped_not_fatal():
    good_text = "Set up OAuth: create a client id and redirect URI for the Notion app. " + "word " * 200

    async def fetch(url):
        if url.endswith("boom"):
            raise AttributeError("'NavigableString' object has no attribute 'parent'")
        if url.endswith("none"):
            return Page(url, url, [], 200, "t", None, None, "http", None)  # malformed: no text at all
        return Page(url, url, [], 200, "t", good_text, "", "http", None)

    urls = ["https://developers.notion.com/boom", "https://developers.notion.com/none",
            "https://developers.notion.com/a", "https://developers.notion.com/b"]
    good, rejected = await find_docs("Notion", "notion", search=lambda q, n: [{"href": u} for u in urls], fetch=fetch)
    assert [p.final_url for p in good] == ["https://developers.notion.com/a", "https://developers.notion.com/b"]
    assert len(rejected) == 2
