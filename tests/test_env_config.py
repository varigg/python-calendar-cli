import pytest
from src.caltool.config import Config


def test_env_override_scalar(monkeypatch):
    monkeypatch.setenv("CALTOOL_TIME_ZONE", "Europe/London")
    config = Config()
    assert config.get("TIME_ZONE") == "Europe/London"


def test_env_override_list(monkeypatch):
    monkeypatch.setenv("CALTOOL_CALENDAR_IDS", "primary,work")
    config = Config()
    assert config.get("CALENDAR_IDS") == ["primary", "work"]
    monkeypatch.setenv("CALTOOL_SCOPES", "scope1,scope2")
    config = Config()
    assert config.get("SCOPES") == ["scope1", "scope2"]


def test_env_override_priority(monkeypatch):
    monkeypatch.setenv("CALTOOL_TIME_ZONE", "Asia/Tokyo")
    config = Config()
    # Should use env var, not config file value
    assert config.get("TIME_ZONE") == "Asia/Tokyo"


def test_config_validation_missing(monkeypatch):
    # Remove required key
    monkeypatch.delenv("CALTOOL_TIME_ZONE", raising=False)
    config = Config()
    config.data.pop("TIME_ZONE", None)
    with pytest.raises(Exception) as exc:
        config.validate()
    assert "Missing required config keys" in str(exc.value)


def test_config_validation_types(monkeypatch):
    config = Config()
    config.data["SCOPES"] = "notalist"
    with pytest.raises(Exception) as exc:
        config.validate()
    assert "SCOPES must be a list" in str(exc.value)
    config.data["SCOPES"] = ["scope"]
    config.data["CALENDAR_IDS"] = "notalist"
    with pytest.raises(Exception) as exc:
        config.validate()
    assert "CALENDAR_IDS must be a list" in str(exc.value)
