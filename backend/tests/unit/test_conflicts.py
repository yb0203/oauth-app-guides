import copy

from app.evidence import find_conflicts
from app.models import Guide


def limit(what, value, quote, scope="per organisation", unit="apps", label="DOCS", source="s1"):
    return {
        "what": what, "value": value, "unit": unit, "scope": scope,
        "evidence": {"label": label, "source_id": source, "quote": quote, "found_in": "visible", "note": None},
    }


def guide_with(github_guide_dict, *limits) -> Guide:
    d = copy.deepcopy(github_guide_dict)
    d["limits"] = list(limits)
    return Guide.model_validate(d)


def test_differing_values_make_one_conflict_with_both_evidences(github_guide_dict):
    g = guide_with(
        github_guide_dict,
        limit("Uncertified apps", 5, "You can connect up to 5 uncertified apps", source="s1"),
        limit("Uncertified apps", 2, "Limited to 2 uncertified apps per organisation", source="s2"),
    )
    conflicts = find_conflicts(g)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert "uncertified" in c.field.lower()
    assert {e.quote for e in c.evidence} == {"You can connect up to 5 uncertified apps", "Limited to 2 uncertified apps per organisation"}
    assert "5" in c.description and "2" in c.description
    assert len(g.limits) == 2  # neither dropped from the guide


def test_what_and_scope_are_normalised(github_guide_dict):
    g = guide_with(
        github_guide_dict,
        limit("Uncertified  apps", 5, "You can connect up to 5 uncertified apps"),
        limit("uncertified APPS", 2, "Limited to 2 uncertified apps per organisation", scope="Per Organisation"),
    )
    assert len(find_conflicts(g)) == 1


def test_equal_values_no_conflict(github_guide_dict):
    g = guide_with(
        github_guide_dict,
        limit("Uncertified apps", 5, "You can connect up to 5 uncertified apps"),
        limit("Uncertified apps", 5, "Limited to 5 uncertified apps per organisation"),
    )
    assert find_conflicts(g) == []


def test_single_claim_no_conflict(github_guide_dict):
    assert find_conflicts(Guide.model_validate(github_guide_dict)) == []


def test_different_scope_is_not_a_conflict(github_guide_dict):
    g = guide_with(
        github_guide_dict,
        limit("Uncertified apps", 5, "You can connect up to 5 uncertified apps", scope="per organisation"),
        limit("Uncertified apps", 2, "Limited to 2 uncertified apps per user", scope="per user"),
    )
    assert find_conflicts(g) == []


def test_non_docs_claims_are_ignored(github_guide_dict):
    g = guide_with(
        github_guide_dict,
        limit("Uncertified apps", 5, "You can connect up to 5 uncertified apps"),
        limit("Uncertified apps", 2, "forum post says only 2 apps", label="COMMUNITY"),
    )
    assert find_conflicts(g) == []
