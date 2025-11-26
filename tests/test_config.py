import json
import os
import tempfile

from unittest.mock import patch

from caltool.config import DEFAULTS, Config


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

    def test_prompt_monkeypatch(self, monkeypatch):
        # Simulate user input for all prompts
        responses = iter([
            "test_credentials.json",
            "test_token.json",
            "Europe/Paris",
            "09:00",
            "17:00",
            "primary,work",
            "https://www.googleapis.com/auth/calendar"
        ])
        monkeypatch.setattr("click.prompt", lambda *a, **k: next(responses))
        monkeypatch.setattr("click.echo", lambda *a, **k: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            cfg = Config(path)
            cfg.prompt()
            assert cfg.data["CREDENTIALS_FILE"] == "test_credentials.json"
            assert cfg.data["TOKEN_FILE"] == "test_token.json"
            assert cfg.data["TIME_ZONE"] == "Europe/Paris"
            assert cfg.data["AVAILABILITY_START"] == "09:00"
            assert cfg.data["AVAILABILITY_END"] == "17:00"
            assert cfg.data["CALENDAR_IDS"] == ["primary", "work"]
            # File should exist
            assert os.path.exists(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["TIME_ZONE"] == "Europe/Paris"

    def test_config_prompt_asks_for_scopes(self):
        """Test that Config.prompt asks for scopes."""
        prompts = []
        def fake_prompt(text, default=None):
            prompts.append(text)
            return default or ""
        config = Config()
        with patch("click.prompt", side_effect=fake_prompt):
            config.prompt()
        assert any("scope" in p.lower() for p in prompts), "Config.prompt should ask for scopes"
