"""
Centralized error handling utilities for calendarcli CLI.
"""

import click
import google.auth.exceptions


class CLIError(Exception):
    """Custom exception for CLI-related errors."""

    pass


def handle_cli_exception(e):
    if isinstance(e, google.auth.exceptions.GoogleAuthError) or "invalid_scope" in str(e):
        click.echo(
            click.style(
                "Google authentication failed. Please check your credentials, token, and SCOPES in config.", fg="red"
            )
        )
        click.echo(click.style("Run 'caltool config' to set up or update your configuration.", fg="yellow"))
    else:
        click.echo(click.style(f"Error: {e}", fg="red"))
    raise click.Abort()
