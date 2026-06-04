# Examples

Sample code produced with MCP-assisted workflows:

- `export-acc-sheets-pdf.js` - ACC **Sheets API**: list sheets → export combined PDF → poll → download
- `testing.js` - ACC **Files API**: export sheet/file versions as PDF ZIP
- `testing.cs` - List ACC projects

These are reference demos, not part of the MCP server runtime.

### Run `export-acc-sheets-pdf.js` (Node 18+)

```bash
set APS_ACCESS_TOKEN=your_token
set ACC_PROJECT_ID=your_project_uuid
set APS_USER_ID=your_user_id   # if using 2-legged OAuth
node examples/export-acc-sheets-pdf.js
```
