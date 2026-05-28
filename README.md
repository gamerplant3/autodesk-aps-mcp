# Autodesk APS MCP Server

An MCP server running over stdio that gives access to Autodesk API schemas.

Look at ```testing.cs``` for a sample run (used github copilot chat).

## Tools

* **`search_autodesk_endpoints`**: Keyword search across API groups, names, and descriptions.
* **`get_endpoint_details`**: Returns complete JSON specs (headers, parameters, and responses).

## Local Development

```bash
# Run server over stdio
uv run fastmcp run server.py

# Open web inspector
uv run fastmcp dev inspector server.py

```

## VS Code Integration (`.vscode/mcp.json`)

```json
{
  "servers": {
    "autodesk-aps": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\[   ]\\Documents\\Local\\autodesk-aps-mcp",
        "run",
        "fastmcp",
        "server.py"
      ]
    }
  }
}

```

*To activate: `Ctrl + Shift + P` -> `MCP: List Servers` -> **Start**.*