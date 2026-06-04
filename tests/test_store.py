import json

import pytest

from api_store import ApiStore


@pytest.fixture
def store() -> ApiStore:
    instance = ApiStore()
    instance.reload()
    return instance


def test_catalog_loads_endpoints(store: ApiStore) -> None:
    assert len(store.endpoints) >= 100


def test_list_groups(store: ApiStore) -> None:
    groups = store.list_groups()
    names = {item["group"] for item in groups}
    assert "ACC" in names
    assert all(item["endpoint_count"] > 0 for item in groups)


def test_search_projects(store: ApiStore) -> None:
    result = store.search("projects", group="ACC", limit=10)
    assert result["count"] >= 1
    assert any("project" in item["name"].lower() for item in result["results"])


def test_get_by_name_exact(store: ApiStore) -> None:
    result = store.get_by_name("Get Projects")
    assert result["match_type"] == "exact"
    assert result["endpoint"]["group"] == "ACC"


def test_get_by_name_fuzzy(store: ApiStore) -> None:
    result = store.get_by_name("Get Projcts")
    assert result["match_type"] in {"fuzzy", "exact", "ambiguous"}


def test_get_by_url_fragment(store: ApiStore) -> None:
    result = store.get_by_url_fragment("/construction/admin/v1/accounts")
    assert result["count"] >= 1


def test_list_endpoints_pagination(store: ApiStore) -> None:
    page = store.list_endpoints(group="ACC", limit=5, offset=0)
    assert page["total"] >= 5
    assert len(page["results"]) == 5


def test_catalog_info(store: ApiStore) -> None:
    info = store.get_catalog_info()
    assert info.total_endpoints == len(store.endpoints)
    assert "refreshed" in info.stale_warning.lower()


def test_group_resource_slug(store: ApiStore) -> None:
    catalog = store.get_group_catalog("acc")
    assert "endpoints" in catalog
    assert catalog["endpoint_count"] >= 1
