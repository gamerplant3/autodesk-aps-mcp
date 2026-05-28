/* 

Testing the mcp

Prompt for copilot:
Look at my Autodesk MCP tools to find out how to print sheets from an ACC project. Write a javascript function for it.

REsponse:
Searched for text `sheet|print` in (`/data/*.json`), 20 results

Read [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/data/acc.json#4361-4361), lines 4361 to 4500

Read [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/testing.js)

Created [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/testing.js)

Done! I've written comprehensive JavaScript functions in testing.js to export/print sheets from ACC projects. Here's what's included:

**Key Functions:**

1. **`initiateSheetExport()`** - Starts the export job with file version URNs
   - POST to `https://developer.api.autodesk.com/construction/files/v1/projects/{projectId}/exports`
   - Returns export job ID and initial status

2. **`getExportJobStatus()`** - Checks the status of an export job
   - GET request to retrieve job status
   - Returns result with signed URL when complete

3. **`printSheetsAndGetDownloadUrl()`** - Main workflow function
   - Initiates export, polls for completion
   - Handles successful, partial, and failed states
   - Returns the signed URL for downloading the ZIP file
   - Configurable timeout and poll interval

4. **`downloadExportedSheets()`** - Downloads the exported ZIP
   - Works in both Node.js and browser environments
   - Auto-downloads in browsers, saves to disk in Node.js

5. **`exportAndDownloadSheets()`** - Complete end-to-end workflow

**Key Details:**
- Supports up to 200 files per export
- Returns S3 signed URL (valid for 1 hour)
- All PDFs packaged in a single ZIP file
- Handles partial successes with detailed error reporting
- Includes error handling and logging throughout

Made changes. */


/**
 * JavaScript functions to export/print sheets from an ACC project
 */

/**
 * Initiates an export job to convert sheets to PDFs
 * @param {string} projectId - The ACC project ID
 * @param {string} accessToken - OAuth access token
 * @param {string[]} fileVersionUrns - Array of file version URNs to export (max 200)
 * @param {object} options - Optional export criteria (markups, links, etc.)
 * @returns {Promise<object>} Export job info with id and status
 */
