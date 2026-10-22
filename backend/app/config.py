"""Paths and environment. `.env` is loaded once; never print its values."""

import os
import pathlib

from dotenv import load_dotenv

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

CURATED_DIR = pathlib.Path(os.getenv("CURATED_DIR", REPO_ROOT / "data" / "guides"))
GENERATED_DIR = pathlib.Path(os.getenv("GENERATED_DIR", BACKEND_DIR / "generated"))
CATALOG_CSV = REPO_ROOT / "research" / "composio" / "catalog.csv"
CATALOG_ALL_CSV = REPO_ROOT / "research" / "composio" / "catalog_all_oauth_toolkits.csv"
GUIDE_SCHEMA = REPO_ROOT / "data" / "schema" / "guide.schema.json"

COMPOSIO_CALLBACK_URL = "https://backend.composio.dev/api/v3/toolkits/auth/callback"
COMPOSIO_CALLBACK_NOTE = (
    "Copy the exact redirect URI shown in your Composio auth config; some toolkits still show the "
    "legacy https://backend.composio.dev/api/v1/auth-apps/add."
)


def llm_mode() -> str:
    return os.getenv("LLM_MODE", "live").lower()


def cors_origins() -> list[str]:
    return [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
