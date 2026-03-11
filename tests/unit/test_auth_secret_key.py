import importlib

import app.config as app_config
import app.core.security as app_security


def test_config_secret_key_uses_default_when_env_empty(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    reloaded_config = importlib.reload(app_config)
    assert reloaded_config.settings.SECRET_KEY == "switch-manage-dev-secret-key-2024-very-long-and-secure"


def test_security_uses_stable_secret_key_when_env_empty(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    reloaded_config = importlib.reload(app_config)
    reloaded_security = importlib.reload(app_security)
    token = reloaded_security.create_access_token({"sub": "1"})
    payload = reloaded_security.decode_access_token(token)
    assert reloaded_security.SECRET_KEY == reloaded_config.settings.SECRET_KEY
    assert payload is not None
    assert payload.get("sub") == "1"


def test_create_access_token_normalizes_numeric_subject():
    reloaded_security = importlib.reload(app_security)
    token = reloaded_security.create_access_token({"sub": 1})
    payload = reloaded_security.decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "1"
