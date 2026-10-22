"""Pick the situation variant that matches the reader's answers."""

from __future__ import annotations

from .models import Guide


def render(guide: dict | Guide, answers: dict[str, str]) -> dict:
    """First variant whose `when` is fully satisfied by `answers`; otherwise the base verdict."""
    g = guide.model_dump(mode="json") if isinstance(guide, Guide) else guide
    for v in g.get("situations", {}).get("variants", []):
        when = v["when"]
        if when and all(answers.get(q) == a for q, a in when.items()):
            return {"tier": v["tier"], "summary": v["summary"], "calendar_label": v["calendar_label"],
                    "notes": list(v.get("notes", [])), "matched": True}
    base = g["verdict"]
    return {"tier": base["tier"], "summary": base["summary"], "calendar_label": base["calendar"]["label"],
            "notes": [], "matched": False}
