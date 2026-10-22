"""Regression for the first live Todoist run: managed-app framing, DOCS from third parties, skipped probe."""

import pathlib

import pytest

from app import config, stream
from app.fetch import Page
from app.models import Guide, GuideContent, Step, WallProbe, iter_evidence
from app.research import Claim, PageClaims, VerifiedClaim
from app.synthesize import ensure_byo_path, postprocess
from tests.unit.test_pipeline import FakeLLM, collect

FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "pages" / "todoist_api_excerpt.html"
QUOTE = "developers need to create their applications in the App Management Console"
OFFICIAL = ["https://developer.todoist.com/api/v1/", "https://doist.github.io/todoist-sdk-typescript/authorization/"]
THIRD = ["https://automatisch.io/docs/apps/todoist/connection", "https://developer.transmitsecurity.com/todoist"]


def page(url: str, html: str = "") -> Page:
    text = ("Todoist OAuth authorization. Register your application and use the client id and redirect URI. " + QUOTE
            + ". " + "filler words " * 80)
    return Page(url, url, [], 200, "Todoist docs", text, text, "http", None, html)


def managed_framing_content(github: dict) -> GuideContent:
    """What the writer produced for a Composio-managed app: no registration step, one 'optional' BYO step."""
    c = GuideContent.model_validate({k: github[k] for k in GuideContent.model_fields})
    ev = c.steps[0].evidence
    c.steps = [
        Step(n=1, title="Use the managed Todoist app", detail="Nothing to register.", actor="agent", evidence=ev),
        Step(n=2, title="Authorize Todoist", detail="Grant access.", actor="human", human_reason="credential", evidence=ev),
        Step(n=3, title="Optional: register a BYO Todoist app", detail="Create an app in the console.", actor="human",
             human_reason="real_account", evidence=ev),
    ]
    return c


def test_postprocess_makes_registering_your_own_app_a_real_step_with_the_callback(github_guide_dict):
    c = managed_framing_content(github_guide_dict)
    postprocess(c, [])
    titles = [s.title for s in c.steps]
    assert "Register a BYO Todoist app" in titles and not any(t.lower().startswith("optional") for t in titles)
    assert any(config.COMPOSIO_CALLBACK_URL in v.value for s in c.steps for v in s.values)
    assert [s.n for s in c.steps] == list(range(1, len(c.steps) + 1))


def test_missing_registration_step_is_inserted_after_sign_in(github_guide_dict):
    c = managed_framing_content(github_guide_dict)
    c.steps = [s for s in c.steps if "register" not in s.title.lower()]
    claim = VerifiedClaim("c1", "s1", Claim(category="registration", text="Create apps in the console", quote=QUOTE), "visible")
    ensure_byo_path(c, [claim])
    reg = next(s for s in c.steps if s.title.startswith("Register your own OAuth app"))
    assert reg.evidence.label == "DOCS" and reg.evidence.quote == QUOTE and reg.evidence.found_in == "visible"
    assert reg.human_reason == "real_account"


@pytest.fixture()
def run_env(github_guide_dict, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "GENERATED_DIR", tmp_path)
    return github_guide_dict


class CitingLLM(FakeLLM):
    """Cites the verified quote from source s1 (official) on half the evidence and from s3 (third party) on the rest."""

    async def run(self, output_type, instructions, prompt, *, label="", **kw):
        if output_type is GuideContent:
            c = managed_framing_content(self.github)
            for i, ev in enumerate(iter_evidence(c)):
                ev.label, ev.source_id, ev.quote, ev.found_in = "DOCS", "s1" if i % 2 == 0 else "s3", QUOTE, None
            return c
        return PageClaims(console_url=None, claims=[Claim(category="registration", text="Create apps in the console", quote=QUOTE)])


async def test_todoist_run_labels_third_party_as_community_and_probes_the_console(run_env):
    pages = {u: page(u, FIX.read_text() if "developer.todoist" in u else "") for u in OFFICIAL + THIRD}
    searched: list[str] = []

    def searcher(q, n):
        searched.append(q)
        return [{"href": u} for u in (OFFICIAL if "site:" in q else THIRD)]

    fetched: list[str] = []

    async def fetcher(url):
        fetched.append(url)
        return pages[url]

    probed: list[str] = []

    async def prober(url):
        probed.append(url)
        return WallProbe(console_url=url, final_url="https://app.todoist.com/auth/login", redirect_chain=[],
                         outcome="login_wall", wall_host="app.todoist.com", asks_for="Todoist account", bot_check=False,
                         method="http", observed_at="2026-10-22")

    from app.pipeline import run_pipeline

    events = stream.parse_sse("".join([e async for e in run_pipeline(
        "todoist.com", llm=CitingLLM(run_env), searcher=searcher, fetcher=fetcher, prober=prober)]))
    guide = Guide.model_validate(next(e for e in events if isinstance(e, dict) and e["type"] == "data-guide")["data"]["guide"])

    assert not any(u in fetched for u in THIRD)  # two official pages were enough: no third-party top-up
    assert all(s.kind == "official_docs" for s in guide.sources if s.kind != "observation")
    assert probed == ["https://app.todoist.com/app/settings/integrations/app-management"]
    assert guide.wall_probe and guide.wall_probe.outcome == "login_wall"
    assert any(config.COMPOSIO_CALLBACK_URL in v.value for s in guide.steps for v in s.values)
    assert any(s.title.startswith("Register") and not s.title.lower().startswith("optional") for s in guide.steps)
    stages = [e["data"] for e in events if isinstance(e, dict) and e["type"] == "data-stage" and e["id"] == "probe"]
    assert [s["status"] for s in stages] == ["running", "done"]


async def test_third_party_pages_only_top_up_when_fewer_than_two_official(run_env):
    pages = {OFFICIAL[0]: page(OFFICIAL[0]), THIRD[0]: page(THIRD[0]), THIRD[1]: page(THIRD[1])}

    def searcher(q, n):
        return [{"href": u} for u in ([OFFICIAL[0]] if "site:" in q else THIRD)]

    async def fetcher(url):
        return pages[url]

    from app.docsearch import find_docs

    good, _ = await find_docs("Todoist", "todoist", search=searcher, fetch=fetcher)
    from app.domains import source_kind

    kinds = [source_kind(p.final_url, "todoist", "Todoist") for p in good]
    assert kinds[0] == "official_docs" and kinds.count("official_docs") == 1
    assert 1 <= kinds.count("community") <= 3 and len(good) <= 5


async def test_console_skipped_only_when_nothing_found_and_says_so(run_env):
    pages = {u: page(u) for u in OFFICIAL}

    async def fetcher(url):
        return pages[url]

    async def prober(url):  # pragma: no cover - must not be called
        raise AssertionError("no console URL, nothing to probe")

    from app.pipeline import run_pipeline

    events = stream.parse_sse("".join([e async for e in run_pipeline(
        "todoist.com", llm=CitingLLM(run_env), searcher=lambda q, n: [{"href": u} for u in OFFICIAL],
        fetcher=fetcher, prober=prober)]))
    probe_stage = [e["data"] for e in events if isinstance(e, dict) and e["type"] == "data-stage" and e["id"] == "probe"][-1]
    assert probe_stage["status"] == "skipped" and "docs pages" in probe_stage["detail"]
