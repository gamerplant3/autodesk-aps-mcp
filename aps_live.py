"""Read-only live HTTP calls to allowed Autodesk APS hosts."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

import httpx

from aps_auth import get_auth
from config import ALLOWED_API_HOSTS


class LiveApiError(Exception):
    pass


def _validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise LiveApiError("Only https URLs are allowed.")
    if parsed.hostname not in ALLOWED_API_HOSTS:
        raise LiveApiError(
            f"Host '{parsed.hostname}' is not allowed. "
            f"Allowed hosts: {', '.join(sorted(ALLOWED_API_HOSTS))}"
        )
    if not parsed.path:
        raise LiveApiError("URL must include a path.")
    return url.strip()


def aps_live_get(
    url: str,
    *,
    query_parameters: dict[str, Any] | None = None,
    scopes: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Perform a GET request against an allowlisted APS host using configured credentials.
    """
    if query_parameters:
        non_strings = [key for key, value in query_parameters.items() if not isinstance(value, str)]
        if non_strings:
            raise LiveApiError(
                "query_parameters values must be strings. "
                f"Non-string keys: {', '.join(non_strings)}"
            )

    validated_url = _validate_url(url)
    auth = get_auth()
    if not auth.is_configured():
        raise LiveApiError(
            "Live reads require APS credentials in .env. "
            "Copy .env.example to .env and set APS_CLIENT_ID/APS_CLIENT_SECRET "
            "or APS_ACCESS_TOKEN."
        )

    token = auth.get_access_token(scopes=scopes)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    try:
        response = httpx.get(
            validated_url,
            params=query_parameters or None,
            headers=headers,
            timeout=60.0,
        )
    except httpx.HTTPError as exc:
        raise LiveApiError(f"HTTP request failed: {exc}") from exc

    body: Any
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = response.text
    else:
        body = response.text

    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
        "stale_catalog_note": (
            "Compare this live response with offline get_endpoint_details when "
            "specs may be outdated."
        ),
    }
