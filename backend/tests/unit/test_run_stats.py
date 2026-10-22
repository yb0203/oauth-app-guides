"""Run statistics (CONTRACT §4 item 8) and the user-selectable generation settings (CONTRACT §3)."""

import json

import pytest
from fastapi.testclient import TestClient

from app import api, ask, config, settings, stream
from app.llm import LLM
from app.runstats import RunStats, summarize_llm
from tests.unit.test_ask import FakeLLM as AskFakeLLM, guide
from tests.unit.test_pipeline import FakeLLM, collect, fake_page, fetcher, prober, searcher  # noqa: F401

PRIMARY, FALLBACK = "minimax/minimax-m3.1-flash:free", "nvidia/nemotron-3-ultra-550b-a55b:free"


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.setenv("FAKE_SPEED", "0")
    monkeypatch.delenv("ALLOWED_MODELS", raising=False)
    monkeypatch.delenv("LLM_MODEL_PRIMARY", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("GENERATE_RATE_LIMIT", raising=False)
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)


def call(model, outcome="ok", tokens=(100, 20), cost=None):
    return {"label": "x", "model": model, "seconds": 1.0, "outcome": outcome, "tokens": tokens, "cost": cost}


# --- totals ---------------------------------------------------------------------------------------------------

def test_summary_adds_up_across_models_retries_and_failures():
    log = [call(PRIMARY, tokens=(1000, 200)), call(PRIMARY, tokens=(500, 50)),
           call(PRIMARY, "http 429", tokens=None), call(FALLBACK, tokens=(300, 70))]
    s = summarize_llm(log)
    assert s["llm"]["calls"] == 4 and s["llm"]["failed_calls"] == 1
    assert (s["llm"]["input_tokens"], s["llm"]["output_tokens"]) == (1800, 320)
    assert s["llm"]["by_model"][PRIMARY] == {"calls": 3, "input_tokens": 1500, "output_tokens": 250}
    assert s["llm"]["by_model"][FALLBACK] == {"calls": 1, "input_tokens": 300, "output_tokens": 70}
    assert sum(m["input_tokens"] for m in s["llm"]["by_model"].values()) == s["llm"]["input_tokens"]
    assert s["cost_usd"] == 0.0


def test_tokens_are_null_when_no_call_reported_any_and_provider_cost_is_preferred():
    s = summarize_llm([call(PRIMARY, "timeout after 45s", tokens=None)])
    assert s["llm"]["input_tokens"] is None and s["llm"]["output_tokens"] is None and s["llm"]["calls"] == 1
    assert summarize_llm([call(PRIMARY, cost=0.0123), call(PRIMARY, cost=0.0077)])["cost_usd"] == 0.02
    assert summarize_llm([])["llm"] == {"calls": 0, "failed_calls": 0, "input_tokens": None, "output_tokens": None, "by_model": {}}


async def test_llm_records_reported_tokens_per_call():
    from pydantic import BaseModel
    from pydantic_ai.messages import ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    class Thing(BaseModel):
        n: int

    llm = LLM("a/one:free", "b/two:free", model_factory=lambda n: FunctionModel(
        lambda m, i: ModelResponse(parts=[TextPart('{"n": 1}')])))
    await llm.run(Thing, "i", "prompt", label="t")
    rec = llm.call_log[0]
    assert rec["model"] == "a/one:free" and rec["outcome"] == "ok" and rec["label"] == "t"
    assert rec["tokens"] is None or all(isinstance(t, int) for t in rec["tokens"])


# --- stream part ----------------------------------------------------------------------------------------------

def test_run_stats_part_shape():
    stats = RunStats("GitHub", "live", {"model": PRIMARY, "fallback_model": FALLBACK, "max_pages": 5, "probe_console": True})
    stats.pages_fetched, stats.quotes_checked = 6, 31
    stats.watch(stream.stage("resolve", "running"))
    stats.watch(stream.stage("resolve", "done"))
    ev = stream.parse_sse(stream.run_stats(stats.to_dict([call(PRIMARY)])))[0]
    assert ev["type"] == "data-run-stats" and ev["id"] == "run-stats"
    d = ev["data"]
    assert set(d) == {"run_id", "app", "mode", "total_seconds", "stages", "llm", "cost_usd", "pages_fetched",
                      "quotes_checked", "config"}
    assert d["stages"]["resolve"]["status"] == "done" and d["stages"]["resolve"]["seconds"] >= 0
    assert set(d["llm"]) == {"calls", "failed_calls", "input_tokens", "output_tokens", "by_model"}
    assert d["pages_fetched"] == 6 and d["quotes_checked"] == 31 and d["config"]["max_pages"] == 5


