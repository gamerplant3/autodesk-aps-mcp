# Autodesk APS MCP Server

MCP server (stdio) for Cursor: offline APS API reference plus optional **read-only live** GETs when `.env` credentials are set.

**Catalog snapshot:** 2025-04-01 — last refresh of `data/*.json`.

## Features

- Offline APS API catalog with search, endpoint details, and browseable MCP resources.
- Live read-only GETs via `aps_live_get` when `.env` credentials are set.
- `aps_auth_status` reports `user_context_available` (true only when `APS_ACCESS_TOKEN` is set). Two-legged `APS_CLIENT_ID` + `APS_CLIENT_SECRET` grant app-level access; user-specific questions ("my hubs", "my projects") require a three-legged token in `APS_ACCESS_TOKEN`.

## Tools

| Tool | Purpose |
|------|---------|
| `get_catalog_info` | When the offline docs were updated, how many endpoints exist, and a note that live APIs may be newer |
| `list_api_groups` | Lists product areas (ACC, Data Management, BIM 360, etc.) and endpoint count per area |
| `list_endpoints` | Lists endpoints from the saved catalog; optional filter by product area or HTTP method |
| `search_autodesk_endpoints` | Keyword search over saved endpoint names, URLs, and descriptions |
| `get_endpoint_details` | Full saved spec for one endpoint (parameters, headers, scopes, responses) |
| `get_endpoint_by_url` | Find saved endpoints whose URL contains your search text |
| `aps_auth_status` | Whether `.env` credentials are set and live calls are available |
| `aps_live_get` | Run a real Autodesk GET request (read-only; `developer.api.autodesk.com` only) |

## Resources

- `aps://catalog` — overview
- `aps://catalog/groups` — product areas and counts
- `aps://catalog/{area}` — endpoints in one area (e.g. `acc`, `data-management`)

## Setup

```bash
uv sync --dev
cp .env.example .env   # add APS_CLIENT_ID + APS_CLIENT_SECRET, or APS_ACCESS_TOKEN
```

For user-specific live reads (e.g. listing *your* hubs or projects), set `APS_ACCESS_TOKEN` with a three-legged OAuth token. Client ID and secret alone only reflect what the app can access, not a particular user.

**Cursor:** open this repo → restart Cursor → **Settings → Tools & MCP** → enable **`autodesk-aps`**.

Config: `.cursor/mcp.json` (loads `.env` via `envFile`).

**APS-only chat:** `/autodesk-aps <question>` or ask the **autodesk-aps** subagent. Project rule `.cursor/rules/autodesk-aps-mcp-only.mdc` is always on.

## Development

```bash
uv run pytest
uv run fastmcp run server.py
```

After editing `data/*.json`, update the **Catalog snapshot** date above.

## Examples

- `examples/list-acc-project-sheets.js` — ACC Sheets API: authenticate, paginate `GET .../sheets`, and print every sheet in a project. Requires `ACC_PROJECT_ID` and `APS_ACCESS_TOKEN` (or `APS_CLIENT_ID` + `APS_CLIENT_SECRET`).
- `examples/export-acc-sheets-pdf.js` — ACC Sheets API: list sheets → export combined PDF.

## Layout

```
.cursor/       mcp.json, agents/, rules/, permissions.json
server.py      MCP entry (also: uv run autodesk-aps-mcp)
api_store.py   Cached catalog index
aps_auth.py    .env + two-legged tokens
aps_live.py    Allowlisted live GET
data/          Offline endpoint JSON
tests/
```
