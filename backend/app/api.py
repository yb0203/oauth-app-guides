"""FastAPI app: guide read endpoints plus the streaming POST /api/generate (docs/CONTRACT.md §3, §4)."""

from __future__ import annotations

import json
import logging
import math
import os
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import ask, catalog, config, fake, markdown, store, stream

log = logging.getLogger(__name__)

MAX_INPUT_CHARS = 200
DEFAULT_RATE_LIMIT = 5  # generations per window per client IP
DEFAULT_RATE_WINDOW = 600.0  # seconds


def extract_app_input(body: object) -> str:
    """The app name or URL from `{"app": ...}` or from the last user message of a useChat body."""
    text = ""
    if isinstance(body, dict):
        if isinstance(body.get("app"), str):
            text = body["app"]
        elif isinstance(body.get("messages"), list):
            text = _last_user_text(body["messages"])
    text = text.strip()
    if not text:
        raise HTTPException(422, "Send {'app': '<app name or URL>'} or a chat message naming the app.")
    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(422, f"Input is too long (max {MAX_INPUT_CHARS} characters).")
    return text


def _last_user_text(messages: list) -> str:
    for msg in reversed(messages):
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content, parts = msg.get("content"), msg.get("parts")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(parts, list):
            return "".join(p["text"] for p in parts if isinstance(p, dict) and p.get("type") == "text"
                           and isinstance(p.get("text"), str))
        return ""
    return ""


class RateLimiter:
    """Sliding-window limiter keyed by client IP. Limit and window are read from env on every call."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def limit() -> int:
        raw = os.getenv("GENERATE_RATE_LIMIT")
        if raw is None:
            # Unset: protect live runs, but never throttle fake mode (frontend dev) or the test suite.
            quiet = config.llm_mode() == "fake" or "PYTEST_CURRENT_TEST" in os.environ
            return 0 if quiet else DEFAULT_RATE_LIMIT
        try:
            return max(0, int(raw))
        except ValueError:
            return DEFAULT_RATE_LIMIT

    def check(self, ip: str) -> int | None:
        """Record a hit; return seconds until retry if over the limit, else None."""
        limit = self.limit()
        if limit == 0:
            return None
        window = float(os.getenv("GENERATE_RATE_WINDOW", DEFAULT_RATE_WINDOW))
        now = time.monotonic()
        hits = self._hits[ip]
        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= limit:
            return max(1, math.ceil(window - (now - hits[0])))
        hits.append(now)
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


async def _source(app_input: str) -> AsyncIterator[str]:
    if config.llm_mode() == "fake":
        async for chunk in fake.fake_run(app_input):
            yield chunk
        return
    from .pipeline import run_pipeline

    async for chunk in run_pipeline(app_input):
        yield chunk


async def _guarded(source: AsyncIterator[str]) -> AsyncIterator[str]:
    """Pass the run through; any exception becomes error, failed stage, finish, [DONE]."""
    started = finished = done = False
    current: str | None = None  # last stage that has been announced as running
    try:
        async for chunk in source:
            if chunk.startswith('data: {"type":"start"'):
                started = True
            elif chunk.startswith('data: {"type":"finish"'):
                finished = True
            elif chunk == stream.DONE:
                done = True
            elif chunk.startswith('data: {"type":"data-stage"'):
                data = json.loads(chunk[len("data: "):])["data"]
                if data["status"] == "running":
                    current = data["stage"]
                elif data["stage"] == current:
                    current = None
            yield chunk
    except Exception as exc:  # the stream has begun, so report in-band
        log.exception("generation failed")
        if not started:
            yield stream.start(uuid.uuid4().hex)
        yield stream.error(f"Generation failed ({type(exc).__name__}). Please try again.")
        yield stream.stage(current or "resolve", "error")
        finished = False
        done = False
    if not finished:
        yield stream.finish()
    if not done:
        yield stream.DONE


def create_app() -> FastAPI:
    app = FastAPI(title="OAuth setup guides")
    limiter = RateLimiter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins(),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/catalog")
    def get_catalog() -> list[dict]:
        return catalog.list_catalog()

    @app.get("/api/guides")
    def get_guides() -> list[dict]:
        return store.list_guides()

    @app.get("/api/guides/{slug}")
    def get_guide(slug: str) -> dict:
        guide = store.get_guide(slug)
        if guide is None:
            raise HTTPException(404, f"No guide for {slug!r}")
        return guide

    @app.get("/api/guides/{slug}/markdown")
    def get_guide_markdown(slug: str) -> Response:
        guide = store.get_guide(slug)
        if guide is None:
            raise HTTPException(404, f"No guide for {slug!r}")
        return Response(markdown.guide_to_markdown(guide), media_type="text/markdown")

    @app.post("/api/generate")
    async def generate(request: Request):
        try:
            body = await request.json()
        except ValueError:
            raise HTTPException(422, "Request body must be JSON.") from None
        app_input = extract_app_input(body)
        retry_after = limiter.check(_client_ip(request))
        if retry_after is not None:
            return JSONResponse(
                {"detail": "Too many generations from this address. Try again later."},
                status_code=429,
                headers={"retry-after": str(retry_after)},
            )
        return StreamingResponse(_guarded(_source(app_input)), headers=stream.STREAM_HEADERS)

    @app.post("/api/guides/{slug}/ask")
    async def ask_guide(slug: str, request: Request):
        guide = store.get_guide(slug)
        if guide is None:
            raise HTTPException(404, f"No guide for {slug!r}")
        try:
            body = await request.json()
        except ValueError:
            raise HTTPException(422, "Request body must be JSON.") from None
        req = ask.parse_ask_body(body)
        return StreamingResponse(ask.ask_stream(guide, req, mode=config.llm_mode()), headers=stream.STREAM_HEADERS)

    return app


app = create_app()
