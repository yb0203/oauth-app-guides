import json

import pytest

from app import stream


def _events(chunk: str) -> list:
    return stream.parse_sse(chunk)


def test_sse_framing():
    chunk = stream.sse({"type": "x", "n": 1})
    assert chunk.startswith("data: ") and chunk.endswith("\n\n")
    assert json.loads(chunk[len("data: "):]) == {"type": "x", "n": 1}


def test_done_sentinel():
    assert stream.DONE == "data: [DONE]\n\n"
    assert stream.parse_sse(stream.DONE) == ["[DONE]"]


def test_start_and_finish():
    assert _events(stream.start("run-1")) == [{"type": "start", "messageId": "run-1"}]
    assert _events(stream.finish()) == [{"type": "finish"}]


def test_stage_defaults_label_and_omits_optionals():
    [ev] = _events(stream.stage("resolve", "running"))
    assert ev == {
        "type": "data-stage",
        "id": "resolve",
        "data": {"stage": "resolve", "status": "running", "label": stream.STAGE_LABELS["resolve"]},
    }


def test_stage_with_detail_counts_and_custom_label():
    [ev] = _events(stream.stage("research", "done", label="Read docs", detail="4 pages", counts={"pages": 4}))
    assert ev["id"] == "research"
    assert ev["data"] == {
        "stage": "research",
        "status": "done",
        "label": "Read docs",
        "detail": "4 pages",
        "counts": {"pages": 4},
    }


def test_stages_and_labels_are_consistent():
    assert stream.STAGES == ["resolve", "find_docs", "research", "probe", "synthesize", "verify", "publish"]
    assert set(stream.STAGE_LABELS) == set(stream.STAGES)


def test_text_is_start_delta_end_with_shared_fresh_id():
    a = _events(stream.text("Found 5 candidate docs pages on xero.com"))
    b = _events(stream.text("Second message"))
    assert [e["type"] for e in a] == ["text-start", "text-delta", "text-end"]
    assert len({e["id"] for e in a}) == 1
    assert a[1]["delta"] == "Found 5 candidate docs pages on xero.com"
    assert a[0]["id"] != b[0]["id"]


def test_text_accepts_explicit_id():
    assert {e["id"] for e in _events(stream.text("hi", text_id="t1"))} == {"t1"}


def test_source_url():
    [ev] = _events(stream.source_url("s1", "https://docs.example.com/a", "Example docs"))
    assert ev == {"type": "source-url", "sourceId": "s1", "url": "https://docs.example.com/a", "title": "Example docs"}


def test_wall_and_verification_and_guide_parts():
    [wall] = _events(stream.wall({"outcome": "login_wall"}))
    assert wall == {"type": "data-wall", "id": "wall", "data": {"outcome": "login_wall"}}

    [ver] = _events(stream.verification(3, 2, 1, 0, 17))
    assert ver == {
        "type": "data-verification",
        "id": "verification",
        "data": {"checked": 3, "docs_verified": 2, "hidden": 1, "downgraded": 0, "total": 17},
    }

    [g] = _events(stream.guide_part("xero", {"slug": "xero"}))
    assert g == {
        "type": "data-guide",
        "id": "guide",
        "data": {"slug": "xero", "permalink": "/guides/xero", "guide": {"slug": "xero"}},
    }


def test_error():
    assert _events(stream.error("boom")) == [{"type": "error", "errorText": "boom"}]


def test_headers():
    h = stream.STREAM_HEADERS
    assert h["content-type"] == "text/event-stream"
    assert h["cache-control"] == "no-cache"
    assert h["x-vercel-ai-ui-message-stream"] == "v1"
    assert h["x-accel-buffering"] == "no"


def test_parse_sse_round_trip_with_unicode_and_newlines():
    body = stream.start("m") + stream.text("line one\nline two, café") + stream.finish() + stream.DONE
    events = stream.parse_sse(body)
    assert events[0]["type"] == "start"
    assert events[2]["delta"] == "line one\nline two, café"
    assert events[-2:] == [{"type": "finish"}, "[DONE]"]


def test_parse_sse_ignores_blank_chunks():
    assert stream.parse_sse("\n\n" + stream.finish() + "\n\n") == [{"type": "finish"}]


@pytest.mark.parametrize("status", ["running", "done", "error", "skipped"])
def test_stage_statuses_pass_through(status):
    [ev] = _events(stream.stage("probe", status))
    assert ev["data"]["status"] == status
