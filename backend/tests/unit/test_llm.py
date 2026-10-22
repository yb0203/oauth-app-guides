import json

import pytest
from pydantic import BaseModel
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.llm import LLM, LLMBudgetExceeded, LLMError


class Thing(BaseModel):
    name: str
    n: int


def good(_msgs, _info: AgentInfo):
    return ModelResponse(parts=[TextPart(json.dumps({"name": "x", "n": 2}))])


def make(models: dict, **kw):
    async def no_sleep(_s):
        return None

    return LLM("primary", "fallback", model_factory=lambda name: models[name], sleep=no_sleep, **kw)


async def test_prompted_output_validates():
    llm = make({"primary": FunctionModel(good), "fallback": FunctionModel(good)})
    out = await llm.run(Thing, "extract", "text")
    assert out == Thing(name="x", n=2) and llm.calls == 1


async def test_invalid_output_retries_then_falls_back():
    def bad(_m, _i):
        return ModelResponse(parts=[TextPart("not json at all")])

    llm = make({"primary": FunctionModel(bad), "fallback": FunctionModel(good)})
    assert (await llm.run(Thing, "i", "p")).n == 2
    assert llm.calls == 2  # one failed run on primary (with its internal retries), one on fallback


async def test_429_backs_off_and_retries_same_model():
    state = {"n": 0}

    def flaky(m, i):
        state["n"] += 1
        if state["n"] < 3:
            raise ModelHTTPError(429, "primary", body="rate limited")
        return good(m, i)

    llm = make({"primary": FunctionModel(flaky), "fallback": FunctionModel(good)})
    assert (await llm.run(Thing, "i", "p")).name == "x"
    assert state["n"] == 3


async def test_all_models_failing_raises_llm_error():
    def boom(_m, _i):
        raise ModelHTTPError(401, "m", body="bad key")

    llm = make({"primary": FunctionModel(boom), "fallback": FunctionModel(boom)})
    with pytest.raises(LLMError):
        await llm.run(Thing, "i", "p")


async def test_call_budget_enforced():
    llm = make({"primary": FunctionModel(good), "fallback": FunctionModel(good)}, max_calls=1)
    await llm.run(Thing, "i", "p")
    with pytest.raises(LLMBudgetExceeded):
        await llm.run(Thing, "i", "p")
