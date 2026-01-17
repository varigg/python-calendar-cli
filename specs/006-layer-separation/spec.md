# Feature Specification: Layer Separation Enforcement

**Feature Branch**: `006-layer-separation`
**Created**: 2026-01-17
**Status**: Draft
**Input**: User description: "Remove UI layer dependencies from infrastructure and config layers to enforce separation of concerns"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Infrastructure Reusability in Non-CLI Contexts (Priority: P1)

Developers building alternative interfaces (GUI, web API, batch scripts) need to reuse the authentication and retry infrastructure without pulling in CLI dependencies. Currently, the infrastructure layer imports `click` and CLI-specific errors, preventing clean reuse.

**Why this priority**: This is the most critical violation blocking reuse. Infrastructure should be the foundation layer usable by any presentation layer.

**Independent Test**: Can be fully tested by importing `gtool.infrastructure.auth` and `gtool.infrastructure.retry` in a non-CLI Python script without requiring `click` installation, and verifying authentication and retry operations work without CLI errors.

**Acceptance Scenarios**:

1. **Given** a Python script that imports `gtool.infrastructure.auth`, **When** the script authenticates without CLI context, **Then** authentication succeeds without requiring `click` or CLI error types
2. **Given** a retry operation encounters an authentication error, **When** retry logic wraps the error, **Then** it raises an infrastructure-level exception (e.g., `AuthError`), not `CLIError` or `AuthenticationError`
3. **Given** infrastructure modules are imported, **When** examining dependencies, **Then** no `click` import or CLI layer reference exists in infrastructure code

---

### User Story 2 - Config Layer Testability and Reusability (Priority: P2)

Developers and automated tests need to read, validate, and modify configuration without interactive prompts or CLI dependencies. Currently, `Config.prompt()` uses `click.prompt` and `click.echo`, making the config layer unusable in non-interactive contexts.

**Why this priority**: Config is a data layer that should be pure validation and persistence. Interactive input belongs in the UI layer.

**Independent Test**: Can be fully tested by creating, validating, and persisting a `Config` object programmatically in a test without any `click` imports, and verifying all validation rules enforce correctly without CLI exceptions.

**Acceptance Scenarios**:

1. **Given** a config object with invalid Gmail scopes, **When** validation runs, **Then** it raises a domain exception (not `click.UsageError`)
2. **Given** a programmatic config update, **When** config is saved, **Then** no interactive prompts appear and no `click` methods are invoked
3. **Given** a test suite importing config, **When** running tests, **Then** no `click` dependency is required

---

### User Story 3 - CLI Error Mapping from Infrastructure (Priority: P3)

CLI users encountering infrastructure errors (auth failures, API errors) should see user-friendly CLI-formatted messages. The CLI layer maps infrastructure exceptions to CLI errors with helpful formatting and guidance.

**Why this priority**: This enables proper error presentation after removing CLI dependencies from infrastructure. It's dependent on P1 being completed first.

**Independent Test**: Can be fully tested by triggering infrastructure errors (mock auth failure, API error) and verifying CLI catches and translates them to appropriate `CLIError` or `AuthenticationError` with user-facing messages.

**Acceptance Scenarios**:

1. **Given** infrastructure raises `AuthError` during authentication, **When** CLI catches the error, **Then** it displays a user-friendly `AuthenticationError` message
2. **Given** infrastructure raises `ServiceError` during API call, **When** CLI catches the error, **Then** it displays an appropriate `CLIError` with context
3. **Given** config validation raises domain exception, **When** CLI catches it, **Then** it converts to `click.UsageError` with helpful guidance

---

### Edge Cases

- What happens when infrastructure errors occur in non-CLI contexts (e.g., API server)? They should propagate as infrastructure exceptions, not CLI errors.
- How does the system handle migration of existing error handling code that expects CLI exceptions from infrastructure? Need clear mapping in CLI layer.
- What if tests were written expecting `click.UsageError` from config? Tests need updating to expect domain exceptions.
- How does exception translation handle authentication scope errors (403 insufficient permissions)?
- What happens when credentials file is missing or invalid during infrastructure initialization?
- How does the system handle token refresh failures in non-CLI contexts?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Infrastructure layer (`gtool.infrastructure.*`) MUST NOT import UI frameworks (`click`) or CLI-specific error types
- **FR-002**: Infrastructure authentication errors MUST raise infrastructure-level exceptions (e.g., `AuthError`) instead of `CLIError` or `AuthenticationError`
- **FR-003**: Config layer (`gtool.config.*`) MUST NOT contain interactive prompting logic (`click.prompt`, `click.echo`)
- **FR-004**: Config validation MUST raise domain/config exceptions instead of `click.UsageError`
- **FR-005**: CLI layer MUST map infrastructure exceptions to CLI-specific errors with user-facing messages
- **FR-006**: CLI layer MUST handle interactive configuration prompting (moved from config layer)
- **FR-007**: All infrastructure and config modules MUST remain independently testable without CLI dependencies
- **FR-008**: Existing CLI functionality MUST remain unchanged from user perspective (same commands, same outputs)
- **FR-009**: Integration tests MUST verify the full flow from CLI → auth → service factory → clients without over-mocking
- **FR-010**: Exception translation MUST preserve error context for debugging while providing user-friendly messages

### Key Entities

- **Infrastructure Exceptions**: New exception types (`AuthError`, `ServiceError`) that represent infrastructure-level failures without UI coupling
- **Config**: Pure data container with validation logic that raises domain exceptions (e.g., `ConfigValidationError`)
- **CLI Error Handlers**: Mapping functions in CLI layer that translate infrastructure/config exceptions to CLI-formatted errors

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Infrastructure modules can be imported and used in non-CLI Python scripts without requiring `click` installation (0 `click` imports in infrastructure layer)
- **SC-002**: Config layer can be tested programmatically without any interactive prompts (100% test coverage without mocking `click`)
- **SC-003**: All existing CLI tests pass without modification (regression test suite passes at 100%)
- **SC-004**: Code can be reused in at least one non-CLI context (e.g., test demonstrating API server using infrastructure)
- **SC-005**: Developers can understand error flow by following exception mapping from infrastructure → CLI (clear documentation of exception hierarchy)
- **SC-006**: Integration tests verify factory/auth/config flow catches real bugs (mocks only external Google API calls)

## Assumptions

- CLI layer remains the only interactive interface in the current scope (no GUI/API implementation required)
- Error messages to end users remain unchanged (backward compatibility)
- Existing test suite provides adequate regression coverage
- Standard Python exception patterns are acceptable for infrastructure exceptions
- Configuration file format and persistence mechanism remain unchanged
- Interactive prompting behavior (currently in `Config.prompt()`) will be reimplemented in CLI layer with same user experience

## Dependencies

- Understanding of current exception hierarchy (see analysis.md)
- Review of all callsites using `Config.prompt()` to ensure CLI layer handles them
- Review of all error handling expecting CLI exceptions from infrastructure

## Out of Scope

- Adding new configuration options or validation rules
- Changing configuration file format or location
- Adding new authentication methods
- Implementing alternative UI layers (GUI, API) - only ensuring they _could_ be implemented
- Performance optimization of authentication or config loading
- Adding new infrastructure services beyond auth and retry

## Related Work

- Feature 005-remove-auth-cli-dependency: Related effort addressing auth/CLI coupling
- Feature 004-gtool-restructure: Established current module structure
- Feature 002-dry-solid-cleanup: Addressed other architectural concerns
