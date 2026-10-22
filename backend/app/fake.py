"""Fake mode: replays a realistic, recorded generation run for any input (no network, no LLM).

The guide is `data/guides/github.json`, rebadged for the requested app. Speed 1.0 takes about 17 s;
`speed` (or env FAKE_SPEED) scales every delay, and 0 means no sleeping at all. The input "!error"
replays a failed run so the error path can be developed against too.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from urllib.parse import urlparse

from . import config, store, stream
from .models import Guide, iter_evidence

ERROR_INPUT = "!error"


@dataclass
class Resolved:
    slug: str
    name: str
    toolkit_slug: str | None
    status: str  # managed | byo | not_in_catalog


def _resolve(query: str) -> Resolved:
    try:
        from . import catalog

        r = catalog.resolve(query)
        return Resolved(r.slug or store.slugify(query) or "app", r.name or query, r.toolkit_slug, r.status)
    except Exception:
        return Resolved(store.slugify(query) or "app", query, None, "not_in_catalog")


@lru_cache(maxsize=1)
def _recorded_guide() -> str:
    return (config.REPO_ROOT / "data" / "guides" / "github.json").read_text()


def _default_speed() -> float:
    try:
        return max(0.0, float(os.getenv("FAKE_SPEED", "1")))
    except ValueError:
        return 1.0


def _host(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _check_sequence(verified: int, hidden: int, downgraded: int) -> list[str]:
    """Order in which quotes pass or fail, with the downgrades spread through the run."""
    seq = ["verified"] * verified + ["hidden"] * hidden
    for k in range(downgraded):
        seq.insert((k + 1) * len(seq) // (downgraded + 1), "downgraded")
    return seq


def _wall_line(wall: dict) -> str:
    hops = _plural(len(wall["redirect_chain"]), "redirect")
    host = wall.get("wall_host") or _host(wall["final_url"])
    return {
        "login_wall": f"Sign-in wall at {host} after {hops}",
        "console_reachable": f"Console reachable at {host} without signing in",
        "blocked": f"Console at {host} blocked automated access",
    }.get(wall["outcome"], f"Couldn't reach the console at {host}")


async def fake_run(app: str, *, speed: float | None = None) -> AsyncIterator[str]:
    speed = _default_speed() if speed is None else speed

    async def pause(seconds: float) -> None:
        await asyncio.sleep(seconds * speed)

    res = _resolve(app)
    yield stream.start(f"fake-{uuid.uuid4().hex[:12]}")

    # 1. resolve
    yield stream.stage("resolve", "running")
    await pause(0.6)
    yield stream.text(f"Looking up {res.name} in the Composio catalog")
    await pause(1.0)
    if res.status == "not_in_catalog":
        yield stream.text(f"{res.name} isn't in the Composio catalog, so this guide covers the OAuth app setup only")
        detail = "Not in the Composio catalog"
    else:
        yield stream.text(f"Resolved {res.name} to Composio toolkit {res.toolkit_slug} ({res.status.upper()})")
        detail = f"Composio toolkit {res.toolkit_slug} ({res.status})"
    yield stream.stage("resolve", "done", detail=detail)

    if app.strip().lower() == ERROR_INPUT:
        yield stream.stage("find_docs", "running")
        await pause(1.2)
        yield stream.text("Searching for the developer docs")
        await pause(1.0)
        yield stream.error("Couldn't find any developer docs for this app (fake-mode error replay)")
        yield stream.stage("find_docs", "error", detail="No developer docs found")
        yield stream.finish()
        yield stream.DONE
        return

    raw = json.loads(_recorded_guide())
    guide = Guide.model_validate(raw)
    docs = [s for s in raw["sources"] if s["kind"] in {"official_docs", "composio_docs"}]
    observation = next((s for s in raw["sources"] if s["kind"] == "observation"), None)
    claims = [ev.source_id for ev in iter_evidence(guide) if ev.source_id]

    # 2. find_docs
    candidates = len(docs) + 1
    yield stream.stage("find_docs", "running")
    await pause(1.0)
    yield stream.text(f"Found {candidates} candidate docs pages on {_host(docs[0]['url'])}")
    await pause(0.6)
    yield stream.text(f"Keeping {len(docs)} that cover app registration, scopes and review")
    yield stream.stage("find_docs", "done", counts={"candidates": candidates, "kept": len(docs)})

    # 3. research
    yield stream.stage("research", "running")
    for src in docs:
        await pause(0.5)
        yield stream.source_url(src["id"], src["url"], src["title"])
        await pause(0.7)
        n = claims.count(src["id"])
        yield stream.text(f"Read {src['title']}: noted {_plural(n, 'claim')} to check later")
    yield stream.stage("research", "done", counts={"pages": len(docs), "claims": len(claims)})

    # 4. probe
    wall = raw["wall_probe"]
    yield stream.stage("probe", "running")
    yield stream.text("Opening the developer console without signing in")
    await pause(1.2)
    if observation:
        yield stream.source_url(observation["id"], observation["url"], observation["title"])
    yield stream.wall(wall)
    yield stream.text(_wall_line(wall))
    await pause(0.6)
    yield stream.stage("probe", "done", detail=wall["outcome"].replace("_", " "))

    # 5. synthesize
    yield stream.stage("synthesize", "running")
    await pause(1.2)
    yield stream.text(f"Drafting the guide from {len(docs)} pages and the console probe")
    await pause(1.8)
    n_steps, n_limits = len(guide.steps), len(guide.limits)
    gotchas = _plural(len(guide.gotchas), "gotcha")
    yield stream.text(f"Drafted {_plural(n_steps, 'step')}, {_plural(n_limits, 'limit')} and {gotchas}")
    yield stream.stage("synthesize", "done", counts={"steps": n_steps, "limits": n_limits})

    # 6. verify
    summary = guide.verification_summary
    hidden, downgraded = summary.docs_hidden, summary.uncertain
    verified = summary.docs_verified - hidden  # docs_verified counts hidden too (CONTRACT §2)
    sequence = _check_sequence(verified, hidden, downgraded)
    yield stream.stage("verify", "running")
    yield stream.text(f"Checking {len(sequence)} quotes against the live pages")
    tally = {"verified": 0, "hidden": 0, "downgraded": 0}
    for outcome in sequence:
        await pause(0.17)
        tally[outcome] += 1
        checked = sum(tally.values())
        yield stream.verification(checked, tally["verified"], tally["hidden"], tally["downgraded"], summary.total)
    yield stream.text(f"Verified {verified + hidden} of {len(sequence)} quotes; downgraded {downgraded}")
    yield stream.stage("verify", "done", counts={"checked": len(sequence), "downgraded": downgraded})

    # 7. publish
    raw["slug"] = res.slug
    raw["app_name"] = res.name
    raw["guide_type"] = "generated"
    raw["last_verified"] = date.today().isoformat()
    raw["composio"] = {**copy.deepcopy(raw["composio"]), "toolkit_slug": res.toolkit_slug, "status": res.status}
    final = Guide.model_validate(raw).model_dump(mode="json")
    yield stream.stage("publish", "running")
    await pause(0.4)
    store.remember(final)  # in memory only, so the permalink works without polluting the guide list
    yield stream.guide_part(res.slug, final)
    yield stream.text(f"Guide ready for {res.name} at /guides/{res.slug}")
    await pause(0.3)
    yield stream.stage("publish", "done", detail=f"/guides/{res.slug}")
    yield stream.finish()
    yield stream.DONE
