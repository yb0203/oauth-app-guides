"""User-selectable generation settings and the free-model allow-list (CONTRACT §3).

Public users can only ever trigger `:free` OpenRouter models: the allow-list is checked on the server, and any
entry in ALLOWED_MODELS that does not end in ":free" is ignored.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

DEFAULT_ALLOWED = [
    "minimax/minimax-m3.1-flash:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]
MAX_PAGES_CHOICES = [3, 5, 8]
DEFAULT_MAX_PAGES = 5
_ID = re.compile(r"^[\w.\-]+/[\w.\-]+:free$")

# What we know about each model from running it. `tested` means a full generation ran end to end on it.
KNOWN: dict[str, dict] = {
    "minimax/minimax-m3.1-flash:free": {
        "label": "MiniMax M3.1 Flash (free)", "tested": True, "notes": "fastest; the default"},
    "nvidia/nemotron-3-ultra-550b-a55b:free": {
        "label": "NVIDIA Nemotron 3 Ultra (free)", "tested": True, "notes": "larger model, slower on long guides"},
    "nvidia/nemotron-3-super-120b-a12b:free": {
        "label": "NVIDIA Nemotron 3 Super (free)", "tested": False,
        "notes": "not available on our OpenRouter account at last check (HTTP 404); runs fall back to another model"},
}


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    provider: str
    tested: bool
    notes: str | None


def allowed_ids() -> list[str]:
    """ALLOWED_MODELS (comma-separated) filtered to well-formed ":free" ids; the default list if unset or empty."""
    raw = os.getenv("ALLOWED_MODELS")
    ids = [m.strip() for m in raw.split(",")] if raw else DEFAULT_ALLOWED
    clean = [m for m in dict.fromkeys(ids) if _ID.match(m)]
    return clean or list(DEFAULT_ALLOWED)


def _label(model_id: str) -> str:
    name = model_id.split("/", 1)[1].removesuffix(":free")
    return f"{name} (free)"


def allowed_models() -> list[ModelInfo]:
    out = []
    for mid in allowed_ids():
        known = KNOWN.get(mid, {})
        out.append(ModelInfo(mid, known.get("label") or _label(mid), mid.split("/", 1)[0],
                             bool(known.get("tested", False)), known.get("notes")))
    return out


def default_model() -> str:
    ids = allowed_ids()
    preferred = os.getenv("LLM_MODEL_PRIMARY", "")
    return preferred if preferred in ids else ids[0]


def fallback_for(model: str) -> str:
    """A different allow-listed model, preferring ones we have run end to end; the same model if it is the only one."""
    others = [m for m in allowed_models() if m.id != model]
    if not others:
        return model
    env = os.getenv("LLM_MODEL_FALLBACK", "")
    if env in {m.id for m in others}:
        return env
    return sorted(others, key=lambda m: not m.tested)[0].id


def label_of(model_id: str) -> str:
    return next((m.label for m in allowed_models() if m.id == model_id), _label(model_id))


@dataclass(frozen=True)
class GenerateConfig:
    model: str
    fallback_model: str
    max_pages: int = DEFAULT_MAX_PAGES
    probe_console: bool = True

    def as_dict(self) -> dict:
        return {"model": self.model, "fallback_model": self.fallback_model, "max_pages": self.max_pages,
                "probe_console": self.probe_console}

    def describe(self) -> str:
        return f"Using {label_of(self.model)}, {self.max_pages} pages"


def resolve_config(raw: object) -> GenerateConfig:
    """Validate the optional `config` of a generate request. Raises HTTP 400 with a plain-language reason."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise HTTPException(400, "config must be an object like {\"model\": \"...\", \"max_pages\": 5}.")
    ids = allowed_ids()
    model = raw.get("model", default_model())
    if not isinstance(model, str) or model not in ids:
        shown = model if isinstance(model, str) else "that value"
        why = "Only free models are available here" if not str(shown).endswith(":free") else "That model isn't offered"
        raise HTTPException(400, f"{why}: {shown!r} is not on the list. Choose one of: {', '.join(ids)}.")
    max_pages = raw.get("max_pages", DEFAULT_MAX_PAGES)
    if isinstance(max_pages, bool) or max_pages not in MAX_PAGES_CHOICES:
        raise HTTPException(400, f"max_pages must be one of {', '.join(map(str, MAX_PAGES_CHOICES))}.")
    probe = raw.get("probe_console", True)
    if not isinstance(probe, bool):
        raise HTTPException(400, "probe_console must be true or false.")
    return GenerateConfig(model, fallback_for(model), int(max_pages), probe)


# --- GET /api/models ---------------------------------------------------------------------------------------

UNAVAILABLE_NOTE = "not available right now (OpenRouter no longer lists it or it returned HTTP 404); runs fall back to another model"
_unavailable: dict[str, float] = {}  # model id -> when a run last got HTTP 404 from it
UNAVAILABLE_SECONDS = 3600


def mark_unavailable(model_id: str) -> None:
    """Called by the LLM layer when a model answers 404: /api/models shows it as not tested for a while."""
    _unavailable[model_id] = time.monotonic()


def _recently_404(model_id: str) -> bool:
    at = _unavailable.get(model_id)
    return at is not None and time.monotonic() - at < UNAVAILABLE_SECONDS


_catalog_cache: dict = {"at": 0.0, "models": {}}
CACHE_SECONDS = 3600


async def _openrouter_models() -> dict[str, dict]:
    """OpenRouter's public model list (no key needed), cached in memory; empty when it can't be reached."""
    if time.monotonic() - _catalog_cache["at"] < CACHE_SECONDS and _catalog_cache["models"]:
        return _catalog_cache["models"]
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            data = (await client.get("https://openrouter.ai/api/v1/models")).json()["data"]
        _catalog_cache.update(at=time.monotonic(), models={m["id"]: m for m in data})
    except Exception:  # offline or rate-limited: serve what we know
        pass
    return _catalog_cache["models"]


async def models_payload() -> dict:
    live = await _openrouter_models()
    models = []
    for m in allowed_models():
        remote = live.get(m.id, {})
        gone = _recently_404(m.id) or (bool(live) and m.id not in live)  # a live list that omits it, or a recent 404
        models.append({"id": m.id, "label": m.label, "provider": m.provider,
                       "context_length": remote.get("context_length"), "free": True,
                       "tested": m.tested and not gone, "notes": UNAVAILABLE_NOTE if gone else m.notes,
                       "recommended": m.id == default_model()})
    return {"default": default_model(), "models": models,
            "options": {"max_pages": {"default": DEFAULT_MAX_PAGES, "choices": MAX_PAGES_CHOICES},
                        "probe_console": {"default": True}}}
