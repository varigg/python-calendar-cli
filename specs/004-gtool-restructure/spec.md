# Feature Specification: Rename to gtool with Layered Directory Architecture

**Feature Branch**: `004-gtool-restructure`
**Created**: January 16, 2026
**Status**: Ready for Implementation
**Backward Compatibility**: Clean break (no `caltool` alias; user aware via package distribution)
**Input**: User description: "Restructure caltool to gtool with layered directory architecture. Rename the tool since it now does more than just calendar access."

## User Scenarios & Testing

### User Story 1 - CLI Rename to gtool (Priority: P1)

As a user, I want to invoke the tool as `gtool` instead of `caltool` so that the name reflects its broader capabilities (Calendar + Gmail).

**Why this priority**: User-facing change that defines the product identity. All other changes are internal.

**Independent Test**: After installation, running `gtool --help` displays the CLI help. Running `caltool` either works (backward compat) or shows a clear deprecation message.

**Acceptance Scenarios**:

1. **Given** the tool is installed, **When** user runs `gtool --help`, **Then** CLI help is displayed with all commands
2. **Given** the tool is installed, **When** user runs `gtool free today`, **Then** free time slots are displayed (same behavior as before)
3. **Given** the tool is installed, **When** user runs `gtool gmail list`, **Then** Gmail messages are listed (same behavior as before)
4. **Given** the tool is installed, **When** user runs `gtool config`, **Then** interactive configuration works as before

---

### User Story 2 - Layered Directory Structure (Priority: P2)

As a developer, I want the codebase organized into clear layers (cli, core, clients, infrastructure, config, utils) so that I can understand and navigate the code by responsibility.

**Why this priority**: Improves maintainability and onboarding. Internal change that doesn't affect users.

**Independent Test**: All 95 existing tests pass after restructure. Import paths are cleaner and follow layer conventions.

**Acceptance Scenarios**:

1. **Given** the restructured codebase, **When** developer imports from `gtool.clients`, **Then** CalendarClient and GmailClient are available
2. **Given** the restructured codebase, **When** developer imports from `gtool.core`, **Then** Scheduler and SearchParameters are available
3. **Given** the restructured codebase, **When** developer imports from `gtool.infrastructure`, **Then** GoogleAuth, RetryPolicy, ServiceFactory are available
4. **Given** the restructured codebase, **When** all tests run, **Then** 95+ tests pass with no failures

---

### User Story 3 - Simplified Class Names (Priority: P3)

As a developer, I want classes named without legacy suffixes (e.g., `CalendarClient` not `GCalClientV2`) so that the codebase feels clean and modern.

**Why this priority**: Polish/cleanup. Can be done during restructure or after.

**Independent Test**: All references to old class names are removed. New names are used consistently.

**Acceptance Scenarios**:

1. **Given** the restructured codebase, **When** developer looks for Calendar client, **Then** it's named `CalendarClient` in `gtool.clients.calendar`
2. **Given** the restructured codebase, **When** developer looks for Gmail client, **Then** it's named `GmailClient` in `gtool.clients.gmail`
3. **Given** the restructured codebase, **When** developer looks for retry logic, **Then** it's in `gtool.infrastructure.retry` as `RetryPolicy`

---

### Edge Cases

- Config files in `~/.config/caltool/` continue to work (config path unchanged)
- Users with `caltool` in scripts will need to update to `gtool` (intentional clean break)
- Package identity changes; distribution will be under `gtool` package on PyPI

## Requirements

### Functional Requirements

**Package Rename**:

- **FR-001**: Package MUST be renamed from `caltool` to `gtool`
- **FR-002**: CLI entry point MUST be `gtool` (defined in pyproject.toml)
- **FR-003**: All internal imports MUST use `gtool` package name

**Directory Structure**:

- **FR-004**: Source MUST be organized into layered directories: `cli/`, `core/`, `clients/`, `infrastructure/`, `config/`, `utils/`
- **FR-005**: Each layer package MUST have `__init__.py` with public API exports
- **FR-006**: Dependencies MUST flow inward: cli → core → clients → infrastructure

**Backward Compatibility**:

- **FR-007**: All existing CLI commands MUST work unchanged (`free`, `show-events`, `get-calendars`, `gmail list`, `gmail show-message`, `gmail delete`, `config`)
- **FR-008**: Config file location (`~/.config/caltool/`) remains unchanged (users with existing configs unaffected)
- **FR-009**: All 95+ existing tests MUST pass after migration
- **FR-010**: `caltool` command is NOT provided (clean break). Users with existing scripts will see "command not found". New package distributed as `gtool` only; user awareness is built-in to installation mechanism (`uv tool install gtool`)

**Class Naming**:

- **FR-011**: `GCalClientV2` MUST be renamed to `CalendarClient`
- **FR-012**: `GMailClientV2` MUST be renamed to `GmailClient`
- **FR-013**: File names MUST be simplified (e.g., `calendar.py` not `gcal_client_v2.py`)

### Key Entities

- **Layer Packages**: cli, core, clients, infrastructure, config, utils - each with distinct responsibility
- **Public API**: Exports from each `__init__.py` that consumers can rely on

## Success Criteria

### Measurable Outcomes

- **SC-001**: `gtool --help` works and displays all commands
- **SC-002**: All 95+ tests pass after restructure
- **SC-003**: No circular imports detected (verified by running tests and linting)
- **SC-004**: Import statements follow layer conventions (cli imports from core, core from clients, etc.)
- **SC-005**: `pip install .` or `uv pip install .` installs `gtool` command successfully
- **SC-006**: Coverage remains at 81% or higher

### Target Directory Structure

```
src/gtool/
├── __init__.py                    # Package exports
├── cli/                           # Presentation Layer
│   ├── __init__.py
│   ├── main.py                    # Click CLI groups & commands
│   ├── formatters.py              # Output formatting (tables, colors)
│   └── errors.py                  # CLI error handling & display
│
├── core/                          # Domain/Business Logic
│   ├── __init__.py
│   ├── scheduler.py               # Free time calculation logic
│   └── models.py                  # Domain models (SearchParameters)
│
├── clients/                       # External API Clients
│   ├── __init__.py
│   ├── calendar.py                # CalendarClient
│   └── gmail.py                   # GmailClient
│
├── infrastructure/                # Cross-cutting Infrastructure
│   ├── __init__.py
│   ├── auth.py                    # GoogleAuth
│   ├── service_factory.py         # Google API service builder
│   ├── retry.py                   # RetryPolicy
│   └── error_categorizer.py       # HTTP error classification
│
├── config/                        # Configuration Management
│   ├── __init__.py
│   └── settings.py                # Config class, defaults, validation
│
└── utils/                         # Pure Utilities
    ├── __init__.py
    └── datetime.py                # Date/time parsing helpers
```
