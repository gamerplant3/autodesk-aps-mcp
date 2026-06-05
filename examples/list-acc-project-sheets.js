/**
 * Lists and prints all sheets in an ACC project.
 *
 * API: GET /construction/sheets/v1/projects/{projectId}/sheets (scope: data:read)
 *
 * Environment:
 *   ACC_PROJECT_ID       - ACC project UUID (with or without b. prefix)
 *   APS_ACCESS_TOKEN     - preferred; 3-legged bearer token
 *   APS_CLIENT_ID        - fallback with APS_CLIENT_SECRET for 2-legged token
 *   APS_CLIENT_SECRET
 *   APS_USER_ID          - optional; user impersonation header for 2-legged ACC access
 *
 * Usage:
 *   node examples/list-acc-project-sheets.js
 */

const BASE_URL = 'https://developer.api.autodesk.com';
const SHEETS_PATH = '/construction/sheets/v1/projects';
const PAGE_SIZE = 100;

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

// Resolves a bearer token from env or a 2-legged client_credentials exchange.
async function getAccessToken() {
  if (process.env.APS_ACCESS_TOKEN) {
    return process.env.APS_ACCESS_TOKEN;
  }

  const clientId = requireEnv('APS_CLIENT_ID');
  const clientSecret = requireEnv('APS_CLIENT_SECRET');
  const credentials = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const response = await fetch(`${BASE_URL}/authentication/v2/token`, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${credentials}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      scope: 'data:read',
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Token request failed (${response.status}): ${body}`);
  }

  const data = await response.json();
  return data.access_token;
}

// Fetches every page of sheets for the project.
async function fetchAllSheets(projectId, accessToken) {
  const sheets = [];
  let offset = 0;
  let totalResults = null;

  while (totalResults === null || offset < totalResults) {
    const params = new URLSearchParams({
      currentOnly: 'true',
      limit: String(PAGE_SIZE),
      offset: String(offset),
    });

    const url = `${BASE_URL}${SHEETS_PATH}/${projectId}/sheets?${params}`;
    const headers = {
      Authorization: `Bearer ${accessToken}`,
    };

    if (process.env.APS_USER_ID) {
      headers['x-user-id'] = process.env.APS_USER_ID;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`List sheets failed (${response.status}): ${body}`);
    }

    const page = await response.json();
    const results = page.results ?? [];

    sheets.push(...results);

    totalResults = page.pagination?.totalResults ?? results.length;
    offset += results.length;

    if (results.length === 0) {
      break;
    }
  }

  return sheets;
}

// Prints sheet number, title, and id for each result.
function printSheets(sheets, projectId) {
  console.log(`ACC project: ${projectId}`);
  console.log(`Total sheets: ${sheets.length}\n`);

  if (sheets.length === 0) {
    console.log('No sheets found.');
    return;
  }

  const numberWidth = Math.max(6, ...sheets.map((sheet) => (sheet.number ?? '').length));

  for (const sheet of sheets) {
    const number = (sheet.number ?? '').padEnd(numberWidth);
    const title = sheet.title ?? '';
    const id = sheet.id ?? '';
    const versionSetId = sheet.versionSet?.id ?? '';
    const tags = Array.isArray(sheet.tags) ? sheet.tags.join(', ') : '';

    console.log(`${number}  ${title}`);
    console.log(`         id: ${id}`);
    if (versionSetId) {
      console.log(`         version set: ${versionSetId}`);
    }
    if (tags) {
      console.log(`         tags: ${tags}`);
    }
    console.log('');
  }
}

async function main() {
  const projectId = requireEnv('ACC_PROJECT_ID');
  const accessToken = await getAccessToken();
  const sheets = await fetchAllSheets(projectId, accessToken);

  printSheets(sheets, projectId);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
