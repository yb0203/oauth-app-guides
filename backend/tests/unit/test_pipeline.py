"""Pipeline with a fake LLM, fake search/fetch/probe: no network."""

import json

import pytest

from app import config, stream
from app.fetch import Page
from app.models import Guide, GuideContent, WallProbe, iter_evidence
from app.pipeline import run_pipeline
from app.research import Claim, PageClaims

REAL = "You can enter up to 10 callback URLs for your OAuth app."
PAGE_TEXT = ("Creating an OAuth app. " + REAL + " Register a new application with the OAuth client ID. " + "x " * 400)


class FakeLLM:
    calls = 0

    def __init__(self, github: dict, extracted: PageClaims | None = None):
        self.github, self.extracted = github, extracted or PageClaims(
            claims=[Claim(category="limits", text="10 callback URLs", quote=REAL, value=10, unit="callback URLs")])

    async def run(self, output_type, instructions, prompt, *, label=""):
        self.calls += 1
        if output_type is PageClaims:
            return self.extracted
        content = GuideContent.model_validate({k: self.github[k] for k in GuideContent.model_fields})
        for i, ev in enumerate(iter_evidence(content)):
            if ev.label == "DOCS":
                ev.source_id, ev.quote = "s1", REAL if i % 2 == 0 else "this sentence is nowhere on the page"
        return content


def fake_page(url="https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app"):
    return Page(url, url, [], 200, "Creating an OAuth app - GitHub Docs", PAGE_TEXT, PAGE_TEXT, "http", None)


async def fetcher(url):
    return fake_page(url)


def searcher(_q, _n):
    return [{"href": "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app"}]


async def prober(url):
    return WallProbe(console_url=url, final_url="https://github.com/login", redirect_chain=["https://github.com/login"],
                     outcome="login_wall", wall_host="github.com", asks_for="GitHub account", bot_check=False,
                     method="http", observed_at="2026-10-21")


async def collect(app, llm, **kw):
    return stream.parse_sse("".join([e async for e in run_pipeline(
        app, llm=llm, searcher=kw.get("searcher", searcher), fetcher=kw.get("fetcher", fetcher), prober=prober)]))


@pytest.fixture()
def github(github_guide_dict, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)
    return github_guide_dict


async def test_happy_path(github, tmp_path):
    events = await collect("github", FakeLLM(github))
    assert events[-1] == "[DONE]" and events[-2] == {"type": "finish"}
    types = [e["type"] for e in events[:-1]]
    assert types[0] == "start" and "data-wall" in types and "source-url" in types
    stages = [e for e in events if isinstance(e, dict) and e["type"] == "data-stage"]
    assert [s["id"] for s in stages if s["data"]["status"] == "running"] == [
        "resolve", "find_docs", "research", "research", "probe", "synthesize", "verify", "publish"]
    guide_ev = next(e for e in events if isinstance(e, dict) and e["type"] == "data-guide")
    guide = Guide.model_validate(guide_ev["data"]["guide"])
    assert guide.guide_type == "generated" and guide.slug == "github"
    # fake claim quotes downgraded, real ones kept, and the wall probe added as TESTED
    assert guide.verification_summary.uncertain >= 1 and guide.verification_summary.docs_verified >= 1
    assert guide.verification_summary.tested >= 1
    assert all(e.label != "DOCS" or e.found_in for e in iter_evidence(guide))
    assert (tmp_path / "github.json").exists()
    ver = [e for e in events if isinstance(e, dict) and e["type"] == "data-verification"][-1]["data"]
    assert ver["downgraded"] >= 1


async def test_no_docs_found_ends_with_error(github):
    events = await collect("github", FakeLLM(github), searcher=lambda q, n: [])
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert "error" in types and "data-guide" not in types and events[-1] == "[DONE]"
    err_stage = [e for e in events if isinstance(e, dict) and e["type"] == "data-stage" and e["data"]["status"] == "error"]
    assert err_stage[-1]["id"] == "find_docs"


async def test_non_oauth_app_stops_without_guide(github):
    llm = FakeLLM(github, PageClaims(oauth_supported=False, claims=[]))
    events = await collect("github", llm)
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert "data-guide" not in types and "error" not in types and events[-1] == "[DONE]"
    texts = "".join(e["delta"] for e in events if isinstance(e, dict) and e["type"] == "text-delta")
    assert "doesn't offer third-party OAuth" in texts or "doesn't use OAuth" in texts


async def test_missing_key_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    events = await collect("github", None)
    err = next(e for e in events if isinstance(e, dict) and e["type"] == "error")
    assert "OPENROUTER_API_KEY" in err["errorText"] and events[-1] == "[DONE]"


async def test_live_path_builds_llm_from_env_and_runs(github, monkeypatch):
    """LLM_MODE=live wiring: with a key set and no injected llm, the pipeline builds its own LLM and uses it."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    built = []
    monkeypatch.setattr("app.pipeline.LLM", lambda: built.append(1) or FakeLLM(github))
    events = await collect("github", None)
    assert built == [1]
    assert any(isinstance(e, dict) and e["type"] == "data-guide" for e in events)


def test_default_llm_targets_free_openrouter_models(monkeypatch):
    from app.llm import LLM

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.delenv("LLM_MODEL_PRIMARY", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    llm = LLM()
    assert llm.model_names == ["nvidia/nemotron-3-super-120b-a12b:free", "minimax/minimax-m3.1-flash:free"]
    model = llm._factory(llm.model_names[0])  # constructs the OpenRouter model; makes no request
    assert type(model).__name__ == "OpenRouterModel" and model.model_name == llm.model_names[0]
