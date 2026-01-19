import os
import tempfile

import pytest

from gtool.config import DEFAULTS, Config


class TestConfig:
    def test_load_defaults_when_missing(self):
        # Use a temp file that does not exist
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            cfg = Config(path)
            assert cfg.data == DEFAULTS

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            cfg = Config(path)
            cfg.data["TIME_ZONE"] = "Europe/London"
            cfg.save()
            # Load again
            cfg2 = Config(path)
            assert cfg2.data["TIME_ZONE"] == "Europe/London"

    def test_get_method(self):
        cfg = Config()
        assert cfg.get("TIME_ZONE") == DEFAULTS["TIME_ZONE"]
        assert cfg.get("NON_EXISTENT", "fallback") == "fallback"

    def test_validate_raises_config_validation_error_on_missing_keys(self, monkeypatch):
        """Test that Config.validate raises ConfigValidationError for missing keys."""
        from gtool.infrastructure.exceptions import ConfigValidationError

        cfg = Config()
        cfg.data = {}  # Clear all data
        with pytest.raises(ConfigValidationError) as exc_info:
            cfg.validate()
        assert "Missing required config keys" in str(exc_info.value)

    def test_validate_raises_error_if_scopes_not_list(self):
        """Test that Config.validate raises ConfigValidationError if SCOPES is not a list."""
        from gtool.infrastructure.exceptions import ConfigValidationError

        cfg = Config()
        cfg.data["SCOPES"] = "calendar"  # String instead of list
        with pytest.raises(ConfigValidationError) as exc_info:
            cfg.validate()
        assert "SCOPES must be a list" in str(exc_info.value)

    def test_validate_raises_error_if_calendar_ids_not_list(self):
        """Test that Config.validate raises ConfigValidationError if CALENDAR_IDS is not a list."""
        from gtool.infrastructure.exceptions import ConfigValidationError

        cfg = Config()
        cfg.data["CALENDAR_IDS"] = "primary"  # String instead of list
        with pytest.raises(ConfigValidationError) as exc_info:
            cfg.validate()
        assert "CALENDAR_IDS must be a list" in str(exc_info.value)
