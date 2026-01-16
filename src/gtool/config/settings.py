import json
import logging
import os

import click
from platformdirs import user_config_dir

logger = logging.getLogger("gtool")

APP_NAME = "caltool"  # Keep original name for backward compat with existing config files
CONFIG_FILENAME = "config.json"
CONFIG_PATH = os.path.join(user_config_dir(APP_NAME), CONFIG_FILENAME)

DEFAULTS = {
    "CREDENTIALS_FILE": "~/.config/caltool/credentials.json",
    "TOKEN_FILE": "~/.config/caltool/token.json",
    "TIME_ZONE": "America/Los_Angeles",
    "AVAILABILITY_START": "08:00",
    "AVAILABILITY_END": "18:00",
    "CALENDAR_IDS": ["primary"],
    "SCOPES": ["https://www.googleapis.com/auth/calendar"],
    "GMAIL_ENABLED": False,
    # OAuth local-server settings (used by GoogleAuth).
    # You can override these via env vars:
    # - GTOOL_OAUTH_HOST (default: localhost)
    # - GTOOL_OAUTH_PORTS (comma-separated allowlist; default: 8400..8410)
}

# Available scopes for configuration
AVAILABLE_SCOPES = {
    "calendar": "https://www.googleapis.com/auth/calendar",
    "gmail.readonly": "https://www.googleapis.com/auth/gmail.readonly",
    "gmail.modify": "https://www.googleapis.com/auth/gmail.modify",
}


