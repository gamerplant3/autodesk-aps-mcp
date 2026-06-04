"""Cached, indexed catalog of offline APS endpoint definitions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from config import DATA_DIR, get_catalog_snapshot_date


def _slugify_group(group: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


@dataclass(frozen=True)
class CatalogInfo:
    snapshot_date: str
    total_endpoints: int
    groups: dict[str, int]
    source: str
    note: str
    stale_warning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_date": self.snapshot_date,
            "total_endpoints": self.total_endpoints,
            "groups": self.groups,
            "source": self.source,
            "note": self.note,
            "stale_warning": self.stale_warning,
        }


class ApiStore:
    """Loads JSON endpoint data once and serves indexed lookups."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or DATA_DIR
        self._endpoints: list[dict[str, Any]] = []
        self._by_name: dict[str, list[dict[str, Any]]] = {}
        self._by_slug: dict[str, list[dict[str, Any]]] = {}
        self._groups: dict[str, list[dict[str, Any]]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._load()
        self._loaded = True

    def _load(self) -> None:
        endpoints: list[dict[str, Any]] = []
        if not self._data_dir.exists():
            self._endpoints = []
            return

        for path in sorted(self._data_dir.glob("*.json")):
            try:
                with path.open(encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Error reading {path.name}: {exc}")
                continue

            if isinstance(data, list):
                endpoints.extend(data)
            elif isinstance(data, dict):
                endpoints.append(data)

        self._endpoints = endpoints
        self._by_name.clear()
        self._by_slug.clear()
        self._groups.clear()

        for endpoint in endpoints:
            name_key = _normalize_name(endpoint.get("name", ""))
            self._by_name.setdefault(name_key, []).append(endpoint)

            slug = _slugify_group(endpoint.get("group", "unknown"))
            self._by_slug.setdefault(slug, []).append(endpoint)

            group = endpoint.get("group", "Unknown")
            self._groups.setdefault(group, []).append(endpoint)

    def reload(self) -> None:
        self._loaded = False
        self._ensure_loaded()

    @property
    def endpoints(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return self._endpoints

    def list_groups(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return [
            {
                "group": group,
                "slug": _slugify_group(group),
                "endpoint_count": len(items),
            }
            for group, items in sorted(self._groups.items())
        ]

    def list_endpoints(
        self,
        *,
        group: str | None = None,
        method: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        self._ensure_loaded()
        items = self.endpoints

        if group:
            group_lower = group.lower()
            items = [
                ep
                for ep in items
                if ep.get("group", "").lower() == group_lower
                or _slugify_group(ep.get("group", "")) == group_lower
            ]

        if method:
            method_upper = method.upper()
            items = [ep for ep in items if ep.get("method", "").upper() == method_upper]

        total = len(items)
        page = items[offset : offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": [self._summary(ep) for ep in page],
        }

    def search(
        self,
        keyword: str,
        *,
        group: str | None = None,
        method: str | None = None,
        scope: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        self._ensure_loaded()
        keyword_lower = keyword.lower()
        matches: list[dict[str, Any]] = []

        for endpoint in self.endpoints:
            if group and not self._matches_group(endpoint, group):
                continue
            if method and endpoint.get("method", "").upper() != method.upper():
                continue
            if scope and not self._matches_scope(endpoint, scope):
                continue

            haystack = " ".join(
                [
                    endpoint.get("name", ""),
                    endpoint.get("group", ""),
                    endpoint.get("url", ""),
                    endpoint.get("description", ""),
                ]
            ).lower()

            if keyword_lower in haystack:
                matches.append(endpoint)
                if len(matches) >= limit:
                    break

        return {
            "keyword": keyword,
            "count": len(matches),
            "results": [self._summary(ep) for ep in matches],
        }

    def get_by_name(self, endpoint_name: str) -> dict[str, Any]:
        self._ensure_loaded()
        key = _normalize_name(endpoint_name)
        exact = self._by_name.get(key, [])
        if len(exact) == 1:
            return {"match_type": "exact", "endpoint": exact[0]}
        if len(exact) > 1:
            return {
                "match_type": "ambiguous",
                "message": f"Multiple endpoints named '{endpoint_name}'.",
                "candidates": [self._summary(ep) for ep in exact],
            }

        names = list(self._by_name.keys())
        close = get_close_matches(key, names, n=5, cutoff=0.6)
        if close:
            candidates = []
            for name in close:
                for ep in self._by_name[name]:
                    candidates.append(self._summary(ep))
            return {
                "match_type": "fuzzy",
                "message": f"No exact match for '{endpoint_name}'. Did you mean one of these?",
                "candidates": candidates,
            }

        return {
            "match_type": "none",
            "message": f"Could not find endpoint named '{endpoint_name}'.",
            "candidates": [],
        }

    def get_by_url_fragment(self, url_fragment: str) -> dict[str, Any]:
        self._ensure_loaded()
        fragment = url_fragment.lower()
        matches = [
            ep for ep in self.endpoints if fragment in ep.get("url", "").lower()
        ]
        return {
            "url_fragment": url_fragment,
            "count": len(matches),
            "results": [self._summary(ep) for ep in matches[:25]],
        }

    def get_group_catalog(self, group_slug: str) -> dict[str, Any]:
        self._ensure_loaded()
        slug = group_slug.lower()
        items = self._by_slug.get(slug, [])
        if not items:
            for group, endpoints in self._groups.items():
                if _slugify_group(group) == slug:
                    items = endpoints
                    break

        if not items:
            return {
                "error": f"Unknown group slug '{group_slug}'.",
                "available_slugs": [_slugify_group(g) for g in self._groups],
            }

        return {
            "group": items[0].get("group"),
            "slug": slug,
            "endpoint_count": len(items),
            "endpoints": [self._summary(ep) for ep in items],
        }

    def get_catalog_info(self) -> CatalogInfo:
        self._ensure_loaded()
        groups = {group: len(eps) for group, eps in sorted(self._groups.items())}
        return CatalogInfo(
            snapshot_date=get_catalog_snapshot_date(),
            total_endpoints=len(self.endpoints),
            groups=groups,
            source="curated-json",
            note=(
                "Offline catalog may lag behind live APS APIs. "
                "Use aps_live_get when credentials are configured."
            ),
            stale_warning=(
                "Cached endpoint specs are not refreshed automatically. "
                "Compare with aps_live_get or update data/*.json and the catalog snapshot date in README.md."
            ),
        )

    @staticmethod
    def _summary(endpoint: dict[str, Any]) -> dict[str, Any]:
        desc = endpoint.get("description", "")
        return {
            "group": endpoint.get("group"),
            "name": endpoint.get("name"),
            "method": endpoint.get("method"),
            "url": endpoint.get("url"),
            "auth_required": endpoint.get("auth_required"),
            "oauth_scopes": endpoint.get("oauth_scopes", []),
            "description_preview": desc[:200] + ("..." if len(desc) > 200 else ""),
        }

    @staticmethod
    def _matches_group(endpoint: dict[str, Any], group: str) -> bool:
        value = endpoint.get("group", "")
        return value.lower() == group.lower() or _slugify_group(value) == group.lower()

    @staticmethod
    def _matches_scope(endpoint: dict[str, Any], scope: str) -> bool:
        scope_lower = scope.lower()
        for item in endpoint.get("oauth_scopes", []):
            if scope_lower in str(item).lower():
                return True
        return False


_store: ApiStore | None = None


def get_store() -> ApiStore:
    global _store
    if _store is None:
        _store = ApiStore()
    return _store
