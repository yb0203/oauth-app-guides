import json

import pytest

from app import config
from app.models import Guide
from app.situations import render

FIXTURE = config.REPO_ROOT / "backend/tests/fixtures/guides/gmail_situations.json"
GMAIL = config.CURATED_DIR / "google-gmail.json"

INTERNAL = {"audience": "internal"}
SEND_ONLY = {"audience": "external", "scopes": "send_only"}
READ = {"audience": "external", "scopes": "read"}


def load(path):
    return json.loads(path.read_text())


@pytest.fixture(params=[FIXTURE, pytest.param(GMAIL, marks=pytest.mark.skipif(not GMAIL.exists(), reason="no curated gmail guide"))], ids=["fixture", "curated"])
def gmail(request):
    return load(request.param)


def test_curated_gmail_three_variants_differ():
    if not GMAIL.exists():
        pytest.skip("no curated gmail guide")
    g = load(GMAIL)
    rs = [render(g, a) for a in ({"audience": "internal"}, {"audience": "external", "capability": "send"},
                                 {"audience": "external", "capability": "read"})]
    assert all(r["matched"] for r in rs) and len({r["summary"] for r in rs}) == 3
    assert "no google review" in rs[0]["summary"].lower()


def test_three_variants_have_expected_verdicts(gmail):
    if "capability" in {q["id"] for q in gmail["situations"]["questions"]}:
        pytest.skip("curated guide uses different question ids; see test_curated_gmail_three_variants_differ")
    internal, send_only, read = (render(gmail, a) for a in (INTERNAL, SEND_ONLY, READ))
    assert all(r["matched"] for r in (internal, send_only, read))
    assert "no google review" in internal["summary"].lower()
    assert "sensitive scope review" in send_only["summary"].lower() and "days" in send_only["summary"].lower()
    assert "restricted scope review" in read["summary"].lower() and "security assessment" in read["summary"].lower()
    assert len({r["summary"] for r in (internal, send_only, read)}) == 3


def test_result_shape(gmail):
    r = render(gmail, READ)
    assert set(r) == {"tier", "summary", "calendar_label", "notes", "matched"}
    assert isinstance(r["notes"], list)


@pytest.mark.parametrize("answers", [{}, {"audience": "external"}, {"scopes": "read"}, {"audience": "nobody"}])
def test_unselected_or_partial_answers_fall_back_to_base(gmail, answers):
    r = render(gmail, answers)
    base = gmail["verdict"]
    assert r == {"tier": base["tier"], "summary": base["summary"], "calendar_label": base["calendar"]["label"], "notes": [], "matched": False} or (
        # a curated guide may define a single-answer variant; then partial answers legitimately match it
        r["matched"] and answers
    )


def test_fixture_partial_answers_use_base_exactly():
    g = load(FIXTURE)
    r = render(g, {"audience": "external"})
    assert r["matched"] is False and r["summary"] == g["verdict"]["summary"] and r["notes"] == []
    assert r["calendar_label"] == g["verdict"]["calendar"]["label"]


def test_extra_answers_do_not_block_a_match():
    r = render(load(FIXTURE), {**INTERNAL, "scopes": "read"})
    assert r["matched"] and "no google review" in r["summary"].lower()


def test_first_matching_variant_wins():
    g = load(FIXTURE)
    g["situations"]["variants"].insert(0, {**g["situations"]["variants"][2], "when": {"audience": "external"}, "summary": "first"})
    assert render(g, READ)["summary"] == "first"


def test_accepts_guide_model_and_dict():
    g = load(FIXTURE)
    assert render(Guide.model_validate(g), READ) == render(g, READ)


def test_github_single_question(github_guide_dict):
    assert render(github_guide_dict, {"org_users": "orgs"})["matched"]
    assert not render(github_guide_dict, {"org_users": "personal"})["matched"]