class Config:
    def validate(self):
        required_keys = [
            "CREDENTIALS_FILE",
            "TOKEN_FILE",
            "SCOPES",
            "CALENDAR_IDS",
            "TIME_ZONE",
            "AVAILABILITY_START",
            "AVAILABILITY_END",
        ]
        logger.debug(f"Validating config: {self.data}")
        missing = [k for k in required_keys if not self.get(k)]
        if missing:
            logger.error(f"Missing required config keys: {missing}")
            raise click.UsageError(f"Missing required config keys: {', '.join(missing)}. Run 'gtool config' to set up.")
        # Basic format validation
        if not isinstance(self.get("SCOPES"), list):
            logger.error(f"SCOPES must be a list, got {type(self.get('SCOPES'))}")
            raise click.UsageError("SCOPES must be a list.")
        if not isinstance(self.get("CALENDAR_IDS"), list):
            logger.error(f"CALENDAR_IDS must be a list, got {type(self.get('CALENDAR_IDS'))}")
            raise click.UsageError("CALENDAR_IDS must be a list.")

    def __init__(self, path=CONFIG_PATH):
        self.path = path
        logger.debug(f"Config init: path={self.path}")
        self.data = self.load()

    def load(self):
        logger.debug(f"Loading config from {self.path}")
        if os.path.exists(self.path):
            with open(self.path) as f:
                data = json.load(f)
            logger.debug(f"Loaded config data: {data}")
            return data
        logger.debug("Config file not found, using DEFAULTS.")
        return DEFAULTS.copy()

    def save(self):
        logger.debug(f"Saving config to {self.path}: {self.data}")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    def prompt(self):
        click.echo(click.style("Creating a new configuration file...", fg="cyan"))
        self.data["CREDENTIALS_FILE"] = click.prompt(
            "Enter the path to your credentials file",
            default=self.data.get("CREDENTIALS_FILE", DEFAULTS["CREDENTIALS_FILE"]),
        )
        self.data["TOKEN_FILE"] = click.prompt(
            "Enter the path to your token file", default=self.data.get("TOKEN_FILE", DEFAULTS["TOKEN_FILE"])
        )
        self.data["TIME_ZONE"] = click.prompt(
            "Enter your time zone", default=self.data.get("TIME_ZONE", DEFAULTS["TIME_ZONE"])
        )
        self.data["AVAILABILITY_START"] = click.prompt(
            "Enter your availability start time (HH:MM)",
            default=self.data.get("AVAILABILITY_START", DEFAULTS["AVAILABILITY_START"]),
        )
        self.data["AVAILABILITY_END"] = click.prompt(
            "Enter your availability end time (HH:MM)",
            default=self.data.get("AVAILABILITY_END", DEFAULTS["AVAILABILITY_END"]),
        )
        cal_ids = click.prompt(
            "Enter the comma-separated calendar IDs"
            "\n(You can update this later. The get-calendars command"
            " will show your current calendars.)",
            default=",".join(self.data.get("CALENDAR_IDS", DEFAULTS["CALENDAR_IDS"])),
        )
        self.data["CALENDAR_IDS"] = [cid.strip() for cid in cal_ids.split(",")]

        # Scope selection with menu
        self._prompt_for_scopes()

        self.save()
        click.echo(click.style(f"Configuration file created at {self.path}", fg="green"))

    def _prompt_for_scopes(self):
        """Interactively prompt user to select scopes with menu-based interface."""
        click.echo(click.style("\nSelect which features to enable:", fg="cyan"))

        # Determine which scopes are already selected
        current_scopes = set(self.data.get("SCOPES", DEFAULTS["SCOPES"]))

        # Calendar scope (always included)
        has_calendar = AVAILABLE_SCOPES["calendar"] in current_scopes
        if not has_calendar:
            self.data["SCOPES"] = self.data.get("SCOPES", [])
            if AVAILABLE_SCOPES["calendar"] not in self.data["SCOPES"]:
                self.data["SCOPES"].append(AVAILABLE_SCOPES["calendar"])

        # Gmail scope selection
        gmail_enabled = click.confirm(
            "Do you want to enable Gmail access? (Read-only)", default=self.data.get("GMAIL_ENABLED", False)
        )
        self.data["GMAIL_ENABLED"] = gmail_enabled

        if gmail_enabled:
            # Ask about write permissions
            gmail_modify = click.confirm(
                "Do you need write permissions (send, delete, modify)? (Read-only is recommended)", default=False
            )

            scopes = self.data.get("SCOPES", DEFAULTS["SCOPES"].copy())
            if gmail_modify:
                scope = AVAILABLE_SCOPES["gmail.modify"]
            else:
                scope = AVAILABLE_SCOPES["gmail.readonly"]

            # Remove old Gmail scopes if present
            scopes = [s for s in scopes if "gmail" not in s]
            scopes.append(scope)
            self.data["SCOPES"] = scopes
            click.echo(
                click.style(
                    f"  ✓ Gmail enabled with {('read-only' if not gmail_modify else 'read-write')} access", fg="green"
                )
            )
        else:
            # Remove Gmail scopes if disabled
            scopes = self.data.get("SCOPES", DEFAULTS["SCOPES"].copy())
            self.data["SCOPES"] = [s for s in scopes if "gmail" not in s]

    def get(self, key, default=None):
        env_key = f"GTOOL_{key.upper()}"
        if env_key in os.environ:
            val = os.environ[env_key]
            logger.debug(f"Overriding config key '{key}' with env value: {val}")
            # Try to parse lists from env vars
            if key in ("SCOPES", "CALENDAR_IDS"):
                parsed = [v.strip() for v in val.split(",")]
                logger.debug(f"Parsed env list for '{key}': {parsed}")
                return parsed
            return val
        value = self.data.get(key, default)
        logger.debug(f"Config get: {key}={value}")
        return value

    def is_gmail_enabled(self) -> bool:
        """Check if Gmail is enabled in configuration.

        Gmail is enabled if GMAIL_ENABLED is True or if Gmail scopes are present.

        Returns:
            True if Gmail is enabled
        """
        gmail_enabled = self.get("GMAIL_ENABLED", False)
        has_gmail_scope = any("gmail" in scope.lower() for scope in self.get("SCOPES", []))
        return gmail_enabled or has_gmail_scope

    def has_gmail_scope(self, scope_type: str = "readonly") -> bool:
        """Check if user has required Gmail scope.

        Args:
            scope_type: 'readonly' or 'modify'

        Returns:
            True if user has the requested Gmail scope or a higher level scope
        """
        scopes = self.get("SCOPES", [])
        if scope_type == "readonly":
            # User has readonly if they have readonly or modify
            return any("gmail.readonly" in s or "gmail.modify" in s for s in scopes)
        elif scope_type == "modify":
            # User has modify only if they explicitly have modify
            return any("gmail.modify" in s for s in scopes)
        return False

    def validate_gmail_scopes(self) -> None:
        """Validate that Gmail scopes are configured when Gmail is enabled.

        Raises:
            click.UsageError: If Gmail is enabled but scopes are not configured
        """
        if self.is_gmail_enabled() and not self.has_gmail_scope("readonly"):
            logger.error("Gmail enabled but no Gmail scope configured")
            raise click.UsageError(
                "Gmail is enabled but no Gmail scope is configured. Run 'gtool config' to add Gmail permissions."
            )
