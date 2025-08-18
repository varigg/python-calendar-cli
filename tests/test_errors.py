"""
Unit tests for errors.py (cli_error).
"""
import click
import pytest

import caltool.errors as errors


def test_cli_error_raises_abort(monkeypatch):
    output = []
    monkeypatch.setattr(click, "echo", lambda msg: output.append(msg))
    with pytest.raises(click.Abort):
        errors.cli_error("Test error", suggestion="Try again", abort=True)
    assert any("Test error" in o for o in output)
    assert any("Try again" in o for o in output)

# You can add more tests for non-abort behavior if needed.
