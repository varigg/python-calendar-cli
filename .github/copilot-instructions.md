# Copilot Instructions for calendarcli

## Project Purpose

This project is a command-line tool (`calendarcli`) for managing Google Calendar events and availability. It allows users to:
- Find free time slots across one or more calendars
- List available calendars
- Show upcoming events
- Interact with Google Calendar via the command line

The tool is designed for productivity, automation, and integration into developer workflows.

## Project Structure

- `main.py`: Entry point for the CLI (may delegate to `src/caltool/cli.py`).
- `src/caltool/`
  - `cli.py`: Main CLI logic using `click`. Handles user commands and output formatting.
  - `gcal_client.py`: Handles Google Calendar API interactions.
  - `scheduler.py`: Contains scheduling logic, including finding free slots and checking slot durations.
  - `__init__.py`: Package marker.
- `tests/`
  - `test_caltool.py`: Unit and integration tests for CLI and scheduling logic.
- `config.json`, `credentials.json`, `token.json`: Configuration and authentication files for Google API.
- `pyproject.toml`, `uv.lock`: Dependency and environment management files.
- `.gitignore`: Standard Python ignores.

## Coding Guidelines

- **Follow PEP8**: Use standard Python style conventions for readability and consistency.
- **Type Annotations**: Use type hints for all function/method signatures.
- **Docstrings**: Add docstrings to all public functions, classes, and modules.
- **Testing**: All new features and bug fixes should include or update tests in `tests/`. Use mocks for external services (e.g., Google API).
- **Dependency Management**: Use `pyproject.toml` for dependencies. Prefer `uv` for environment management.
- **CLI Design**: Use `click` for CLI commands. Group related commands and provide helpful `--help` messages.
- **Separation of Concerns**: Keep CLI, business logic, and API interactions in separate modules.
- **Error Handling**: Use logging and user-friendly error messages. Avoid exposing stack traces to end users.
- **Configuration**: Store user config in a file (e.g., `config.json` or `~/.caltool.cfg`). Do not hardcode secrets or credentials.
- **Imports**: Use absolute imports within the package. Avoid circular imports.
- **Version Control**: Do not commit secrets, credentials, or user-specific config. Respect `.gitignore`.

## Best Practices for Copilot

- When adding new features, update or add tests in `tests/`.
- When fixing bugs, add regression tests if possible.
- When refactoring, ensure all tests pass and code remains modular.
- When updating dependencies, check for compatibility and update lock files.
- When editing CLI commands, ensure help messages and options are clear and consistent.
- When interacting with Google APIs, use mocks in tests to avoid real API calls.

## Implementation Strategy
Focus on one file at a time and within a file proceed method by method followed by a holistic analysis of the file. 
For each finding come up with a plan to address it. Layout the plan for each file, but do not implement,
instead provide a prompt that can be used to do the changes later.

## How to Run Tests

- Use `uv run pytest` to run all tests.
- Ensure all tests pass before submitting changes.

---

By following these guidelines, Copilot (and other contributors) can maintain code quality, reliability, and usability for the `calendarcli` project.
