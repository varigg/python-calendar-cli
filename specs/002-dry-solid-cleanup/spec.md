# Feature Specification: DRY/SOLID Code Cleanup

**Feature Branch**: `002-dry-solid-cleanup`  
**Created**: January 15, 2026  
**Status**: Draft  
**Input**: User description: "Refactor codebase to address DRY, YAGNI, KISS, and SOLID principle violations identified in code review"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainable Codebase for Contributors (Priority: P1)

As a developer contributing to calendarcli, I want the codebase to follow DRY principles so that when I need to modify retry logic or error handling, I only need to change code in one place.

**Why this priority**: Duplicate code is the highest-risk issue—bugs fixed in one location may not be fixed in duplicates, leading to inconsistent behavior and maintenance burden.

**Independent Test**: Can be verified by searching for duplicate method signatures and confirming each pattern exists exactly once. Running the existing test suite confirms no regressions.

**Acceptance Scenarios**:

1. **Given** the `GoogleAPIClient` class, **When** I search for retry implementations, **Then** I find exactly one retry decorator/method (not two duplicates)
2. **Given** the `Config` class, **When** I search for `is_gmail_enabled` method definitions, **Then** I find exactly one definition
3. **Given** the `Config` class, **When** I search for `has_gmail_scope` method definitions, **Then** I find exactly one definition
4. **Given** the `Config` class, **When** I search for `validate_gmail_scopes` method definitions, **Then** I find exactly one definition

---

### User Story 2 - Clean Error Handling (Priority: P2)

As a developer debugging issues, I want exception handling to catch specific exceptions so that unexpected bugs propagate with full stack traces rather than being silently converted to generic error messages.

**Why this priority**: Overly broad exception handling masks bugs and makes debugging difficult. Specific exception handling improves developer experience.

**Independent Test**: Verify CLI commands catch `CLIError` and auth exceptions specifically, allowing other exceptions to propagate for debugging.

**Acceptance Scenarios**:

1. **Given** a CLI command encounters a `CLIError`, **When** the exception is caught, **Then** a user-friendly message is displayed and the command aborts cleanly
2. **Given** a CLI command encounters an unexpected `TypeError`, **When** the exception occurs, **Then** the full stack trace is visible for debugging (not silently absorbed)

---

### User Story 3 - Dead Code Removal (Priority: P3)

As a developer reading the codebase, I want unused functions removed so that I don't waste time understanding code that is never executed.

**Why this priority**: Dead code adds cognitive load but doesn't affect runtime behavior. Lower priority than functional issues.

**Independent Test**: Search for removed function names across the codebase and confirm zero usages exist.

**Acceptance Scenarios**:

1. **Given** the `errors.py` module, **When** I look for the `cli_error()` function, **Then** it does not exist (removed as unused)
2. **Given** the `GoogleAPIClient` class, **When** I look for `retry_on_exception()` method, **Then** it does not exist (removed as unused duplicate)

---

### User Story 4 - Consistent Import Patterns (Priority: P4)

As a developer reading the codebase, I want all imports at module level so that dependencies are immediately visible and the code style is consistent.

**Why this priority**: Style consistency improves readability but has no functional impact. Lowest priority.

**Independent Test**: Verify no function-level imports exist (except for circular dependency avoidance).

**Acceptance Scenarios**:

1. **Given** the `format.py` module, **When** I check `print_events_grouped_by_date()`, **Then** `defaultdict` is imported at module level, not inside the function
2. **Given** the `gmail_client.py` module, **When** I check `_validate_config()`, **Then** there is no local import of `CLIError`

---

### Edge Cases

- What happens when removing duplicate methods if they have slightly different implementations? **Answer**: The more complete/correct version is kept.
- How does removing broad exception handling affect existing error messages? **Answer**: `CLIError` is still caught and handled gracefully; only unexpected exceptions propagate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST have exactly one implementation of retry logic in `GoogleAPIClient` (the `@retry` static decorator)
- **FR-002**: System MUST have exactly one definition of each Config method (`is_gmail_enabled`, `has_gmail_scope`, `validate_gmail_scopes`)
- **FR-003**: System MUST NOT contain the unused `cli_error()` function in `errors.py`
- **FR-004**: System MUST NOT contain the unused `retry_on_exception()` method in `GoogleAPIClient`
- **FR-005**: CLI commands MUST catch `CLIError` specifically rather than bare `Exception`
- **FR-006**: CLI commands MUST catch `google.auth.exceptions.GoogleAuthError` for authentication errors
- **FR-007**: All module-level imports MUST be at the top of each file (no function-level imports except for documented circular dependency cases)
- **FR-008**: The `_validate_config()` method MUST NOT be marked `@abstractmethod` since it has a concrete implementation
- **FR-009**: `GCalClient._validate_config()` SHOULD be removed if it only calls `super()` with no additional logic
- **FR-010**: All existing tests MUST continue to pass after refactoring

### Key Entities

- **GoogleAPIClient**: Abstract base class providing shared authentication, retry decorator, and error handling for all Google API clients
- **Config**: Configuration management class handling settings, environment overrides, and Gmail scope validation
- **CLIError**: Custom exception for user-friendly CLI error reporting

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero duplicate method definitions exist in the codebase (verified by static analysis)
- **SC-002**: All existing tests pass with 100% success rate after refactoring
- **SC-003**: Code search for removed functions (`cli_error`, `retry_on_exception`) returns zero results
- **SC-004**: Pylint/flake8 reports zero "duplicate code" warnings for the refactored modules
- **SC-005**: Function-level imports reduced to zero (or documented exceptions only)
- **SC-006**: Developer can modify retry behavior by changing code in exactly one location

## Assumptions

- The second definition of duplicate methods (later in the file) is the authoritative version to keep
- The `@retry` static decorator is the preferred retry implementation (used by all API methods)
- Removing broad `Exception` catching will not break existing user-facing error messages for known error types
- No circular import issues will arise from moving function-level imports to module level

## Out of Scope

- Splitting `google_auth.py` into smaller modules (629 lines) - tracked separately as a larger refactor
- Adding a Protocol type hint for `Scheduler.client` - minor type safety improvement for future work
- Refactoring test files to match new patterns
