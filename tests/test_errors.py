"""
Unit tests for errors.py (CLIError, AuthenticationError, handle_cli_exception).
"""

import click
import pytest

import gtool.cli.errors as errors


class TestAuthenticationError:
    """Tests for AuthenticationError exception class."""

    def test_authentication_error_can_be_caught_as_cli_error(self):
        """AuthenticationError should be catchable as CLIError."""
        with pytest.raises(errors.CLIError):
            raise errors.AuthenticationError("Auth failed")

    def test_authentication_error_can_be_caught_directly(self):
        """AuthenticationError should be catchable directly."""
        with pytest.raises(errors.AuthenticationError):
            raise errors.AuthenticationError("Auth failed")


class TestHandleCliException:
    """Tests for handle_cli_exception function."""

    def test_handle_cli_exception_authentication_error(self, monkeypatch):
        """handle_cli_exception should handle AuthenticationError with auth-specific message."""
        output = []
        monkeypatch.setattr(click, "echo", lambda msg: output.append(msg))

        with pytest.raises(click.Abort):
            errors.handle_cli_exception(errors.AuthenticationError("auth failed"))

        # Should display authentication failure message
        output_text = "\n".join(str(o) for o in output)
        assert "authentication failed" in output_text.lower()
        assert "gtool config" in output_text

    def test_handle_cli_exception_generic_cli_error(self, monkeypatch):
        """handle_cli_exception should handle generic CLIError."""
        output = []
        monkeypatch.setattr(click, "echo", lambda msg: output.append(msg))

        with pytest.raises(click.Abort):
            errors.handle_cli_exception(errors.CLIError("Generic error"))

        output_text = "\n".join(str(o) for o in output)
        assert "Generic error" in output_text
