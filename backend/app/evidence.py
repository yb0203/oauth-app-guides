"""Evidence rules: check quotes against fetched pages, find conflicting limits, count labels."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Iterator

from .models import Conflict, Evidence, GuideContent, VerificationSummary, iter_evidence
from .verify import match_quote, normalize


@dataclass
class PageText:
    visible: str
    hidden: str  # all text, including collapsed sections


@dataclass
class Downgrade:
    location: str
    source_id: str | None
    quote: str | None
    reason: str


def _located(content: GuideContent) -> Iterator[tuple[str, Evidence]]:
    """Like models.iter_evidence, but with a path such as "steps[2]" for each item."""
    for name in ("before_you_start", "customer_gates", "gotchas", "limits", "steps", "blockers"):
        for i, item in enumerate(getattr(content, name)):
            yield f"{name}[{i}]", item.evidence
    for i, ev in enumerate(content.review.evidence):
        yield f"review.evidence[{i}]", ev


def _check(ev: Evidence, pages: dict[str, PageText]) -> str | None:
    """Set found_in when the quote is on the page; otherwise return the reason it failed."""
    page = pages.get(ev.source_id or "")
    if page is None:
        return f"source page {ev.source_id} was not fetched"
    result = match_quote(ev.quote or "", page.visible, page.hidden)
    if result.too_weak:
        return "quote is too short to verify"
    if not result.found:
        return "quote not found on the source page"
    ev.found_in = result.found_in
    return None


def apply_verification(content: GuideContent, pages: dict[str, PageText]) -> list[Downgrade]:
    """Verify DOCS (and quoted COMMUNITY) evidence in place; downgrade what can't be verified to UNCERTAIN."""
    downgrades: list[Downgrade] = []
    for location, ev in _located(content):
        if ev.label == "DOCS" or (ev.label == "COMMUNITY" and ev.quote):
            reason = _check(ev, pages)
            if reason is None:
                continue
            downgrades.append(Downgrade(location, ev.source_id, ev.quote, reason))
            old_note = f" {ev.note}" if ev.note else ""
            ev.note = f'Downgraded from {ev.label}: {reason}. Original quote: "{ev.quote}".{old_note}'
            ev.label, ev.found_in, ev.quote = "UNCERTAIN", None, None
    return downgrades


def _fmt(limit) -> str:
    return f"{limit.value:g} {limit.unit}"


def find_conflicts(content: GuideContent) -> list[Conflict]:
    """One Conflict per group of DOCS limits with the same what+scope but different values."""
    groups = defaultdict(list)
    for lim in content.limits:
        if lim.evidence.label == "DOCS" and lim.value is not None:
            groups[(normalize(lim.what), normalize(lim.scope))].append(lim)
    conflicts = []
    for group in groups.values():
        if len({(lim.value, normalize(lim.unit)) for lim in group}) < 2:
            continue
        first = group[0]
        values = " vs ".join(dict.fromkeys(_fmt(lim) for lim in group))
        conflicts.append(Conflict(
            field=first.what,
            description=f"Docs disagree on {first.what} ({first.scope}): {values}.",
            evidence=[lim.evidence for lim in group],
        ))
    return conflicts


def verification_summary(content: GuideContent, conflicts: Sequence[Conflict] = ()) -> VerificationSummary:
    """Count every evidence object, including those inside conflicts (CONTRACT §2).

    docs_verified = all DOCS items (visible and hidden); docs_hidden = the hidden_section subset.
    Unverified DOCS (found_in None) counts as uncertain.
    """
    evs = [*iter_evidence(content), *(ev for c in conflicts for ev in c.evidence)]
    s = VerificationSummary(total=len(evs))
    for ev in evs:
        if ev.label == "TESTED":
            s.tested += 1
        elif ev.label == "COMMUNITY":
            s.community += 1
        elif ev.label == "DOCS" and ev.found_in:
            s.docs_verified += 1
            s.docs_hidden += ev.found_in == "hidden_section"
        else:
            s.uncertain += 1
    return s
