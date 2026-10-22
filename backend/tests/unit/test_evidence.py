import copy

import pytest
from pydantic import ValidationError

from app.evidence import PageText, apply_verification, verification_summary
from app.models import Evidence, Guide, iter_evidence

QUOTE = "A user or organization can own up to 100 OAuth apps"
PAGE_FILLER = "Creating an OAuth app. Some unrelated documentation text goes here. "


def guide_with_limit_evidence(github_guide_dict) -> Guide:
    """GitHub guide whose first limit is an unverified DOCS claim (found_in reset after validation)."""
    d = copy.deepcopy(github_guide_dict)
    d["limits"][0]["evidence"].update(source_id="s1", quote=QUOTE)
    g = Guide.model_validate(d)
    g.limits[0].evidence.found_in = None
    return g


def test_visible_quote_sets_found_in_visible(github_guide_dict):
    g = guide_with_limit_evidence(github_guide_dict)
    downgrades = apply_verification(g, {"s1": PageText(visible=PAGE_FILLER + QUOTE, hidden=PAGE_FILLER + QUOTE)})
    ev = g.limits[0].evidence
    assert (ev.label, ev.found_in) == ("DOCS", "visible")
    assert not [d for d in downgrades if d.location.startswith("limits[0]")]


def test_hidden_only_quote_stays_docs_hidden_section(github_guide_dict):
    g = guide_with_limit_evidence(github_guide_dict)
    apply_verification(g, {"s1": PageText(visible=PAGE_FILLER, hidden=PAGE_FILLER + QUOTE)})
    ev = g.limits[0].evidence
    assert (ev.label, ev.found_in) == ("DOCS", "hidden_section")


def test_quote_not_found_downgrades_with_reason(github_guide_dict):
    g = guide_with_limit_evidence(github_guide_dict)
    downgrades = apply_verification(g, {"s1": PageText(visible=PAGE_FILLER, hidden=PAGE_FILLER)})
    ev = g.limits[0].evidence
    assert ev.label == "UNCERTAIN" and ev.found_in is None
    assert "not found" in ev.note and QUOTE in ev.note  # reason recorded, old quote kept in the note
    d = next(d for d in downgrades if d.location == "limits[0]")
    assert d.source_id == "s1" and d.quote == QUOTE and "not found" in d.reason


def test_near_miss_is_not_a_match(github_guide_dict):
    g = guide_with_limit_evidence(github_guide_dict)
    page = PAGE_FILLER + QUOTE.replace("100", "200")
    apply_verification(g, {"s1": PageText(visible=page, hidden=page)})
    assert g.limits[0].evidence.label == "UNCERTAIN"


def test_missing_source_page_downgrades(github_guide_dict):
    g = guide_with_limit_evidence(github_guide_dict)
    downgrades = apply_verification(g, {})
    ev = g.limits[0].evidence
    assert ev.label == "UNCERTAIN" and "page" in ev.note
    assert any(d.location == "limits[0]" and "page" in d.reason for d in downgrades)


def test_too_weak_quote_downgrades(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    g = Guide.model_validate(d)
    ev = g.limits[0].evidence
    ev.quote = "100 apps"  # shorter than 12 chars once normalised; bypasses validation by mutation
    ev.found_in = None
    downgrades = apply_verification(g, {"s1": PageText(visible="up to 100 apps here", hidden="up to 100 apps here")})
    assert ev.label == "UNCERTAIN"
    assert any("short" in x.reason or "weak" in x.reason for x in downgrades)


def test_tested_and_uncertain_are_left_alone(github_guide_dict):
    g = Guide.model_validate(github_guide_dict)
    keep = [e.model_dump() for e in iter_evidence(g) if e.label in ("TESTED", "UNCERTAIN")]
    apply_verification(g, {})
    assert [e.model_dump() for e in iter_evidence(g) if e.model_dump() in keep][: len(keep)] == keep
    assert sum(e.label == "TESTED" for e in iter_evidence(g)) == 2


def test_community_with_quote_is_checked_without_quote_is_not(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    d["gotchas"][0]["evidence"] = {"label": "COMMUNITY", "source_id": "s2", "quote": "People on the forum say this is slow", "found_in": None, "note": None}
    d["gotchas"][1]["evidence"] = {"label": "COMMUNITY", "source_id": "s2", "quote": None, "found_in": None, "note": "anecdote"}
    g = Guide.model_validate(d)
    apply_verification(g, {"s2": PageText(visible="nothing", hidden="nothing")})
    assert g.gotchas[0].evidence.label == "UNCERTAIN"
    assert g.gotchas[1].evidence.label == "COMMUNITY"


def test_tested_without_note_fails_validation():
    with pytest.raises(ValidationError):
        Evidence(label="TESTED", source_id="s5")


def test_apply_verification_on_unverified_github_guide_downgrades_all_docs(github_guide_dict):
    g = Guide.model_validate(github_guide_dict)
    docs = sum(e.label == "DOCS" for e in iter_evidence(g))
    downgrades = apply_verification(g, {})
    assert len(downgrades) == docs and docs > 0
    assert not any(e.label == "DOCS" for e in iter_evidence(g))


def counts_add_up(s):
    return s.tested + s.docs_verified + s.community + s.uncertain == s.total


def test_summary_matches_curated_github_guide(github_guide_dict):
    g = Guide.model_validate(github_guide_dict)
    s = verification_summary(g)
    assert counts_add_up(s)
    assert s.model_dump() == github_guide_dict["verification_summary"]


def test_summary_counts_add_up_on_mutated_guide(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    d["limits"][0]["evidence"]["found_in"] = "hidden_section"
    d["gotchas"][0]["evidence"] = {"label": "COMMUNITY", "source_id": "s2", "quote": None, "found_in": None, "note": "forum"}
    d["steps"][1]["evidence"] = {"label": "UNCERTAIN", "note": "unknown"}
    s = verification_summary(Guide.model_validate(d))
    assert counts_add_up(s)
    assert (s.docs_hidden, s.community, s.total) == (1, 1, 17)
    assert s.docs_verified == 10  # all DOCS incl. the hidden one (12 minus those turned community/uncertain)
    assert s.uncertain == 4


def test_summary_recomputed_for_every_curated_guide():
    import glob
    import json

    from app import config

    files = sorted(glob.glob(str(config.CURATED_DIR / "*.json")))
    assert files
    for f in files:
        raw = json.load(open(f))
        g = Guide.model_validate(raw)
        s = verification_summary(g, g.conflicts)
        assert s.model_dump() == raw["verification_summary"], f
        assert s.tested + s.docs_verified + s.community + s.uncertain == s.total
