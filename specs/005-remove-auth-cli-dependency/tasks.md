# Tasks: Remove Google Auth Exception Dependencies from CLI

**Input**: Design documents from `/specs/005-remove-auth-cli-dependency/`
**Prerequisites**: plan.md, spec.md

**Organization**: Tasks are organized by implementation phase. Each phase has specific, actionable tasks with exact file paths.

## Phase 1: Foundation - Add AuthenticationError Class

**Purpose**: Create the domain exception class that will replace Google auth exceptions in the CLI layer

**Files Modified**: `src/gtool/cli/errors.py`, `tests/test_errors.py`

- [ ] T001 [P] Add AuthenticationError class to src/gtool/cli/errors.py
  - Inherit from CLIError
  - Add type hints for **init**(message: str) → None
  - Add comprehensive docstring explaining purpose and usage
  - Include example of how it will be used (wrapping Google auth errors)

- [ ] T002 [P] Write test for AuthenticationError in tests/test_errors.py
  - Test that AuthenticationError inherits from CLIError
  - Test that exception message is preserved
  - Test that exception can be caught as CLIError

- [ ] T003 Run Phase 1 validation
  - Run pytest on test_errors.py to verify new class works
  - Verify all other tests still pass
  - Check that AuthenticationError is properly exported from errors module

**Checkpoint**: AuthenticationError class exists and is tested. Ready for Phase 2.

---

## Phase 2: Infrastructure - Wrap Exceptions in GoogleAPIClient

**Purpose**: Add exception translation at the infrastructure boundary so Google auth errors become domain errors

**Files Modified**: `src/gtool/infrastructure/google_client.py`, `tests/test_google_client.py`

- [ ] T004 [P] Update GoogleAPIClient.\_execute_with_retry() in src/gtool/infrastructure/google_client.py
  - Add exception handling for google.auth.exceptions.GoogleAuthError
  - Wrap caught exception as AuthenticationError with original message preserved
  - Add logging when exception is translated
  - Add comment explaining why this translation happens (dependency inversion)

- [ ] T005 [P] Write test for exception translation in tests/test_google_client.py
  - Create mock that raises google.auth.exceptions.GoogleAuthError
  - Call \_execute_with_retry() and verify it raises AuthenticationError instead
  - Verify original error message is included in AuthenticationError
  - Test multiple retry scenarios with auth errors

- [ ] T006 Update CalendarClient tests in tests/test_gcal_client_v2.py
  - Change mock auth errors from google.auth.exceptions to AuthenticationError
  - Update exception handling assertions to expect AuthenticationError
  - Verify all calendar client tests still pass

- [ ] T007 Update GmailClient tests in tests/test_gmail_client_v2.py
  - Change mock auth errors from google.auth.exceptions to AuthenticationError
  - Update exception handling assertions to expect AuthenticationError
  - Verify all Gmail client tests still pass

- [ ] T008 Run Phase 2 validation
  - Run full test suite: pytest tests/test_google_client.py tests/test_gcal_client_v2.py tests/test_gmail_client_v2.py
  - Verify exception translation works correctly
  - Verify no Google auth exceptions leak from client classes

**Checkpoint**: All client exceptions properly translated. Ready for Phase 3.

---

## Phase 3: CLI - Remove Google Auth Imports

**Purpose**: Update CLI layer to use only domain exceptions, removing all Google auth imports

**Files Modified**: `src/gtool/cli/main.py`, `tests/test_cli.py`

- [ ] T009 Remove google.auth.exceptions import from src/gtool/cli/main.py
  - Delete: `import google.auth.exceptions`
  - Delete: All aliases like `as google_auth_exceptions`

- [ ] T010 [P] Update cli() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T011 [P] Update free() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T012 [P] Update get_calendars() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T013 [P] Update show_events() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T014 [P] Update gmail_list() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T015 [P] Update gmail_show_message() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T016 [P] Update gmail_delete() command in src/gtool/cli/main.py
  - Change exception handling from `except (CLIError, google_auth_exceptions.GoogleAuthError)` to `except CLIError`
  - Verify docstring still accurate

- [ ] T017 Update CLI tests in tests/test_cli.py
  - Review all test mocks for google_auth_exceptions
  - Update any test fixtures or mocks that raise google.auth.exceptions to raise AuthenticationError instead
  - Update test assertions that expect google.auth.exceptions to expect AuthenticationError
  - Verify all CLI tests still pass

- [ ] T018 Run Phase 3 validation
  - Verify: `grep -r "google.auth" src/gtool/cli/` returns NO matches
  - Run full CLI tests: pytest tests/test_cli.py
  - Verify all exception handling works correctly
  - Verify error messages shown to users are unchanged

**Checkpoint**: CLI layer is Google auth-free. Ready for Phase 4.

---

## Phase 4: Verification & Finalization

**Purpose**: Comprehensive testing and validation of entire refactor

**Files Modified**: (none - verification only)

- [ ] T019 Run full test suite
  - Command: `pytest tests/ -v`
  - Verify all 95+ tests pass
  - Verify no test failures or warnings

- [ ] T020 Check code coverage
  - Command: `pytest --cov=gtool --cov-report=term-missing tests/`
  - Verify coverage ≥80%
  - Identify any uncovered code (should be minimal)

- [ ] T021 Verify no Google auth imports in CLI
  - Command: `grep -r "google.auth" src/gtool/cli/`
  - Verify: command returns empty (no matches)
  - If matches found, resolve before proceeding

- [ ] T022 Check architecture integrity
  - Verify: No circular imports between layers
  - Verify: CLI imports only from core, config, utils (not infrastructure directly)
  - Verify: All Google auth imports are only in infrastructure layer

- [ ] T023 Manual testing of error scenarios (optional but recommended)
  - Test expired credentials: verify AuthenticationError is raised and handled properly
  - Test invalid credentials: verify error message is clear
  - Test missing credentials file: verify helpful error message

- [ ] T024 Review and finalize
  - Review all changes for code style and consistency
  - Verify all docstrings are accurate
  - Verify type hints are correct
  - Check commit messages are clear and descriptive

- [ ] T025 Prepare PR summary
  - Document all changes made
  - List files modified
  - Note any breaking changes (there should be none)
  - Provide reproduction steps for testing

**Checkpoint**: All validation complete. Ready for PR and review.

---

## Implementation Notes

### Parallelization

Tasks that can run in parallel (marked with [P]):

- **Phase 1**: T001, T002 (both modify different test files)
- **Phase 2**: T004, T005, T006, T007 (updating different test files)
- **Phase 3**: T010-T016 (updating different CLI commands - can be done in any order)

### Testing Strategy

1. **Write tests first** (Phase 1 & 2): Tests fail before implementation
2. **Implement code** (Phase 2 & 3): Code makes tests pass
3. **Verify comprehensively** (Phase 4): Full test suite + coverage + manual testing

### Success Criteria

- ✅ All 95+ tests pass
- ✅ Code coverage ≥80%
- ✅ `grep -r "google.auth" src/gtool/cli/` returns empty
- ✅ All CLI commands catch only `CLIError` (not Google exceptions)
- ✅ `AuthenticationError` class exists and is used
- ✅ User-facing behavior unchanged (error messages identical)
- ✅ Architecture follows dependency inversion principle

### Estimated Time per Phase

- **Phase 1**: 1-2 hours (new class + tests)
- **Phase 2**: 2-3 hours (wrap exceptions + update client tests)
- **Phase 3**: 1-2 hours (update CLI commands)
- **Phase 4**: 1 hour (verification + finalization)
- **Total**: 5-8 hours
