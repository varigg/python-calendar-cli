import json
import logging
import os

from platformdirs import user_config_dir

from gtool.infrastructure.exceptions import ConfigValidationError

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
            raise ConfigValidationError(
                f"Missing required config keys: {', '.join(missing)}. Run 'gtool config' to set up."
            )
        # Basic format validation
        if not isinstance(self.get("SCOPES"), list):
            logger.error(f"SCOPES must be a list, got {type(self.get('SCOPES'))}")
            raise ConfigValidationError("SCOPES must be a list.")
        if not isinstance(self.get("CALENDAR_IDS"), list):
            logger.error(f"CALENDAR_IDS must be a list, got {type(self.get('CALENDAR_IDS'))}")
            raise ConfigValidationError("CALENDAR_IDS must be a list.")

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
            ConfigValidationError: If Gmail is enabled but scopes are not configured
        """
        if self.is_gmail_enabled() and not self.has_gmail_scope("readonly"):
            logger.error("Gmail enabled but no Gmail scope configured")
            raise ConfigValidationError(
                "Gmail is enabled but no Gmail scope is configured. Run 'gtool config' to add Gmail permissions."
            )
