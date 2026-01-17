# Implementation Plan: gtool Restructure

**Branch**: `004-gtool-restructure` | **Date**: January 16, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-gtool-restructure/spec.md`

## Summary

Rename `caltool` to `gtool` and restructure the codebase into a layered directory architecture. The package name, CLI entry point, and all imports will change from `caltool` to `gtool`. Source code will be organized into six layer packages (cli, core, clients, infrastructure, config, utils) following modern Python best practices. Class names will be simplified (e.g., `GCalClientV2` → `CalendarClient`).

**Technical Approach**:

1. Create new `src/gtool/` directory structure with layer packages
2. Move files to appropriate layers, updating imports progressively (8-phase plan)
3. Rename classes and simplify file names
4. Update `pyproject.toml` entry points and package configuration
5. Update all test imports
6. Verify 95+ tests pass with 81%+ coverage

## Technical Context

**Language/Version**: Python 3.12.11
**Primary Dependencies**: google-auth, google-auth-oauthlib, google-api-python-client, click 8.x, pytest 8.3.5
**Storage**: N/A (token persistence via config files at `~/.config/caltool/`)
**Testing**: pytest with 95 tests, 81% coverage, dependency injection pattern
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single Python CLI application
**Performance Goals**: No degradation from restructure; tests < 5s
**Constraints**: All CLI commands must work unchanged; config path preserved
**Scale/Scope**: ~900 LOC across 13 modules; 95 tests; two Google API clients

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

✅ **I. Separation of Concerns**: Layered architecture directly implements this principle. Each layer (cli, core, clients, infrastructure, config, utils) has single responsibility with clear boundaries.

✅ **II. Test-First Development**: All 95 existing tests will be migrated. Test structure will mirror new source structure.

✅ **III. Type Safety & Documentation**: All type hints and docstrings preserved during migration. New `__init__.py` files will have module docstrings.

✅ **IV. CLI-First Design**: CLI commands unchanged. Entry point moves from `caltool` to `gtool` in `pyproject.toml`.

✅ **V. PEP8 & Best Practices**: Imports will be cleaner with layer-based organization. All imports will use `gtool` package name.

**Gate Status**: ✅ PASS - Feature strengthens Separation of Concerns principle.

## Project Structure

### Documentation (this feature)

```text
specs/004-gtool-restructure/
├── plan.md              # This file
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Task breakdown (to be created)
```

### Source Code - Current State

```text
src/caltool/
├── __init__.py
├── cli.py                  → gtool/cli/main.py
├── format.py               → gtool/cli/formatters.py
├── errors.py               → gtool/cli/errors.py
├── scheduler.py            → gtool/core/scheduler.py
├── gcal_client_v2.py       → gtool/clients/calendar.py (rename class)
├── gmail_client_v2.py      → gtool/clients/gmail.py (rename class)
├── google_auth.py          → gtool/infrastructure/auth.py
├── service_factory.py      → gtool/infrastructure/service_factory.py
├── retry_policy.py         → gtool/infrastructure/retry.py
├── error_categorizer.py    → gtool/infrastructure/error_categorizer.py
├── config.py               → gtool/config/settings.py
└── datetime_utils.py       → gtool/utils/datetime.py
```

### Source Code - Target State

```text
src/gtool/
├── __init__.py                    # Package exports (version, main CLI)
│
├── cli/                           # Presentation Layer
│   ├── __init__.py               # Exports: cli (main group)
│   ├── main.py                   # Click CLI groups & commands
│   ├── formatters.py             # Output formatting (tables, colors)
│   └── errors.py                 # CLI error handling & display
│
├── core/                          # Domain/Business Logic
│   ├── __init__.py               # Exports: Scheduler, SearchParameters
│   ├── scheduler.py              # Free time calculation logic
│   └── models.py                 # Domain models (SearchParameters extracted)
│
├── clients/                       # External API Clients
│   ├── __init__.py               # Exports: CalendarClient, GmailClient
│   ├── calendar.py               # CalendarClient (was GCalClientV2)
│   └── gmail.py                  # GmailClient (was GMailClientV2)
│
├── infrastructure/                # Cross-cutting Infrastructure
│   ├── __init__.py               # Exports: GoogleAuth, RetryPolicy, etc.
│   ├── auth.py                   # GoogleAuth
│   ├── service_factory.py        # Google API service builder
│   ├── retry.py                  # RetryPolicy
│   └── error_categorizer.py      # HTTP error classification
│
├── config/                        # Configuration Management
│   ├── __init__.py               # Exports: Config, DEFAULTS
│   └── settings.py               # Config class, defaults, validation
│
└── utils/                         # Pure Utilities
    ├── __init__.py               # Exports: parse_date_range, etc.
    └── datetime.py               # Date/time parsing helpers
