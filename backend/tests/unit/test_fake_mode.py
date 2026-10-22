import time
from datetime import date

import pytest

from app import fake, stream
from app.models import Guide, iter_evidence

STAGES = stream.STAGES


async def run(app: str, speed: float | None = 0) -> list:
    body = "".join([chunk async for chunk in fake.fake_run(app, speed=speed)])
    return stream.parse_sse(body)


def of_type(events: list, kind: str) -> list[dict]:
    return [e for e in events if isinstance(e, dict) and e["type"] == kind]


def stage_events(events: list) -> list[dict]:
    return of_type(events, "data-stage")


async def test_event_envelope_start_finish_done():
    events = await run("xero")
    assert events[0]["type"] == "start" and events[0]["messageId"]
    assert events[-2] == {"type": "finish"}
    assert events[-1] == "[DONE]"
    assert [e for e in events if e == "[DONE]"] == ["[DONE]"]


async def test_every_stage_runs_then_completes_with_same_id_in_order():
    events = await run("xero")
    stages = stage_events(events)
    by_stage: dict[str, list[dict]] = {}
    for e in stages:
        assert e["id"] == e["data"]["stage"]
        assert e["data"]["label"]
        by_stage.setdefault(e["id"], []).append(e)
    assert list(by_stage) == STAGES
    for sid, evs in by_stage.items():
        assert evs[0]["data"]["status"] == "running", sid
        assert evs[-1]["data"]["status"] in {"done", "error", "skipped"}, sid
        assert evs[-1]["data"]["status"] == "done"


async def test_stages_do_not_overlap():
    running: set[str] = set()
    for e in stage_events(await run("xero")):
        status, sid = e["data"]["status"], e["id"]
        if status == "running":
            assert not running
            running.add(sid)
        else:
            running.discard(sid)
    assert not running


async def test_text_triples_share_id_and_ids_are_fresh():
    events = await run("xero")
    texts = [e for e in events if isinstance(e, dict) and e["type"].startswith("text-")]
    assert len(texts) % 3 == 0 and texts
    ids = []
    for i in range(0, len(texts), 3):
        start, delta, end = texts[i : i + 3]
        assert (start["type"], delta["type"], end["type"]) == ("text-start", "text-delta", "text-end")
        assert start["id"] == delta["id"] == end["id"]
        assert delta["delta"].strip()
        ids.append(start["id"])
    assert len(set(ids)) == len(ids)


async def test_narration_is_realistic():
    events = await run("xero")
    lines = [e["delta"] for e in of_type(events, "text-delta")]
    joined = "\n".join(lines)
    assert any(line.startswith("Resolved ") and "Composio toolkit" in line for line in lines)
    assert any(line.startswith("Found 5 candidate docs pages on ") for line in lines)
    assert "Sign-in wall at github.com after 1 redirect" in joined
    assert any(line.startswith("Verified ") and " quotes; downgraded " in line for line in lines)
    assert len(lines) >= 8


async def test_source_urls_use_guide_sources(github_guide_dict):
    events = await run("xero")
    sources = of_type(events, "source-url")
    assert len(sources) >= 5
    real = {s["id"]: s for s in github_guide_dict["sources"]}
    for s in sources:
        assert real[s["sourceId"]]["url"] == s["url"]
        assert s["title"]
    assert len({s["sourceId"] for s in sources}) == len(sources)


async def test_wall_event_matches_guide_wall_probe(github_guide_dict):
    [wall] = of_type(await run("xero"), "data-wall")
    assert wall["id"] == "wall"
    assert wall["data"] == github_guide_dict["wall_probe"]


async def test_verification_counts_progress_monotonically(github_guide_dict):
    events = await run("xero")
    vers = of_type(events, "data-verification")
    assert len(vers) >= 3
    keys = ["checked", "docs_verified", "hidden", "downgraded"]
    for e in vers:
        assert e["id"] == "verification"
        assert set(e["data"]) == {*keys, "total"}
        d = e["data"]
        assert d["docs_verified"] + d["hidden"] + d["downgraded"] == d["checked"] <= d["total"]
    for prev, cur in zip(vers, vers[1:]):
        assert all(cur["data"][k] >= prev["data"][k] for k in keys)
    assert vers[0]["data"]["checked"] < vers[-1]["data"]["checked"]
    summary = github_guide_dict["verification_summary"]
    last = vers[-1]["data"]
    assert last["total"] == summary["total"]
    assert last["docs_verified"] == summary["docs_verified"]
    assert last["hidden"] == summary["docs_hidden"]


