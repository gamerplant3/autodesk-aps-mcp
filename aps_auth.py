"""APS OAuth helpers: load .env credentials and manage two-legged tokens."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

from config import APS_TOKEN_URL, DEFAULT_LIVE_SCOPES, ENV_FILE


@dataclass
class TokenState:
    access_token: str
    expires_at: float
    token_type: str
    scope: str | None


class ApsAuth:
    """Resolves APS credentials from environment and caches two-legged tokens."""

    def __init__(self) -> None:
        load_dotenv(ENV_FILE, override=False)
        self._client_id = os.getenv("APS_CLIENT_ID", "").strip()
        self._client_secret = os.getenv("APS_CLIENT_SECRET", "").strip()
        self._static_token = os.getenv("APS_ACCESS_TOKEN", "").strip()
        self._cached: TokenState | None = None

    @property
    def client_id_configured(self) -> bool:
        return bool(self._client_id)

    @property
    def client_secret_configured(self) -> bool:
        return bool(self._client_secret)

    @property
    def static_token_configured(self) -> bool:
        return bool(self._static_token)

    @property
    def user_context_available(self) -> bool:
        """True when APS_ACCESS_TOKEN is set (expected to be a three-legged user token)."""
        return self.static_token_configured

    @property
    def token_mode(self) -> str | None:
        if self.static_token_configured:
            return "three_legged"
        if self.client_id_configured and self.client_secret_configured:
            return "two_legged"
        return None

    def status(self) -> dict[str, Any]:
        token = self._resolve_token(scopes=None, required=False)
        return {
            "env_file": str(ENV_FILE),
            "client_id_configured": self.client_id_configured,
            "client_secret_configured": self.client_secret_configured,
            "static_access_token_configured": self.static_token_configured,
            "user_context_available": self.user_context_available,
            "token_mode": self.token_mode,
            "live_reads_available": self.is_configured(),
            "token_source": token.source if token else None,
            "token_expires_at": token.expires_at if token else None,
            "token_scope": token.scope if token else None,
            "message": self._status_message(),
            "user_context_message": self._user_context_message(),
        }

    def is_configured(self) -> bool:
        return self.static_token_configured or (
            self.client_id_configured and self.client_secret_configured
        )

    def get_access_token(self, scopes: str | None = None) -> str:
        token = self._resolve_token(scopes=scopes, required=True)
        return token.access_token

    def _status_message(self) -> str:
        if self.static_token_configured:
            return "Using APS_ACCESS_TOKEN from .env for live reads (user context)."
        if self.client_id_configured and self.client_secret_configured:
            return (
                "Will obtain two-legged tokens using APS_CLIENT_ID and APS_CLIENT_SECRET "
                "(app context only)."
            )
        if self.client_id_configured or self.client_secret_configured:
            return "Set both APS_CLIENT_ID and APS_CLIENT_SECRET, or provide APS_ACCESS_TOKEN."
        return "Copy .env.example to .env and add APS credentials to enable live reads."

    def _user_context_message(self) -> str | None:
        if self.user_context_available:
            return None
        if self.client_id_configured and self.client_secret_configured:
            return (
                "User context is not configured. APS_CLIENT_ID and APS_CLIENT_SECRET provide "
                "app-level (two-legged) access only; they cannot answer what a specific user "
                "can access. Set APS_ACCESS_TOKEN with a three-legged OAuth token for "
                "user-specific questions."
            )
        return (
            "User context is not configured. Set APS_ACCESS_TOKEN with a three-legged OAuth "
            "token to answer user-specific questions (e.g. my hubs, my projects)."
        )

    def _resolve_token(self, *, scopes: str | None, required: bool) -> "_ResolvedToken | None":
        if self._static_token:
            return _ResolvedToken(
                access_token=self._static_token,
                source="static_env",
                expires_at=None,
                scope=None,
            )

        if not (self._client_id and self._client_secret):
            if required:
                raise RuntimeError(
                    "APS credentials missing. Set APS_ACCESS_TOKEN or both "
                    "APS_CLIENT_ID and APS_CLIENT_SECRET in .env (see .env.example)."
                )
            return None

        scope_value = scopes or DEFAULT_LIVE_SCOPES
        if self._cached and self._cached.expires_at > time.time() + 30:
            if not scope_value or (self._cached.scope or "") == scope_value:
                return _ResolvedToken(
                    access_token=self._cached.access_token,
                    source="two_legged_cached",
                    expires_at=self._cached.expires_at,
                    scope=self._cached.scope,
                )

        token = self._fetch_two_legged_token(scope_value)
        self._cached = token
        return _ResolvedToken(
            access_token=token.access_token,
            source="two_legged",
            expires_at=token.expires_at,
            scope=token.scope,
        )

    def _fetch_two_legged_token(self, scopes: str) -> TokenState:
        data = {
            "grant_type": "client_credentials",
            "scope": scopes,
        }
        try:
            response = httpx.post(
                APS_TOKEN_URL,
                data=data,
                auth=(self._client_id, self._client_secret),
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to obtain APS access token: {exc}") from exc

        expires_in = int(payload.get("expires_in", 3600))
        return TokenState(
            access_token=payload["access_token"],
            expires_at=time.time() + expires_in,
            token_type=payload.get("token_type", "Bearer"),
            scope=payload.get("scope", scopes),
        )


@dataclass
class _ResolvedToken:
    access_token: str
    source: str
    expires_at: float | None
    scope: str | None


_auth: ApsAuth | None = None


def get_auth() -> ApsAuth:
    global _auth
    if _auth is None:
        _auth = ApsAuth()
    return _auth
