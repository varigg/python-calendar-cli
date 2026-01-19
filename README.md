# calendarcli

A command-line tool for managing Google Calendar events and Gmail messages. Designed for productivity, automation, and integration into developer workflows.

## Features

- **Calendar Management**:
  - Find free time slots across one or more calendars
  - List available calendars
  - Show upcoming events
  - Interactive configuration

- **Gmail Management**:
  - List messages with subject display in formatted tables
  - Filter messages by label or search query
  - View message details
  - Delete messages
  - Full Unicode and emoji support

## Quick Start

### Installation

Install as a user script:

```sh
# Build the wheel
uv build

# Install globally
uv tool install dist/caltool-0.1.0-py3-none-any.whl
```

After installation, `gtool` is available from any shell:

```sh
gtool --help
```

### Initial Setup

1. **Get Google API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a project and enable Google Calendar API (and Gmail API if needed)
   - Create OAuth client ID (Desktop app)
   - Download `credentials.json`

2. **Configure the tool**:
```sh
gtool config
```

You'll be prompted to:
- Set credentials and token file paths
- Choose your time zone
- Set availability hours
- Select calendar IDs
- Enable Gmail access (optional)

3. **First run** (authentication):
```sh
gtool get-calendars
```

Your browser will open for OAuth consent. After authorization, a `token.json` is created.

## Gmail Commands

### List Messages

```sh
# Quick inbox check (default: 10 messages with subjects in table)
gtool gmail list

# List unread messages
gtool gmail list --query "is:unread" --count 5

# Filter by label
gtool gmail list --label "Work"

# Combine label and query
gtool gmail list --label "Work" --query "is:unread" --count 20

# Search by sender
gtool gmail list --query "from:user@example.com"

# Legacy simple format (no table)
gtool gmail list --format simple
```

### View Message Details

```sh
# Show full message details
gtool gmail show-message <message_id>

# Show minimal format
gtool gmail show-message <message_id> --format minimal
```

### Delete Messages

```sh
# Delete with confirmation prompt
gtool gmail delete <message_id>

# Delete without confirmation
gtool gmail delete <message_id> --confirm
```

## Gmail List Features

The `gmail list` command provides powerful message browsing:

### 1. Subject Display
- Email subjects shown in formatted table
- Blank subjects display as "(No Subject)"
- Long subjects automatically truncated
- Full Unicode and emoji support (🎉, émoji, etc.)

### 2. Label Filtering
- Filter by Gmail labels: `--label "Work"`
- Combines with search queries: `--label "Work" --query "is:unread"`
- Defaults to INBOX when no filters specified
- Supports all Gmail label types (system and custom)

### 3. Batch Size Control
- Specify count: `--count 20`
- Default: 10 messages
- Backward compatible: `--limit` still works
- Non-negative validation

### 4. Output Formats
- **Table format** (default): Formatted with columns for #, Message ID, Subject, Preview
- **Simple format**: Legacy text output for scripts

### Gmail Search Query Syntax

The `--query` option supports Gmail's powerful search operators:

```sh
# Message states
gtool gmail list --query "is:unread"
gtool gmail list --query "is:read"
gtool gmail list --query "is:starred"

# Sender/recipient
gtool gmail list --query "from:boss@company.com"
gtool gmail list --query "to:team@company.com"

# Content
gtool gmail list --query "subject:meeting"
gtool gmail list --query "has:attachment"

# Dates
gtool gmail list --query "after:2024/01/01"
gtool gmail list --query "before:2024/12/31"
gtool gmail list --query "newer_than:7d"

# Combine operators
gtool gmail list --query "from:boss@company.com has:attachment is:unread"
```

For more search operators, see: https://support.google.com/mail/answer/7190

## Calendar Commands

```sh
# List all accessible calendars
gtool get-calendars

# Find free time slots
gtool free today+1 --duration 30

# Show upcoming events
gtool show-events thursday+2
```

## Configuration

