import copy

from app.markdown import guide_to_markdown
from app.models import Guide


def test_contains_core_content(github_guide_dict):
    md = guide_to_markdown(github_guide_dict)
    g = github_guide_dict
    assert g["app_name"] in md and g["verdict"]["tier"] in md.replace("_", "_")
    assert g["composio"]["callback_url"] in md
    assert g["wall_probe"]["console_url"] in md and g["wall_probe"]["outcome"] in md
    for s in g["sources"]:
        assert s["url"] in md and s["title"] in md
    vs = g["verification_summary"]
    assert f"{vs['docs_verified']}" in md and f"{vs['total']}" in md and "uncertain" in md.lower()


def test_steps_in_order_with_actor_and_reason(github_guide_dict):
    md = guide_to_markdown(github_guide_dict)
    pos = -1
    for step in github_guide_dict["steps"]:
        i = md.index(step["title"])
        assert i > pos, step["title"]
        pos = i
    assert "human" in md and "credential" in md and "submit" in md and "either" in md
    assert "Evidence" in md or "DOCS" in md


def test_human_reason_text_appears_per_step(github_guide_dict):
    md = guide_to_markdown(github_guide_dict)
    start = md.index(github_guide_dict["steps"][0]["title"])
    end = md.index(github_guide_dict["steps"][1]["title"])
    assert "human" in md[start:end] and "credential" in md[start:end]


def test_accepts_dict_or_guide_and_is_not_raw_json(github_guide_dict):
    a = guide_to_markdown(github_guide_dict)
    assert a == guide_to_markdown(Guide.model_validate(github_guide_dict))
    assert a.lstrip().startswith("# ") and '"schema_version"' not in a and "{'" not in a


def test_table_cells_escape_pipes(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    d["limits"][0]["what"] = "Apps | per owner"
    d["situations"]["variants"][0]["summary"] = "orgs | approve\nlater"
    md = guide_to_markdown(d)
    assert "Apps \\| per owner" in md and "Apps | per owner" not in md
    assert "orgs \\| approve later" in md


def test_irreversible_flag_and_conflicts_render(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    d["steps"][5]["irreversible"] = True
    ev = {"label": "DOCS", "source_id": "s1", "quote": "five uncertified apps allowed", "found_in": "visible", "note": None}
    d["conflicts"] = [{"field": "Uncertified apps", "description": "5 vs 2", "evidence": [ev, {**ev, "quote": "two uncertified apps allowed"}]}]
    md = guide_to_markdown(d)
    assert "irreversible" in md.lower()
    assert "Uncertified apps" in md and "five uncertified apps allowed" in md and "two uncertified apps allowed" in md


def test_works_without_wall_probe(github_guide_dict):
    d = copy.deepcopy(github_guide_dict)
    d["wall_probe"] = None
    assert github_guide_dict["app_name"] in guide_to_markdown(d)
