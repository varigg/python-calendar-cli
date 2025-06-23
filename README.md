# calendarcli

A command-line tool for managing Google Calendar events and availability. Designed for productivity, automation, and integration into developer workflows.

## Features

- Find free time slots across one or more calendars
- List available calendars
- Show upcoming events
- Interact with Google Calendar via the command line

## Installation

Clone the repository and install dependencies using [uv](https://github.com/astral-sh/uv):

```sh
uv install
```

Or with pip:

```sh
pip install -e .
```

## Google API Credentials Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a new project (or select an existing one).
3. Enable the Google Calendar API for your project.
4. Go to **APIs & Services > Credentials**.
5. Click **Create Credentials > OAuth client ID**.
6. Choose **Desktop app** and give it a name.
7. Download the `credentials.json` file and place it in your project root directory.

The first time you run a command, you will be prompted to authenticate and a `token.json` will be created for future use.

## Usage

All commands are available via the `caltool` CLI

### Find Free Time Slots

```sh
uv run caltool free --start-date 2025-06-24 --end-date 2025-06-24 --pretty
```

### List Calendars

```sh
uv run caltool get-calendars
```

### Show Upcoming Events

```sh
uv run caltool show-events --start-time "2025-06-24T09:00:00" --end-time "2025-06-24T18:00:00"
```

## Configuration

The tool will look for `.caltool.cfg` in the home directory and create it if it is not found.
You can edit the file later to change your calendar IDs, time zone, and availability window. Example:

```json
{
  "CREDENTIALS_FILE": "credentials.json",
  "TOKEN_FILE": "token.json",
  "SCOPES": ["https://www.googleapis.com/auth/calendar"],
  "CALENDAR_IDS": ["primary"],
  "AVAILABILITY_START": "08:00",
  "AVAILABILITY_END": "18:00",
  "TIME_ZONE": "America/Los_Angeles"
}
```

## Testing

Run all tests with:

```sh
uv run pytest
```

## License

MIT
