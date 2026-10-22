"""Run statistics (CONTRACT §4 item 8): per-stage seconds, LLM calls and tokens, pages, quotes, cost."""

from __future__ import annotations

import json
import logging
import time
import uuid

log = logging.getLogger("runstats")


def summarize_llm(call_log: list[dict]) -> dict:
    """Aggregate LLM call records. Every attempt is a call (retries and fallbacks included); failed ones are counted
    separately. Tokens are the provider-reported totals, null when no call reported any."""
    by_model: dict[str, dict] = {}
    inp = out = 0
    reported = False
    cost = 0.0
    for c in call_log:
        m = by_model.setdefault(c["model"], {"calls": 0, "input_tokens": None, "output_tokens": None})
        m["calls"] += 1
        if c.get("tokens"):
            i, o = c["tokens"]
            m["input_tokens"] = (m["input_tokens"] or 0) + i
            m["output_tokens"] = (m["output_tokens"] or 0) + o
            inp, out, reported = inp + i, out + o, True
        if c.get("cost") is not None:
            cost += c["cost"]  # the provider's own figure; absent for free models, which cost 0
    return {
        "llm": {"calls": len(call_log), "failed_calls": sum(1 for c in call_log if c["outcome"] != "ok"),
                "input_tokens": inp if reported else None, "output_tokens": out if reported else None,
                "by_model": by_model},
        "cost_usd": round(cost, 6),
    }


class RunStats:
    def __init__(self, app: str, mode: str, config: dict | None = None, with_stages: bool = True) -> None:
        self.run_id = uuid.uuid4().hex[:12]
        self.app, self.mode, self.config = app, mode, config or {}
        self.with_stages = with_stages
        self.pages_fetched = 0
        self.quotes_checked = 0
        self._t0 = time.monotonic()
        self._starts: dict[str, float] = {}
        self._stages: dict[str, dict] = {}

    def watch(self, chunk: str) -> str:
        """Pass an SSE chunk through, noting stage starts and ends from data-stage events."""
        if chunk.startswith('data: {"type":"data-stage"'):
            data = json.loads(chunk[6:])["data"]
            stage, status, now = data["stage"], data["status"], time.monotonic()
            self._starts.setdefault(stage, now)
            if status in ("done", "error", "skipped"):
                self._stages[stage] = {"seconds": round(now - self._starts[stage], 1), "status": status}
        return chunk

    def to_dict(self, call_log: list[dict] | None = None) -> dict:
        data = {"run_id": self.run_id, "app": self.app, "mode": self.mode,
                "total_seconds": round(time.monotonic() - self._t0, 1)}
        if self.with_stages:
            data["stages"] = dict(self._stages)
        data.update(summarize_llm(call_log or []))
        data.update(pages_fetched=self.pages_fetched, quotes_checked=self.quotes_checked, config=self.config)
        return data

    def log_line(self, data: dict) -> None:
        log.info("run_stats %s", json.dumps(data, separators=(",", ":")))
