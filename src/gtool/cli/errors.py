"""
Centralized error handling utilities for gtool CLI.
"""

import click


class CLIError(Exception):
    """Custom exception for CLI-related errors."""

    pass


class AuthenticationError(CLIError):
    """Raised when authentication fails with any provider.

    This exception wraps authentication failures from the underlying auth provider
    (e.g., Google Auth) and presents them as domain exceptions. This keeps the CLI
    layer independent of authentication implementation details and enables easy
    swapping of auth providers in the future.

    Attributes:
        message: The authentication failure reason

    Example:
        >>> try:
        ...     credentials = auth.get_credentials()
        ... except google.auth.exceptions.GoogleAuthError as e:
        ...     raise AuthenticationError(f"Failed to get credentials: {e}")
    """

    def __init__(self, message: str) -> None:
        """Initialize AuthenticationError with a message.

        Args:
            message: Detailed description of what authentication failure occurred
        """
        super().__init__(message)
        self.message = message


def handle_cli_exception(e: CLIError) -> None:
    """Handle CLI exceptions with appropriate user-facing error messages.

    Routes exceptions to appropriate error messages and ensures consistent
    error formatting across all CLI commands.

    Args:
        e: CLIError instance (or subclass like AuthenticationError)

    Raises:
        click.Abort: Always raised after displaying error message
    """
    if isinstance(e, AuthenticationError) or "invalid_scope" in str(e):
        click.echo(
            click.style(
                "Google authentication failed. Please check your credentials, token, and SCOPES in config.", fg="red"
            )
        )
        click.echo(click.style("Run 'gtool config' to set up or update your configuration.", fg="yellow"))
    else:
        click.echo(click.style(f"Error: {e}", fg="red"))
    raise click.Abort()
