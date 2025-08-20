instead provide a prompt that can be used to do the changes later.

# Copilot Instructions for calendarcli

## Project Purpose

`calendarcli` is a command-line tool for managing Google Calendar events and availability. It enables users to:

- Find free time slots across one or more calendars
- List available calendars
- Show upcoming events
- Interact with Google Calendar via the command line

The tool is designed for productivity, automation, and integration into developer workflows.

## Project Structure

- `main.py`: Entry point for the CLI (may delegate to `src/caltool/cli.py`)
- `src/caltool/`
  - `cli.py`: Main CLI logic using `click`. Handles user commands, argument parsing, and delegates formatting and error handling.
  - `datetime_utils.py`: Date/time parsing and formatting utilities. Supports intuitive range strings (e.g., `today+1`, `thursday+2`).
  - `format.py`: Formatting and color helper functions for CLI output.
  - `errors.py`: Centralized error handling utilities.
  - `gcal_client.py`: Handles Google Calendar API interactions. Now accepts a `Config` object for all credentials and settings.
  - `scheduler.py`: Scheduling logic, including finding free slots and checking slot durations. Uses a `SearchParameters` dataclass.
  - `__init__.py`: Package marker.
- `tests/`
  - `test_caltool.py`: Unit and integration tests for CLI and scheduling logic.
  - `test_cli_gcal.py`: CLI and GCalClient tests, including error handling and dependency injection.
  - Other test modules for config, formatting, and error handling.
- `config.json`, `credentials.json`, `token.json`: Configuration and authentication files for Google API.
- `pyproject.toml`, `uv.lock`: Dependency and environment management files.
- `.gitignore`: Standard Python ignores.

## CLI Usage

- **Find free slots:**  
  `calendarcli free today+1 --duration 30 --pretty`
- **List calendars:**  
  `calendarcli get-calendars`
- **Show events:**  
  `calendarcli show-events thursday+2`
- **Config setup:**  
  `calendarcli config`

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

- Focus on one file at a time; within a file, proceed method by method followed by a holistic analysis.
- For each finding, come up with a plan to address it. Layout the plan for each file, but do not implement immediately—instead, provide a prompt that can be used to do the changes later.

## How to Run Tests

- Use `uv run pytest` to run all tests.
- Ensure all tests pass before submitting changes.

---

By following these guidelines, Copilot (and other contributors) can maintain code quality, reliability, and usability for the `calendarcli` project.
