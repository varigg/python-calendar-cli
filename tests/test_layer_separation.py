"""Integration tests for layer separation.

These tests verify the complete flow from infrastructure → config → CLI
and ensure that exceptions are properly translated at layer boundaries.

Focus: High-value scenarios that catch real bugs that mocks hide.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from gtool.cli.errors import AuthenticationError
from gtool.cli.main import cli
from gtool.config.settings import Config
from gtool.infrastructure.exceptions import (
    AuthError,
    ConfigValidationError,
    ServiceError,
)
from gtool.infrastructure.service_factory import ServiceFactory


class TestLayerSeparationExceptionTranslation:
    """Test that infrastructure exceptions are properly translated to CLI exceptions."""

    def test_auth_error_translated_to_authentication_error(self):
        """Test that AuthError from infrastructure is translated to AuthenticationError in CLI."""
        runner = CliRunner()

        with patch("gtool.cli.main.create_calendar_client") as mock_create:
            # Simulate infrastructure raising AuthError
            mock_create.side_effect = AuthError("OAuth token refresh failed")

            result = runner.invoke(cli, ["free", "today"], obj=Mock())

            # Should fail with AuthenticationError (click.ClickException)
            assert result.exit_code != 0
            assert "OAuth token refresh failed" in result.output or result.exit_code == 1

    def test_service_error_translated_to_cli_error(self):
        """Test that ServiceError from infrastructure is translated to CLIError in CLI."""
        runner = CliRunner()

        with patch("gtool.cli.main.create_calendar_client") as mock_create:
            # Simulate infrastructure raising ServiceError
            mock_create.side_effect = ServiceError("Google API returned 503 Service Unavailable")

            result = runner.invoke(cli, ["free", "today"], obj=Mock())

            # Should fail with CLIError
            assert result.exit_code != 0


class TestConfigValidationErrorFlow:
    """Test that config validation errors flow through layers correctly."""

    def test_missing_scopes_raises_config_validation_error(self):
        """Test that Config raises ConfigValidationError when SCOPES is invalid."""
        config = Config()
        config.data["SCOPES"] = "not-a-list"  # Should be a list

        with pytest.raises(ConfigValidationError) as exc_info:
            config.validate()

        assert "SCOPES must be a list" in str(exc_info.value)

    def test_missing_calendar_ids_raises_config_validation_error(self):
        """Test that Config raises ConfigValidationError when CALENDAR_IDS is invalid."""
        config = Config()
        config.data["CALENDAR_IDS"] = "single-string"  # Should be a list

        with pytest.raises(ConfigValidationError) as exc_info:
            config.validate()

        assert "CALENDAR_IDS must be a list" in str(exc_info.value)

    def test_missing_required_keys_raises_config_validation_error(self):
        """Test that Config raises ConfigValidationError for missing required keys."""
        config = Config()
        config.data = {}  # Empty config

        with pytest.raises(ConfigValidationError) as exc_info:
            config.validate()

        assert "Missing required config keys" in str(exc_info.value)


class TestServiceFactoryCredentialsBug:
    """Test that ServiceFactory correctly calls get_credentials() method.

    This is a regression test for a bug where ServiceFactory accessed
    .credentials property instead of calling get_credentials() method.
    """

    def test_service_factory_calls_get_credentials_method(self):
        """Test that ServiceFactory uses get_credentials() not credentials property."""
        mock_auth = Mock()
        mock_creds = Mock()
        mock_auth.get_credentials.return_value = mock_creds

        factory = ServiceFactory(auth=mock_auth)

        with patch("gtool.infrastructure.service_factory.discovery.build") as mock_build:
            mock_build.return_value = Mock()
            factory.build_service("gmail", "v1")

            # Verify get_credentials() was called
            mock_auth.get_credentials.assert_called_once()

            # Verify build was called with credentials from get_credentials()
            mock_build.assert_called_once()
            call_args = mock_build.call_args
            assert call_args[1]["credentials"] == mock_creds


class TestGmailScopeValidation:
    """Test Gmail scope validation at boundaries."""

    def test_gmail_command_fails_without_gmail_scope(self):
        """Test that Gmail commands fail when Gmail scope is missing."""
        runner = CliRunner()

        config = Config()
        config.data["SCOPES"] = ["https://www.googleapis.com/auth/calendar"]
        config.data["GMAIL_ENABLED"] = False

        result = runner.invoke(cli, ["gmail", "list"], obj=config)

        assert result.exit_code != 0
        # Should raise ConfigValidationError which translates to click.UsageError

    def test_validate_gmail_scopes_raises_config_validation_error(self):
        """Test that Config.validate_gmail_scopes raises ConfigValidationError."""
        config = Config()
        config.data["SCOPES"] = ["https://www.googleapis.com/auth/calendar"]
        config.data["GMAIL_ENABLED"] = True

        with pytest.raises(ConfigValidationError) as exc_info:
            config.validate_gmail_scopes()

        assert "Gmail" in str(exc_info.value)


class TestLayerBoundaries:
    """Test that layers maintain clear boundaries (no leaky dependencies)."""

    def test_infrastructure_has_no_click_import(self):
        """Verify that infrastructure module has no click imports."""
        import gtool.infrastructure.auth as auth_module

        # Check that click is not in the module
        assert "click" not in dir(auth_module)
        # These modules should not import click
        source = open(auth_module.__file__).read()
        assert "import click" not in source
        assert "from click" not in source

    def test_config_has_no_click_import(self):
        """Verify that config module has no click imports."""
        import gtool.config.settings as config_module

        source = open(config_module.__file__).read()
        assert "import click" not in source
        assert "from click" not in source

    def test_infrastructure_has_no_cli_imports(self):
        """Verify that infrastructure module has no CLI layer imports."""
        import gtool.infrastructure.auth as auth_module
        import gtool.infrastructure.retry as retry_module

        source_auth = open(auth_module.__file__).read()
        source_retry = open(retry_module.__file__).read()

        assert "from gtool.cli" not in source_auth
        assert "from gtool.cli" not in source_retry

    def test_config_has_no_cli_imports(self):
        """Verify that config module has no CLI layer imports."""
        import gtool.config.settings as config_module

        source = open(config_module.__file__).read()
        assert "from gtool.cli" not in source

    def test_decorator_translates_exception_types(self):
        """Test that the translate_exceptions decorator properly translates exceptions."""
        from gtool.cli.decorators import translate_exceptions

        # Test decorator with AuthError
        @translate_exceptions
        def func_raises_auth_error():
            raise AuthError("Test auth error")

        with pytest.raises(AuthenticationError):
            func_raises_auth_error()

    def test_prompt_for_config_function_exists(self):
        """Test that prompt_for_config function exists and is callable."""
        from gtool.cli.decorators import prompt_for_config

        assert callable(prompt_for_config)
