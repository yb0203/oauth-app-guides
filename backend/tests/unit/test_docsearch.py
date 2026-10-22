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
