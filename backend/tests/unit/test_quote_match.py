"""L1: quote matcher (FR4). No network."""

import pathlib

import pytest

from app import verify
from app.fetch import Page, html_to_texts
from app.verify import MIN_QUOTE_LEN, check_quote_on_page, match_quote, normalize

PAGES = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "pages"
QUOTE = "You can enter up to 10 callback URLs"


def test_exact_visible_match():
    r = match_quote(QUOTE, f"Intro. {QUOTE} per app.", f"Intro. {QUOTE} per app.")
    assert r.found and r.found_in == "visible" and not r.too_weak and not r.case_differs
    assert QUOTE.lower() in r.context


def test_hidden_only_match():
    hidden = "Collapsed: Projects in Testing are limited to up to 100 test users listed in the consent screen."
    r = match_quote("limited to up to 100 test users listed", "Nothing here.", f"Nothing here. {hidden}")
    assert r.found and r.found_in == "hidden_section"


def test_absent_quote():
    r = match_quote("a sentence that does not exist anywhere", "some visible text", "some visible text")
    assert not r.found and r.found_in is None and r.context is None and not r.too_weak


def test_whitespace_and_line_breaks():
    text = "You can enter  up\nto 10\t callback\n\n URLs per app"
    assert match_quote(QUOTE, text, text).found_in == "visible"
    assert match_quote("up   to 10 \n callback URLs", text, text).found


def test_curly_vs_straight_quotes():
    page = "The app’s “client secret” must stay private."
    assert match_quote("The app's \"client secret\" must stay", page, page).found
    straight = "The app's \"client secret\" must stay private."
    assert match_quote("The app’s “client secret” must stay", straight, straight).found


def test_case_difference_is_found_and_recorded():
    page = "You Can Enter Up To 10 Callback URLs."
    r = match_quote(QUOTE, page, page)
    assert r.found and r.case_differs


def test_same_case_not_flagged():
    assert not match_quote(QUOTE, QUOTE, QUOTE).case_differs


def test_one_word_near_miss_is_not_a_match():
    page = "You can enter up to 100 callback URLs"
    assert not match_quote(QUOTE, page, page).found
    assert not match_quote(QUOTE, "You can enter up to 10 redirect URLs", "You can enter up to 10 redirect URLs").found


@pytest.mark.parametrize("quote", ["", "   ", "too short", "x" * (MIN_QUOTE_LEN - 1)])
def test_short_quote_is_too_weak(quote):
    r = match_quote(quote, f"{quote} appears here", f"{quote} appears here")
    assert r.too_weak and not r.found and r.found_in is None


def test_quote_at_min_length_is_checked():
    quote = "x" * MIN_QUOTE_LEN
    assert match_quote(quote, f"a {quote} b", f"a {quote} b").found


def test_normalize():
    assert normalize("  “Hi”  there’s \n Ok ") == "\"hi\" there's ok"


def test_fixture_page_visible_vs_hidden():
    visible, everything, _ = html_to_texts((PAGES / "hidden_sections.html").read_text())
    page = Page("u", "u", ["u"], 200, "t", visible, everything, "http", None)
    assert check_quote_on_page(page, "You can enter up to 10 callback URLs").found_in == "visible"
    hidden = check_quote_on_page(page, "limited to up to 100 test users listed in the consent screen")
    assert hidden.found and hidden.found_in == "hidden_section"
    assert check_quote_on_page(page, "limited to 25 unverified redirect URIs overall").found_in == "hidden_section"
    assert not check_quote_on_page(page, "limited to up to 25 unverified redirect URIs overall").found


def test_module_constant_matches_spec():
    assert verify.MIN_QUOTE_LEN == 12
