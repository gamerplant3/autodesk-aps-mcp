# Autodesk APS MCP Server

An MCP server running over stdio that gives access to Autodesk API schemas.

Look at ```testing.cs``` and ```testing.js``` for a sample run (used github copilot chat). You can also use it for inline code generation by using the inline prompt bar (Ctrl + I) and telling it what to do, without going to the chat interface.

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

<img width="1102" height="463" alt="Screenshot 2026-05-28 111202" src="https://github.com/user-attachments/assets/d156fe84-fceb-4923-a01d-496d3f97edf0" />

*To activate: `Ctrl + Shift + P` -> `MCP: List Servers` -> **Start**.*