# --- pipeline: stats on every path ------------------------------------------------------------------------------

class CountingLLM(FakeLLM):
    """Records calls with known token usage, like the real LLM class would."""

    def __init__(self, github):
        super().__init__(github)
        self.call_log = []

    async def run(self, output_type, instructions, prompt, *, label="", **kw):
        self.call_log.append(call(PRIMARY, tokens=(1000, 100)))
        return await super().run(output_type, instructions, prompt, label=label, **kw)


def stats_of(events):
    return next(e for e in events if isinstance(e, dict) and e["type"] == "data-run-stats")["data"]


async def test_success_run_reports_stage_times_tokens_pages_and_quotes(github_guide_dict, monkeypatch):
    events = await collect("github", CountingLLM(github_guide_dict))
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert types[-2:] == ["data-run-stats", "finish"] and events[-1] == "[DONE]"
    d = stats_of(events)
    assert d["mode"] == "live" and d["app"] == "github"
    assert list(d["stages"]) == ["resolve", "find_docs", "research", "probe", "synthesize", "verify", "publish"]
    assert all(v["status"] == "done" and v["seconds"] >= 0 for v in d["stages"].values())
    assert d["llm"]["calls"] == 3 and d["llm"]["failed_calls"] == 0  # 1 page extraction + 2 writer parts
    assert (d["llm"]["input_tokens"], d["llm"]["output_tokens"]) == (3000, 300)
    assert d["llm"]["by_model"][PRIMARY]["calls"] == 3
    assert d["pages_fetched"] >= 2 and d["quotes_checked"] >= 2 and d["cost_usd"] == 0.0


async def test_error_run_still_reports_stats(github_guide_dict):
    events = await collect("github", CountingLLM(github_guide_dict), searcher=lambda q, n: [])
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert types[-2:] == ["data-run-stats", "finish"] and "error" in types
    d = stats_of(events)
    assert d["stages"]["find_docs"]["status"] == "error" and d["llm"]["calls"] == 0


async def test_degraded_run_reports_stats(github_guide_dict):
    from tests.unit.test_pipeline import SlowSynthLLM

    class Both(SlowSynthLLM, CountingLLM):
        pass

    events = await collect("github", Both(github_guide_dict))
    d = stats_of(events)
    assert d["stages"]["synthesize"]["status"] == "done" and d["llm"]["calls"] >= 1


async def test_missing_key_error_path_has_stats(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    events = await collect("github", None)
    assert stats_of(events)["llm"]["calls"] == 0


def test_stats_are_logged_as_one_json_line(caplog):
    caplog.set_level("INFO", logger="runstats")
    stats = RunStats("x", "live", {})
    stats.log_line(stats.to_dict([call(PRIMARY)]))
    line = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("run_stats "))
    assert json.loads(line.removeprefix("run_stats "))["llm"]["calls"] == 1


# --- /ask -----------------------------------------------------------------------------------------------------

async def test_ask_stream_sends_run_stats_without_stages_before_finish():
    req = ask.AskRequest("how many organisations can connect?", {}, [])
    events = stream.parse_sse("".join([c async for c in ask.ask_stream(guide("xero"), req, mode="fake")]))
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert types[-2:] == ["data-run-stats", "finish"]
    d = stats_of(events)
    assert "stages" not in d and d["mode"] == "fake" and d["llm"]["calls"] == 0 and d["app"] == "xero"


async def test_ask_live_stats_come_from_the_llm_call_log(monkeypatch):
    class Logged(AskFakeLLM):
        call_log = [call("nvidia/nemotron-3-ultra-550b-a55b:free", tokens=(4000, 120))]
        model_names = ["nvidia/nemotron-3-ultra-550b-a55b:free"]

    out = ask.LLMAnswer(covered=True, answer_text="Five [1].", citations=[ask.LLMCitation(marker="1", ref="limits.0")])
    a = await ask.answer_question(guide("xero"), "q", {}, [], mode="live", llm=Logged(out))
    assert a.calls[0]["tokens"] == (4000, 120) and a.model == "nvidia/nemotron-3-ultra-550b-a55b:free"


