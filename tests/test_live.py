import pytest

import aps_auth
from aps_auth import ApsAuth
from aps_live import LiveApiError, aps_live_get


def _auth_without_env(monkeypatch: pytest.MonkeyPatch) -> ApsAuth:
    monkeypatch.setattr(aps_auth, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("APS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("APS_CLIENT_ID", raising=False)
    monkeypatch.delenv("APS_CLIENT_SECRET", raising=False)
    aps_auth._auth = None
    return ApsAuth()


def test_live_rejects_non_allowlisted_host() -> None:
    with pytest.raises(LiveApiError, match="not allowed"):
        aps_live_get("https://example.com/v1/test")


def test_live_rejects_http() -> None:
    with pytest.raises(LiveApiError, match="https"):
        aps_live_get("http://developer.api.autodesk.com/v1/test")


def test_live_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth_without_env(monkeypatch)
    monkeypatch.setattr("aps_live.get_auth", lambda: auth)

    with pytest.raises(LiveApiError, match="credentials"):
        aps_live_get("https://developer.api.autodesk.com/authentication/v2/keys")


def test_auth_status_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth_without_env(monkeypatch)
    status = auth.status()
    assert status["live_reads_available"] is False
    assert "APS" in status["message"]
