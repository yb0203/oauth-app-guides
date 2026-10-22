"""A stalled or blocked stage must never silence the stream, and a slow stage must not sink the run."""

import asyncio
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app import api, config, pipeline, stream
from tests.unit.test_pipeline import FakeLLM, collect, fetcher, prober, searcher
from tests.unit.test_run_stats import CountingLLM, stats_of


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.delenv("GENERATE_RATE_LIMIT", raising=False)
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)


# --- the keep-alive cannot be starved ------------------------------------------------------------------------

async def test_pings_continue_while_the_pipeline_thread_blocks_its_own_event_loop():
    def blocking_source():
        async def gen():
            yield stream.start("m")
            time.sleep(1.2)  # synchronous: blocks the pipeline's loop, as heavy parsing or a bad regex would
            yield stream.finish()
            yield stream.DONE
        return gen()

    out = [c async for c in stream.run_in_thread(blocking_source, interval=0.05)]
    assert out.count(stream.PING) >= 10
    assert [c for c in out if c != stream.PING] == [stream.start("m"), stream.finish(), stream.DONE]


def test_api_stream_pings_while_a_stage_blocks(monkeypatch):
    import sys
    import types

    monkeypatch.setenv("HEARTBEAT_SECONDS", "0.05")

    async def run_pipeline(app, **kw):
        yield stream.start("m1")
        time.sleep(1.0)  # a stage that blocks the loop for "30 seconds", scaled down
        yield stream.finish()
        yield stream.DONE

    monkeypatch.setitem(sys.modules, "app.pipeline", types.SimpleNamespace(run_pipeline=run_pipeline))
    r = TestClient(api.create_app()).post("/api/generate", json={"app": "xero"})
    assert r.text.count(": ping") >= 8
    assert stream.parse_sse(r.text) == [{"type": "start", "messageId": "m1"}, {"type": "finish"}, "[DONE]"]


async def test_errors_from_the_pipeline_thread_reach_the_consumer():
    def failing():
        async def gen():
            yield stream.start("m")
            raise ValueError("boom")
        return gen()

    got = []
    with pytest.raises(ValueError):
        async for c in stream.run_in_thread(failing, interval=0.05):
            got.append(c)
    assert got == [stream.start("m")]


async def test_closing_the_stream_cancels_the_worker():
    stopped = threading.Event()

    def endless():
        async def gen():
            try:
                yield stream.start("m")
                await asyncio.sleep(60)
            finally:
                stopped.set()
        return gen()

    agen = stream.run_in_thread(endless, interval=0.05)
    assert await agen.__anext__() == stream.start("m")
    await agen.aclose()
    for _ in range(40):
        if stopped.is_set():
            break
        await asyncio.sleep(0.05)
    assert stopped.is_set()


# --- stage deadlines: continue with what we have ---------------------------------------------------------------

class SlowPageLLM(CountingLLM):
    """Extraction for the page of source s2 never returns."""

    async def run(self, output_type, instructions, prompt, *, label="", **kw):
        if label.endswith(":s2"):
            await asyncio.sleep(3600)
        return await super().run(output_type, instructions, prompt, label=label, **kw)


async def test_a_page_that_never_finishes_is_abandoned_at_the_research_deadline(github_guide_dict, monkeypatch):
    monkeypatch.setattr(pipeline, "RESEARCH_STAGE_S", 0.5)

    def many(q, n):
        return [{"href": f"https://docs.github.com/en/apps/oauth-apps/page{i}"} for i in range(3)]

    t0 = time.monotonic()
    events = await collect("github", SlowPageLLM(github_guide_dict), searcher=many)
    assert time.monotonic() - t0 < 10
    types = [e["type"] for e in events if isinstance(e, dict)]
    assert "data-guide" in types and types[-2:] == ["data-run-stats", "finish"] and events[-1] == "[DONE]"
    narration = "".join(e["delta"] for e in events if isinstance(e, dict) and e["type"] == "text-delta")
    assert "Stopped waiting for 1 slow page" in narration
    assert stats_of(events)["stages"]["research"]["status"] == "done"


async def test_find_docs_deadline_ends_the_run_cleanly(github_guide_dict, monkeypatch):
    monkeypatch.setattr(pipeline, "FIND_DOCS_STAGE_S", 0.2)

    async def stuck_fetch(url):
        await asyncio.sleep(3600)

    events = await collect("github", FakeLLM(github_guide_dict), fetcher=stuck_fetch)
    types = [e["type"] for e in events if isinstance(e, dict)]
    err = next(e for e in events if isinstance(e, dict) and e["type"] == "error")
    assert "longer than" in err["errorText"] and types[-2:] == ["data-run-stats", "finish"] and events[-1] == "[DONE]"
    assert stats_of(events)["stages"]["find_docs"]["status"] == "error"


async def test_probe_deadline_skips_the_probe_and_still_publishes(github_guide_dict, monkeypatch):
    monkeypatch.setattr(pipeline, "PROBE_STAGE_S", 0.2)

    async def stuck_probe(url):
        await asyncio.sleep(3600)

    from app.pipeline import run_pipeline

    events = stream.parse_sse("".join([e async for e in run_pipeline(
        "github", llm=FakeLLM(github_guide_dict), searcher=searcher, fetcher=fetcher, prober=stuck_probe)]))
    probe = [e["data"] for e in events if isinstance(e, dict) and e["type"] == "data-stage" and e["id"] == "probe"][-1]
    assert probe["status"] == "skipped" and probe["detail"] == "probe timed out"
    assert any(isinstance(e, dict) and e["type"] == "data-guide" for e in events)
