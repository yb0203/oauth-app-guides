from app.fetch import Page
from app.research import Claim, PageClaims, select_relevant, verify_claims


def page(text: str, hidden: str = "") -> Page:
    return Page("http://x", "http://x", [], 200, "t", text, hidden or text, "http", None)


def test_select_relevant_keeps_short_pages_and_budgets_long_ones():
    assert select_relevant("a\n\nb") == "a\nb"
    long = "\n".join(["filler words here"] * 2000 + ["You can enter up to 10 callback URLs for OAuth."])
    out = select_relevant(long, budget=500)
    assert len(out) <= 500 and "callback URLs" in out


def test_verify_claims_keeps_only_quotes_found_on_page():
    p = page("Apps are limited to 100 users. Hidden limits live elsewhere.", hidden="secret cap is 25 installs per app")
    pc = PageClaims(claims=[
        Claim(text="100 users", quote="Apps are limited to 100 users."),
        Claim(text="made up", quote="Apps are limited to 5000 users."),
        Claim(text="hidden", quote="secret cap is 25 installs per app"),
    ])
    got = verify_claims("s1", p, pc)
    assert [(v.id, v.found_in) for v in got] == [("c1", "visible"), ("c2", "hidden_section")]
