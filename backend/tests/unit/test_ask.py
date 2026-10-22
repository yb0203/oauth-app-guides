"""Ask this guide: facts index, keyword answerer, post-check, live answerer (mocked), SSE stream and endpoint."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from app import api, ask, config, stream
from app.llm import LLMError


def guide(slug: str) -> dict:
    return json.loads((config.CURATED_DIR / f"{slug}.json").read_text())


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.delenv("GENERATE_RATE_LIMIT", raising=False)


# --- facts index -------------------------------------------------------------------------------

def test_facts_index_covers_sections_with_stable_refs():
    g = guide("github")
    facts = ask.build_facts(g)
    refs = [f.ref for f in facts]
    assert len(refs) == len(set(refs))
    for ref in ("verdict", "before_you_start.0", "limits.0", "steps.0"):
        assert ref in refs
    assert any(r.startswith("review.") for r in refs) or not g["review"]["trigger"]
    assert "review.trigger" in [f.ref for f in ask.build_facts(guide("google-gmail"))]
    assert ask.build_facts(g) == facts  # stable
    step = next(f for f in facts if f.ref == "steps.0")
    assert step.evidence == g["steps"][0]["evidence"] and g["steps"][0]["title"] in step.text
    assert next(f for f in facts if f.ref == "verdict").evidence is None


def test_variant_facts_carry_their_situation():
    facts = ask.build_facts(guide("google-gmail"))
    variants = [f for f in facts if f.kind == "variant"]
    assert variants and all(f.when for f in variants) and all(f.evidence is None for f in variants)


# --- keyword answerer: the three required examples --------------------------------------------

def test_gmail_avoid_review_cites_internal_fact_and_offers_internal_option():
    a = ask.keyword_answer(guide("google-gmail"), "can I avoid Google review?")
    assert a.covered and a.citations
    assert any("internal" in c["fact"].lower() for c in a.citations)
    labels = [x["label"] for x in a.actions]
    assert any(x["question_id"] == "audience" and x["option_id"] == "internal" for x in a.actions)
    assert "Apply: Only people inside our own Google Workspace organization" in labels
    assert "[1]" in a.text


def test_xero_how_many_organisations_cites_the_five_connection_limit():
    a = ask.keyword_answer(guide("xero"), "how many organisations can connect?")
    assert a.covered and 1 <= len(a.citations) <= 3
    assert any(re.search(r"\b5\b|five", c["fact"], re.I) and "connection" in c["fact"].lower() for c in a.citations)
    assert all(c["label"] in ("DOCS", "COMMUNITY", "TESTED", "UNCERTAIN") for c in a.citations)


def test_github_off_topic_is_not_covered():
    a = ask.keyword_answer(guide("github"), "what's the capital of France?")
    assert a.covered is False and a.citations == [] and a.actions == []
    assert "doesn't cover" in a.text or "does not cover" in a.text


@pytest.mark.parametrize("q", ["who won the world cup", "tell me a joke", "", "???"])
def test_other_off_topic_questions_not_covered(q):
    assert ask.keyword_answer(guide("github"), q).covered is False


def test_situation_words_map_to_options_and_skip_already_selected():
    g = guide("google-gmail")
    a = ask.keyword_answer(g, "my agent needs to read email, what happens?")
    assert any(x["question_id"] == "capability" and x["option_id"] == "read" for x in a.actions)
    b = ask.keyword_answer(g, "my agent needs to read email, what happens?", {"capability": "read"})
    assert not any(x["question_id"] == "capability" for x in b.actions)


def test_markers_are_sequential_and_match_citations():
    a = ask.keyword_answer(guide("xero"), "how long do refresh tokens last?")
    assert a.covered
    markers = re.findall(r"\[(\d+)\]", a.text)
    assert sorted(set(markers)) == [c["marker"] for c in a.citations]


def test_citation_entries_point_to_real_evidence_and_sources():
    g = guide("xero")
    a = ask.keyword_answer(g, "how many organisations can connect?")
    src = {s["id"]: s for s in g["sources"]}
    for c in a.citations:
        assert set(c) >= {"marker", "label", "source_id", "url", "title", "quote", "found_in", "fact"}
        if c["source_id"]:
            assert c["url"] == src[c["source_id"]]["url"] and c["title"] == src[c["source_id"]]["title"]


# --- post-check ---------------------------------------------------------------------------------

def raw(text, cites, actions=(), covered=True):
    return ask.RawAnswer(text=text, citations=cites, actions=list(actions), covered=covered)


def test_post_check_strips_unresolvable_markers_and_renumbers():
    g = guide("github")
    out = ask.post_check(g, raw("Ten URLs [1]. Ghost [2]. Another real one [3].",
                                [("1", "limits.0"), ("2", "nope.9"), ("3", "gotchas.0")]))
    assert out.text == "Ten URLs [1]. Ghost. Another real one [2]." and [c["marker"] for c in out.citations] == ["1", "2"]


def test_post_check_drops_citations_never_used_in_text_and_uncitable_facts():
    g = guide("github")
    out = ask.post_check(g, raw("Only this [1].", [("1", "limits.0"), ("2", "steps.1")]))
    assert [c["marker"] for c in out.citations] == ["1"]
    out = ask.post_check(g, raw("Verdict has no evidence [1].", [("1", "verdict")]))
    # the verdict has no evidence of its own: it is cited via the best-matching fact that has real evidence, or not at all
    assert all(c["label"] != "UNCERTAIN" and c["quote"] for c in out.citations)
    assert bool(out.citations) == ("[1]" in out.text)


def test_post_check_drops_actions_for_unknown_questions_or_options():
    g = guide("google-gmail")
    acts = [("audience", "internal"), ("audience", "martian"), ("nope", "internal")]
    out = ask.post_check(g, raw("Answer.", [], acts))
    assert [(a["question_id"], a["option_id"]) for a in out.actions] == [("audience", "internal")]
    assert out.actions[0]["kind"] == "set_situation" and out.actions[0]["label"].startswith("Apply: ")


def test_post_check_uncovered_has_no_citations_or_actions():
    out = ask.post_check(guide("github"), raw("Nothing.", [("1", "limits.0")], [], covered=False))
    assert out.covered is False and out.citations == [] and out.actions == []


# --- live answerer (mocked LLM) ------------------------------------------------------------------

class FakeLLM:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.prompts = result, error, []

    async def run(self, output_type, instructions, prompt, *, label="", **kw):
        self.kw = kw
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.result


async def test_live_answer_uses_llm_output_then_post_checks():
    llm_out = ask.LLMAnswer(covered=True, answer_text="You can add 10 callback URLs [1] and a ghost [7].",
                            citations=[ask.LLMCitation(marker="1", ref="limits.0"),
                                       ask.LLMCitation(marker="7", ref="zzz")],
                            actions=[ask.LLMAction(question_id="x", option_id="y")])
    llm = FakeLLM(llm_out)
    a = await ask.answer_question(guide("github"), "how many callback URLs?", {}, [], mode="live", llm=llm)
    assert a.text == "You can add 10 callback URLs [1] and a ghost." and len(a.citations) == 1 and a.actions == []
    assert "limits.0" in llm.prompts[0] and "how many callback URLs?" in llm.prompts[0]


async def test_live_answer_falls_back_to_keywords_on_error():
    a = await ask.answer_question(guide("xero"), "how many organisations can connect?", {}, [], mode="live",
                                  llm=FakeLLM(error=LLMError("boom")))
    assert a.covered and a.citations


async def test_live_without_key_falls_back(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    a = await ask.answer_question(guide("xero"), "how many organisations can connect?", {}, [], mode="live")
    assert a.covered


# --- request parsing -----------------------------------------------------------------------------

def test_parse_plain_and_usechat_bodies():
    r = ask.parse_ask_body({"question": " hi ", "situation": {"a": "b"}, "history": [{"role": "user", "text": "x"}]})
    assert (r.question, r.situation, r.history) == ("hi", {"a": "b"}, [{"role": "user", "text": "x"}])
    r = ask.parse_ask_body({"messages": [{"role": "user", "content": "first"}, {"role": "assistant", "content": "ok"},
                                         {"role": "user", "parts": [{"type": "text", "text": "second"}]}],
                            "situation": {"a": "b"}})
    assert r.question == "second" and r.situation == {"a": "b"}
    assert r.history == [{"role": "user", "text": "first"}, {"role": "assistant", "text": "ok"}]


@pytest.mark.parametrize("body", [{}, {"question": "  "}, {"messages": []}, {"question": "x" * 2000}, []])
def test_parse_rejects_bad_bodies(body):
    with pytest.raises(Exception) as exc:
        ask.parse_ask_body(body)
    assert getattr(exc.value, "status_code", 422) == 422


def test_bad_situation_values_are_ignored():
    r = ask.parse_ask_body({"question": "q", "situation": {"a": 1, "b": "ok"}, "history": "nope"})
    assert r.situation == {"b": "ok"} and r.history == []


# --- endpoint + SSE ------------------------------------------------------------------------------

@pytest.fixture()
def client():
    return TestClient(api.create_app())


def test_endpoint_streams_per_contract(client):
    r = client.post("/api/guides/google-gmail/ask", json={"question": "can I avoid Google review?"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["x-vercel-ai-ui-message-stream"] == "v1"
    ev = stream.parse_sse(r.text)
    assert ev[0]["type"] == "start" and ev[-1] == "[DONE]" and ev[-2] == {"type": "finish"}
    types = [e["type"] for e in ev[:-1]]
    assert types.index("text-start") < types.index("text-delta") < types.index("text-end") < types.index("data-citations")
    assert types.index("data-citations") < types.index("data-answer-meta") < types.index("finish")
    ids = {e["id"] for e in ev if isinstance(e, dict) and e["type"].startswith("text-")}
    assert len(ids) == 1
    text = "".join(e["delta"] for e in ev if isinstance(e, dict) and e["type"] == "text-delta")
    cites = next(e for e in ev if isinstance(e, dict) and e["type"] == "data-citations")
    assert cites["id"] == "citations"
    assert sorted(set(re.findall(r"\[(\d+)\]", text))) == [c["marker"] for c in cites["data"]]
    actions = [e for e in ev if isinstance(e, dict) and e["type"] == "data-action"]
    assert actions and actions[0]["id"] == "action-1" and actions[0]["data"]["kind"] == "set_situation"
    meta = next(e for e in ev if isinstance(e, dict) and e["type"] == "data-answer-meta")
    assert meta["id"] == "meta" and meta["data"] == {"covered": True, "suggest": None}


def test_endpoint_uncovered_has_regenerate_suggestion_and_no_citations(client):
    ev = stream.parse_sse(client.post("/api/guides/github/ask", json={"question": "capital of France?"}).text)
    cites = next(e for e in ev if isinstance(e, dict) and e["type"] == "data-citations")
    meta = next(e for e in ev if isinstance(e, dict) and e["type"] == "data-answer-meta")
    assert cites["data"] == [] and meta["data"] == {"covered": False, "suggest": "regenerate"}
    assert not [e for e in ev if isinstance(e, dict) and e["type"] == "data-action"]


def test_endpoint_usechat_body_and_situation(client):
    body = {"messages": [{"role": "user", "content": "I need to read email"}], "situation": {"audience": "internal"}}
    ev = stream.parse_sse(client.post("/api/guides/google-gmail/ask", json=body).text)
    actions = [e["data"] for e in ev if isinstance(e, dict) and e["type"] == "data-action"]
    assert any(a["question_id"] == "capability" for a in actions)
    assert not any(a["question_id"] == "audience" for a in actions)


def test_endpoint_404_and_422(client):
    assert client.post("/api/guides/nope/ask", json={"question": "hi"}).status_code == 404
    assert client.post("/api/guides/github/ask", json={}).status_code == 422
    assert client.post("/api/guides/github/ask", content=b"not json").status_code == 422


def test_endpoint_live_mode_uses_llm_path(client, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    seen = {}

    async def fake_answer(g, question, situation, history, *, mode, llm=None):
        seen["mode"] = mode
        return ask.Answer(text="Mocked [1].", covered=True, actions=[], citations=[
            {"marker": "1", "label": "UNCERTAIN", "source_id": None, "url": "", "title": "", "quote": None,
             "found_in": None, "fact": "x"}])

    monkeypatch.setattr(ask, "answer_question", fake_answer)
    ev = stream.parse_sse(client.post("/api/guides/github/ask", json={"question": "anything"}).text)
    assert seen["mode"] == "live" and ev[-1] == "[DONE]"


def test_endpoint_error_becomes_in_band_error(client, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("secret internals")

    monkeypatch.setattr(ask, "answer_question", boom)
    r = client.post("/api/guides/github/ask", json={"question": "anything"})
    ev = stream.parse_sse(r.text)
    err = next(e for e in ev if isinstance(e, dict) and e["type"] == "error")
    assert "secret" not in err["errorText"] and ev[-1] == "[DONE]"


# --- answer quality regressions (main-session review, 2026-10-22) ---------------------------------

def words(a) -> int:
    return len(a.text.split())


def test_gmail_avoid_review_leads_with_internal_exemption_with_its_own_evidence():
    g = guide("google-gmail")
    a = ask.keyword_answer(g, "can I avoid Google review?")
    assert a.text.startswith("No Google review: apps used only inside your own Workspace organization")
    assert words(a) <= 75
    assert [(x["question_id"], x["option_id"]) for x in a.actions][:1] == [("audience", "internal")]
    first = a.citations[0]
    assert first["fact"].startswith("An Internal app only works for people inside your own Workspace organization")
    assert first["quote"].startswith("use of restricted or sensitive scopes doesn't require further review")
    quotes = [c["quote"] for c in a.citations]
    assert len(quotes) == len(set(quotes)) and len(a.citations) <= 3  # no repeated evidence
    assert not any("third-party server" in (c["quote"] or "") for c in a.citations[:1])


def test_each_citation_is_the_evidence_of_the_sentence_it_follows():
    for slug, q in [("google-gmail", "can I avoid Google review?"), ("spotify", "can a solo developer get extended quota?"),
                    ("xero", "how many organisations can connect?")]:
        g = guide(slug)
        a = ask.keyword_answer(g, q)
        facts = {f.text: f for f in ask.build_facts(g)}
        assert a.citations
        for c in a.citations:
            sentence = ask._say(facts[c["fact"]])
            assert f"{sentence} [{c['marker']}]" in a.text, (slug, sentence)


def test_spotify_solo_developer_leads_with_organizations_only_rule():
    a = ask.keyword_answer(guide("spotify"), "can a solo developer get extended quota?")
    assert a.covered and words(a) <= 75
    assert a.citations[0]["quote"] == "Spotify only accepts applications from organizations (not individuals)"
    assert any("250" in c["fact"] or "250k" in (c["quote"] or "") for c in a.citations)
    assert "QUOTA_EXCEEDED" not in a.text and not any("429" in c["fact"] for c in a.citations)
    assert any(x["question_id"] == "applicant" and x["option_id"] == "individual" for x in a.actions)


def test_blockers_rank_high_only_when_the_question_mentions_a_symptom():
    g = guide("spotify")
    plain = ask.keyword_answer(g, "what happens when I exceed the request quota?")
    assert plain.covered
    sym = ask.keyword_answer(g, "I get a 429 QUOTA_EXCEEDED error, what is wrong?")
    assert any("429" in c["fact"] for c in sym.citations)


def test_multi_evidence_review_fact_cites_the_quote_that_fits_the_question():
    a = ask.keyword_answer(guide("spotify"), "how long does extended quota review take?")
    assert any("six weeks" in (c["quote"] or "") for c in a.citations)


def test_xero_still_cites_the_five_limits():
    a = ask.keyword_answer(guide("xero"), "how many organisations can connect?")
    facts = " ".join(c["fact"] for c in a.citations)
    assert "5 connections" in facts or "5 apps" in facts and words(a) <= 75


RAW_ENUMS = ("human (", "either (", "agent (", "real_account", "legal_acceptance", "(conditional)", "(yes)", "(no)",
             "review_required", "verify_to_scale", "partner_only")


def test_no_answer_leaks_raw_enum_names():
    import glob
    for f in sorted(glob.glob(str(config.CURATED_DIR / "*.json"))):
        g = json.load(open(f))
        questions = ["how do I create the app?", "what are the steps to register?", "who does each step?",
                     "can I avoid review?", "how long does review take?", "how much does it cost?",
                     "what do I submit for review?", "what are the limits?", "I get an error", "how many users?"]
        for q in questions:
            a = ask.keyword_answer(g, q)
            for raw in RAW_ENUMS:
                assert raw not in a.text, (f, q, raw, a.text)
        for fact in ask.build_facts(g):  # and no fact text carries them either
            for raw in ("human (", "real_account", "legal_acceptance"):
                assert raw not in fact.text


def test_step_facts_use_plain_words():
    facts = {f.ref: f.text for f in ask.build_facts(guide("google-gmail"))}
    assert facts["steps.2"].startswith("Step 3 (you do this, needs your own account): Choose the Audience")


# --- markers the model forgot, and the live /ask model choice --------------------------------------

async def test_live_answer_without_markers_gets_them_attached_to_the_matching_sentences():
    g = guide("google-gmail")
    text = ("Choosing Internal means there is no Google review. "
            "Sending with gmail.send needs sensitive scope verification, which takes about 3 to 5 business days.")
    llm_out = ask.LLMAnswer(covered=True, answer_text=text, citations=[
        ask.LLMCitation(marker="1", ref="steps.11"), ask.LLMCitation(marker="2", ref="customer_gates.2")])
    a = await ask.answer_question(g, "how long will review take?", {}, [], mode="live", llm=FakeLLM(llm_out))
    assert len(a.citations) == 2
    pieces = re.findall(r"(.*?)\s\[(\d+)\]", a.text)  # (sentence, marker) pairs
    assert len(pieces) == 2
    by_marker = {c["marker"]: c["fact"] for c in a.citations}
    # the Internal-app fact lands on the Internal sentence, the 3-5 days step on the gmail.send sentence
    assert "Internal" in pieces[0][0] and by_marker[pieces[0][1]].startswith("An Internal app")
    assert "gmail.send" in pieces[1][0] and by_marker[pieces[1][1]].startswith("Step 12")


async def test_markers_fall_back_to_end_of_answer_when_no_sentence_matches():
    g = guide("github")
    llm_out = ask.LLMAnswer(covered=True, answer_text="Zzz qqq.", citations=[ask.LLMCitation(marker="1", ref="limits.0")])
    a = await ask.answer_question(g, "q", {}, [], mode="live", llm=FakeLLM(llm_out))
    assert a.text == "Zzz qqq. [1]" and len(a.citations) == 1


async def test_ask_uses_its_own_fast_model_with_a_20s_timeout(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.delenv("LLM_MODEL_ASK", raising=False)
    seen = {}

    class Spy(ask.LLM):
        async def run(self, output_type, instructions, prompt, *, label="", **kw):
            seen.update(models=self.model_names, **kw)
            raise LLMError("timeout")

    monkeypatch.setattr(ask, "LLM", Spy)
    a = await ask.answer_question(guide("xero"), "how many organisations can connect?", {}, [], mode="live")
    assert seen["models"] == ["nvidia/nemotron-3-ultra-550b-a55b:free"] and seen["timeout"] == 20.0
    assert a.covered and a.citations  # fell back to deterministic retrieval
    monkeypatch.setenv("LLM_MODEL_ASK", "minimax/minimax-m3.1-flash:free")
    await ask.answer_question(guide("xero"), "how many organisations can connect?", {}, [], mode="live")
    assert seen["models"] == ["minimax/minimax-m3.1-flash:free"]


async def test_ask_endpoint_sends_heartbeats(client, monkeypatch):
    import asyncio

    monkeypatch.setenv("HEARTBEAT_SECONDS", "0.05")

    async def slow(g, question, situation, history, *, mode, llm=None):
        await asyncio.sleep(0.3)
        return ask.Answer(text="Done.", covered=True)

    monkeypatch.setattr(ask, "answer_question", slow)
    r = client.post("/api/guides/github/ask", json={"question": "anything"})
    assert r.text.count(": ping") >= 2
    ev = stream.parse_sse(r.text)
    assert ev[-1] == "[DONE]" and any(isinstance(e, dict) and e["type"] == "data-answer-meta" for e in ev)


# --- production bug: the real model reply shape (markers written as "[1]", refs to evidence-less facts) -----------

REAL_SHAPE = ask.LLMAnswer(
    covered=True,
    answer_text=("Yes, you can avoid Google review if your app is used only inside your own Google Workspace "
                 "organization by choosing Internal as the audience [1]. For External apps, review is required when "
                 "you request sensitive scopes like gmail.send or restricted scopes like gmail.readonly [2]."),
    citations=[ask.LLMCitation(marker="[1]", ref="variants.0"), ask.LLMCitation(marker="[2]", ref="review.trigger")],
    actions=[ask.LLMAction(question_id="audience", option_id="internal"),
             ask.LLMAction(question_id="audience", option_id="external"),
             ask.LLMAction(question_id="capability", option_id="send"),
             ask.LLMAction(question_id="capability", option_id="read")])


async def test_bracketed_markers_and_evidence_less_refs_still_give_citations():
    a = await ask.answer_question(guide("google-gmail"), "Can I avoid Google review?", {}, [], mode="live",
                                  llm=FakeLLM(REAL_SHAPE))
    assert re.findall(r"\[(\d+)\]", a.text) == ["1", "2"] and len(a.citations) == 2
    assert a.citations[0]["fact"].startswith("An Internal app only works")  # backed by the fact that supports the variant
    assert all(c["quote"] for c in a.citations)


async def test_only_the_recommended_option_is_offered_not_all_four():
    a = await ask.answer_question(guide("google-gmail"), "Can I avoid Google review?", {}, [], mode="live",
                                  llm=FakeLLM(REAL_SHAPE))
    assert [(x["question_id"], x["option_id"]) for x in a.actions] == [("audience", "internal")]


async def test_actions_for_options_the_question_names_are_kept_up_to_two():
    out = ask.LLMAnswer(covered=True, answer_text="Reading mail needs a restricted scope, so expect a security assessment.",
                        citations=[], actions=[ask.LLMAction(question_id="capability", option_id="read"),
                                               ask.LLMAction(question_id="capability", option_id="send"),
                                               ask.LLMAction(question_id="audience", option_id="external"),
                                               ask.LLMAction(question_id="audience", option_id="internal")])
    a = await ask.answer_question(guide("google-gmail"), "What if my agent needs to read email for outside customers?", {},
                                  [], mode="live", llm=FakeLLM(out))
    got = {(x["question_id"], x["option_id"]) for x in a.actions}
    assert ("capability", "read") in got and ("capability", "send") not in got and len(got) <= 2
