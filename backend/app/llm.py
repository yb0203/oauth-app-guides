"""LLM layer: Pydantic AI on OpenRouter, free models only.

Code orchestrates; the model does two narrow jobs (extract claims, write the guide). Every output is
validated by Pydantic (with retries), then falls back to a second model, with backoff on 429.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from typing import TypeVar

from pydantic import ValidationError
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from . import settings  # noqa: E402

log = logging.getLogger("llm")
if not log.handlers:  # per-call timing lines (never the key) show up in uvicorn's console
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%H:%M:%S"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False
T = TypeVar("T")

# Measured 2026-10-22: nemotron-3-super is gone for our account (HTTP 404). minimax answers an extraction call in ~6 s
# with reasoning=low; nemotron-3-ultra in ~6 s with reasoning off. Both need reasoning curbed (30 s otherwise).
DEFAULT_PRIMARY = "minimax/minimax-m3.1-flash:free"
DEFAULT_FALLBACK = "nvidia/nemotron-3-ultra-550b-a55b:free"


class LLMError(Exception):
    pass


class LLMBudgetExceeded(LLMError):
    pass


def has_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _openrouter(name: str) -> Model:
    from pydantic_ai.models.openrouter import OpenRouterModel
    from pydantic_ai.providers.openrouter import OpenRouterProvider

    return OpenRouterModel(name, provider=OpenRouterProvider(api_key=os.environ["OPENROUTER_API_KEY"]))


class LLM:
    """One instance per pipeline run: it counts requests against the run's budget."""

    def __init__(
        self,
        primary: str | None = None,
        fallback: str | None = None,
        *,
        model_factory: Callable[[str], Model] = _openrouter,
        max_calls: int = 15,
        concurrency: int = 3,
        max_attempts_per_model: int = 3,
        sleep: Callable[[float], object] = asyncio.sleep,
    ) -> None:
        self.model_names = [
            primary or os.getenv("LLM_MODEL_PRIMARY", DEFAULT_PRIMARY),
            fallback or os.getenv("LLM_MODEL_FALLBACK", DEFAULT_FALLBACK),
        ]
        self._factory = model_factory
        self.max_calls = max_calls
        self.max_attempts = max_attempts_per_model
        self._sem = asyncio.Semaphore(concurrency)
        self._sleep = sleep
        self.calls = 0
        self.call_log: list[dict] = []  # one entry per request: label, model, seconds, outcome, tokens
        # "prompted" asks for JSON in plain text, which free models handle more reliably than tool calls.
        self.output_mode = os.getenv("LLM_OUTPUT_MODE", "prompted")

    def _agent(self, model_name: str, output_type: type[T], instructions: str, timeout: float = 90.0) -> Agent:
        spec = PromptedOutput(output_type) if self.output_mode == "prompted" else output_type
        return Agent(
            self._factory(model_name),
            output_type=spec,
            instructions=instructions,
            retries={"output": 2, "tools": 1},
            model_settings={"temperature": 0.2, "max_tokens": 8000, "timeout": timeout, "openrouter_usage": {"include": True},
                            **_reasoning_settings(model_name)},
        )

    async def run(self, output_type: type[T], instructions: str, prompt: str, *, label: str = "",
                  timeout: float = 90.0, deadline: float | None = None) -> T:
        """`timeout` caps each request; `deadline` (a time.monotonic() value) caps the whole call, so a
        slow primary model leaves time for the fallback or for the caller's own fallback."""
        errors: list[str] = []
        for model_name in self.model_names:
            for attempt in range(self.max_attempts):
                if self.calls >= self.max_calls:
                    raise LLMBudgetExceeded(f"LLM request budget of {self.max_calls} reached")
                budget = timeout if deadline is None else min(timeout, deadline - time.monotonic())
                if budget < 5:
                    raise LLMError(f"out of time for {label or 'call'}: " + "; ".join(errors))
                self.calls += 1
                started = time.monotonic()
                outcome, tokens, cost = "ok", None, None
                try:
                    async with self._sem:
                        result = await asyncio.wait_for(
                            self._agent(model_name, output_type, instructions, budget).run(prompt), budget)
                    tokens = _tokens_of(result)
                    cost = _cost_of(result)
                    return result.output
                except TimeoutError:
                    outcome = f"timeout after {budget:.0f}s"
                    errors.append(f"{model_name}: timeout")
                    break  # a model that is this slow won't be faster on retry: try the next one
                except ModelHTTPError as exc:
                    outcome = f"http {exc.status_code}"
                    if exc.status_code == 404:
                        settings.mark_unavailable(model_name)
                    errors.append(f"{model_name}: HTTP {exc.status_code}")
                    if exc.status_code in (429, 502, 503, 504) and attempt + 1 < self.max_attempts:
                        await self._sleep(_backoff(exc, attempt))
                        continue
                    break  # 4xx other than 429: this model won't work, try the next one
                except (UnexpectedModelBehavior, ValidationError) as exc:
                    outcome = f"invalid output ({type(exc).__name__})"
                    errors.append(f"{model_name}: invalid output ({type(exc).__name__})")
                    break
                except ModelAPIError as exc:
                    outcome = type(exc).__name__
                    errors.append(f"{model_name}: {type(exc).__name__}")
                    break
                finally:
                    secs = time.monotonic() - started
                    self.call_log.append({"label": label, "model": model_name, "seconds": round(secs, 1),
                                          "outcome": outcome, "tokens": tokens, "cost": cost})
                    log.info("label=%s model=%s secs=%.1f outcome=%s tokens=%s calls=%d", label, model_name,
                             secs, outcome, tokens and f"{tokens[0]}+{tokens[1]}", self.calls)
        raise LLMError(f"all models failed for {label or 'call'}: " + "; ".join(errors))


def _tokens_of(result) -> tuple[int, int] | None:
    """(input, output) tokens the provider reported for this run, or None when it reported nothing."""
    usage = result.usage
    inp, out = getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0
    return (inp, out) if inp or out else None


def _cost_of(result) -> float | None:
    """The cost OpenRouter reports in the response (`usage.cost`, surfaced in provider_details), if any."""
    total, seen = 0.0, False
    for msg in result.all_messages():
        cost = (getattr(msg, "provider_details", None) or {}).get("cost")
        if isinstance(cost, (int, float)):
            total, seen = total + float(cost), True
    return total if seen else None


def _reasoning_settings(model_name: str = "") -> dict:
    """Free models are reasoning models and spend most of their time thinking, which extraction and drafting
    don't need. LLM_REASONING overrides for every model: off, minimal/low/medium/high, or default (model's own).
    Otherwise per model: minimax can't switch reasoning off (HTTP 400), so it gets effort=low; others get off."""
    mode = os.getenv("LLM_REASONING", "").lower()
    if mode == "default":
        return {}
    if not mode:
        mode = "low" if model_name.startswith("minimax/") else "off"
    return {"openrouter_reasoning": {"enabled": False} if mode == "off" else {"effort": mode}}


def _backoff(exc: ModelHTTPError, attempt: int) -> float:
    retry_after = (exc.headers or {}).get("retry-after")
    try:
        return min(float(retry_after), 60.0)
    except (TypeError, ValueError):
        return min(4.0 * 2**attempt, 40.0)
