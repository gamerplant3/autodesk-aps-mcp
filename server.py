import json
import os
from pathlib import Path
from typing import List, Dict, Any
from fastmcp import FastMCP

# start FastMCP
mcp = FastMCP("Autodesk APS Reference")

# JSON data folder
DATA_DIR = Path(__file__).parent / "data"

def load_all_apis() -> List[Dict[str, Any]]:
    """If you want to load all API definitions"""
    all_apis = []
    if not DATA_DIR.exists():
        return []
    
    for file in DATA_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_apis.extend(data)
                elif isinstance(data, dict):
                    all_apis.append(data)
        except Exception as e:
            print(f"Error reading {file.name}: {e}")
            
    return all_apis

@mcp.tool()
def search_autodesk_endpoints(keyword: str) -> str:
    """
    Search for Autodesk APS endpoints using keywords. 
    Matches against the group, endpoint name, description, and URL.
    """
    apis = load_all_apis()
    results = []
    keyword_lower = keyword.lower()
    
    for api in apis:
        # Pull searchable text
        name = api.get("name", "")
        group = api.get("group", "")
        url = api.get("url", "")
        desc = api.get("description", "")
        
        if (keyword_lower in name.lower() or 
            keyword_lower in group.lower() or 
            keyword_lower in url.lower() or 
            keyword_lower in desc.lower()):
            
            # Return a summary of matching endpoints
            results.append(
                f"Group: {group}\n"
                f"Name: {name}\n"
                f"HTTP Method: {api.get('method')}\n"
                f"URL: {url}\n"
                f"Summary: {desc[:120]}...\n"
                f"---"
            )
            
    if not results:
        return f"No Autodesk endpoints found matching the keyword: '{keyword}'"
        
    return f"Found {len(results)} matching endpoints:\n\n" + "\n".join(results)

@mcp.tool()
def get_endpoint_details(endpoint_name: str) -> str:
    """
    Retrieves the full headers, query parameters, URI parameters, and response structures.
    """
    apis = load_all_apis()
    
    for api in apis:
        if api.get("name", "").lower() == endpoint_name.lower():
            # Return the full clean JSON structure back to the LLM
            return json.dumps(api, indent=2)
            
    return f"Could not find exact endpoint named '{endpoint_name}'."

if __name__ == "__main__":
    mcp.run()