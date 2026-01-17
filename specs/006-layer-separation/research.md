# Research: Layer Separation Enforcement

**Feature**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Date**: 2026-01-17

## Purpose

This document consolidates research findings for enforcing layer separation in the gtool codebase. The goal is to remove UI dependencies from infrastructure and config layers while maintaining backward compatibility.

## Research Questions Resolved

### 1. Current State Analysis

**Question**: What are the exact locations and patterns of UI layer dependencies in infrastructure and config?

**Findings**:

From [analysis.md](../../../analysis.md):

1. **Infrastructure → CLI Dependencies**:
   - `src/gtool/infrastructure/auth.py` imports `click` (line 19)
   - `src/gtool/infrastructure/retry.py` imports `gtool.cli.errors.AuthenticationError`
   - Docstrings in auth module reference CLIError

2. **Config → CLI Dependencies**:
   - `src/gtool/config/settings.py` imports `click` (line 5)
   - `Config.prompt()` method uses `click.prompt` and `click.echo`
   - `validate_gmail_scopes()` raises `click.UsageError`

3. **Current Exception Infrastructure**:
   - `src/gtool/infrastructure/exceptions.py` already exists with:
     - `AuthError` — authentication failures (infrastructure level)
     - `ServiceError` — API service failures (infrastructure level)
   - `src/gtool/cli/errors.py` has CLI-specific exceptions:
     - `CLIError` — general CLI errors
     - `AuthenticationError(CLIError)` — CLI auth presentation

**Decision**: Use existing `AuthError` and `ServiceError` from infrastructure.exceptions. Add `ConfigError` base class and `ConfigValidationError` for config layer.

**Alternatives Considered**:

- Create entirely new exception hierarchy → Rejected: existing exceptions are well-designed
- Use standard Python exceptions only → Rejected: domain-specific exceptions provide better error context

---

### 2. Exception Mapping Patterns

**Question**: What is the best pattern for mapping infrastructure exceptions to CLI exceptions?

**Findings**:

**Python Exception Handling Best Practices**:

1. **Catch-and-Translate Pattern**:

   ```python
   try:
       infrastructure_operation()
   except InfrastructureError as e:
       raise CLIError(f"User-friendly message: {e}") from e
   ```

2. **Decorator Pattern for CLI Commands**:

   ```python
   def handle_infrastructure_errors(func):
       def wrapper(*args, **kwargs):
           try:
               return func(*args, **kwargs)
           except AuthError as e:
               raise AuthenticationError(str(e)) from e
           except ServiceError as e:
               raise CLIError(str(e)) from e
       return wrapper
   ```

3. **Context Manager Pattern**:
   ```python
   @contextmanager
   def cli_error_handler():
       try:
           yield
       except AuthError as e:
           raise AuthenticationError(str(e)) from e
   ```

**Decision**: Use decorator pattern for click commands, as it's most idiomatic for click framework and provides centralized error handling.

**Rationale**:

- Fits naturally with click's command decorators
- Centralizes error translation logic
- Maintains exception chain with `from e` for debugging
- Easy to apply consistently across all commands

**Alternatives Considered**:

- Try-except in every command → Rejected: too much duplication
- Custom click exception handler → Rejected: less explicit, harder to debug

---

### 3. Config Prompting Migration

**Question**: Where should interactive prompting logic move from `Config.prompt()`, and how should it be structured?

**Findings**:

**Current State**:

- `Config.prompt()` in settings.py contains:
  - `click.prompt()` calls for user input
  - `click.echo()` for messages
  - File path expansion logic
  - Config saving logic

**Refactoring Strategy**:

1. **Keep in Config class**:
   - Data validation (no click dependency)
   - File I/O (load, save)
   - Default value management
   - Scope validation (raise ConfigValidationError)

2. **Move to CLI layer** (`cli/main.py`):
   - Interactive prompting with click.prompt
   - User messages with click.echo
   - Orchestration of prompting flow
   - Calling Config.save() after collecting input

**Implementation Pattern**:

```python
# In cli/main.py
@cli.command()
def config():
    """Interactive configuration setup."""
    # Collect input from user
    credentials = click.prompt("Path to credentials.json", default=config.get("CREDENTIALS_FILE"))
    # ... more prompts

    # Update config (no click dependency)
    config.set("CREDENTIALS_FILE", credentials)
    config.save()

    click.echo("Configuration saved!")
```

**Decision**: Create `prompt_config_interactive()` function in CLI layer that orchestrates the prompting flow, keeping Config class purely data-focused.

**Alternatives Considered**:

- Keep Config.prompt() but inject click as dependency → Rejected: still couples config to UI
- Move to separate prompting module → Rejected: over-engineering for single use case

---

### 4. Test Migration Strategy

**Question**: How should tests be updated to reflect new exception types?

**Findings**:

**Current Test Patterns**:

1. Tests expecting `click.UsageError` from config validation
2. Tests expecting CLI exceptions from infrastructure
3. Tests mocking click.prompt in config tests

**Migration Approach**:

1. **Infrastructure Tests** (`test_google_auth.py`, `test_retry_policy.py`):
   - Update assertions to expect `AuthError` instead of `AuthenticationError`
   - Verify infrastructure can be imported without click
   - Add test for non-CLI usage (demonstrates reusability)

2. **Config Tests** (`test_config.py`):
   - Update assertions to expect `ConfigValidationError` instead of `click.UsageError`
   - Remove click.prompt mocking (no longer needed)
   - Test config programmatically without interactive prompting