async def test_event_order_follows_contract():
    events = await run("xero")
    idx = {}
    for i, e in enumerate(events):
        if isinstance(e, dict):
            idx.setdefault(e["type"], i)
    guide_i = idx["data-guide"]
    assert idx["start"] == 0
    assert idx["source-url"] < idx["data-wall"] < idx["data-verification"] < guide_i < idx["finish"]
    # the guide arrives while publish is running, and only once
    assert len(of_type(events, "data-guide")) == 1
    publish = [i for i, e in enumerate(events) if isinstance(e, dict) and e.get("id") == "publish"]
    assert publish[0] < guide_i < publish[-1]


@pytest.mark.parametrize(
    "query,slug",
    [("xero", "xero"), ("Totally Unknown App", "totally-unknown-app"), ("github", "github")],
)
async def test_guide_validates_and_has_expected_identity(query, slug):
    [part] = of_type(await run(query), "data-guide")
    data = part["data"]
    assert data["slug"] == slug
    assert data["permalink"] == f"/guides/{slug}"
    guide = Guide.model_validate(data["guide"])
    assert guide.guide_type == "generated"
    assert guide.slug == slug
    assert guide.last_verified == date.today().isoformat()
    assert all(ev.label != "DOCS" or ev.found_in for ev in iter_evidence(guide))


async def test_guide_app_name_falls_back_to_input_for_unknown_app():
    [part] = of_type(await run("Totally Unknown App"), "data-guide")
    assert part["data"]["guide"]["app_name"] == "Totally Unknown App"
    assert part["data"]["guide"]["composio"]["status"] == "not_in_catalog"
    assert part["data"]["guide"]["composio"]["toolkit_slug"] is None


async def test_known_app_gets_resolved_name_and_composio_block(monkeypatch):
    monkeypatch.setattr(fake, "_resolve", lambda q: fake.Resolved("xero", "Xero", "xero", "byo"))
    events = await run("xero.com")
    guide = of_type(events, "data-guide")[0]["data"]["guide"]
    assert (guide["slug"], guide["app_name"]) == ("xero", "Xero")
    assert guide["composio"]["status"] == "byo" and guide["composio"]["toolkit_slug"] == "xero"
    assert any(e["delta"] == "Resolved Xero to Composio toolkit xero (BYO)" for e in of_type(events, "text-delta"))


async def test_resolution_failure_falls_back_to_slugified_input(monkeypatch):
    import app.catalog as catalog

    def boom(_query):
        raise RuntimeError("csv missing")

    monkeypatch.setattr(catalog, "resolve", boom, raising=False)
    [part] = of_type(await run("Some App"), "data-guide")
    assert part["data"]["slug"] == "some-app"


async def test_error_replay():
    events = await run("!error")
    types = [e["type"] if isinstance(e, dict) else e for e in events]
    assert types[0] == "start"
    assert types[-4:] == ["error", "data-stage", "finish", "[DONE]"]
    assert "data-guide" not in types
    stages = stage_events(events)
    failed = stages[-1]
    assert failed["data"]["status"] == "error"
    assert any(e["id"] == failed["id"] and e["data"]["status"] == "running" for e in stages)
    assert events[-4]["errorText"]


async def test_speed_zero_is_instant():
    t0 = time.perf_counter()
    await run("xero", speed=0)
    assert time.perf_counter() - t0 < 1.0


async def test_speed_scales_delays(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(fake.asyncio, "sleep", fake_sleep)
    await run("xero", speed=1.0)
    full = sum(slept)
    slept.clear()
    await run("xero", speed=0.5)
    assert 12 <= full <= 20
    assert sum(slept) == pytest.approx(full / 2)


async def test_speed_defaults_to_env(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(fake.asyncio, "sleep", fake_sleep)
    monkeypatch.setenv("FAKE_SPEED", "0")
    await run("xero", speed=None)
    assert sum(slept) == 0
