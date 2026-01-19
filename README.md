# calendarcli

A command-line tool for managing Google Calendar events and availability. Designed for productivity, automation, and integration into developer workflows.

## Features

- Find free time slots across one or more calendars
- List available calendars
- Show upcoming events
- Interact with Google Calendar via the command line
- **New:** Manage Gmail messages (list, read, delete) with Gmail API integration

## Gmail Integration

`calendarcli` now supports Gmail management alongside Calendar features.

### Enabling Gmail

During `caltool config`, you'll be asked if you want to enable Gmail access. Choose "yes" to add Gmail scopes to your configuration. You can select:

- **Read-only access**: View and search messages
- **Modify access**: View, search, and delete messages

### Gmail Commands

```sh
# List unread messages with subjects displayed (NEW: Phase 3)
gtool gmail list --query "is:unread" --count 5

# Filter by label (NEW: Phase 4)
gtool gmail list --label "Work" --count 10

# Combine label and query filters (NEW: Phase 4)
gtool gmail list --label "Work" --query "is:unread"

# List messages from a specific sender
gtool gmail list --query "from:user@example.com" --count 10

# Default: Shows INBOX with subjects in table format
gtool gmail list

# Legacy simple format (without subject table)
gtool gmail list --format simple

# Show full details of a message
gtool gmail show-message <message_id>

# Show message in minimal format
gtool gmail show-message <message_id> --format minimal

# Delete a message (with confirmation)
gtool gmail delete <message_id>

# Delete a message (skip confirmation)
gtool gmail delete <message_id> --confirm
```

### Gmail List Features (Feature 007)

The `gmail list` command has been enhanced with:

1. **Subject Display**: Email subjects are shown in a formatted table for quick identification
   - Blank subjects display as "(No Subject)"
   - Long subjects are truncated to fit terminal width
   - Unicode and emoji fully supported

2. **Label Filtering**: Filter emails by Gmail labels
   - Use `--label` option: `gtool gmail list --label "Work"`
   - Combines with search queries: `--label "Work" --query "is:unread"`
   - Defaults to INBOX when no filters specified

3. **Batch Size Control**: Configure how many messages to retrieve
   - Use `--count` option: `gtool gmail list --count 20`
   - Default is 10 messages
   - Backward compatible with `--limit` option

4. **Output Formats**:
   - `--format table` (default): Formatted table with subjects
   - `--format simple`: Legacy output without table

**Examples**:
```sh
# Find unread work emails
gtool gmail list --label "Work" --query "is:unread" --count 5

# Quick inbox check (shows subjects in table)
gtool gmail list

# Get first 20 emails from a label
gtool gmail list --label "Personal" --count 20
```

### Gmail Scope Requirements

- To list and view messages: `https://www.googleapis.com/auth/gmail.readonly`
- To delete messages: `https://www.googleapis.com/auth/gmail.modify`

If you change scopes, you'll need to re-authenticate. Delete `token.json` and run any command to trigger a new OAuth flow.

## Installation

### Install the CLI as a user script

1. Build the wheel:

```sh
uv build
```

2. Install the wheel as a user script:

```sh
uv tool install dist/caltool-0.1.0-py3-none-any.whl
```

After installation, you can run `caltool` from any shell:

```sh
caltool --help
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

## Module Structure

The codebase is organized for clarity and maintainability:

- `src/caltool/cli.py`: Main CLI logic and command definitions.
- `src/caltool/datetime_utils.py`: Date/time parsing and formatting utilities.
- `src/caltool/format.py`: Formatting and color helper functions for CLI output.
- `src/caltool/errors.py`: Centralized error handling utilities.
- `src/caltool/gcal_client.py`: Google Calendar API interactions.
- `src/caltool/scheduler.py`: Scheduling logic and free slot calculations.

## Usage

All commands are available via the `caltool` CLI

## Configuration

Configuration is stored in a platform-standard location (e.g., `~/.config/caltool/config.json` on Linux).

### Interactive Setup

Run the following command to interactively set up or edit your configuration:

```sh
uv run caltool config
```

You will be prompted for credentials file, token file, time zone, availability window, calendar IDs, and Google API scopes.

Example config file:

```json
{
  "CREDENTIALS_FILE": "~/.config/caltool/credentials.json",
  "TOKEN_FILE": "~/.config/caltool/token.json",
  "SCOPES": ["https://www.googleapis.com/auth/calendar"],
  "CALENDAR_IDS": ["primary"],
  "AVAILABILITY_START": "08:00",
  "AVAILABILITY_END": "18:00",
  "TIME_ZONE": "America/Los_Angeles"
}
```

### Environment Variable Overrides

Any config value can be overridden by setting an environment variable named `CALTOOL_<KEY>`. For example:

```sh
export CALTOOL_TIME_ZONE="Europe/London"
export CALTOOL_CALENDAR_IDS="primary,work"
```

Lists (like `SCOPES` and `CALENDAR_IDS`) should be comma-separated.

### Error Handling & Validation

If required config values are missing or invalid, the CLI will show a clear error and prompt you to run `caltool config`.

All config values are validated for type and presence before running commands.

### Debug Logging

Enable debug logging for troubleshooting by passing `--debug` to any command:

```sh
uv run caltool --debug show-events
```

This will print detailed logs about config loading, API calls, and event formatting to help diagnose issues.

## Testing

Run all tests with:

```sh
uv run pytest
```

## License

MIT