3. **CLI Tests** (`test_cli.py`):
   - Add tests for exception translation (AuthError → AuthenticationError)
   - Add tests for new `prompt_config_interactive()` function
   - Verify user-facing error messages remain unchanged

**Decision**: Update tests incrementally alongside implementation, maintaining test-first development for new exception translation layer.

---

### 5. Backward Compatibility Verification

**Question**: How do we ensure 100% backward compatibility for CLI users?

**Findings**:

**Compatibility Checkpoints**:

1. **User-Facing Behavior**:
   - Error messages to users must remain identical
   - `gtool config` command behavior unchanged
   - All existing commands work without modification
   - Exit codes remain the same

2. **Configuration Files**:
   - config.json format unchanged
   - credentials.json and token.json unchanged
   - File locations unchanged

3. **Test Coverage**:
   - All existing CLI tests pass without modification to test expectations
   - Regression test suite provides 100% coverage

**Verification Strategy**:

1. Run full test suite before and after each phase
2. Manual testing of `gtool config` command
3. Manual testing of error scenarios (auth failure, invalid config)
4. Document any behavioral changes (there should be none)

**Decision**: Use existing test suite as regression coverage. No new compatibility layer needed since refactoring is internal.

---

## Technology Decisions

### Exception Hierarchy

```
Exception (Python built-in)
│
├── AuthError (infrastructure.exceptions)
│   └── [Specific auth errors if needed]
│
├── ServiceError (infrastructure.exceptions)
│   └── [Specific service errors if needed]
│
├── ConfigError (infrastructure.exceptions - NEW)
│   └── ConfigValidationError (config.settings - NEW)
│
└── click.ClickException
    └── CLIError (cli.errors)
        └── AuthenticationError (cli.errors)
```

**Rationale**: Clear hierarchy with infrastructure exceptions independent of UI, CLI exceptions wrapping infrastructure errors for user presentation.

---

### Import Structure After Refactoring

```
gtool/
├── infrastructure/
│   ├── exceptions.py       # No external deps (pure Python)
│   ├── auth.py            # No click import ✅
│   └── retry.py           # No CLI error import ✅
│
├── config/
│   └── settings.py        # No click import ✅
│                         # Uses ConfigValidationError
│
└── cli/
    ├── errors.py          # Can import infrastructure exceptions
    └── main.py            # Translates infrastructure → CLI exceptions
                          # Contains interactive prompting
```

**Rationale**: Clear dependency direction (CLI depends on infrastructure, not vice versa).

---

## Best Practices Applied

### Python Exception Best Practices

1. **Exception chaining**: Use `raise ... from e` to preserve original exception
2. **Descriptive names**: Exception names clearly indicate what went wrong
3. **Inheritance hierarchy**: Use base exceptions for catching multiple types
4. **Documentation**: Docstrings explain when exceptions are raised

### Click Framework Patterns

1. **Command decorators**: Apply error handling via decorators
2. **Context objects**: Use click.Context for sharing state
3. **UsageError**: Use for user input validation errors (CLI layer only)

### Testing Patterns

1. **pytest.raises**: Verify specific exception types
2. **Mock elimination**: Remove unnecessary mocks when simplifying dependencies
3. **Isolation**: Test layers independently

---

## Implementation Guidance

### Phase 1: Infrastructure Layer (Priority P1)

**Files to modify**:

- `src/gtool/infrastructure/exceptions.py` — Add `ConfigError` base class
- `src/gtool/infrastructure/auth.py` — Remove `import click`, verify `AuthError` usage
- `src/gtool/infrastructure/retry.py` — Replace CLI error with `AuthError`

**Testing approach**:

- Write test that imports infrastructure without click installed
- Verify AuthError raised in auth failures
- Verify infrastructure tests pass

### Phase 2: Config Layer (Priority P2)

**Files to modify**:

- `src/gtool/config/settings.py`:
  - Remove `import click`
  - Add `ConfigValidationError(ConfigError)`
  - Remove `Config.prompt()` method
  - Replace `raise click.UsageError` with `raise ConfigValidationError`

**Testing approach**:

- Update config tests to expect `ConfigValidationError`
- Remove click.prompt mocking
- Verify config tests pass without click

### Phase 3: CLI Layer (Priority P3)

**Files to modify**:

- `src/gtool/cli/main.py`:
  - Add `@handle_infrastructure_errors` decorator
  - Implement `prompt_config_interactive()` function
  - Update `config` command to use new prompting

**Testing approach**:

- Test exception translation (infrastructure → CLI)
- Test interactive prompting function
- Verify all CLI tests pass
- Verify user experience unchanged

---

## Risks Identified

| Risk                           | Mitigation                                     | Status                      |
| ------------------------------ | ---------------------------------------------- | --------------------------- |
| Missing exception callsites    | Grep for all exception usage before modifying  | ✅ Addressed in plan        |
| Test brittleness               | Update tests incrementally with implementation | ✅ Addressed in plan        |
| Circular imports               | Maintain clear dependency direction            | ✅ No risk (CLI→infra only) |
| Breaking Config.prompt() users | Search for all callsites, move logic to CLI    | ✅ Addressed in plan        |

---

## Summary

All research questions resolved. No NEEDS CLARIFICATION markers remain. Implementation can proceed following the patterns documented above.

**Key Decisions**:

1. Use existing infrastructure exceptions (AuthError, ServiceError)
2. Add ConfigError and ConfigValidationError for config layer
3. Use decorator pattern for CLI exception translation
4. Move interactive prompting to CLI layer via dedicated function
5. Maintain 100% backward compatibility via existing test coverage

**Ready for**: Phase 1 implementation (data-model.md and contracts/)
