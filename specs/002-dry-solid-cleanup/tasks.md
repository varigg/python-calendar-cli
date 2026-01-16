# Tasks: DRY/SOLID Code Cleanup

**Input**: Design documents from `/specs/002-dry-solid-cleanup/`  
**Branch**: `002-dry-solid-cleanup`  
**Date**: January 15, 2026

## Format: `- [ ] [ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1, US2, US3, US4) - omitted for setup/foundational phases
- Exact file paths included in all descriptions

## User Stories (Priority Mapping)

- **P1 (US1)**: Remove duplicate code (DRY violations)
- **P2 (US2)**: Clean exception handling in CLI
- **P3 (US3)**: Remove dead code (YAGNI)
- **P4 (US4)**: Consistent import patterns (KISS)

---

## Phase 1: Setup & Verification

**Purpose**: Baseline validation before refactoring

- [ ] T001 Run full test suite to establish baseline in working directory
- [ ] T002 Verify current codebase compiles without errors
- [ ] T003 Document current test coverage metrics

---

## Phase 2: Dead Code Removal (P3/US3) - Lowest Risk

**Purpose**: Remove unused functions and methods that add cognitive load

**Independent Test**: Code search confirms removed functions have zero usages

### Implementation for User Story 3

- [ ] T004 [P] [US3] Remove unused `cli_error()` function from src/caltool/errors.py (lines 13-19)
- [ ] T005 [P] [US3] Remove unused `retry_on_exception()` method from src/caltool/google_client.py (lines 228-276)
- [ ] T006 [US3] Verify no references to `cli_error()` exist in codebase
- [ ] T007 [US3] Verify no references to `retry_on_exception()` exist in codebase
- [ ] T008 [US3] Run test suite to confirm no regressions from dead code removal

**Checkpoint**: Dead code removed, all tests passing

---

## Phase 3: Duplicate Code Removal (P1/US1) - Medium Risk

**Purpose**: Eliminate duplicate method definitions per DRY principle

**Independent Test**: Each method signature exists exactly once in the codebase

### Implementation for User Story 1

- [ ] T009 [P] [US1] Remove duplicate `validate_gmail_scopes()` method from src/caltool/config.py (lines 63-73)
- [ ] T010 [P] [US1] Remove duplicate `is_gmail_enabled()` method from src/caltool/config.py (lines 76-86)
- [ ] T011 [P] [US1] Remove duplicate `has_gmail_scope()` method from src/caltool/config.py (lines 88-99)
- [ ] T012 [US1] Remove `@abstractmethod` decorator from `_validate_config()` in src/caltool/google_client.py (line 281)
- [ ] T013 [US1] Remove unnecessary `_validate_config()` override from src/caltool/gcal_client.py (lines 40-45)
- [ ] T014 [US1] Verify Config class methods execute expected (later) implementation via unit tests
- [ ] T015 [US1] Run test suite to confirm no regressions from duplicate removal

**Checkpoint**: All duplicate definitions removed, single authoritative version remains, tests passing

---

## Phase 4: Import Pattern Cleanup (P4/US4) - Low Risk

**Purpose**: Consistent module-level imports following PEP8

**Independent Test**: No function-level imports detected (except documented circular dependency cases)

### Implementation for User Story 4

- [ ] T016 [P] [US4] Move `from collections import defaultdict` import to module level in src/caltool/format.py (move line 116 to top with other imports)
- [ ] T017 [P] [US4] Remove local `from .errors import CLIError` import from `_validate_config()` in src/caltool/gmail_client.py (remove line 48)
- [ ] T018 [US4] Verify format.py still executes correctly after import reorganization
- [ ] T019 [US4] Verify gmail_client.py still raises CLIError correctly after import removal
- [ ] T020 [US4] Run test suite to confirm no import-related regressions

**Checkpoint**: All imports organized at module level, no local imports, tests passing

---

## Phase 5: Exception Handling Refinement (P2/US2) - Highest Risk

**Purpose**: Specific exception handling allows debugging while preserving user experience

**Independent Test**: CLIError caught and displayed; unexpected exceptions propagate with stack trace; auth errors handled specifically

### Implementation for User Story 2

