"""Production stall (Asana): the SSE iterator must never die silently, whatever strings flow through it."""

import asyncio
import json
import sys
import threading
import types

import pytest
from fastapi.testclient import TestClient

from app import api, config, runs, store, stream
from app.fetch import Page
from app.models import Guide
from tests.unit.test_pipeline import FakeLLM, collect, prober
from tests.unit.test_run_stats import stats_of

ODD = [
    "\ud83d",                       # lone high surrogate (what a model's \ud83d escape decodes to)
    "ok \ude00 tail",               # lone low surrogate
    "😀 paired is fine",  # a valid pair written as two surrogates stays well-formed JSON
    "nul\x00 bell\x07 esc\x1b del\x7f",
    "line\nbreak\ttab\r\n",
    "   separators",
    "x" * 300_000,
    "emoji 🚀 and 日本語 and ñ",
    "",
]


@pytest.mark.parametrize("value", ODD)
def test_every_event_encodes_to_ascii_utf8_and_parses_back(value):
    for chunk in (stream.source_url("s1", f"https://x.test/{value[:5]}", value), stream.text(value),
                  stream.text_chunks(value), stream.stage("research", "running", detail=value),
                  stream.error(value), stream.citations([{"fact": value}]),
                  stream.guide_part("x", {"title": value, "n": None})):
        raw = chunk.encode("utf-8")  # must not raise
        assert raw.isascii()
        events = stream.parse_sse(chunk)
        assert events and all(isinstance(e, dict) for e in events)


def test_none_and_non_json_values_do_not_break_encoding():
    chunk = stream.source_url("s1", None, None)  # type: ignore[arg-type]
    assert stream.parse_sse(chunk)[0]["title"] is None
    assert stream.parse_sse(stream.sse({"type": "x", "data": {"when": types.SimpleNamespace}}))  # default=str


def test_to_bytes_repairs_a_raw_chunk_with_a_lone_surrogate():
    assert stream.to_bytes("data: ok \ud83d\n\n") == "data: ok ?\n\n".encode()
    assert stream.to_bytes(b"raw") == b"raw"


def test_store_clean_removes_surrogates_and_control_characters_but_keeps_text():
    cleaned = store.clean({"a": ["x\ud83dy", {"b": "nul\x00z\n\tkeep 🚀"}], "n": 3, "none": None})
    assert cleaned == {"a": ["x�y", {"b": "nul�z\n\tkeep 🚀"}], "n": 3, "none": None}
    json.dumps(cleaned, ensure_ascii=False).encode("utf-8")  # encodable


# --- the forum page ---------------------------------------------------------------------------------------------

FORUM = "https://forum.asana.com/t/support-http-localhost-loopback-redirect-uris-for-oauth/12345"
DOCS = "https://developers.asana.com/docs/oauth"
QUOTE = "You must register your application and set a redirect URI"


class OddLLM(FakeLLM):
    """Returns claims and prose full of characters that used to be able to break the stream."""

    async def run(self, output_type, instructions, prompt, *, label="", **kw):
        from app.research import Claim, PageClaims

        if output_type is PageClaims:
            return PageClaims(console_url="https://app.asana.com/0/developer-console",
                              claims=[Claim(category="registration", text="Register \ud83d the app \x00 first", quote=QUOTE)])
        return await super().run(output_type, instructions, prompt, label=label, **kw)


async def test_forum_page_with_odd_title_and_odd_model_output_still_streams_to_the_end(github_guide_dict, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)
    body = "Asana OAuth: create a client id, redirect URI and scopes. " + QUOTE + ". " + "filler " * 200

    async def fetch(url):
        title = "Support localhost \U0001f680 \x00 \x1b[31mred\ud83d" if "forum" in url else "OAuth | Asana"
        return Page(url, url, [], 200, title, body, body, "http", None)

    events = await collect("Asana", OddLLM(github_guide_dict), fetcher=fetch,
                           searcher=lambda q, n: [{"href": u} for u in (FORUM, DOCS)])
    types_ = [e["type"] for e in events if isinstance(e, dict)]
    assert "source-url" in types_ and "data-guide" in types_ and types_[-2:] == ["data-run-stats", "finish"]
    assert events[-1] == "[DONE]"
    assert any(e["type"] == "source-url" and "forum.asana.com" in e["url"] for e in events if isinstance(e, dict))
    guide = next(e for e in events if isinstance(e, dict) and e["type"] == "data-guide")["data"]["guide"]
    Guide.model_validate(guide)
    json.dumps(guide, ensure_ascii=False).encode("utf-8")  # a response built from it cannot fail either
    assert not any(0xD800 <= ord(c) <= 0xDFFF for c in json.dumps(guide, ensure_ascii=False))
    assert store.get_guide("asana") is not None  # published and readable


# --- transport guard --------------------------------------------------------------------------------------------

