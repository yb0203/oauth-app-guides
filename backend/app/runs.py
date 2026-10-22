"""In-memory registry of generation runs, so a client whose stream went quiet can ask what happened
(GET /api/runs/{run_id}). The run id is the stream's start messageId. Process-local; old runs are dropped."""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

MAX_RUNS = 200
KEEP_SECONDS = 3600


@dataclass
class RunRecord:
    run_id: str
    app: str
    status: str = "running"  # running | done | error
    stage: str | None = None
    slug: str | None = None
    permalink: str | None = None
    error: str | None = None
    updated_at: str = ""
    created: float = field(default_factory=time.monotonic)
    snapshot: Callable[[], dict] | None = None  # current run-stats, for the transport's last-resort tail

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def observe(self, chunk: str) -> str:
        """Note what an emitted event says about the run's progress, and pass the chunk through."""
        if chunk.startswith('data: {"type":"data-stage"') or chunk.startswith('data: {"type":"data-guide"') \
                or chunk.startswith('data: {"type":"error"'):
            try:
                ev = json.loads(chunk[6:])
            except ValueError:
                return chunk
            if ev["type"] == "data-stage":
                self.stage = ev["data"]["stage"]
                if ev["data"]["status"] == "error":
                    self.status = "error"
            elif ev["type"] == "data-guide":
                self.slug, self.permalink = ev["data"]["slug"], ev["data"]["permalink"]
                self.status, self.error = "done", None
            else:
                self.error = ev.get("errorText")
                self.status = "error"
            self.touch()
        return chunk

    def finish(self) -> None:
        """The stream ended: a run that never reported an error is done (even if it produced no guide)."""
        if self.status == "running":
            self.status = "done"
        self.touch()

    def public(self) -> dict:
        return {"status": self.status, "stage": self.stage, "slug": self.slug, "permalink": self.permalink,
                "error": self.error, "updated_at": self.updated_at}


_runs: OrderedDict[str, RunRecord] = OrderedDict()


def start(run_id: str, app: str, snapshot: Callable[[], dict] | None = None) -> RunRecord:
    now = time.monotonic()
    for rid in [r for r, rec in _runs.items() if now - rec.created > KEEP_SECONDS]:
        del _runs[rid]
    while len(_runs) >= MAX_RUNS:
        _runs.popitem(last=False)
    rec = _runs[run_id] = RunRecord(run_id, app, snapshot=snapshot)
    rec.touch()
    return rec


def get(run_id: str) -> RunRecord | None:
    return _runs.get(run_id)