# --- allow-list and config --------------------------------------------------------------------------------------

def test_default_allow_list_is_free_models_only(monkeypatch):
    assert settings.allowed_ids() == settings.DEFAULT_ALLOWED and all(m.endswith(":free") for m in settings.allowed_ids())


def test_non_free_and_malformed_env_entries_are_ignored(monkeypatch):
    monkeypatch.setenv("ALLOWED_MODELS", "openai/gpt-5, minimax/minimax-m3.1-flash:free ,anthropic/claude-opus-5-5,bad id:free,"
                                          "google/gemma-4-31b-it:free")
    assert settings.allowed_ids() == ["minimax/minimax-m3.1-flash:free", "google/gemma-4-31b-it:free"]
    monkeypatch.setenv("ALLOWED_MODELS", "openai/gpt-5")  # nothing valid: back to the safe default list
    assert settings.allowed_ids() == settings.DEFAULT_ALLOWED


def test_config_defaults_and_fallback_is_a_different_allow_listed_model():
    cfg = settings.resolve_config(None)
    assert (cfg.model, cfg.max_pages, cfg.probe_console) == (PRIMARY, 5, True)
    assert cfg.fallback_model != cfg.model and cfg.fallback_model in settings.allowed_ids()
    assert cfg.fallback_model == FALLBACK  # the other tested model comes first
    other = settings.resolve_config({"model": FALLBACK, "max_pages": 8, "probe_console": False})
    assert (other.max_pages, other.probe_console, other.fallback_model) == (8, False, PRIMARY)
    assert settings.resolve_config({}).as_dict() == cfg.as_dict()


@pytest.mark.parametrize("raw,fragment", [
    ({"model": "openai/gpt-5"}, "Only free models"),
    ({"model": "anthropic/claude-opus-5-5"}, "Only free models"),
    ({"model": "someone/unlisted:free"}, "isn't offered"),
    ({"model": 5}, "Choose one of"),
    ({"max_pages": 4}, "max_pages must be one of 3, 5, 8"),
    ({"max_pages": True}, "max_pages must be one of"),
    ({"probe_console": "yes"}, "probe_console must be true or false"),
    ("minimax", "config must be an object"),
])
def test_bad_config_is_rejected_in_plain_language(raw, fragment):
    with pytest.raises(Exception) as exc:
        settings.resolve_config(raw)
    assert exc.value.status_code == 400 and fragment in exc.value.detail


@pytest.fixture()
def client():
    return TestClient(api.create_app())


def test_generate_rejects_paid_models_with_http_400_before_streaming(client):
    r = client.post("/api/generate", json={"app": "xero", "config": {"model": "openai/gpt-5"}})
    assert r.status_code == 400 and "free" in r.json()["detail"].lower()
    r = client.post("/api/generate", json={"messages": [{"role": "user", "content": "xero"}], "config": {"max_pages": 99}})
    assert r.status_code == 400


def test_generate_echoes_the_effective_config_in_narration_and_stats(client):
    body = {"app": "xero", "config": {"model": FALLBACK, "max_pages": 8, "probe_console": False}}
    ev = stream.parse_sse(client.post("/api/generate", json=body).text)
    narration = [e["delta"] for e in ev if isinstance(e, dict) and e["type"] == "text-delta"]
    assert narration[0].startswith("Demo replay")  # fake mode: the replay label always comes first
    assert any(n.startswith("Using NVIDIA Nemotron 3 Ultra (free), 8 pages") for n in narration)
    assert stats_of(ev)["config"] == {"model": FALLBACK, "fallback_model": PRIMARY, "max_pages": 8, "probe_console": False}


