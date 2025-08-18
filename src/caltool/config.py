
import json
import logging
import os

import click
from platformdirs import user_config_dir

logger = logging.getLogger("caltool")

APP_NAME = "caltool"
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
            raise click.UsageError(
                f"Missing required config keys: {', '.join(missing)}. Run 'caltool config' to set up."
            )
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
        import click

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
        scopes_input = click.prompt(
            "Enter the comma-separated Google API scopes",
            default=",".join(self.data.get("SCOPES", DEFAULTS["SCOPES"])),
        )
        self.data["SCOPES"] = [s.strip() for s in scopes_input.split(",") if s.strip()]
        self.save()
        click.echo(click.style(f"Configuration file created at {self.path}", fg="green"))

    def get(self, key, default=None):
        env_key = f"CALTOOL_{key.upper()}"
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
