"""AI SDK UI message stream (v1) framing: one `data: <json>` line per event, ended by `[DONE]`."""

from __future__ import annotations

import json
import uuid

STAGES = ["resolve", "find_docs", "research", "probe", "synthesize", "verify", "publish"]
STAGE_LABELS = {
    "resolve": "Resolve the app",
    "find_docs": "Find the developer docs",
    "research": "Read the docs",
    "probe": "Probe the developer console",
    "synthesize": "Write the guide",
    "verify": "Verify every quote",
    "publish": "Publish",
}

STREAM_HEADERS = {
    "content-type": "text/event-stream",
    "cache-control": "no-cache",
    "x-vercel-ai-ui-message-stream": "v1",
    "connection": "keep-alive",
    "x-accel-buffering": "no",
}
DONE = "data: [DONE]\n\n"


def sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, separators=(',', ':'), ensure_ascii=False)}\n\n"


def start(message_id: str) -> str:
    return sse({"type": "start", "messageId": message_id})


def stage(
    stage: str,
    status: str,
    label: str | None = None,
    detail: str | None = None,
    counts: dict | None = None,
) -> str:
    data: dict = {"stage": stage, "status": status, "label": label or STAGE_LABELS[stage]}
    if detail is not None:
        data["detail"] = detail
    if counts is not None:
        data["counts"] = counts
    return sse({"type": "data-stage", "id": stage, "data": data})


def text(message: str, text_id: str | None = None) -> str:
    tid = text_id or uuid.uuid4().hex
    return (
        sse({"type": "text-start", "id": tid})
        + sse({"type": "text-delta", "id": tid, "delta": message})
        + sse({"type": "text-end", "id": tid})
    )


def source_url(source_id: str, url: str, title: str) -> str:
    return sse({"type": "source-url", "sourceId": source_id, "url": url, "title": title})


def wall(data: dict) -> str:
    return sse({"type": "data-wall", "id": "wall", "data": data})


def verification(checked: int, docs_verified: int, hidden: int, downgraded: int, total: int) -> str:
    data = {
        "checked": checked,
        "docs_verified": docs_verified,
        "hidden": hidden,
        "downgraded": downgraded,
        "total": total,
    }
    return sse({"type": "data-verification", "id": "verification", "data": data})


def guide_part(slug: str, guide: dict) -> str:
    data = {"slug": slug, "permalink": f"/guides/{slug}", "guide": guide}
    return sse({"type": "data-guide", "id": "guide", "data": data})


def error(error_text: str) -> str:
    return sse({"type": "error", "errorText": error_text})


def finish() -> str:
    return sse({"type": "finish"})


def parse_sse(body: str) -> list[dict | str]:
    """Inverse of `sse`, for tests: JSON events, with the `[DONE]` sentinel as the string "[DONE]"."""
    events: list[dict | str] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        payload = block.removeprefix("data:").strip()
        events.append(payload if payload == "[DONE]" else json.loads(payload))
    return events


# --- "Ask this guide" stream (CONTRACT §4b) ---------------------------------------------------------

def text_chunks(message: str, chunk_words: int = 4) -> str:
    """One text part whose body arrives as several deltas, so the client renders it progressively."""
    tid = uuid.uuid4().hex
    words = message.split(" ")
    deltas = [" ".join(words[i:i + chunk_words]) + (" " if i + chunk_words < len(words) else "")
              for i in range(0, len(words), chunk_words)]
    return (sse({"type": "text-start", "id": tid})
            + "".join(sse({"type": "text-delta", "id": tid, "delta": d}) for d in deltas if d)
            + sse({"type": "text-end", "id": tid}))


def citations(entries: list[dict]) -> str:
    return sse({"type": "data-citations", "id": "citations", "data": entries})


def action(n: int, data: dict) -> str:
    return sse({"type": "data-action", "id": f"action-{n}", "data": data})


def answer_meta(covered: bool, suggest: str | None) -> str:
    return sse({"type": "data-answer-meta", "id": "meta", "data": {"covered": covered, "suggest": suggest}})
