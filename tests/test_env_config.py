from gtool.config.settings import Config


def test_env_override_scalar(monkeypatch):
    monkeypatch.setenv("GTOOL_TIME_ZONE", "Europe/London")
    config = Config()
    assert config.get("TIME_ZONE") == "Europe/London"


def test_env_override_list(monkeypatch):
    monkeypatch.setenv("GTOOL_CALENDAR_IDS", "primary,work")
    config = Config()
    assert config.get("CALENDAR_IDS") == ["primary", "work"]
    monkeypatch.setenv("GTOOL_SCOPES", "scope1,scope2")
    config = Config()
    assert config.get("SCOPES") == ["scope1", "scope2"]


def test_env_override_priority(monkeypatch):
    monkeypatch.setenv("GTOOL_TIME_ZONE", "Asia/Tokyo")
    config = Config()
    # Should use env var, not config file value
    assert config.get("TIME_ZONE") == "Asia/Tokyo"
