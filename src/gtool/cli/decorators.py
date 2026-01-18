"""CLI decorators for exception translation and interactive prompting.

This module provides decorators that translate infrastructure exceptions
to CLI exceptions for user-friendly error messages.
"""

import functools
import logging
from typing import Callable

import click

from gtool.cli.errors import AuthenticationError
from gtool.infrastructure.exceptions import (
    AuthError,
    ConfigError,
    ConfigValidationError,
)

logger = logging.getLogger(__name__)


def translate_exceptions(func: Callable) -> Callable:
    """Decorator that translates infrastructure exceptions to CLI exceptions.

    Translation rules:
    - AuthError → AuthenticationError
    - ConfigValidationError → click.UsageError
    - ConfigError → click.UsageError

    Usage:
        @click.command()
        @translate_exceptions
        def my_command():
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigValidationError as e:
            logger.debug(f"ConfigValidationError caught: {e}")
            raise click.UsageError(str(e)) from e
        except ConfigError as e:
            logger.debug(f"ConfigError caught: {e}")
            raise click.UsageError(str(e)) from e
        except AuthError as e:
            logger.debug(f"AuthError caught: {e}")
            raise AuthenticationError(str(e)) from e

    return wrapper


def prompt_for_config(config: object) -> None:
    """Interactively prompt user to configure required settings.

    This function replaces the removed Config.prompt() method.
    It prompts the user for configuration values and saves them to the config file.

    Args:
        config: Config object to populate

    Note:
        This function uses click for interactive prompts and should only be
        called from CLI commands, not from infrastructure or config layers.
    """
    click.echo(click.style("Creating a new configuration file...", fg="cyan"))

    # Credentials and token files
    config.data["CREDENTIALS_FILE"] = click.prompt(
        "Enter the path to your credentials file",
        default=config.data.get("CREDENTIALS_FILE", config.data.get("CREDENTIALS_FILE")),
    )
    config.data["TOKEN_FILE"] = click.prompt(
        "Enter the path to your token file",
        default=config.data.get("TOKEN_FILE", config.data.get("TOKEN_FILE")),
    )

    # Time zone
    config.data["TIME_ZONE"] = click.prompt(
        "Enter your time zone",
        default=config.data.get("TIME_ZONE", "America/Los_Angeles"),
    )

    # Availability hours
    config.data["AVAILABILITY_START"] = click.prompt(
        "Enter your availability start time (HH:MM)",
        default=config.data.get("AVAILABILITY_START", "08:00"),
    )
    config.data["AVAILABILITY_END"] = click.prompt(
        "Enter your availability end time (HH:MM)",
        default=config.data.get("AVAILABILITY_END", "18:00"),
    )

    # Calendar IDs
    cal_ids = click.prompt(
        "Enter the comma-separated calendar IDs\n"
        "(You can update this later. The get-calendars command will show your current calendars.)",
        default=",".join(config.data.get("CALENDAR_IDS", ["primary"])),
    )
    config.data["CALENDAR_IDS"] = [cid.strip() for cid in cal_ids.split(",")]

    # Scope selection
    _prompt_for_scopes(config)

    # Save and confirm
    config.save()
    click.echo(click.style(f"Configuration file created at {config.path}", fg="green"))


def _prompt_for_scopes(config: object) -> None:
    """Interactively prompt user to select scopes.

    Prompts for calendar and Gmail access levels.

    Args:
        config: Config object to populate with scopes
    """
    from gtool.config.settings import AVAILABLE_SCOPES

    click.echo(click.style("\nSelect which features to enable:", fg="cyan"))

    # Calendar scope (always included)
    current_scopes = set(config.data.get("SCOPES", []))
    if AVAILABLE_SCOPES["calendar"] not in current_scopes:
        config.data["SCOPES"] = config.data.get("SCOPES", [])
        if AVAILABLE_SCOPES["calendar"] not in config.data["SCOPES"]:
            config.data["SCOPES"].append(AVAILABLE_SCOPES["calendar"])

    # Gmail scope selection
    gmail_enabled = click.confirm(
        "Do you want to enable Gmail access? (Read-only)",
        default=config.data.get("GMAIL_ENABLED", False),
    )
    config.data["GMAIL_ENABLED"] = gmail_enabled

    if gmail_enabled:
        # Ask about write permissions
        gmail_modify = click.confirm(
            "Do you need write permissions (send, delete, modify)? (Read-only is recommended)",
            default=False,
        )

        scopes = config.data.get("SCOPES", ["https://www.googleapis.com/auth/calendar"])
        if gmail_modify:
            scope = AVAILABLE_SCOPES["gmail.modify"]
        else:
            scope = AVAILABLE_SCOPES["gmail.readonly"]

        # Remove old Gmail scopes if present
        scopes = [s for s in scopes if "gmail" not in s]
        scopes.append(scope)
        config.data["SCOPES"] = scopes
        click.echo(
            click.style(
                f"  ✓ Gmail enabled with {('read-only' if not gmail_modify else 'read-write')} access",
                fg="green",
            )
        )
    else:
        # Remove Gmail scopes if disabled
        scopes = config.data.get("SCOPES", ["https://www.googleapis.com/auth/calendar"])
        config.data["SCOPES"] = [s for s in scopes if "gmail" not in s]
