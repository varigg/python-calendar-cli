# Implementation Plan: Remove Google Auth Exception Dependencies from CLI

**Branch**: `005-remove-auth-cli-dependency` | **Date**: January 17, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-remove-auth-cli-dependency/spec.md`

## Summary

Remove `google.auth.exceptions` imports from CLI layer to enforce dependency inversion principle. Add `AuthenticationError(CLIError)` class to errors.py and wrap auth exceptions in `GoogleAPIClient` base class. This makes CLI depend only on domain abstractions, not Google implementation details, enabling future auth provider swaps and cleaner architecture.

**Technical Approach**:

1. Add `AuthenticationError` exception class to `gtool/cli/errors.py`
2. Update `GoogleAPIClient._execute_with_retry()` to catch `google.auth.exceptions.GoogleAuthError` and wrap as `AuthenticationError`
3. Remove `google.auth.exceptions` imports from all CLI commands in `gtool/cli/main.py`
4. Update all CLI commands to catch only `CLIError` and subclasses
5. Update tests to use `AuthenticationError` instead of Google exceptions
6. Verify all 95+ tests pass with improved architecture

## Technical Context

**Language/Version**: Python 3.12.11
**Primary Dependencies**: google-auth, google-auth-oauthlib, google-api-python-client, click 8.x, pytest 8.3.5
**Storage**: N/A (config files at `~/.config/caltool/`)
**Testing**: pytest with 95 tests, 80% coverage
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single Python CLI application (6-layer architecture: cli, core, clients, infrastructure, config, utils)
**Performance Goals**: No degradation; tests <5s
**Constraints**: All existing CLI behavior preserved; no user-facing changes; 80%+ coverage maintained
**Scale/Scope**: ~2500 LOC across 18 source modules; 95 tests; 2 API clients

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

✅ **I. Separation of Concerns**: Refactor directly enforces this principle by removing infrastructure details from CLI layer. Each layer (CLI, Core, Clients, Infrastructure) has clear responsibilities with no cross-layer imports of implementation details.

✅ **II. Test-First Development**: All 95+ existing tests will be migrated. Exception wrapping behavior will be tested to ensure auth errors properly convert to AuthenticationError.

✅ **III. Type Safety & Documentation**: All type hints and docstrings preserved. New `AuthenticationError` class will have proper type hints and comprehensive docstring.

✅ **IV. CLI-First Design**: CLI remains the presentation layer. Changes improve CLI abstraction by removing direct dependencies on Google libraries.

✅ **V. PEP8 & Best Practices**: Refactor follows SOLID principles (dependency inversion). Code organization remains clean. No new dependencies added.

**Gate Status**: ✅ PASS - Feature strengthens Separation of Concerns and follows SOLID principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-remove-auth-cli-dependency/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 (research clarifications) - TBD
├── data-model.md        # Phase 1 (contracts/design) - TBD
├── quickstart.md        # Phase 1 (implementation quickstart) - TBD
└── tasks.md             # Phase 2 (task breakdown) - TBD
```

### Source Code - Modified Files

```text
src/gtool/cli/
├── errors.py            # ADD: AuthenticationError class
└── main.py              # MODIFY: Remove google.auth imports, update exception handling

src/gtool/infrastructure/
└── google_client.py     # MODIFY: Add exception wrapping in _execute_with_retry()

tests/
├── test_cli.py          # MODIFY: Update mocked exceptions
├── test_google_client.py # MODIFY: Verify exception translation
└── test_errors.py       # ADD: Test AuthenticationError class
```

**Structure Decision**: Minimal changes across 3 source files and 3 test files. Exception translation happens at infrastructure boundary (GoogleAPIClient). CLI layer becomes independent of Google auth details.

## Implementation Phases

### Phase 1: Foundation - Add AuthenticationError Class (1-2 hours)

**Files Modified**: `src/gtool/cli/errors.py`

**Tasks**:

1. Add `AuthenticationError` class inheriting from `CLIError`
2. Add comprehensive docstring explaining purpose and usage
3. Add type hints for **init** method
4. Write tests in `tests/test_errors.py` for new class

**Success Criteria**:

- `AuthenticationError` class exists and properly inherits from `CLIError`
- Class has proper type hints and documentation
- All tests for AuthenticationError pass

---

### Phase 2: Infrastructure - Wrap Exceptions in GoogleAPIClient (2-3 hours)

**Files Modified**: `src/gtool/infrastructure/google_client.py`, `tests/test_google_client.py`

**Tasks**:

1. Update `GoogleAPIClient._execute_with_retry()` to catch `google.auth.exceptions.GoogleAuthError`
2. Convert Google auth exceptions to `AuthenticationError`
3. Write tests verifying exception translation
4. Update existing tests to expect `AuthenticationError` instead of Google exceptions
5. Verify no other Google exceptions leak from client classes

**Success Criteria**:

- `_execute_with_retry()` wraps auth errors as `AuthenticationError`
- All client tests pass
- Google auth exceptions don't leak to CLI layer

---

### Phase 3: CLI - Remove Google Auth Imports (1-2 hours)

**Files Modified**: `src/gtool/cli/main.py`, `tests/test_cli.py`

**Tasks**:

1. Remove `import google.auth.exceptions` from main.py
2. Update all CLI commands to catch only `CLIError` (not Google exceptions)
3. Affected commands: `cli()`, `free()`, `get_calendars()`, `show_events()`, `gmail_list()`, `gmail_show_message()`, `gmail_delete()`
4. Update test mocks to use `AuthenticationError` instead of Google exceptions
5. Run full test suite

**Success Criteria**:

- No `google.auth` imports in `src/gtool/cli/`
- All CLI commands only catch `CLIError` and subclasses
- All 95+ tests pass
- User-facing error messages unchanged

---

### Phase 4: Verification & Finalization (1 hour)

**Tasks**:

1. Run full test suite: `pytest tests/ -q`
2. Check coverage: `pytest --cov=gtool tests/`
3. Verify: `grep -r "google.auth" src/gtool/cli/` returns nothing
4. Review all changes for consistency
5. Create comprehensive commit message

**Success Criteria**:

- All tests pass (95+)
- Coverage ≥80%
- No Google auth imports in CLI
- Commit history is clean and logical

## Estimated Effort

- **Total**: 5-8 hours
- **Per Phase**: 1-3 hours
- **Testing**: ~30% of effort (TDD approach)

## Known Unknowns & Risks

**Low Risk**: Internal refactor with comprehensive test coverage. Exception messages preserved. CLI behavior unchanged.

**Potential Issues**:

1. **Google Auth Error Variants**: What if GoogleAuthError has subclasses? → Solution: Catch broad GoogleAuthError base class
2. **Message Preservation**: Need to preserve original error messages in AuthenticationError → Solution: Wrap message in constructor
3. **Multiple Exception Types**: Could multiple auth-related exceptions need handling? → Solution: Wrap any auth-related Google exceptions

**Mitigation**: All caught by existing test suite. TDD approach ensures discovery during phase 2.
