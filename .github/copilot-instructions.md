instead provide a prompt that can be used to do the changes later.

# Copilot Instructions for calendarcli

## Project Purpose

`calendarcli` is a command-line tool for managing Google Calendar and Gmail. It enables users to:

- Find free time slots across one or more calendars
- List available calendars
- Show upcoming events
- Manage Gmail messages (list, read, delete)
- Interact with Google Calendar and Gmail via the command line

The tool is designed for productivity, automation, and integration into developer workflows.

## Project Structure

- `main.py`: Entry point for the CLI (may delegate to `src/caltool/cli.py`)
- `src/caltool/`
  - `cli.py`: Main CLI logic using `click`. Handles user commands, argument parsing, and delegates formatting and error handling. Includes Calendar and Gmail command groups.
  - `datetime_utils.py`: Date/time parsing and formatting utilities. Supports intuitive range strings (e.g., `today+1`, `thursday+2`).
  - `format.py`: Formatting and color helper functions for CLI output.
  - `errors.py`: Centralized error handling utilities, including `handle_cli_exception` and `CLIError`.
  - `google_auth.py`: Shared Google OAuth flow, scope change detection, token refresh & persistence. Singleton pattern.
  - `google_client.py`: Abstract base class for all Google API clients. Provides shared authentication, retry decorator with smart categorization, and error handling patterns.
  - `gcal_client.py`: Google Calendar API client. Inherits from `GoogleAPIClient`. Methods: get_calendar_list, get_events, get_day_busy_times, get_event_details.
  - `gmail_client.py`: Gmail API client. Inherits from `GoogleAPIClient`. Methods: list_messages, get_message, delete_message. Includes JSON structured logging.
  - `config.py`: Configuration management with environment variable overrides. Includes Gmail-specific methods: is_gmail_enabled, has_gmail_scope, validate_gmail_scopes.
  - `scheduler.py`: Scheduling logic for free slot calculations. Uses SearchParameters dataclass.
  - `__init__.py`: Package marker.
- `tests/`
  - `test_caltool.py`: Unit and integration tests for CLI and scheduling logic.
  - `test_cli.py`: CLI and GCalClient tests, including error handling, retry logic, and authentication mocking.
  - `test_backward_compatibility.py`: Tests to ensure Calendar API contract is preserved after refactoring.
  - `test_gmail_client.py`: GMailClient tests with mock Gmail API responses.
  - Other test modules: test_config.py, test_google_auth.py, test_google_client.py, test_format.py, test_errors.py, test_datetime_utils.py.
- `config.json`, `credentials.json`, `token.json`: Configuration and authentication files for Google API.
- `pyproject.toml`, `uv.lock`: Dependency and environment management files.
- `.gitignore`: Standard Python ignores.

## CLI Usage

### Calendar

- `calendarcli free today+1 --duration 30 --pretty` - Find free time slots
- `calendarcli get-calendars` - List all accessible calendars
- `calendarcli show-events thursday+2` - Show upcoming events
- `calendarcli config` - Interactive configuration setup

### Gmail

- `calendarcli gmail list --query "is:unread" --limit 5` - List unread messages
- `calendarcli gmail list --query "from:user@example.com"` - Search messages
- `calendarcli gmail show-message <message_id>` - Show full message details
- `calendarcli gmail show-message <message_id> --format minimal` - Show minimal format
- `calendarcli gmail delete <message_id>` - Delete message (with confirmation)
- `calendarcli gmail delete <message_id> --confirm` - Delete without confirmation

### Date Range Argument

- Accepts intuitive strings: `today`, `today+N`, `tomorrow`, `monday+N`, etc.
- Example: `calendarcli free today+2` finds free slots for today and the next two days.

## Coding Guidelines

- **PEP8**: Use standard Python style conventions.
- **Type Annotations**: Use type hints for all function/method signatures.
- **Docstrings**: Add docstrings to all public functions, classes, and modules.
- **Testing**: All new features and bug fixes should include or update tests in `tests/`. Use mocks for external services (e.g., Google API).
- **Dependency Management**: Use `pyproject.toml` for dependencies. Prefer `uv` for environment management.
- **CLI Design**: Use `click` for CLI commands. Group related commands and provide helpful `--help` messages.
- **Separation of Concerns**: Keep CLI, business logic, formatting, and error handling in separate modules.
- **Error Handling**: Use logging and user-friendly error messages. Use `handle_cli_exception` from `errors.py` for consistent CLI error reporting. Avoid exposing stack traces to end users.
- **Logging**: Prefer structured logging via `logging.getLogger(__name__)`. Log auth flow steps, scope changes, API call parameters (sanitized), and message counts.
- **Configuration**: Store user config in a platform-standard file (e.g., `~/.config/caltool/config.json`).
- **Imports**: Use absolute imports within the package. Avoid circular imports. Always import at the top of the module.
- **Version Control**: Do not commit secrets, credentials, or user-specific config. Respect `.gitignore`.

## Best Practices for Copilot

- When adding new features, update or add tests in `tests/`.
- When fixing bugs, add regression tests if possible.
- When refactoring, ensure all tests pass and code remains modular.
- When updating dependencies, check for compatibility and update lock files.
- When editing CLI commands, ensure help messages and options are clear and consistent.
- When interacting with Google APIs, use mocks in tests to avoid real API calls.
- When refactoring, update documentation and Copilot instructions to reflect new module structure and responsibilities.

## Implementation Strategy

- Focus on one file at a time; within a file, proceed method by method, followed by holistic analysis.
- For each finding, come up with a plan to address it. Layout the plan for each file, but do not implement immediately—instead, provide a prompt that can be used to do the changes later.
- When adding Gmail functionality, ensure scope validation and helpful guidance when missing (`Run 'caltool config' ...`).

## How to Run Tests

- Use `uv run pytest` to run all tests.
- Ensure all tests pass before submitting changes.

---

By following these guidelines, Copilot (and other contributors) can maintain code quality, reliability, and usability for the `calendarcli` project.
