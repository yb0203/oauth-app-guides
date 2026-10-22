import json
import sys
import types

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import api, config, stream
from app.models import Guide


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.setenv("FAKE_SPEED", "0")
    monkeypatch.delenv("GENERATE_RATE_LIMIT", raising=False)
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path / "generated")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(api.create_app())


def events_of(resp) -> list:
    return stream.parse_sse(resp.text)


def use_pipeline(monkeypatch, run_pipeline) -> None:
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setitem(sys.modules, "app.pipeline", types.SimpleNamespace(run_pipeline=run_pipeline))


# --- extract_app_input -------------------------------------------------------------------------


def test_extract_from_app_field():
    assert api.extract_app_input({"app": "  xero "}) == "xero"


def test_extract_from_usechat_content_string():
    body = {"messages": [{"role": "user", "content": "first"}, {"role": "assistant", "content": "hm"},
                         {"role": "user", "content": "Shopify"}]}
    assert api.extract_app_input(body) == "Shopify"


def test_extract_from_usechat_parts():
    body = {"messages": [{"role": "user", "id": "1", "parts": [
        {"type": "step-start"}, {"type": "text", "text": "https://www."}, {"type": "text", "text": "xero.com"}]}]}
    assert api.extract_app_input(body) == "https://www.xero.com"


def test_extract_ignores_trailing_assistant_message():
    body = {"messages": [{"role": "user", "parts": [{"type": "text", "text": "slack"}]},
                         {"role": "assistant", "parts": [{"type": "text", "text": "ok"}]}]}
    assert api.extract_app_input(body) == "slack"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"app": ""},
        {"app": "   "},
        {"app": 5},
        {"messages": []},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "parts": [{"type": "step-start"}]}]},
        {"messages": [{"role": "assistant", "content": "hello"}]},
        {"messages": "nope"},
        ["xero"],
        {"app": "x" * 500},
    ],
)
def test_extract_rejects_bad_input(body):
    with pytest.raises(HTTPException) as exc:
        api.extract_app_input(body)
    assert exc.value.status_code == 422


# --- read endpoints ----------------------------------------------------------------------------


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"ok": True}


def test_catalog(client):
    r = client.get("/api/catalog")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 100
    assert {"slug", "name", "composio_status", "tier_guess", "has_guide"} <= set(rows[0])
    assert any(row["slug"] == "github" and row["has_guide"] for row in rows)


def test_guides_list_includes_curated_github(client):
    rows = client.get("/api/guides").json()
    github = next(r for r in rows if r["slug"] == "github")
    assert set(github) == {"slug", "app_name", "guide_type", "tier", "last_verified"}
    assert github["guide_type"] == "curated"


def test_get_guide(client):
    r = client.get("/api/guides/github")
    assert r.status_code == 200
    assert Guide.model_validate(r.json()).slug == "github"


def test_get_generated_guide(client, github_guide_dict):
    github_guide_dict.update(slug="acme", app_name="Acme", guide_type="generated")
    config.GENERATED_DIR.mkdir(parents=True)
    (config.GENERATED_DIR / "acme.json").write_text(json.dumps(github_guide_dict))
    assert client.get("/api/guides/acme").json()["app_name"] == "Acme"
    assert any(g["slug"] == "acme" for g in client.get("/api/guides").json())


@pytest.mark.parametrize("slug", ["nope", "..%2Fsecret", "UPPER"])
def test_get_guide_404(client, slug):
    assert client.get(f"/api/guides/{slug}").status_code == 404
    assert client.get(f"/api/guides/{slug}/markdown").status_code == 404


def test_markdown_export(client):
    r = client.get("/api/guides/github/markdown")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "GitHub" in r.text and "{" not in r.text.splitlines()[0]


# --- POST /api/generate (fake mode) --------------------------------------------------------------


