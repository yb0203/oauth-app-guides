"""Generation pipeline: resolve -> find_docs -> research -> probe -> synthesize -> verify -> publish.

Code orchestrates; the LLM only extracts claims (one call per docs page) and writes the guide (one call).
`run_pipeline` is an async generator of AI SDK UI message stream events (see stream.py).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from urllib.parse import urlparse

from . import catalog, config, consoles, docsearch, domains, evidence, probe, research, store, stream, synthesize
from .fetch import Page, fetch_page
from .llm import LLM, LLMError, has_key
from .models import Composio, Evidence, Fact, Guide, Source, WallProbe, iter_evidence
from .research import VerifiedClaim

log = logging.getLogger("pipeline")
# A run must fit a 300 s serverless limit: LLM work stops by LLM_BUDGET_S, and the run as a whole by RUN_TIMEOUT_S.
RUN_TIMEOUT_S = float(os.getenv("RUN_TIMEOUT_S", "285"))
LLM_BUDGET_S = float(os.getenv("LLM_BUDGET_S", "240"))
RESEARCH_BUDGET_S = float(os.getenv("RESEARCH_BUDGET_S", "110"))


PART_NAMES = {"synthesize-a": "the verdict, limits and review", "synthesize-b": "the steps and gotchas"}
PART_SHORT = {"synthesize-a": "verdict and limits", "synthesize-b": "steps and gotchas"}


class PipelineError(Exception):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").removeprefix("www.")


async def run_pipeline(
    app: str, *, llm: LLM | None = None,
    searcher: docsearch.Searcher = docsearch.ddgs_search,
    fetcher: Callable[[str], Awaitable[Page]] = fetch_page,
    prober: Callable[[str], Awaitable[WallProbe]] = probe.probe_console,
) -> AsyncIterator[str]:
    yield stream.start(str(uuid.uuid4()))
    current = "resolve"
    try:
        async with asyncio.timeout(RUN_TIMEOUT_S):
            async for ev in _run(app, llm, searcher, fetcher, prober):
                if isinstance(ev, tuple):  # ("stage", name) bookkeeping so errors land on the right stage
                    current = ev[1]
                else:
                    yield ev
    except PipelineError as exc:
        yield stream.error(str(exc))
        yield stream.stage(exc.stage, "error", detail=str(exc))
    except LLMError as exc:
        yield stream.error(f"The language model could not produce a valid result: {exc}")
        yield stream.stage(current, "error", detail=str(exc))
    except TimeoutError:
        yield stream.error(f"The run took longer than {RUN_TIMEOUT_S:.0f} seconds and was stopped.")
        yield stream.stage(current, "error", detail="timed out")
    except Exception as exc:  # never leave the client hanging
        log.exception("pipeline failed")
        yield stream.error(f"Unexpected error: {type(exc).__name__}: {exc}")
        yield stream.stage(current, "error", detail=type(exc).__name__)
    yield stream.finish()
    yield stream.DONE


async def _run(app, llm, searcher, fetcher, prober) -> AsyncIterator[str | tuple]:
    """Yields SSE strings, plus ("stage", name) markers so failures are attributed to the right stage."""
    today = dt.date.today().isoformat()
    started = time.monotonic()
    if llm is None:
        if not has_key():
            raise PipelineError("resolve", "OPENROUTER_API_KEY is not set; set it or use LLM_MODE=fake.")
        llm = LLM()

    # 1. resolve ------------------------------------------------------------------------------------
    yield ("stage", "resolve")
    yield stream.stage("resolve", "running")
    res = catalog.resolve(app)
    slug = res.slug or store.slugify(app) or "app"
    name = res.name or app.strip()
    if res.not_in_catalog:
        yield stream.text(f"{name} is not in Composio's OAuth toolkit catalog; the guide will say so and still proceed.")
    else:
        yield stream.text(f"Resolved {name} to Composio toolkit {res.toolkit_slug} ({res.status.upper()}).")
    if res.alternatives:
        alts = ", ".join(a["name"] for a in res.alternatives[:3])
        yield stream.text(f"The name was ambiguous; picked {name}. Other matches: {alts}.")
    if res.auth_scheme and "OAUTH" not in res.auth_scheme.upper() and "DCR" not in res.auth_scheme.upper():
        yield stream.stage("resolve", "done", detail=f"{name} uses {res.auth_scheme}, not OAuth")
        for st in stream.STAGES[1:]:
            yield stream.stage(st, "skipped")
        yield stream.text(f"{name} doesn't use OAuth for third-party access (auth type: {res.auth_scheme}), so there "
                          "is no OAuth app to set up and no guide was generated.")
        return
    yield stream.stage("resolve", "done", detail=f"{name} -> {slug}", counts={"alternatives": len(res.alternatives)})

    # 2. find docs ----------------------------------------------------------------------------------
    yield ("stage", "find_docs")
    yield stream.stage("find_docs", "running")
    typed = [app.strip()] if re.match(r"^(https?://)?[\w-]+(\.[\w-]+)+(/.*)?$", app.strip()) else []
    official = domains.official_domains(slug, name, typed)  # a URL the user typed is the vendor's own domain
    pages, rejected = await docsearch.find_docs(name, slug, search=searcher, fetch=fetcher, domains=official or None)
    if not pages:
        raise PipelineError("find_docs", f"Couldn't find current docs pages about OAuth apps for {name}.")
    sources: list[Source] = []
    page_by_id: dict[str, Page] = {}
    for i, page in enumerate(pages, start=1):
        sid = f"s{i}"
        page_by_id[sid] = page
        sources.append(Source(id=sid, url=page.final_url, title=page.title or page.final_url, accessed=today,
                              kind=domains.source_kind(page.final_url, slug, name, official or None)))
    hosts = ", ".join(sorted({_host(p.final_url) for p in pages}))
    yield stream.text(f"Found {len(pages)} docs pages ({hosts}); skipped {len(rejected)} that were unreadable or don't cover the topic.")
    yield stream.stage("find_docs", "done", counts={"pages": len(pages), "rejected": len(rejected)})

    # 3. research (parallel, one LLM call per page) -------------------------------------------------
    yield ("stage", "research")
    yield stream.stage("research", "running", counts={"pages": len(pages), "claims": 0})
    claims: list[VerifiedClaim] = []
    oauth_votes: list[bool] = []
    console_urls: list[str] = []
    used: set[str] = set()

    async def extract(sid: str) -> tuple[str, research.PageClaims | None]:
        try:
            return sid, await research.extract_page(llm, name, sid, page_by_id[sid],
                                                             started + RESEARCH_BUDGET_S)
        except Exception as exc:  # LLM failures and anything odd in one page: skip that page only
            log.warning("extract %s failed: %s", sid, exc)
            return sid, None

    for fut in asyncio.as_completed([extract(sid) for sid in page_by_id]):
        sid, extracted = await fut
        page = page_by_id[sid]
        if extracted is None:
            yield stream.text(f"Couldn't read {_host(page.final_url)}; skipping that page.")
            continue
        if extracted.oauth_supported is not None:
            oauth_votes.append(extracted.oauth_supported)
        if extracted.console_url:
            console_urls.append(extracted.console_url)
        good = research.verify_claims(sid, page, extracted, start=len(claims) + 1)
        claims.extend(good)
        yield stream.text(f"{_host(page.final_url)}: {len(good)} of {len(extracted.claims)} claims have a quote "
                          "found on the page.")
        if good:
            used.add(sid)
            yield stream.source_url(sid, page.final_url, page.title or page.final_url)
        yield stream.stage("research", "running", counts={"pages": len(pages), "claims": len(claims)})
    if oauth_votes and not any(oauth_votes):
        yield stream.stage("research", "done", detail="no third-party OAuth")
        for st in stream.STAGES[3:]:
            yield stream.stage(st, "skipped")
        yield stream.text(f"{name}'s docs say it doesn't offer third-party OAuth, so there is no OAuth app to set up "
                          "and no guide was generated.")
        return
    if not claims:
        raise PipelineError("research", "No claims with a verifiable quote could be extracted from the docs pages.")
    yield stream.stage("research", "done", counts={"pages": len(used), "claims": len(claims)})

    # 4. probe the sign-in wall ---------------------------------------------------------------------
    yield ("stage", "probe")
    known = probe.KNOWN_CONSOLES.get(slug) or probe.KNOWN_CONSOLES.get(slug.split("_")[0]) or store.curated_console(slug)
    from_pages = [u for sid in sorted(used) for u in consoles.console_candidates(page_by_id[sid], slug, name, official or None)]
    from_model = [u for u in console_urls if consoles.looks_like_console(u)
                  and domains.is_official(u, slug, name, official or None)]
    console_url = known or next(iter(from_pages + from_model), None)
    wall: WallProbe | None = None
    if console_url:
        yield stream.stage("probe", "running", detail=console_url)
        wall = await prober(console_url)
        yield stream.wall(wall.model_dump(mode="json"))
        yield stream.text(f"Developer console probe: {wall.outcome.replace('_', ' ')}"
                          f"{' at ' + wall.wall_host if wall.wall_host else ''}. {wall.asks_for}")
        yield stream.stage("probe", "done", detail=wall.outcome)
    else:
        yield stream.stage("probe", "skipped", detail="no developer console URL found in the docs pages")

    # 5. synthesize ---------------------------------------------------------------------------------
    yield ("stage", "synthesize")
    yield stream.stage("synthesize", "running")
    src_titles = {s.id: f"{s.title} [{s.kind}]" for s in sources}
    deadline = started + LLM_BUDGET_S
    degraded: list[str] = []
    official_ids = {s.id for s in sources if s.kind in ("official_docs", "composio_docs")}
    if deadline - time.monotonic() < 20:  # no time for the writer: plain draft of everything
        log.warning("not enough time left for the writer model; publishing a degraded guide")
        content, degraded = synthesize.degraded_content(claims, reason="out of time"), ["synthesize-a", "synthesize-b"]
        synthesize.apply_tier_rule(content, claims, official_ids)
    else:
        content, degraded = await synthesize.synthesize(llm, name, res.status, claims, src_titles, wall,
                                                        deadline=deadline, official_sources=official_ids)
    if degraded:
        yield stream.text("The guide writer didn't finish " + " and ".join(PART_NAMES[d] for d in degraded) +
                          "; those parts are a plain draft built only from the quotes verified on the docs pages.")
    if wall:
        sid = f"s{len(sources) + 1}"
        sources.append(Source(id=sid, url=wall.console_url, title="Developer console sign-in wall probe",
                              accessed=today, kind="observation"))
        content.before_you_start.insert(0, Fact(
            text=f"The developer console needs a signed-in account: {wall.asks_for}.",
            evidence=Evidence(label="TESTED", source_id=sid, note=(
                f"Our read-only probe on {wall.observed_at} loaded {wall.console_url} and ended at {wall.final_url} "
                f"({wall.outcome.replace('_', ' ')})."))))
    yield stream.stage("synthesize", "done", counts={"llm_calls": llm.calls},
                       detail=("plain draft for " + " and ".join(PART_SHORT[d] for d in degraded)) if degraded else None)

    # 6. verify (independent re-check of every DOCS quote against the live page text) ---------------
    yield ("stage", "verify")
    yield stream.stage("verify", "running")
    total = sum(1 for _ in iter_evidence(content))
    yield stream.verification(0, 0, 0, 0, total)
    page_text = {sid: evidence.PageText(visible=p.visible_text, hidden=p.hidden_text) for sid, p in page_by_id.items()}
    kinds = {s.id: s.kind for s in sources}
    downgrades = evidence.apply_verification(content, page_text, kinds)
    conflicts = evidence.find_conflicts(content)
    summary = evidence.verification_summary(content, conflicts)
    checked = summary.docs_verified + len(downgrades)
    yield stream.verification(checked, summary.docs_verified, summary.docs_hidden,
                              len(downgrades), summary.total)
    yield stream.text(f"Verified {summary.docs_verified} of {checked} quotes on the live pages; "
                      f"downgraded {len(downgrades)} to UNCERTAIN; {len(conflicts)} conflicts.")
    cited = {ev.source_id for ev in iter_evidence(content) if ev.source_id}
    guide = Guide(
        slug=slug, app_name=name, guide_type="generated", last_verified=today,
        composio=Composio(toolkit_slug=res.toolkit_slug, status=res.status,
                          callback_url=config.COMPOSIO_CALLBACK_URL, callback_note=config.COMPOSIO_CALLBACK_NOTE), wall_probe=wall, conflicts=conflicts,
        sources=[s for s in sources if s.id in cited], verification_summary=summary,
        **content.model_dump(),
    )
    yield stream.stage("verify", "done", counts={"checked": checked, "downgraded": len(downgrades)})

    # 7. publish ------------------------------------------------------------------------------------
    yield ("stage", "publish")
    yield stream.stage("publish", "running")
    data = guide.model_dump(mode="json")
    permalink = store.save_generated(data)
    yield stream.stage("publish", "done", detail=permalink, counts={"llm_calls": llm.calls})
    yield stream.guide_part(slug, data)