def run_with(monkeypatch, run_pipeline):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setitem(sys.modules, "app.pipeline", types.SimpleNamespace(run_pipeline=run_pipeline))
    return TestClient(api.create_app()).post("/api/generate", json={"app": "xero"})


def test_a_raw_chunk_with_a_lone_surrogate_is_repaired_not_fatal(monkeypatch):
    async def run_pipeline(app, **kw):
        yield stream.start("r1")
        yield "data: {\"type\":\"text-delta\",\"id\":\"a\",\"delta\":\"bad \ud83d\"}\n\n"  # bypasses sse()
        yield stream.finish()
        yield stream.DONE

    r = run_with(monkeypatch, run_pipeline)
    ev = stream.parse_sse(r.text)
    assert ev[0]["type"] == "start" and ev[-1] == "[DONE]" and any(e.get("type") == "text-delta" for e in ev if isinstance(e, dict))


def test_an_exception_in_the_transport_ends_the_stream_with_error_stats_finish_done(monkeypatch):
    async def explode(source):  # simulates the layer between the pipeline thread and the socket failing
        raise RuntimeError("boom")
        yield  # pragma: no cover

    async def run_pipeline(app, **kw):
        yield stream.start("r2")
        yield stream.finish()

    monkeypatch.setattr(stream, "run_in_thread", lambda factory, **kw: factory())
    runs.start("r2", "xero", lambda: {"run_id": "r2", "llm": {"calls": 0}})

    async def failing_pipeline(app, **kw):
        yield stream.start("r2")
        raise RuntimeError("encoder exploded")

    monkeypatch.setattr(api, "_guarded", lambda source: source)  # let the raw failure reach the transport
    r = run_with(monkeypatch, failing_pipeline)
    ev = stream.parse_sse(r.text)
    types_ = [e["type"] if isinstance(e, dict) else e for e in ev]
    assert types_ == ["start", "error", "data-run-stats", "finish", "[DONE]"]
    assert "/api/runs/r2" in ev[1]["errorText"] and ev[2]["data"]["run_id"] == "r2"


def test_every_tenth_event_is_logged(monkeypatch, caplog):
    caplog.set_level("INFO", logger="app.api")

    async def run_pipeline(app, **kw):
        yield stream.start("r3")
        for i in range(24):
            yield stream.text(f"line {i}")
        yield stream.finish()
        yield stream.DONE

    run_with(monkeypatch, run_pipeline)
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("stream run=")]
    assert len(lines) >= 2 and all("type=" in line for line in lines)
    assert any(r.getMessage().startswith("stream ended: run=r3") for r in caplog.records)


# --- runs registry and endpoint -----------------------------------------------------------------------------------

def test_run_status_follows_the_stream_and_is_served_by_the_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.setenv("FAKE_SPEED", "0")
    client = TestClient(api.create_app())
    ev = stream.parse_sse(client.post("/api/generate", json={"app": "xero"}).text)
    run_id = ev[0]["messageId"]
    r = client.get(f"/api/runs/{run_id}")
    assert r.status_code == 200
    d = r.json()
    assert set(d) == {"status", "stage", "slug", "permalink", "error", "updated_at"}
    assert d["status"] == "done" and d["slug"] == "xero" and d["permalink"] == "/guides/xero" and d["stage"] == "publish"
    assert client.get("/api/runs/nope").status_code == 404


def test_failed_run_reports_its_error(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.setenv("FAKE_SPEED", "0")
    client = TestClient(api.create_app())
    ev = stream.parse_sse(client.post("/api/generate", json={"app": "!error"}).text)
    d = client.get(f"/api/runs/{ev[0]['messageId']}").json()
    assert d["status"] == "error" and d["error"] and d["slug"] is None


async def test_live_run_is_recorded_and_ends_done(github_guide_dict, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)
    events = await collect("github", FakeLLM(github_guide_dict))
    rec = runs.get(events[0]["messageId"])
    assert rec and rec.status == "done" and rec.slug == "github" and rec.stage == "publish"


def test_runs_registry_is_bounded():
    for i in range(runs.MAX_RUNS + 20):
        runs.start(f"bound-{i}", "x")
    assert runs.get("bound-0") is None and runs.get(f"bound-{runs.MAX_RUNS + 19}") is not None


# --- a client that disconnects does not stop the run ---------------------------------------------------------------

async def test_run_keeps_going_and_publishes_after_the_client_disconnects():
    done = threading.Event()

    def factory():
        async def gen():
            yield stream.start("m")
            await asyncio.sleep(0.4)
            done.set()  # "publish" happens after the client is gone
            yield stream.finish()
        return gen()

    agen = stream.run_in_thread(factory, interval=0.05, cancel_on_close=False)
    assert await agen.__anext__() == stream.start("m")
    await agen.aclose()  # the client disconnects
    for _ in range(40):
        if done.is_set():
            break
        await asyncio.sleep(0.05)
    assert done.is_set()
