# Changelog

## 0.2.0 - 2026-06-04

- New tools: `get_catalog_info`, `list_api_groups`, `list_endpoints`, `get_endpoint_by_url`, `aps_auth_status`, `aps_live_get`
- Enhanced `search_autodesk_endpoints` with filters; structured JSON responses
- Fuzzy matching in `get_endpoint_details`
- Live read-only GET access via `.env` credentials (two-legged or static token)
- JSON schema validation for `data/*.json`, pytest suite
- Examples moved to `examples/`
- Cursor MCP config in `.cursor/mcp.json`

## 0.1.0

- Initial offline search and endpoint detail tools