Configuration is stored in `~/.config/gtool/config.json` on Linux/macOS, or equivalent on Windows.

### Interactive Setup

Set up or edit your configuration interactively:

```sh
gtool config
```

You'll be prompted for:
- **Credentials file path**: Where your `credentials.json` is stored
- **Token file path**: Where to store authentication token
- **Time zone**: Your local timezone (e.g., "America/Los_Angeles")
- **Availability window**: When you're available for meetings (e.g., 08:00-18:00)
- **Calendar IDs**: Which calendars to check (comma-separated)
- **Gmail access**: Whether to enable Gmail features and access level

### Example Configuration

```json
{
  "CREDENTIALS_FILE": "~/.config/gtool/credentials.json",
  "TOKEN_FILE": "~/.config/gtool/token.json",
  "SCOPES": [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly"
  ],
  "CALENDAR_IDS": ["primary"],
  "AVAILABILITY_START": "08:00",
  "AVAILABILITY_END": "18:00",
  "TIME_ZONE": "America/Los_Angeles",
  "GMAIL_ENABLED": true
}
```

### Environment Variable Overrides

Override any config value with environment variables:

```sh
export GTOOL_TIME_ZONE="Europe/London"
export GTOOL_CALENDAR_IDS="primary,work@company.com"
export GTOOL_SCOPES="https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/gmail.readonly"
```

Lists should be comma-separated.

### Gmail Scope Requirements

Choose the appropriate scope based on your needs:

- **Read-only** (`gmail.readonly`): List, search, and view messages
- **Modify** (`gmail.modify`): All read-only plus delete messages

To change scopes:
1. Run `gtool config` and update Gmail settings
2. Delete your `token.json` file
3. Run any Gmail command to re-authenticate

## Troubleshooting

### Gmail Access Issues

**Error: "Gmail scope missing"**
- Run `gtool config` and enable Gmail access
- Delete `token.json` and re-authenticate

**Error: "Permission denied"**
- Check that you selected the correct Gmail scope
- Verify API is enabled in Google Cloud Console

### Authentication Issues

**Token expired or invalid**
```sh
# Delete token and re-authenticate
rm ~/.config/gtool/token.json
gtool get-calendars
```

**Credentials file not found**
```sh
# Check credentials path in config
gtool config
```

### Debug Mode

Enable detailed logging:

```sh
gtool --debug gmail list
gtool --debug show-events
```

## Development

### Project Structure

```
src/gtool/
├── cli/                 # CLI command definitions and formatting
│   ├── main.py         # Main CLI entry point with all commands
│   ├── formatters.py   # Output formatting and tables
│   ├── decorators.py   # CLI decorators and validation
│   └── errors.py       # Error handling and messages
├── clients/            # API client implementations
│   ├── gmail.py        # Gmail API client
│   └── gcal.py         # Google Calendar API client (if exists)
├── core/               # Business logic
│   ├── models.py       # Data models
│   └── scheduler.py    # Scheduling and free time logic
├── infrastructure/     # Low-level infrastructure
│   ├── auth.py         # Google OAuth authentication
│   ├── retry.py        # Retry logic for API calls
│   └── exceptions.py   # Exception definitions
├── config/             # Configuration management
│   └── settings.py     # Config loading and validation
└── utils/              # Utility functions
    └── datetime.py     # Date/time parsing and formatting
```

### Running Tests

```sh
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/gtool --cov-report=html

# Run specific test file
uv run pytest tests/test_gmail_client.py -v

# Run specific test
uv run pytest tests/test_cli.py::test_gmail_list_displays_subjects -v
```

### Code Quality

The project uses pre-commit hooks:

```sh
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Includes:
- `ruff`: Linting and formatting
- `pytest`: Automated tests
- Security checks for secrets and keys

### Contributing

1. Create a feature branch
2. Make changes with tests
3. Ensure all tests pass: `uv run pytest`
4. Ensure code is formatted: `pre-commit run --all-files`
5. Submit pull request

## License

MIT
