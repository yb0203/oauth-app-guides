"""AI SDK UI message stream (v1) framing: one `data: <json>` line per event, ended by `[DONE]`."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator

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
    replay: bool = False,
) -> str:
    data: dict = {"stage": stage, "status": status, "label": label or STAGE_LABELS[stage]}
    if replay:  # fake mode: this is a recorded demo run, not research for the requested app
        data["replay"] = True
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


def guide_part(slug: str, guide: dict, replay: bool = False) -> str:
    data = {"slug": slug, "permalink": f"/guides/{slug}", "guide": guide}
    if replay:
        data["replay"] = True
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
        if not block or block.startswith(":"):  # blank, or an SSE comment such as the keep-alive ping
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


# --- keep-alive --------------------------------------------------------------------------------------

PING = ": ping\n\n"  # an SSE comment: parsers (eventsource-parser, used by the AI SDK) ignore it


async def with_heartbeat(source: AsyncIterator[str], interval: float | None = None) -> AsyncIterator[str]:
    """Pass `source` through, adding a ping whenever it has been silent for `interval` seconds, so idle
    proxies and serverless gateways don't drop a slow stage. Errors from `source` propagate unchanged."""
    interval = float(os.getenv("HEARTBEAT_SECONDS", "10")) if interval is None else interval
    it = source.__aiter__()
    pending = asyncio.ensure_future(it.__anext__())
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=interval) if interval > 0 else ({pending}, set())
            if not done:
                yield PING
                continue
            try:
                chunk = pending.result()
            except StopAsyncIteration:
                return
            yield chunk
            pending = asyncio.ensure_future(it.__anext__())
    finally:
        pending.cancel()


def run_stats(data: dict) -> str:
    """Performance and cost numbers for the run, sent right before `finish` (CONTRACT §4 item 8)."""
    return sse({"type": "data-run-stats", "id": "run-stats", "data": data})


_END = object()


async def run_in_thread(factory, interval: float | None = None) -> AsyncIterator[str]:
    """Run `factory()` (an async generator of chunks) on its own thread and event loop; this loop only forwards
    chunks and sends pings. A blocked or starved pipeline can therefore never silence the keep-alive."""
    import threading

    interval = float(os.getenv("HEARTBEAT_SECONDS", "10")) if interval is None else interval
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    worker: dict = {}

    def post(item) -> None:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, item)
        except RuntimeError:  # the consumer's loop is already gone (client disconnected)
            pass

    def run() -> None:
        async def pump() -> None:
            worker["loop"], worker["task"] = asyncio.get_running_loop(), asyncio.current_task()
            try:
                async for chunk in factory():
                    post(chunk)
            except asyncio.CancelledError:
                pass
            except BaseException as exc:  # handed to the consumer, which re-raises it
                post(exc)
            finally:
                post(_END)

        asyncio.run(pump())

    thread = threading.Thread(target=run, name="pipeline", daemon=True)
    thread.start()
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), interval) if interval > 0 else await queue.get()
            except TimeoutError:
                yield PING
                continue
            if item is _END:
                return
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:  # the client went away (or we finished): stop the worker
        if "task" in worker and thread.is_alive():
            try:
                worker["loop"].call_soon_threadsafe(worker["task"].cancel)
            except RuntimeError:  # the worker loop finished in the meantime
                pass
