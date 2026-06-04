"""Autodesk APS MCP server: offline catalog, resources, and live read access."""

from __future__ import annotations

import json
from typing import Any

from fastmcp import FastMCP

from api_store import get_store
from aps_auth import get_auth
from aps_live import LiveApiError
from aps_live import aps_live_get as execute_live_get

mcp = FastMCP("Autodesk APS Reference")

# Load catalog once at import so tools/resources do not re-read JSON per call.
_STORE = get_store()
_STORE.reload()


def _json(data: Any) -> str:
    return json.dumps(data, indent=2)


# --- MCP resources (browse without tool calls) ---


@mcp.resource(
    "aps://catalog",
    name="APSCatalogOverview",
    description="Snapshot metadata and API group counts for the offline APS catalog.",
    mime_type="application/json",
)
def resource_catalog_overview() -> str:
    info = _STORE.get_catalog_info()
    auth = get_auth()
    payload = info.to_dict()
    payload["live_reads_available"] = auth.is_configured()
    return _json(payload)


@mcp.resource(
    "aps://catalog/groups",
    name="APSCatalogGroups",
    description="List of API groups in the offline catalog with endpoint counts.",
    mime_type="application/json",
)
def resource_catalog_groups() -> str:
    return _json({"groups": _STORE.list_groups()})


@mcp.resource(
    "aps://catalog/{group_slug}",
    name="APSCatalogGroupEndpoints",
    description="Summaries of all endpoints in one API group (use group slug, e.g. acc, bim-360).",
    mime_type="application/json",
)
def resource_group_catalog(group_slug: str) -> str:
    return _json(_STORE.get_group_catalog(group_slug))


# --- Catalog tools ---


@mcp.tool()
def get_catalog_info() -> str:
    """Returns offline catalog version, group counts, and stale-data guidance."""
    info = _STORE.get_catalog_info()
    payload = info.to_dict()
    payload["live_reads_available"] = get_auth().is_configured()
    return _json(payload)


@mcp.tool()
def list_api_groups() -> str:
    """Lists API groups in the offline catalog with endpoint counts and slugs."""
    return _json({"groups": _STORE.list_groups()})


@mcp.tool()
def list_endpoints(
    group: str | None = None,
    method: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Lists endpoint summaries, optionally filtered by group or HTTP method."""
    return _json(_STORE.list_endpoints(group=group, method=method, limit=limit, offset=offset))


@mcp.tool()
def search_autodesk_endpoints(
    keyword: str,
    group: str | None = None,
    method: str | None = None,
    scope: str | None = None,
    limit: int = 25,
) -> str:
    """
    Search offline APS endpoint specs by keyword.
    Optional filters: group, method, oauth scope substring.
    """
    return _json(_STORE.search(keyword, group=group, method=method, scope=scope, limit=limit))


@mcp.tool()
def get_endpoint_details(endpoint_name: str) -> str:
    """Returns full offline spec for an endpoint (exact or fuzzy name match)."""
    result = _STORE.get_by_name(endpoint_name)
    if result.get("match_type") == "exact":
        return _json(result["endpoint"])
    return _json(result)


@mcp.tool()
def get_endpoint_by_url(url_fragment: str) -> str:
    """Find offline endpoint specs whose URL contains the given fragment."""
    return _json(_STORE.get_by_url_fragment(url_fragment))


# --- Live APS tools ---


@mcp.tool()
def aps_auth_status() -> str:
    """Reports whether .env APS credentials are configured for live API reads."""
    return _json(get_auth().status())


@mcp.tool()
def aps_live_get(
    url: str,
    query_parameters: dict[str, str] | None = None,
    scopes: str | None = None,
) -> str:
    """
    Perform a read-only GET against developer.api.autodesk.com using .env credentials.
    Uses APS_ACCESS_TOKEN if set; otherwise obtains a two-legged token (APS_CLIENT_ID/SECRET).
    """
    try:
        return _json(
            execute_live_get(
                url,
                query_parameters=query_parameters,
                scopes=scopes,
            )
        )
    except LiveApiError as exc:
        return _json({"error": str(exc)})


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
