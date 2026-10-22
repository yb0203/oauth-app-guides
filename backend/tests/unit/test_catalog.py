import pytest

from app import catalog, store


@pytest.mark.parametrize(
    "query, slug, status",
    [
        ("gmail", "gmail", "managed"),
        ("Gmail", "gmail", "managed"),
        ("google mail", "gmail", "managed"),
        ("Shopify", "shopify", "byo"),
        ("SHOPIFY", "shopify", "byo"),
        ("https://www.xero.com", "xero", "byo"),
        ("xero.com/about", "xero", "byo"),
        ("github", "github", "managed"),
        ("Microsoft Teams", "microsoft_teams", "managed"),
        ("microsoft_teams", "microsoft_teams", "managed"),
        ("  Slack ", "slack", "managed"),
        ("Shopfy", "shopify", "byo"),  # typo tolerated
    ],
)
def test_resolves(query, slug, status):
    r = catalog.resolve(query)
    assert (r.slug, r.status, r.not_in_catalog) == (slug, status, False)
    assert r.name and r.toolkit_slug == slug and r.matched_via


def test_ambiguous_teams_gives_best_match_and_alternatives():
    r = catalog.resolve("Teams")
    assert r.slug == "microsoft_teams" and not r.not_in_catalog
    assert r.alternatives
    assert all({"slug", "name", "status"} <= set(a) for a in r.alternatives)
    assert "microsoft_teams" not in [a["slug"] for a in r.alternatives]


def test_unknown_app_is_not_in_catalog_but_can_proceed():
    r = catalog.resolve("Totally Unknown App")
    assert r.not_in_catalog is True and r.status == "not_in_catalog"
    assert r.slug == "totally-unknown-app" and r.toolkit_slug is None and r.name is None
    assert r.alternatives == []


def test_unknown_url_uses_host_label_as_slug():
    r = catalog.resolve("https://www.acmewidgets.io/docs")
    assert r.not_in_catalog and r.slug == "acmewidgets"


def test_exact_match_beats_token_match():
    assert catalog.resolve("zoom").slug == "zoom"


def test_list_catalog_has_100_apps_and_normalised_fields(monkeypatch):
    monkeypatch.setattr(store, "find_by_toolkit", lambda slug: (
        {"slug": slug, "verdict": {"tier": "instant"}} if slug == "github" else None))
    items = catalog.list_catalog()
    assert len(items) == 100
    assert all(set(i) == {"slug", "name", "composio_status", "tier_guess", "has_guide", "tier", "guide_slug"}
               for i in items)
    assert next(i for i in items if i["slug"] == "github")["tier"] == "instant"
    assert {i["composio_status"] for i in items} <= {"managed", "byo"}
    assert {i["tier_guess"] for i in items} <= {"instant", "verify_to_scale", "review_required", "partner_only", "unknown"}
    assert {i["slug"] for i in items if i["has_guide"]} == {"github"}
    gmail = next(i for i in items if i["slug"] == "gmail")
    assert gmail["name"] == "Gmail" and gmail["composio_status"] == "managed"
    assert next(i for i in items if i["slug"] == "linkedin_ads")["tier_guess"] == "partner_only"
