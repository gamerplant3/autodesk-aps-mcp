/**
 * Export ACC Sheets tool sheets to a single PDF (ACC Sheets API).
 *
 * Endpoints (from autodesk-aps MCP catalog):
 * - GET  /construction/sheets/v1/projects/{projectId}/sheets
 * - POST /construction/sheets/v1/projects/{projectId}/exports
 * - GET  /construction/sheets/v1/projects/{projectId}/exports/{exportId}
 *
 * Scopes: data:read (list), data:write (export start), data:read (poll)
 * Two-legged OAuth: pass xUserId (ACC/Autodesk user id).
 */

const SHEETS_BASE = "https://developer.api.autodesk.com/construction/sheets/v1";

/**
 * @param {object} opts
 * @param {string} opts.accessToken
 * @param {string} [opts.xUserId] - Required for 2-legged OAuth
 */
function buildHeaders({ accessToken, xUserId }) {
  const headers = {
    Authorization: `Bearer ${accessToken}`,
    Accept: "application/json",
  };
  if (xUserId) {
    headers["x-user-id"] = xUserId;
  }
  return headers;
}

async function parseError(response) {
  const text = await response.text();
  throw new Error(`HTTP ${response.status}: ${text}`);
}

/**
 * List sheets in a project (paginated).
 * @returns {Promise<Array<{ id: string, number?: string, title?: string }>>}
 */
async function listAllSheets(projectId, accessToken, options = {}) {
  const { xUserId, limit = 100, query = {} } = options;
  const all = [];
  let offset = 0;

  while (true) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      ...Object.fromEntries(
        Object.entries(query).map(([k, v]) => [k, String(v)])
      ),
    });

    const url = `${SHEETS_BASE}/projects/${projectId}/sheets?${params}`;
    const response = await fetch(url, {
      method: "GET",
      headers: buildHeaders({ accessToken, xUserId }),
    });

    if (!response.ok) {
      await parseError(response);
    }

    const body = await response.json();
    const page = body.results ?? [];
    all.push(...page);

    const total = body.pagination?.totalResults ?? all.length;
    offset += page.length;
    if (offset >= total || page.length === 0) {
      break;
    }
  }

  return all;
}

/**
 * Start async PDF export for up to 1000 sheet UUIDs.
 * @returns {Promise<{ id: string, status: string }>}
 */
async function startSheetsPdfExport(
  projectId,
  accessToken,
  { sheetIds, outputFileName = "acc-sheets-export", options = {}, xUserId }
) {
  if (!Array.isArray(sheetIds) || sheetIds.length === 0) {
    throw new Error("sheetIds must be a non-empty array");
  }
  if (sheetIds.length > 1000) {
    throw new Error("Maximum 1000 sheets per export");
  }

  const url = `${SHEETS_BASE}/projects/${projectId}/exports`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...buildHeaders({ accessToken, xUserId }),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      outputFileName,
      sheets: sheetIds,
      options,
    }),
  });

  if (!response.ok) {
    await parseError(response);
  }

  return response.json();
}

/**
 * Poll export job status (Sheets API).
 */
async function getSheetsExportStatus(
  projectId,
  exportId,
  accessToken,
  { xUserId } = {}
) {
  const url = `${SHEETS_BASE}/projects/${projectId}/exports/${exportId}`;
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders({ accessToken, xUserId }),
  });

  if (!response.ok) {
    await parseError(response);
  }

  return response.json();
}

/**
 * Wait for export completion and return the signed download URL.
 * @returns {Promise<string>} signedUrl (valid ~1 hour)
 */
async function exportSheetsPdfAndGetDownloadUrl(
  projectId,
  accessToken,
  { sheetIds, outputFileName, options, xUserId },
  { maxWaitMs = 600000, pollIntervalMs = 3000 } = {}
) {
  const job = await startSheetsPdfExport(projectId, accessToken, {
    sheetIds,
    outputFileName,
    options,
    xUserId,
  });

  const exportId = job.id;
  const started = Date.now();
  let status = job;

  while (status.status === "processing") {
    if (Date.now() - started > maxWaitMs) {
      throw new Error(`Export ${exportId} did not finish within ${maxWaitMs}ms`);
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs));
    status = await getSheetsExportStatus(projectId, exportId, accessToken, {
      xUserId,
    });
  }

  if (status.status === "successful") {
    const signedUrl = status.result?.output?.signedUrl;
    if (!signedUrl) {
      throw new Error("Export successful but no signedUrl in response");
    }
    return signedUrl;
  }

  const details =
    status.result?.error?.details ??
    status.result?.error?.description ??
    "Unknown error";
  throw new Error(`Export failed (${status.status}): ${details}`);
}

/**
 * Download PDF bytes from signed URL.
 * @returns {Promise<ArrayBuffer>}
 */
async function downloadPdfFromSignedUrl(signedUrl) {
  const response = await fetch(signedUrl);
  if (!response.ok) {
    throw new Error(`Download failed: HTTP ${response.status}`);
  }
  return response.arrayBuffer();
}

/**
 * End-to-end: list sheets (optional), export, poll, download.
 */
async function exportAndDownloadAccSheetsPdf(
  projectId,
  accessToken,
  {
    sheetIds: providedSheetIds,
    listQuery,
    outputFileName = "acc-sheets-export",
    exportOptions = {},
    xUserId,
    outputPath = null,
  } = {}
) {
  let sheetIds = providedSheetIds;
  if (!sheetIds) {
    const sheets = await listAllSheets(projectId, accessToken, {
      xUserId,
      query: listQuery ?? {},
    });
    sheetIds = sheets.map((s) => s.id);
    if (sheetIds.length === 0) {
      throw new Error("No sheets found in project");
    }
  }

  const signedUrl = await exportSheetsPdfAndGetDownloadUrl(
    projectId,
    accessToken,
    {
      sheetIds,
      outputFileName,
      options: exportOptions,
      xUserId,
    }
  );

  const data = await downloadPdfFromSignedUrl(signedUrl);

  if (typeof process !== "undefined" && outputPath) {
    const fs = await import("node:fs/promises");
    await fs.writeFile(outputPath, Buffer.from(data));
    console.log(`Saved PDF to ${outputPath}`);
  }

  return { signedUrl, sheetCount: sheetIds.length, bytes: data.byteLength };
}

// --- Example (Node 18+ with fetch) ---
async function example() {
  const projectId = process.env.ACC_PROJECT_ID;
  const accessToken = process.env.APS_ACCESS_TOKEN;
  const xUserId = process.env.APS_USER_ID;

  if (!projectId || !accessToken) {
    console.error("Set ACC_PROJECT_ID and APS_ACCESS_TOKEN");
    process.exit(1);
  }

  const result = await exportAndDownloadAccSheetsPdf(projectId, accessToken, {
    xUserId,
    outputPath: "acc-sheets.pdf",
    listQuery: { currentOnly: "true" },
  });

  console.log(result);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    listAllSheets,
    startSheetsPdfExport,
    getSheetsExportStatus,
    exportSheetsPdfAndGetDownloadUrl,
    downloadPdfFromSignedUrl,
    exportAndDownloadAccSheetsPdf,
  };
}

if (typeof require !== "undefined" && require.main === module) {
  example().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
