<!--
SYNC IMPACT REPORT (v1.0.0 - Initial Ratification)
=================================================
Initial Constitution adoption for calendarcli project.

Version: 0.0.0 → 1.0.0 (MAJOR: Initial ratification)
Principles: 5 core principles established
  1. Separation of Concerns (CLI, business logic, formatting, error handling isolated)
  2. Test-First Development (TDD mandatory, mocks for external services)
  3. Type Safety & Documentation (type hints and docstrings required)
  4. CLI-First Design (click framework, intuitive UX, text I/O protocols)
  5. PEP8 & Best Practices (code style, imports, version control)

New Sections:
  - Error Handling & Observability (centralized exception handling, logging, configuration)
  - Development Standards (dependencies, testing, version control, refactoring)
  - Governance (amendment procedure, versioning policy, compliance review)

Templates Updated:
  ✅ plan-template.md - References Constitution Check gate
  ✅ spec-template.md - Aligned with project requirements format
  ✅ tasks-template.md - Task organization supports principle-driven development

No deferred TODO items. All placeholders resolved from project context.
-->

# calendarcli Constitution

## Core Principles

### I. Separation of Concerns (NON-NEGOTIABLE)

CLI logic, business logic, formatting, error handling, and external service interactions MUST be isolated in separate modules. Each module has a single responsibility and clear contracts with other modules. This enables independent testing, maintainability, and code reuse.

**Rationale**: The project is organized into `cli.py`, `scheduler.py`, `format.py`, `errors.py`, and `gcal_client.py`. Each module must respect these boundaries to ensure code clarity and testability.

### II. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written before implementation (TDD mandatory). Tests MUST fail first, then code is written to pass them. External services (Google Calendar API) MUST use mocks in tests to avoid real API calls during development and testing. All new features and bug fixes require corresponding tests.

**Rationale**: Ensures code is testable by design, catches regressions early, and builds confidence in refactoring and maintenance.

### III. Type Safety & Documentation (MUST)

All function and method signatures MUST include type hints. All public functions, classes, and modules MUST have docstrings explaining purpose, parameters, and return values. No type inference without explicit annotations—clarity is required for maintainability.

**Rationale**: Type hints and docstrings improve IDE support, catch errors during development, and serve as living documentation for future contributors.

### IV. CLI-First Design (MUST)

Every feature MUST be accessible via CLI using the `click` framework. CLI output MUST support both human-readable and JSON formats where applicable. Arguments MUST be intuitive (e.g., `today+1` for date ranges). Help messages and option descriptions MUST be clear and concise.

**Rationale**: The project is CLI-first by design. All functionality must be discoverable and usable from the command line with minimal friction.

### V. PEP8 & Best Practices (MUST)

Code MUST follow PEP8 style conventions. Imports MUST be absolute (not relative) within the package and ordered logically. Circular imports are forbidden. Configuration MUST be stored in platform-standard locations (e.g., `~/.config/caltool/config.json` on Linux). Secrets and user-specific config MUST NOT be committed to version control—respect `.gitignore`.

**Rationale**: Consistent style, clear imports, and secure configuration management make the codebase professional and maintainable.

## Error Handling & Observability

**Centralized Exception Handling**: All CLI exceptions MUST be handled via `handle_cli_exception` from `errors.py`. Error messages MUST be user-friendly and MUST NOT expose internal stack traces to end users.

**Logging**: Structured logging SHOULD be used for internal debugging and troubleshooting. Log levels MUST be appropriate (DEBUG for development, INFO/WARNING for production).

**Configuration Management**: Configuration values CAN be overridden by environment variables (e.g., `CALTOOL_TIME_ZONE`). The `config` command MUST provide interactive setup for all required settings.

**Rationale**: Users trust the tool when errors are clear and non-technical. Internal logging enables debugging without compromising user experience.

## Development Standards

**Dependency Management**: Dependencies MUST be declared in `pyproject.toml`. Use `uv` for environment management and `uv run pytest` for testing. Pin dependencies in `uv.lock`.

**Testing Framework**: Tests MUST use `pytest`. Test files MUST mirror the source structure (e.g., `tests/test_cli.py` for `src/caltool/cli.py`). Integration tests MAY use mocks to simulate Google Calendar API responses.

**Version Control**: Do NOT commit `config.json`, `credentials.json`, `token.json`, or `.env` files. Ensure `.gitignore` is respected by all contributors.

**Refactoring**: When refactoring, ensure all tests pass before and after changes. Update this constitution and Copilot instructions if module responsibilities change.

## Governance

**Amendment Procedure**: Changes to this constitution MUST be documented in a Pull Request with a summary of:

- Which principle(s) changed or why
- Version number (using semantic versioning: MAJOR.MINOR.PATCH)
- Justification for the change

**Version Policy**:

- **MAJOR**: Backward-incompatible changes to principles or removal of required practices
- **MINOR**: New principles added or existing guidance materially expanded
- **PATCH**: Clarifications, typo fixes, non-semantic refinements

**Compliance Review**: All PRs MUST verify compliance with these principles before merging. Code reviews SHOULD check:

- Does the change respect separation of concerns?
- Are new features tested first?
- Are type hints and docstrings present?
- Is CLI design intuitive and documented?
- Does the code follow PEP8?

**Runtime Guidance**: This constitution supersedes all other practices. For implementation details not covered here, refer to `.github/copilot-instructions.md`.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
