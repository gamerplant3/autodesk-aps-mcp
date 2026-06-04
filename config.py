"""Paths and constants for the Autodesk APS MCP server."""

import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
README_FILE = ROOT_DIR / "README.md"
SCHEMA_FILE = ROOT_DIR / "schemas" / "endpoint.schema.json"
ENV_FILE = ROOT_DIR / ".env"

APS_TOKEN_URL = "https://developer.api.autodesk.com/authentication/v2/token"
ALLOWED_API_HOSTS = frozenset({"developer.api.autodesk.com"})

DEFAULT_LIVE_SCOPES = "data:read account:read"

_CATALOG_SNAPSHOT_RE = re.compile(
    r"^\*\*Catalog snapshot:\*\*\s*(\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)


def get_catalog_snapshot_date() -> str:
    """Read catalog snapshot date from README.md (single source of truth)."""
    if not README_FILE.exists():
        return "unknown"
    match = _CATALOG_SNAPSHOT_RE.search(README_FILE.read_text(encoding="utf-8"))
    return match.group(1) if match else "unknown"
