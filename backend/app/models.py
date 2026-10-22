"""Pydantic models matching data/schema/guide.schema.json exactly.

`Guide` is the full, published shape. `GuideContent` is the subset the LLM writes in the
synthesize stage; code owns the rest (slug, composio, wall probe, sources, conflicts, summary).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Tier = Literal["instant", "verify_to_scale", "review_required", "partner_only", "unknown"]
Label = Literal["TESTED", "DOCS", "COMMUNITY", "UNCERTAIN"]
FoundIn = Literal["visible", "hidden_section"]
Actor = Literal["agent", "human", "either"]
HumanReason = Literal["credential", "legal_acceptance", "payment", "identity", "real_account", "submit", "wait"]
MIN_QUOTE = 12


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(Base):
    label: Label
    source_id: str | None = None
    quote: str | None = None
    found_in: FoundIn | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _label_rules(self) -> Evidence:
        if self.label == "DOCS":
            if not self.source_id:
                raise ValueError("DOCS evidence needs source_id")
            if not self.quote or len(self.quote) < MIN_QUOTE:
                raise ValueError(f"DOCS evidence needs a quote of at least {MIN_QUOTE} characters")
        if self.label == "TESTED" and not self.note:
            raise ValueError("TESTED evidence needs a note describing what was observed")
        return self


class Fact(Base):
    text: str
    evidence: Evidence


class Limit(Base):
    what: str
    value: float | None = None
    unit: str
    scope: str
    evidence: Evidence


class Value(Base):
    label: str
    value: str


class Step(Base):
    n: int = Field(ge=1)
    title: str
    detail: str
    actor: Actor
    human_reason: HumanReason | None = None
    irreversible: bool = False
    values: list[Value] = Field(default_factory=list)
    evidence: Evidence

    @model_validator(mode="after")
    def _human_needs_reason(self) -> Step:
        if self.actor == "human" and self.human_reason is None:
            raise ValueError("human steps need a human_reason")
        return self


class Review(Base):
    required: Literal["yes", "no", "conditional"]
    trigger: str | None = None
    submit: list[str] = Field(default_factory=list)
    reviewer: str | None = None
    wait_official: str | None = None
    wait_community: str | None = None
    cost: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class Blocker(Base):
    symptom: str
    cause: str
    fix: str
    evidence: Evidence


class PreparedScope(Base):
    scope: str
    why: str
    review_class: Literal["none", "sensitive", "restricted", "unknown"]


class Prepared(Base):
    scopes: list[PreparedScope] = Field(default_factory=list)
    privacy_policy_outline: list[str] = Field(default_factory=list)
    consent_screen: dict[str, str] = Field(default_factory=dict)
    review_text: str | None = None


class EffortHours(Base):
    min: float
    max: float


class Calendar(Base):
    min_days: float
    max_days: float | None = None
    label: str


class Verdict(Base):
    tier: Tier
    summary: str
    effort_hours: EffortHours
    calendar: Calendar
    calendar_basis: Literal["official", "community", "estimate"]
    confidence: Literal["high", "medium", "low"]


class Option(Base):
    id: str
    label: str


class Question(Base):
    id: str
    text: str
    options: list[Option] = Field(min_length=2)


class Variant(Base):
    when: dict[str, str]
    tier: Tier
    summary: str
    calendar_label: str
    notes: list[str] = Field(default_factory=list)


class Situations(Base):
    questions: list[Question] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)


class Composio(Base):
    toolkit_slug: str | None = None
    status: Literal["managed", "byo", "not_in_catalog"]
    callback_url: str
    callback_note: str


class WallProbe(Base):
    console_url: str
    final_url: str
    redirect_chain: list[str] = Field(default_factory=list)
    outcome: Literal["login_wall", "console_reachable", "blocked", "error"]
    wall_host: str | None = None
    asks_for: str
    bot_check: bool
    method: Literal["http", "browser"]
    observed_at: str


class Conflict(Base):
    field: str
    description: str
    evidence: list[Evidence] = Field(min_length=2)


class Source(Base):
    id: str
    url: str
    title: str
    accessed: str
    kind: Literal["official_docs", "composio_docs", "community", "observation"]


class VerificationSummary(Base):
    total: int = 0
    tested: int = 0
    docs_verified: int = 0
    docs_hidden: int = 0
    community: int = 0
    uncertain: int = 0


class GuideContent(Base):
    """What the LLM writes. Everything else on a Guide is filled in by code."""

    verdict: Verdict
    situations: Situations
    byo_advice: str | None = None
    before_you_start: list[Fact] = Field(default_factory=list)
    limits: list[Limit] = Field(default_factory=list)
    steps: list[Step] = Field(min_length=1)
    review: Review
    customer_gates: list[Fact] = Field(default_factory=list)
    gotchas: list[Fact] = Field(default_factory=list)
    blockers: list[Blocker] = Field(default_factory=list)
    prepared: Prepared = Field(default_factory=Prepared)
    open_questions: list[str] = Field(default_factory=list)


class Guide(GuideContent):
    schema_version: Literal["1"] = "1"
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    app_name: str
    guide_type: Literal["curated", "generated"]
    last_verified: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    composio: Composio
    wall_probe: WallProbe | None = None
    conflicts: list[Conflict] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    verification_summary: VerificationSummary = Field(default_factory=VerificationSummary)

    @model_validator(mode="after")
    def _published_evidence_rules(self) -> Guide:
        for ev in iter_evidence(self):
            if ev.label == "DOCS" and ev.found_in is None:
                raise ValueError("DOCS evidence must have found_in (the quote was not verified on the live page)")
        return self


def iter_evidence(guide: GuideContent):
    """Yield every Evidence object in a guide (same traversal order as the page)."""
    for fact in [*guide.before_you_start, *guide.customer_gates, *guide.gotchas]:
        yield fact.evidence
    for lim in guide.limits:
        yield lim.evidence
    for step in guide.steps:
        yield step.evidence
    yield from guide.review.evidence
    for blk in guide.blockers:
        yield blk.evidence
