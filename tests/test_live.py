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


def test_live_rejects_unsafe_urls() -> None:
    with pytest.raises(LiveApiError, match="not allowed"):
        aps_live_get("https://example.com/v1/test")

    with pytest.raises(LiveApiError, match="https"):
        aps_live_get("http://developer.api.autodesk.com/v1/test")


def test_live_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth_without_env(monkeypatch)
    monkeypatch.setattr("aps_live.get_auth", lambda: auth)

    with pytest.raises(LiveApiError, match="credentials"):
        aps_live_get("https://developer.api.autodesk.com/authentication/v2/keys")


def test_auth_two_legged_has_no_user_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aps_auth, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("APS_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("APS_CLIENT_ID", "test-id")
    monkeypatch.setenv("APS_CLIENT_SECRET", "test-secret")
    aps_auth._auth = None

    auth = ApsAuth()

    assert auth.token_mode == "two_legged"
    assert auth.user_context_available is False
    message = auth._user_context_message()
    assert message is not None
    assert "three-legged" in message


def test_auth_three_legged_has_user_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aps_auth, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("APS_ACCESS_TOKEN", "user-token")
    monkeypatch.delenv("APS_CLIENT_ID", raising=False)
    monkeypatch.delenv("APS_CLIENT_SECRET", raising=False)
    aps_auth._auth = None

    auth = ApsAuth()

    assert auth.token_mode == "three_legged"
    assert auth.user_context_available is True
    assert auth._user_context_message() is None