- [ ] T021 Add import for google.auth.exceptions to top of src/caltool/cli.py
- [ ] T022 [P] [US2] Replace `except Exception as e:` with specific handlers in `free()` command (line 95) in src/caltool/cli.py
- [ ] T023 [P] [US2] Replace `except Exception as e:` with specific handlers in `get_calendars()` command (line 106) in src/caltool/cli.py
- [ ] T024 [P] [US2] Replace `except Exception as e:` with specific handlers in `show_events()` command (line 136) in src/caltool/cli.py
- [ ] T025 [P] [US2] Replace `except Exception as e:` with specific handlers in `gmail_list()` command (line 147) in src/caltool/cli.py
- [ ] T026 [P] [US2] Replace `except Exception as e:` with specific handlers in `gmail_show_message()` command (line 174) in src/caltool/cli.py
- [ ] T027 [P] [US2] Replace `except Exception as e:` with specific handlers in `gmail_delete()` command (line 209) in src/caltool/cli.py
- [ ] T028 [US2] Test free command with valid input to verify user-friendly CLIError handling
- [ ] T029 [US2] Test get_calendars command with invalid credentials to verify auth error handling
- [ ] T030 [US2] Test show_events command to verify existing functionality preserved
- [ ] T031 [US2] Test gmail_list command with valid and invalid input
- [ ] T032 [US2] Test gmail_show_message command with valid and invalid message IDs
- [ ] T033 [US2] Test gmail_delete command with confirmation prompt
- [ ] T034 [US2] Run full test suite to confirm exception handling changes don't break existing tests

**Checkpoint**: Specific exception handling in place, CLI UX preserved, all tests passing

---

## Phase 6: Final Verification & Documentation

**Purpose**: Validate all requirements met and no regressions introduced

### Verification Tasks

- [ ] T035 Run full test suite with coverage report to confirm all tests pass
- [ ] T036 Run pylint/flake8 to verify code style compliance
- [ ] T037 Search codebase for removed function names (`cli_error`, `retry_on_exception`) and confirm zero results
- [ ] T038 Search codebase for duplicate method definitions (`is_gmail_enabled`, `has_gmail_scope`, `validate_gmail_scopes`) and confirm single occurrence each
- [ ] T039 Verify no function-level imports remain in codebase (except documented exceptions)
- [ ] T040 Manual CLI smoke test: Run all major commands and verify user-facing output/errors unchanged
- [ ] T041 Document completion of refactoring in commit message referencing spec.md requirements

**Checkpoint**: All success criteria met, refactoring complete

---

## Dependency Graph

```
Phase 1 (Setup)
  ↓
Phase 2 (Dead Code Removal - T004:T008) ← can run in parallel with Phase 3-4
  ↓
Phase 3 (Duplicate Code Removal - T009:T015) [blocks T016-T034] ← can run in parallel with Phase 4
  ↓
Phase 4 (Import Cleanup - T016:T020) ← can run in parallel with Phase 3
  ↓
Phase 5 (Exception Handling - T021:T034) [depends on phases 2-4]
  ↓
Phase 6 (Final Verification - T035:T041)
```

## Parallelization Opportunities

**Can execute in parallel:**

- T004-T005 (removing separate dead code items)
- T009-T011 (removing separate duplicate methods)
- T016-T017 (moving separate imports)
- T022-T027 (updating separate CLI commands)
- T028-T033 (testing separate CLI commands)

**Cannot parallelize:**

- T006-T008 (depend on T004-T005 completion)
- T012-T015 (depend on T009-T011 completion)
- T018-T020 (depend on T016-T017 completion)
- T021-T034 (depend on earlier phases)
- T035-T041 (final verification requires all prior tasks)

---

## Summary by Story

| Story | ID Range  | Title                  | Phase   |
| ----- | --------- | ---------------------- | ------- |
| US3   | T004-T008 | Dead Code Removal      | Phase 2 |
| US1   | T009-T015 | Duplicate Code Removal | Phase 3 |
| US4   | T016-T020 | Import Cleanup         | Phase 4 |
| US2   | T021-T034 | Exception Handling     | Phase 5 |

---

## Task Count Summary

- **Total tasks**: 41
- **Setup/Verification**: 7 tasks (Phase 1 + Phase 6)
- **User Story 1 (P1)**: 7 tasks
- **User Story 2 (P2)**: 14 tasks
- **User Story 3 (P3)**: 5 tasks
- **User Story 4 (P4)**: 5 tasks

## MVP Scope

Minimum viable scope (implement US1 only):

- Remove duplicate methods from Config class
- Fix @abstractmethod pattern in GoogleAPIClient
- Remove unnecessary override in GCalClient
- Validates DRY principle improvements
- **Tasks**: T001-T003, T009-T015, T035-T041 (~14 tasks, ~30 mins)

Progressive scope:

1. **MVP (US1)**: Duplicate code removal (~14 tasks)
2. **+US3**: Add dead code removal (~19 tasks)
3. **+US4**: Add import cleanup (~24 tasks)
4. **+US2**: Add exception handling (~41 tasks all)