async function initiateSheetExport(projectId, accessToken, fileVersionUrns, options = {}) {
  const baseUrl = "https://developer.api.autodesk.com/construction/files/v1";
  const url = `${baseUrl}/projects/${projectId}/exports`;

  if (!Array.isArray(fileVersionUrns) || fileVersionUrns.length === 0) {
    throw new Error("fileVersionUrns must be a non-empty array");
  }

  if (fileVersionUrns.length > 200) {
    throw new Error("Maximum 200 files can be exported at once");
  }

  const requestBody = {
    fileVersions: fileVersionUrns,
    options: options
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${accessToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Export initiation failed with status ${response.status}: ${errorData}`);
    }

    const exportJob = await response.json();
    return exportJob; // { id: "uuid", status: "processing" }
  } catch (error) {
    throw new Error(`Failed to initiate sheet export: ${error.message}`);
  }
}

/**
 * Retrieves the status of an export job
 * @param {string} projectId - The ACC project ID
 * @param {string} exportId - The export job ID
 * @param {string} accessToken - OAuth access token
 * @returns {Promise<object>} Export job status with result, error details, or failedFiles
 */
async function getExportJobStatus(projectId, exportId, accessToken) {
  const baseUrl = "https://developer.api.autodesk.com/construction/files/v1";
  const url = `${baseUrl}/projects/${projectId}/exports/${exportId}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Status check failed with status ${response.status}: ${errorData}`);
    }

    const jobStatus = await response.json();
    return jobStatus;
  } catch (error) {
    throw new Error(`Failed to get export job status: ${error.message}`);
  }
}

/**
 * Exports sheets and waits for completion, then returns the download URL
 * @param {string} projectId - The ACC project ID
 * @param {string} accessToken - OAuth access token
 * @param {string[]} fileVersionUrns - Array of file version URNs to export
 * @param {object} options - Optional export criteria
 * @param {number} maxWaitMs - Maximum time to wait for completion (default: 5 minutes)
 * @param {number} pollIntervalMs - Time between status checks (default: 2 seconds)
 * @returns {Promise<string>} Signed URL for downloading the exported ZIP file
 */
async function printSheetsAndGetDownloadUrl(
  projectId,
  accessToken,
  fileVersionUrns,
  options = {},
  maxWaitMs = 300000,
  pollIntervalMs = 2000
) {
  try {
    // Step 1: Initiate the export job
    console.log("Initiating sheet export...");
    const exportJob = await initiateSheetExport(projectId, accessToken, fileVersionUrns, options);
    const exportId = exportJob.id;
    console.log(`Export job created with ID: ${exportId}`);

    // Step 2: Poll for completion
    const startTime = Date.now();
    let jobStatus = exportJob;

    while (jobStatus.status === "processing") {
      if (Date.now() - startTime > maxWaitMs) {
        throw new Error(`Export job did not complete within ${maxWaitMs}ms`);
      }

      console.log(`Waiting for export job ${exportId} to complete...`);
      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
      jobStatus = await getExportJobStatus(projectId, exportId, accessToken);
    }

    // Step 3: Handle completion
    if (jobStatus.status === "successful") {
      const signedUrl = jobStatus.result?.output?.signedUrl;
      if (!signedUrl) {
        throw new Error("Export successful but no download URL provided");
      }
      console.log("Export completed successfully!");
      return signedUrl;
    } else if (jobStatus.status === "partialSuccess") {
      const signedUrl = jobStatus.result?.output?.signedUrl;
      const failedFiles = jobStatus.result?.failedFiles || [];
      console.warn(`Export partial success. ${failedFiles.length} files failed:`);
      failedFiles.forEach(file => {
        console.warn(`  - ${file.urn}: ${file.reason}`);
      });
      if (signedUrl) {
        return signedUrl;
      } else {
        throw new Error("Partial export success but no download URL provided");
      }
    } else if (jobStatus.status === "failed") {
      const errorMessage = jobStatus.result?.error?.message || "Unknown error";
      throw new Error(`Export job failed: ${errorMessage}`);
    } else {
      throw new Error(`Unexpected export status: ${jobStatus.status}`);
    }
  } catch (error) {
    throw new Error(`Failed to print and export sheets: ${error.message}`);
  }
}

/**
 * Downloads the exported sheets ZIP file from the signed URL
 * @param {string} signedUrl - The signed URL returned from export job
 * @param {string} outputPath - Path where to save the downloaded file (Node.js only)
 * @returns {Promise<Buffer|Blob>} The file data
 */
async function downloadExportedSheets(signedUrl, outputPath = null) {
  try {
    const response = await fetch(signedUrl);

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`);
    }

    // For Node.js environments
    if (typeof process !== "undefined" && outputPath) {
      const fs = require("fs").promises;
      const buffer = await response.arrayBuffer();
      await fs.writeFile(outputPath, Buffer.from(buffer));
      console.log(`Downloaded sheets saved to ${outputPath}`);
      return buffer;
    }

    // For browser environments
    if (typeof window !== "undefined") {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sheets-export.zip";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      console.log("Download started in browser");
      return blob;
    }

    // Fallback
    return await response.arrayBuffer();
  } catch (error) {
    throw new Error(`Failed to download exported sheets: ${error.message}`);
  }
}

/**
 * Complete workflow: Export sheets and download the result
 * @param {string} projectId - The ACC project ID
 * @param {string} accessToken - OAuth access token
 * @param {string[]} fileVersionUrns - Array of file version URNs to export
 * @param {string} outputPath - Optional file path to save (Node.js)
 * @returns {Promise<object>} Object with status and downloadUrl
 */
async function exportAndDownloadSheets(projectId, accessToken, fileVersionUrns, outputPath = null) {
  try {
    // Get the download URL
    const downloadUrl = await printSheetsAndGetDownloadUrl(projectId, accessToken, fileVersionUrns);

    // Download the file
    if (outputPath) {
      await downloadExportedSheets(downloadUrl, outputPath);
    } else {
      await downloadExportedSheets(downloadUrl);
    }

    return {
      status: "success",
      downloadUrl: downloadUrl
    };
  } catch (error) {
    console.error(`Export and download failed: ${error.message}`);
    return {
      status: "failed",
      error: error.message
    };
  }
}

// ============ EXAMPLE USAGE ============

async function exampleUsage() {
  const projectId = "your-project-id";
  const accessToken = "your-oauth-access-token";
  const fileVersionUrns = [
    "urn:adsk.objects:os.object:bucket/object-id-1",
    "urn:adsk.objects:os.object:bucket/object-id-2"
  ];

  try {
    // Option 1: Simple export and get download URL
    const downloadUrl = await printSheetsAndGetDownloadUrl(
      projectId,
      accessToken,
      fileVersionUrns
    );
    console.log(`Download your sheets from: ${downloadUrl}`);
    console.log("Note: URL is valid for 1 hour");

    // Option 2: Complete workflow with download
    // const result = await exportAndDownloadSheets(
    //   projectId,
    //   accessToken,
    //   fileVersionUrns,
    //   "exported-sheets.zip" // For Node.js
    // );
    // console.log(result);

  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

// Export functions for module usage
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    initiateSheetExport,
    getExportJobStatus,
    printSheetsAndGetDownloadUrl,
    downloadExportedSheets,
    exportAndDownloadSheets
  };
}
