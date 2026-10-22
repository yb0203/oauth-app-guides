import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    return ROOT


@pytest.fixture()
def github_guide_dict() -> dict:
    return json.loads((ROOT / "data/guides/github.json").read_text())


@pytest.fixture(scope="session")
def poc_runs() -> pathlib.Path:
    return ROOT / "experiments/oauth-capture-poc/runs"
