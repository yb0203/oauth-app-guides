"""LLM layer: Pydantic AI on OpenRouter, free models only.

Code orchestrates; the model does two narrow jobs (extract claims, write the guide). Every output is
validated by Pydantic (with retries), then falls back to a second model, with backoff on 429.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from typing import TypeVar

from pydantic import ValidationError
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.models import Model

log = logging.getLogger("llm")
T = TypeVar("T")

DEFAULT_PRIMARY = "nvidia/nemotron-3-super-120b-a12b:free"
DEFAULT_FALLBACK = "minimax/minimax-m3.1-flash:free"


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
        # "prompted" asks for JSON in plain text, which free models handle more reliably than tool calls.
        self.output_mode = os.getenv("LLM_OUTPUT_MODE", "prompted")

    def _agent(self, model_name: str, output_type: type[T], instructions: str) -> Agent:
        spec = PromptedOutput(output_type) if self.output_mode == "prompted" else output_type
        return Agent(
            self._factory(model_name),
            output_type=spec,
            instructions=instructions,
            retries={"output": 2, "tools": 1},
            model_settings={"temperature": 0.2, "max_tokens": 8000, "timeout": 150},
        )

    async def run(self, output_type: type[T], instructions: str, prompt: str, *, label: str = "") -> T:
        errors: list[str] = []
        for model_name in self.model_names:
            for attempt in range(self.max_attempts):
                if self.calls >= self.max_calls:
                    raise LLMBudgetExceeded(f"LLM request budget of {self.max_calls} reached")
                self.calls += 1
                try:
                    async with self._sem:
                        result = await self._agent(model_name, output_type, instructions).run(prompt)
                    log.info("llm ok label=%s model=%s calls=%d", label, model_name, self.calls)
                    return result.output
                except ModelHTTPError as exc:
                    errors.append(f"{model_name}: HTTP {exc.status_code}")
                    if exc.status_code in (429, 502, 503, 504) and attempt + 1 < self.max_attempts:
                        await self._sleep(_backoff(exc, attempt))
                        continue
                    break  # 4xx other than 429: this model won't work, try the next one
                except (UnexpectedModelBehavior, ValidationError) as exc:
                    errors.append(f"{model_name}: invalid output ({type(exc).__name__})")
                    break
                except ModelAPIError as exc:
                    errors.append(f"{model_name}: {type(exc).__name__}")
                    break
        raise LLMError(f"all models failed for {label or 'call'}: " + "; ".join(errors))


def _backoff(exc: ModelHTTPError, attempt: int) -> float:
    retry_after = (exc.headers or {}).get("retry-after")
    try:
        return min(float(retry_after), 60.0)
    except (TypeError, ValueError):
        return min(4.0 * 2**attempt, 40.0)
