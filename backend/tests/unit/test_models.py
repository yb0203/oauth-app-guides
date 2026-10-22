import copy

import pytest
from pydantic import ValidationError

from app.models import Guide


def test_github_guide_validates_and_roundtrips(github_guide_dict):
    g = Guide.model_validate(github_guide_dict)
    assert g.slug == "github" and g.guide_type == "curated"
    assert g.model_dump(mode="json") == github_guide_dict  # exact shape, no extra/missing keys


def broken(d, fn):
    d = copy.deepcopy(d)
    fn(d)
    return d


@pytest.mark.parametrize("mutate", [
    lambda d: d.pop("verdict"),
    lambda d: d["verdict"].update(tier="easy"),
    lambda d: d["steps"][0].pop("actor"),
    lambda d: d["steps"][0].update(actor="human", human_reason=None),
    lambda d: d["steps"][1].update(evidence={"label": "DOCS", "source_id": None, "quote": None, "found_in": None, "note": None}),
    lambda d: d["steps"][1]["evidence"].update(label="MAYBE"),
    lambda d: d["steps"][1]["evidence"].update(label="DOCS", found_in=None),
    lambda d: d.update(extra_field=1),
])
def test_broken_guides_fail(github_guide_dict, mutate):
    with pytest.raises(ValidationError):
        Guide.model_validate(broken(github_guide_dict, mutate))
