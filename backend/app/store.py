"""Guide storage: curated guides from data/guides/, generated guides under backend/generated/."""

from __future__ import annotations

import json
import re

from . import config

_SLUG_OK = re.compile(r"^[a-z0-9-]+$")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


_memory: dict[str, dict] = {}  # fake-mode guides: served by permalink, never written to disk


def remember(guide: dict) -> None:
    _memory[guide["slug"]] = guide


def _read(path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


ALIASES = {"gmail": "google-gmail"}  # catalog slug -> slug of the curated guide


def get_guide(slug: str) -> dict | None:
    """Curated guides win over generated ones. Returns the raw guide JSON or None."""
    if not _SLUG_OK.match(slug):
        return None
    slug = ALIASES.get(slug, slug)
    for folder in (config.CURATED_DIR, config.GENERATED_DIR):
        g = _read(folder / f"{slug}.json")
        if g is not None:
            return g
    return _memory.get(slug)


def list_guides() -> list[dict]:
    """[{slug, app_name, guide_type, tier, last_verified}], curated first, then generated."""
    seen: dict[str, dict] = {}
    for folder in (config.CURATED_DIR, config.GENERATED_DIR):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            g = _read(path)
            if not g or g.get("slug") in seen or "verdict" not in g:
                continue
            seen[g["slug"]] = {
                "slug": g["slug"],
                "app_name": g["app_name"],
                "guide_type": g["guide_type"],
                "tier": g["verdict"]["tier"],
                "last_verified": g["last_verified"],
            }
    return list(seen.values())


def save_generated(guide: dict) -> str:
    """Store a generated guide; returns the permalink path."""
    slug = guide["slug"]
    if not _SLUG_OK.match(slug):
        raise ValueError(f"bad slug {slug!r}")
    config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    (config.GENERATED_DIR / f"{slug}.json").write_text(json.dumps(guide, indent=2))
    return f"/guides/{slug}"


def find_by_toolkit(toolkit_slug: str) -> dict | None:
    """The guide for a Composio toolkit slug (catalog `gmail` -> guide `google-gmail`), curated first."""
    direct = get_guide(toolkit_slug)
    if direct is not None:
        return direct
    for folder in (config.CURATED_DIR, config.GENERATED_DIR):
        if folder.exists():
            for path in sorted(folder.glob("*.json")):
                g = _read(path)
                if g and (g.get("composio") or {}).get("toolkit_slug") == toolkit_slug:
                    return g
    return None


def curated_console(slug: str) -> str | None:
    """The developer console URL recorded in a curated guide for this app (matched by guide or toolkit slug)."""
    if config.CURATED_DIR.exists():
        for path in sorted(config.CURATED_DIR.glob("*.json")):
            g = _read(path)
            if g and slug in (g.get("slug"), (g.get("composio") or {}).get("toolkit_slug")):
                return ((g.get("wall_probe") or {}).get("console_url")) or None
    return None
