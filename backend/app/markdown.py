"""Export a guide as Markdown."""

from __future__ import annotations

from .models import Evidence, Guide

ACTOR_LABELS = {"agent": "agent", "human": "human", "either": "either"}
FOUND_IN_LABELS = {"visible": "verified on page", "hidden_section": "verified in a collapsed section"}


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _table(header: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return [*lines, ""]


def _bullets(items: list[str]) -> list[str]:
    return [*(f"- {i}" for i in items), ""]


def guide_to_markdown(guide: dict | Guide) -> str:
    g = guide if isinstance(guide, Guide) else Guide.model_validate(guide)
    sources = {s.id: s for s in g.sources}

    def ev(e: Evidence) -> str:
        parts = [f"**{e.label}**"]
        if e.found_in:
            parts.append(FOUND_IN_LABELS[e.found_in])
        if e.quote:
            parts.append(f'"{e.quote}"')
        if e.source_id in sources:
            parts.append(f"[{sources[e.source_id].title}]({sources[e.source_id].url})")
        if e.note:
            parts.append(e.note)
        return " - ".join(parts)

    v, c = g.verdict, g.composio
    hours, days = v.effort_hours, v.calendar
    out = [
        f"# {g.app_name}: OAuth app setup guide", "",
        f"- Tier: **{v.tier}**",
        f"- Summary: {v.summary}",
        f"- Effort: {hours.min:g} to {hours.max:g} hours",
        f"- Calendar time: {days.label} ({days.min_days:g} to {'?' if days.max_days is None else f'{days.max_days:g}'} days, basis: {v.calendar_basis})",
        f"- Confidence: {v.confidence}",
        f"- Guide type: {g.guide_type}, last verified {g.last_verified}", "",
        "## Composio", "",
        f"- Status: {c.status}" + (f" (toolkit `{c.toolkit_slug}`)" if c.toolkit_slug else ""),
        f"- Callback URL: `{c.callback_url}`",
        f"- Note: {c.callback_note}", "",
    ]
    if g.byo_advice:
        out += [f"Should you bring your own app? {g.byo_advice}", ""]

    if g.situations.variants:
        questions = {q.id: q for q in g.situations.questions}

        def when(w: dict[str, str]) -> str:
            def label(qid: str, oid: str) -> str:
                q = questions.get(qid)
                return next((o.label for o in q.options if o.id == oid), oid) if q else oid
            return "; ".join(f"{questions[q].text if q in questions else q}: {label(q, o)}" for q, o in w.items())

        out += ["## Situations", ""]
        out += _table(["If", "Tier", "Verdict", "Calendar time"], [[when(x.when), x.tier, x.summary, x.calendar_label] for x in g.situations.variants])

    if g.before_you_start:
        out += ["## Before you start", ""] + _bullets([f"{f.text} ({ev(f.evidence)})" for f in g.before_you_start])

    if g.limits:
        out += ["## Limits", ""]
        out += _table(["Limit", "Value", "Scope", "Evidence"], [[x.what, "unknown" if x.value is None else f"{x.value:g} {x.unit}", x.scope, ev(x.evidence)] for x in g.limits])

    out += ["## Steps", ""]
    for s in g.steps:
        actor = f"{ACTOR_LABELS[s.actor]}" + (f", reason: {s.human_reason}" if s.human_reason else "")
        out += [f"### {s.n}. {s.title}", "", s.detail, "", f"- Actor: {actor}"]
        if s.irreversible:
            out.append("- Irreversible: yes, double-check before you do this step")
        out += [f"- {x.label}: `{x.value}`" for x in s.values]
        out += [f"- Evidence: {ev(s.evidence)}", ""]

    r = g.review
    out += ["## Review", "", f"- Required: {r.required}"]
    for label, value in (("Trigger", r.trigger), ("Reviewer", r.reviewer), ("Wait (official)", r.wait_official), ("Wait (community)", r.wait_community), ("Cost", r.cost)):
        if value:
            out.append(f"- {label}: {value}")
    if r.submit:
        out += ["- What to submit:"] + [f"  - {x}" for x in r.submit]
    out += [f"- Evidence: {ev(e)}" for e in r.evidence] + [""]

    if g.customer_gates:
        out += ["## Customer gates", ""] + _bullets([f"{f.text} ({ev(f.evidence)})" for f in g.customer_gates])
    if g.gotchas:
        out += ["## Gotchas", ""] + _bullets([f"{f.text} ({ev(f.evidence)})" for f in g.gotchas])
    if g.blockers:
        out += ["## Blockers", ""]
        for b in g.blockers:
            out += [f"- **{b.symptom}**", f"  - Cause: {b.cause}", f"  - Fix: {b.fix}", f"  - Evidence: {ev(b.evidence)}"]
        out.append("")

    p = g.prepared
    if p.scopes or p.privacy_policy_outline or p.consent_screen or p.review_text:
        out += ["## Prepared for you", ""]
        if p.scopes:
            out += _table(["Scope", "Why", "Review class"], [[x.scope, x.why, x.review_class] for x in p.scopes])
        if p.privacy_policy_outline:
            out += ["Privacy policy outline:", ""] + _bullets(p.privacy_policy_outline)
        if p.consent_screen:
            out += ["Consent screen:", ""] + _bullets([f"{k}: {val}" for k, val in p.consent_screen.items()])
        if p.review_text:
            out += ["Review submission text:", "", p.review_text, ""]

    if g.open_questions:
        out += ["## Open questions", ""] + _bullets(g.open_questions)

    if g.wall_probe:
        w = g.wall_probe
        out += [
            "## Sign-in wall probe", "",
            f"- Console URL: {w.console_url}", f"- Ended at: {w.final_url}", f"- Outcome: {w.outcome}",
            f"- Asks for: {w.asks_for}", f"- Bot check mentioned: {'yes' if w.bot_check else 'no'}",
            f"- Method: {w.method}, observed {w.observed_at}", "",
        ]

    if g.conflicts:
        out += ["## Conflicts between sources", ""]
        for x in g.conflicts:
            out += [f"- **{x.field}**: {x.description}"] + [f"  - {ev(e)}" for e in x.evidence]
        out.append("")

    out += ["## Sources", ""] + _bullets([f"[{s.id}] [{s.title}]({s.url}) ({s.kind}, accessed {s.accessed})" for s in g.sources])

    vs = g.verification_summary
    out += [
        "## Verification summary", "",
        f"{vs.total} claims in total: {vs.tested} tested, {vs.docs_verified} verified in docs, "
        f"{vs.docs_hidden} verified in collapsed docs sections, {vs.community} community, {vs.uncertain} uncertain.", "",
    ]
    return "\n".join(out)
