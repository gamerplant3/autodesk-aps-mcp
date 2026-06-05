import pytest

from api_store import ApiStore


@pytest.fixture
def store() -> ApiStore:
    instance = ApiStore()
    instance.reload()
    return instance


def test_catalog_loads_endpoints(store: ApiStore) -> None:
    assert len(store.endpoints) >= 100


def test_search_and_lookup(store: ApiStore) -> None:
    search = store.search("projects", group="ACC", limit=10)
    assert search["count"] >= 1

    result = store.get_by_name("Get Projects")
    assert result["match_type"] == "exact"
    assert result["endpoint"]["group"] == "ACC"