def test_generate_fake_stream_and_headers(client):
    r = client.post("/api/generate", json={"app": "xero"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache"
    assert r.headers["x-vercel-ai-ui-message-stream"] == "v1"
    assert r.headers["x-accel-buffering"] == "no"
    events = events_of(r)
    assert events[0]["type"] == "start"
    assert events[-2:] == [{"type": "finish"}, "[DONE]"]
    assert r.text.endswith("data: [DONE]\n\n")
    [part] = [e for e in events if isinstance(e, dict) and e["type"] == "data-guide"]
    assert part["data"]["slug"] == "xero"
    assert Guide.model_validate(part["data"]["guide"]).guide_type == "generated"


def test_generate_accepts_usechat_body(client):
    body = {"messages": [{"role": "user", "parts": [{"type": "text", "text": "Totally Unknown App"}]}]}
    events = events_of(client.post("/api/generate", json=body))
    [part] = [e for e in events if isinstance(e, dict) and e["type"] == "data-guide"]
    assert part["data"]["slug"] == "totally-unknown-app"


@pytest.mark.parametrize("body", [{}, {"app": " "}, {"messages": []}])
def test_generate_rejects_empty_input(client, body):
    assert client.post("/api/generate", json=body).status_code == 422


def test_generate_rejects_invalid_json(client):
    r = client.post("/api/generate", content=b"not json", headers={"content-type": "application/json"})
    assert r.status_code == 422


# --- POST /api/generate (live pipeline wiring) ---------------------------------------------------


def test_generate_live_streams_pipeline_output(client, monkeypatch):
    seen = []

    async def run_pipeline(app):
        seen.append(app)
        yield stream.start("m1")
        yield stream.text("hello")
        yield stream.finish()
        yield stream.DONE

    use_pipeline(monkeypatch, run_pipeline)
    r = client.post("/api/generate", json={"app": "xero"})
    assert seen == ["xero"]
    assert [e["type"] if isinstance(e, dict) else e for e in events_of(r)][-2:] == ["finish", "[DONE]"]
    assert r.headers["x-vercel-ai-ui-message-stream"] == "v1"


def test_pipeline_exception_becomes_error_stage_finish_done(client, monkeypatch):
    async def run_pipeline(app):
        yield stream.start("m1")
        yield stream.stage("resolve", "running")
        yield stream.stage("resolve", "done")
        yield stream.stage("research", "running")
        raise RuntimeError("secret-token-123 exploded")

    use_pipeline(monkeypatch, run_pipeline)
    r = client.post("/api/generate", json={"app": "xero"})
    assert r.status_code == 200
    events = events_of(r)
    assert "secret-token-123" not in r.text
    assert events[-1] == "[DONE]" and events[-2] == {"type": "finish"}
    assert events[-4]["type"] == "error" and events[-4]["errorText"]
    failed = events[-3]
    assert failed["type"] == "data-stage" and failed["id"] == "research" and failed["data"]["status"] == "error"


def test_failure_before_any_event_still_starts_the_stream(client, monkeypatch):
    async def run_pipeline(app):
        raise ValueError("nope")
        yield  # pragma: no cover

    use_pipeline(monkeypatch, run_pipeline)
    types_ = [e["type"] if isinstance(e, dict) else e for e in events_of(client.post("/api/generate", json={"app": "x"}))]
    assert types_ == ["start", "error", "data-stage", "finish", "[DONE]"]


def test_missing_pipeline_module_is_reported_as_stream_error(client, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setitem(sys.modules, "app.pipeline", None)  # makes the import fail
    events = events_of(client.post("/api/generate", json={"app": "x"}))
    assert any(isinstance(e, dict) and e["type"] == "error" for e in events)
    assert events[-1] == "[DONE]"


def test_pipeline_that_forgets_terminator_is_closed_properly(client, monkeypatch):
    async def run_pipeline(app):
        yield stream.start("m1")

    use_pipeline(monkeypatch, run_pipeline)
    events = events_of(client.post("/api/generate", json={"app": "x"}))
    assert events == [{"type": "start", "messageId": "m1"}, {"type": "finish"}, "[DONE]"]


# --- CORS --------------------------------------------------------------------------------------


def test_cors_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, http://localhost:3000")
    c = TestClient(api.create_app())
    for origin in ("https://app.example.com", "http://localhost:3000"):
        r = c.options("/api/generate", headers={"origin": origin, "access-control-request-method": "POST",
                                                "access-control-request-headers": "content-type"})
        assert r.headers["access-control-allow-origin"] == origin
    r = c.get("/api/health", headers={"origin": "https://app.example.com"})
    assert r.headers["access-control-allow-origin"] == "https://app.example.com"


def test_cors_rejects_other_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    r = TestClient(api.create_app()).get("/api/health", headers={"origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


# --- rate limit --------------------------------------------------------------------------------


def test_rate_limit_off_by_default_under_pytest(client):
    assert all(client.post("/api/generate", json={"app": "x"}).status_code == 200 for _ in range(8))


def test_rate_limit_blocks_after_limit(monkeypatch):
    monkeypatch.setenv("GENERATE_RATE_LIMIT", "2")
    c = TestClient(api.create_app())
    assert [c.post("/api/generate", json={"app": "x"}).status_code for _ in range(3)] == [200, 200, 429]
    r = c.post("/api/generate", json={"app": "x"})
    assert int(r.headers["retry-after"]) > 0
    assert c.get("/api/health").status_code == 200  # only /api/generate is limited


def test_rate_limit_is_per_ip(monkeypatch):
    monkeypatch.setenv("GENERATE_RATE_LIMIT", "1")
    c = TestClient(api.create_app())
    assert c.post("/api/generate", json={"app": "x"}, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
    assert c.post("/api/generate", json={"app": "x"}, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 429
    assert c.post("/api/generate", json={"app": "x"}, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 200


def test_rate_limit_zero_disables(monkeypatch):
    monkeypatch.setenv("GENERATE_RATE_LIMIT", "0")
    c = TestClient(api.create_app())
    assert all(c.post("/api/generate", json={"app": "x"}).status_code == 200 for _ in range(7))


def test_invalid_input_does_not_consume_rate_limit(monkeypatch):
    monkeypatch.setenv("GENERATE_RATE_LIMIT", "1")
    c = TestClient(api.create_app())
    assert c.post("/api/generate", json={}).status_code == 422
    assert c.post("/api/generate", json={"app": "x"}).status_code == 200


def test_module_level_app_exists():
    assert api.app.title


def test_catalog_rows_have_tier_and_guide_slug(client):
    rows = {r["slug"]: r for r in client.get("/api/catalog").json()}
    assert all({"tier", "guide_slug", "has_guide", "tier_guess"} <= set(r) for r in rows.values())
    gmail = rows["gmail"]  # catalog slug differs from the guide slug: matched by composio.toolkit_slug
    assert gmail["has_guide"] and gmail["guide_slug"] == "google-gmail" and gmail["tier"] == "review_required"
    assert rows["github"]["guide_slug"] == "github" and rows["github"]["tier"] == "instant"
    nothing = next(r for r in rows.values() if not r["has_guide"])
    assert nothing["tier"] is None and nothing["guide_slug"] is None
