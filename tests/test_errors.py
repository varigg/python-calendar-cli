"""
Unit tests for errors.py (handle_cli_exception).
"""

import click
import google.auth.exceptions
import pytest

import caltool.errors as errors


def test_handle_cli_exception_google_auth_error(monkeypatch):
    output = []
    monkeypatch.setattr(click, "echo", lambda msg: output.append(msg))
    with pytest.raises(click.Abort):
        errors.handle_cli_exception(google.auth.exceptions.GoogleAuthError("auth failed"))
    assert any("authentication" in o.lower() for o in output)
