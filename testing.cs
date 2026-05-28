/* 
Testing the mcp

Prompt for copilot:
Look at my Autodesk MCP tools to find out how to fetch a list of projects from ACC. Write a c# function for it.

Response:
I'll help you find the ACC project fetching endpoint and write a C# function for it. Let me examine your MCP tools and data files.  

Read [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/server.py#1-1), lines 1 to 50

Read [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/data/acc.json#1-1), lines 1 to 100

Read [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/testing.cs)

Now I'll write a C# function to fetch projects from ACC using the endpoint information I found: 

Created [](file:///c%3A/Users/[   ]/Documents/Local/autodesk-aps-mcp/testing.cs)

Done! I've written a comprehensive C# solution in testing.cs that fetches projects from ACC. Here's what it includes:

**Key Components:**
1. **`GetProjectsAsync()`** - Main function that fetches a paginated list of projects
   - Takes `accountId`, `accessToken`, optional `limit` and `offset`
   - Calls: `GET https://developer.api.autodesk.com/construction/admin/v1/accounts/{accountId}/projects`
   - Includes Authorization header with Bearer token

2. **`GetAllProjectsAsync()`** - Helper function for automatic pagination that fetches all projects

3. **Data Models:**
   - `Project` - Individual project with id, name, status, dates, platform, and type
   - `ProjectListResponse` - API response with pagination and results
   - `Pagination` - Pagination metadata

4. **Example Usage** - Shows how to call the function with error handling

The implementation uses:
- `HttpClient` for API calls
- Newtonsoft.Json for JSON deserialization
- Async/await for non-blocking operations
- Proper error handling with meaningful exceptions

Made changes. */

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

/// <summary>
/// C# function to fetch a list of projects from Autodesk Construction Cloud (ACC)
/// </summary>
public class ACCProjectClient
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "https://developer.api.autodesk.com/construction/admin/v1";

    public ACCProjectClient(HttpClient httpClient = null)
    {
        _httpClient = httpClient ?? new HttpClient();
    }

    /// <summary>
    /// Fetches a list of projects from an ACC account
    /// </summary>
    /// <param name="accountId">The unique account ID for the ACC account (UUID format)</param>
    /// <param name="accessToken">The OAuth access token for authentication</param>
    /// <param name="limit">Maximum number of records to return (default: 20)</param>
    /// <param name="offset">Pagination offset (default: 0)</param>
    /// <returns>ProjectListResponse containing projects and pagination info</returns>
    public async Task<ProjectListResponse> GetProjectsAsync(string accountId, string accessToken, int limit = 20, int offset = 0)
    {
        try
        {
            var url = $"{BaseUrl}/accounts/{accountId}/projects?limit={limit}&offset={offset}";

            // Create the request with authorization header
            var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Add("Authorization", $"Bearer {accessToken}");

            // Make the API call
            var response = await _httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            // Parse the response
            var content = await response.Content.ReadAsStringAsync();
            var projectListResponse = JsonConvert.DeserializeObject<ProjectListResponse>(content);

            return projectListResponse;
        }
        catch (HttpRequestException ex)
        {
            throw new Exception($"Error fetching projects from ACC: {ex.Message}", ex);
        }
        catch (JsonException ex)
        {
            throw new Exception($"Error deserializing ACC projects response: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Fetches all projects from an ACC account with automatic pagination
    /// </summary>
    public async Task<List<Project>> GetAllProjectsAsync(string accountId, string accessToken, int pageSize = 100)
    {
        var allProjects = new List<Project>();
        int offset = 0;

        while (true)
        {
            var response = await GetProjectsAsync(accountId, accessToken, pageSize, offset);
            allProjects.AddRange(response.Results);

            if (allProjects.Count >= response.Pagination.Total)
                break;

            offset += pageSize;
        }

        return allProjects;
    }
}

/// <summary>
/// Response model for ACC projects list endpoint
/// </summary>
public class ProjectListResponse
{
    [JsonProperty("pagination")]
    public Pagination Pagination { get; set; }

    [JsonProperty("results")]
    public List<Project> Results { get; set; }
}

public class Pagination
{
    [JsonProperty("total")]
    public int Total { get; set; }

    [JsonProperty("limit")]
    public int Limit { get; set; }

    [JsonProperty("offset")]
    public int Offset { get; set; }
}

public class Project
{
    [JsonProperty("id")]
    public string Id { get; set; }

    [JsonProperty("name")]
    public string Name { get; set; }

    [JsonProperty("status")]
    public string Status { get; set; }

    [JsonProperty("startDate")]
    public string StartDate { get; set; }

    [JsonProperty("endDate")]
    public string EndDate { get; set; }

    [JsonProperty("platform")]
    public string Platform { get; set; }

    [JsonProperty("type")]
    public string Type { get; set; }
}

/// <summary>
/// Example usage
/// </summary>
public class Program
{
    public static async Task Main(string[] args)
    {
        var client = new ACCProjectClient();
        
        // Replace with actual values
        string accountId = "your-account-id-uuid";
        string accessToken = "your-oauth-access-token";

        try
        {
            var projects = await client.GetProjectsAsync(accountId, accessToken);
            
            Console.WriteLine($"Total projects: {projects.Pagination.Total}");
            foreach (var project in projects.Results)
            {
                Console.WriteLine($"- {project.Name} ({project.Status})");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}