```

**Structure Decision**: Single Python CLI application with layered internal organization. Six layer packages with clear responsibilities and dependency flow (cli → core → clients → infrastructure).

## Migration Strategy

### Phase 1: Infrastructure Layer (No Dependencies on Other Layers)

Migrate infrastructure components first since they have no internal dependencies:

1. `error_categorizer.py` → `gtool/infrastructure/error_categorizer.py`
2. `retry_policy.py` → `gtool/infrastructure/retry.py`
3. `service_factory.py` → `gtool/infrastructure/service_factory.py`
4. `google_auth.py` → `gtool/infrastructure/auth.py`

### Phase 2: Config and Utils Layers

These have minimal dependencies:

1. `config.py` → `gtool/config/settings.py`
2. `datetime_utils.py` → `gtool/utils/datetime.py`

### Phase 3: Clients Layer (Depends on Infrastructure)

Rename classes during migration:

1. `gcal_client_v2.py` → `gtool/clients/calendar.py` (GCalClientV2 → CalendarClient)
2. `gmail_client_v2.py` → `gtool/clients/gmail.py` (GMailClientV2 → GmailClient)

### Phase 4: Core Layer (Depends on Clients)

1. Extract `SearchParameters` to `gtool/core/models.py`
2. `scheduler.py` → `gtool/core/scheduler.py`

### Phase 5: CLI Layer (Depends on All)

1. `errors.py` → `gtool/cli/errors.py`
2. `format.py` → `gtool/cli/formatters.py`
3. `cli.py` → `gtool/cli/main.py`

### Phase 6: Finalization

1. Update `pyproject.toml` (package name, entry points)
2. Migrate all tests to new structure
3. Delete old `src/caltool/` directory
4. Final verification

## Complexity Tracking

> **No Constitution violations. No complexity trade-offs needed.**

This refactor simplifies the codebase by introducing clear layer boundaries.

## File Mapping Reference

| Old Path                                  | New Path                                    | Class Rename                  |
| ----------------------------------------- | ------------------------------------------- | ----------------------------- |
| `caltool/__init__.py`                     | `gtool/__init__.py`                         | -                             |
| `caltool/cli.py`                          | `gtool/cli/main.py`                         | -                             |
| `caltool/format.py`                       | `gtool/cli/formatters.py`                   | -                             |
| `caltool/errors.py`                       | `gtool/cli/errors.py`                       | -                             |
| `caltool/scheduler.py`                    | `gtool/core/scheduler.py`                   | -                             |
| `caltool/scheduler.py` (SearchParameters) | `gtool/core/models.py`                      | -                             |
| `caltool/gcal_client_v2.py`               | `gtool/clients/calendar.py`                 | GCalClientV2 → CalendarClient |
| `caltool/gmail_client_v2.py`              | `gtool/clients/gmail.py`                    | GMailClientV2 → GmailClient   |
| `caltool/google_auth.py`                  | `gtool/infrastructure/auth.py`              | -                             |
| `caltool/service_factory.py`              | `gtool/infrastructure/service_factory.py`   | -                             |
| `caltool/retry_policy.py`                 | `gtool/infrastructure/retry.py`             | -                             |
| `caltool/error_categorizer.py`            | `gtool/infrastructure/error_categorizer.py` | -                             |
| `caltool/config.py`                       | `gtool/config/settings.py`                  | -                             |
| `caltool/datetime_utils.py`               | `gtool/utils/datetime.py`                   | -                             |
