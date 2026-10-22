"""Quote verification (FR4): find a cited quote on a fetched page, in visible or hidden text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .fetch import Page

MIN_QUOTE_LEN = 12
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
_CONTEXT = 80


def _fold(text: str) -> str:
    """Straighten curly quotes and collapse whitespace, keeping case."""
    return re.sub(r"\s+", " ", text.translate(_QUOTES)).strip()


def normalize(text: str) -> str:
    return _fold(text).lower()


@dataclass
class MatchResult:
    found: bool
    found_in: Literal["visible", "hidden_section"] | None = None
    too_weak: bool = False
    context: str | None = None
    case_differs: bool = False


def match_quote(quote: str, visible_text: str, all_text: str) -> MatchResult:
    """Search visible text first, then all text (which includes collapsed sections)."""
    needle = normalize(quote)
    if len(needle) < MIN_QUOTE_LEN:
        return MatchResult(found=False, too_weak=True)
    exact = _fold(quote)
    for where, text in (("visible", visible_text), ("hidden_section", all_text)):
        folded = _fold(text)
        haystack = folded.lower()
        idx = haystack.find(needle)
        if idx >= 0:
            context = haystack[max(0, idx - _CONTEXT) : idx + len(needle) + _CONTEXT]
            return MatchResult(True, where, False, context, case_differs=exact not in folded)
    return MatchResult(found=False)


def check_quote_on_page(page: Page, quote: str) -> MatchResult:
    return match_quote(quote, page.visible_text, page.hidden_text)