async def test_live_run_uses_the_chosen_models_and_page_limit_and_narrates_it(github_guide_dict, monkeypatch):
    from app.pipeline import run_pipeline

    cfg = settings.resolve_config({"model": FALLBACK, "max_pages": 3, "probe_console": False})
    made = {}

    class Spy(CountingLLM):
        def __init__(self, primary, fallback):
            super().__init__(github_guide_dict)
            made.update(primary=primary, fallback=fallback)

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setattr("app.pipeline.LLM", Spy)
    seen = []

    def searcher_(q, n):
        seen.append(q)
        return [{"href": f"https://docs.github.com/en/apps/oauth-apps/p{i}"} for i in range(6)]

    probed = []

    async def prober_(url):
        probed.append(url)
        raise AssertionError("probe is turned off")

    ev = stream.parse_sse("".join([e async for e in run_pipeline("github", config=cfg, searcher=searcher_, fetcher=fetcher, prober=prober_)]))
    first_text = next(e for e in ev if isinstance(e, dict) and e["type"] == "text-delta")["delta"]
    assert first_text == "Using NVIDIA Nemotron 3 Ultra (free), 3 pages"
    assert made == {"primary": FALLBACK, "fallback": PRIMARY} and probed == []
    d = stats_of(ev)
    assert d["config"]["max_pages"] == 3 and d["stages"]["probe"]["status"] == "skipped"
    guide_ev = next(e for e in ev if isinstance(e, dict) and e["type"] == "data-guide")
    assert len([s for s in guide_ev["data"]["guide"]["sources"] if s["kind"] != "observation"]) <= 3


async def test_models_endpoint_lists_only_allow_listed_free_models(client, monkeypatch):
    async def offline():
        return {PRIMARY: {"context_length": 1000000}}

    monkeypatch.setattr(settings, "_openrouter_models", offline)
    r = client.get("/api/models")
    assert r.status_code == 200
    d = r.json()
    assert d["default"] == PRIMARY and [m["id"] for m in d["models"]] == settings.DEFAULT_ALLOWED
    assert all(m["free"] is True and m["id"].endswith(":free") for m in d["models"])
    first = d["models"][0]
    assert first["label"] == "MiniMax M3.1 Flash (free)" and first["context_length"] == 1000000 and first["tested"] is True
    assert d["models"][1]["context_length"] is None  # not in the (partial) live list: tolerated
    assert d["options"] == {"max_pages": {"default": 5, "choices": [3, 5, 8]}, "probe_console": {"default": True}}


async def test_openrouter_catalog_failure_is_tolerated(monkeypatch):
    import httpx

    settings._catalog_cache.update(at=0.0, models={})

    async def boom(self, url, **kw):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", boom)
    payload = await settings.models_payload()
    assert [m["id"] for m in payload["models"]] == settings.DEFAULT_ALLOWED
    assert all(m["context_length"] is None for m in payload["models"])


def test_super_model_is_no_longer_in_the_default_allow_list():
    assert "nvidia/nemotron-3-super-120b-a12b:free" not in settings.DEFAULT_ALLOWED
    assert [m.id for m in settings.allowed_models()] == [PRIMARY, FALLBACK]


async def test_models_missing_from_the_live_list_or_that_returned_404_are_marked_untested(monkeypatch):
    monkeypatch.setenv("ALLOWED_MODELS", f"{PRIMARY},{FALLBACK}")

    async def live():
        return {PRIMARY: {"context_length": 1000000}}  # OpenRouter no longer lists the second model

    monkeypatch.setattr(settings, "_openrouter_models", live)
    by_id = {m["id"]: m for m in (await settings.models_payload())["models"]}
    assert by_id[PRIMARY]["tested"] is True and by_id[FALLBACK]["tested"] is False
    assert "not available right now" in by_id[FALLBACK]["notes"]
    settings.mark_unavailable(PRIMARY)  # what the LLM layer does on an HTTP 404
    try:
        assert (await settings.models_payload())["models"][0]["tested"] is False
    finally:
        settings._unavailable.clear()


async def test_llm_marks_a_model_unavailable_on_404():
    from pydantic import BaseModel
    from pydantic_ai.exceptions import ModelHTTPError
    from pydantic_ai.models.function import FunctionModel

    class T(BaseModel):
        n: int

    def gone(_m, _i):
        raise ModelHTTPError(404, "x/gone:free", body="not found")

    llm = LLM("x/gone:free", "x/gone:free", model_factory=lambda n: FunctionModel(gone), max_attempts_per_model=1)
    with pytest.raises(Exception):
        await llm.run(T, "i", "p")
    assert settings._recently_404("x/gone:free")
    settings._unavailable.clear()
