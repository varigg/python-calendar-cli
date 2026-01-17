# Feature Specification: Remove Google Auth Exception Dependencies from CLI

**Feature Branch**: `005-remove-auth-cli-dependency`
**Created**: January 17, 2026
**Status**: Draft
**Input**: User description: "Remove Google Auth exception dependencies from CLI layer - CLI should not import google.auth.exceptions directly. Add AuthenticationError to errors.py and wrap exceptions in GoogleAPIClient."

## User Scenarios & Testing

### User Story 1 - Clean Architectural Boundaries (Priority: P1)

As a developer, I want the CLI layer to be independent of Google's auth library implementation details so that I can maintain clean separation of concerns and easily swap auth providers in the future.

**Why this priority**: Violates dependency inversion principle. CLI depends on infrastructure details (google.auth.exceptions) when it should only depend on domain abstractions (CLIError and subclasses).

**Independent Test**: After refactor, `grep -r "google.auth" src/gtool/cli/` returns no matches. All auth errors surface as domain exceptions (`AuthenticationError`).

**Acceptance Scenarios**:

1. **Given** a Google auth error occurs, **When** the client layer catches it, **Then** it raises `AuthenticationError(CLIError)` instead
2. **Given** CLI commands encounter auth errors, **When** they catch exceptions, **Then** they only catch `CLIError` (not `google.auth.exceptions.GoogleAuthError`)
3. **Given** the refactored codebase, **When** developer inspects CLI imports, **Then** no Google auth imports exist
4. **Given** all existing CLI commands, **When** auth fails, **Then** user sees the same error messages as before

---

### User Story 2 - Consistent Error Handling (Priority: P2)

As a CLI user, I want authentication errors to be handled consistently across all commands so that I understand what went wrong regardless of which command I'm using.

**Why this priority**: User-facing benefit. Consistent error messages improve user experience and debugging.

**Independent Test**: Trigger auth failures in different commands (free, gmail list, get-calendars) - all should show similar error formatting and guidance.

**Acceptance Scenarios**:

1. **Given** expired credentials, **When** user runs `gtool free today`, **Then** error message clearly indicates authentication failure
2. **Given** revoked credentials, **When** user runs `gtool gmail list`, **Then** error message is consistent with other commands
3. **Given** missing credentials file, **When** user runs any command, **Then** error message guides user to run `gtool config`

---

### Edge Cases

- What happens when `google.auth.exceptions.GoogleAuthError` has a message with sensitive info? (AuthenticationError should sanitize/wrap appropriately)
- How does system handle auth errors during token refresh vs. initial auth?
- What if GoogleAPIClient catches multiple exception types - do they all become AuthenticationError or should there be subclasses?

## Requirements

### Functional Requirements

**Exception Handling**:

- **FR-001**: CLI layer MUST NOT import `google.auth.exceptions` directly
- **FR-002**: New `AuthenticationError(CLIError)` MUST be added to `gtool/cli/errors.py`
- **FR-003**: `GoogleAPIClient` MUST catch `google.auth.exceptions.GoogleAuthError` and convert to `AuthenticationError`
- **FR-004**: All CLI commands MUST catch only `CLIError` and its subclasses (not Google exceptions)
- **FR-005**: Error messages to users MUST remain unchanged (backward compatible user experience)

**Architecture**:

- **FR-006**: CLI → Core → Clients → Infrastructure dependency flow MUST be preserved
- **FR-007**: Infrastructure details (Google auth exceptions) MUST NOT leak to CLI layer
- **FR-008**: All existing tests MUST pass (95+ tests)
- **FR-009**: Auth error handling MUST be centralized in `GoogleAPIClient` base class

### Non-Functional Requirements

**NFR-001**: Code changes MUST follow existing error handling patterns (using `handle_cli_exception`)
**NFR-002**: All type hints MUST be preserved
**NFR-003**: Docstrings MUST be updated to reflect new exception types
**NFR-004**: No changes to user-facing behavior (CLI output, error messages stay the same)

### Key Entities

- **AuthenticationError**: New domain exception class inheriting from CLIError, represents authentication failures regardless of auth provider
- **GoogleAPIClient**: Base class for all API clients - becomes the exception translation boundary
- **CLI commands**: 6 command functions (cli, free, get_calendars, show_events, gmail commands) that currently catch google.auth exceptions

### Technical Constraints

- Python 3.12.11
- Must maintain 80%+ test coverage
- All 95+ tests must pass
- No breaking changes to public API
- Module-level imports preserved for readability (no lazy imports needed if google.auth not imported in CLI)

## Out of Scope

- Changing actual error messages (only exception types change)
- Refactoring retry logic (separate concern)
- Adding new auth providers (future feature)
- Changing config file locations or formats
- Performance optimizations (not needed if architecture is clean)

## Success Criteria

1. ✅ No `google.auth` imports in `src/gtool/cli/`
2. ✅ All CLI commands catch only `CLIError` and subclasses
3. ✅ New `AuthenticationError` class exists and is used
4. ✅ All 95+ tests pass
5. ✅ User-facing behavior unchanged (error messages identical)
6. ✅ Code follows dependency inversion principle (CLI depends on abstractions, not implementation details)

## Dependencies & Integration Points

**Modified Files**:

- `src/gtool/cli/errors.py` - Add AuthenticationError class
- `src/gtool/infrastructure/google_client.py` - Add exception wrapping in base class
- `src/gtool/cli/main.py` - Remove google.auth imports, update exception handling

**Test Files**:

- `tests/test_cli.py` - Update mocked exceptions
- `tests/test_google_client.py` - Verify exception translation
- `tests/test_errors.py` - Test new AuthenticationError class

## Risk Assessment

**Low Risk**: Internal refactor only. No user-facing changes. Well-defined scope.

**Mitigation**:

- Comprehensive test coverage ensures behavior preservation
- Exception messages remain identical
- Gradual rollout via feature branch
- All changes reviewed before merge
