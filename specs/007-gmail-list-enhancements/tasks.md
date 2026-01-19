# Implementation Tasks: Gmail List Enhancements

**Feature**: 007-gmail-list-enhancements
**Branch**: `007-gmail-list-enhancements`
**Specification**: [spec.md](spec.md)
**Design**: [data-model.md](data-model.md) | [contracts/gmail-list-contracts.md](contracts/gmail-list-contracts.md) | [quickstart.md](quickstart.md)

---

## Overview

This feature adds two independent user stories to the Gmail list command:

1. **US1 (P1)**: Display email subjects/titles for quick identification
2. **US2 (P2)**: Filter emails by Gmail labels with a configurable batch size (default 10); no offset-based pagination (rerun list after processing to get the next batch)

Both stories enhance the existing `gtool gmail list` command without breaking changes.

---

## Phase 1: Setup & Validation _(Prerequisite)_

These tasks establish the foundation for all user stories.

- [X] T001 Create test fixtures for Gmail API mocked responses in `tests/conftest.py`
- [X] T002 Add validation utility functions in `src/gtool/cli/decorators.py` for count/offset validation

---

## Phase 2: Foundational Tasks _(Blocking prerequisites)_

These tasks prepare the codebase for feature implementation.

- [X] T003 [P] Extract subject lines from Gmail message headers in `src/gtool/clients/gmail.py`
- [X] T004 [P] Create email list formatter function in `src/gtool/cli/formatters.py`

---

## Phase 3: User Story 1 - View Email Titles (P1) _(Independently testable)_

**Goal**: Display email subject lines in the list output so users can quickly identify messages.

**Independent Test Criteria**:

- ✅ Can list emails and see subject lines displayed
- ✅ Subjects with special characters render correctly
- ✅ Blank subjects display as "(No Subject)"
- ✅ Long subjects are truncated appropriately

### Implementation Tasks

- [X] T006 [P] [US1] Extract subject from message headers and include in list response in `src/gtool/clients/gmail.py` method `list_messages()`
- [X] T007 [P] [US1] Update `format_gmail_list_table()` to display subject column in `src/gtool/cli/formatters.py`
- [X] T008 [US1] Add `--format` option (if needed) to CLI command in `src/gtool/cli/main.py`
- [X] T009 [US1] Update `gmail_list()` command to use new formatter in `src/gtool/cli/main.py`

### Testing Tasks

- [X] T010 [US1] Unit test: subject extraction from headers in `tests/test_gmail_client.py`
- [X] T011 [US1] Unit test: handle blank subject as "(No Subject)" in `tests/test_gmail_client.py`
- [X] T012 [US1] Unit test: subject with special characters and Unicode in `tests/test_gmail_client.py`
- [X] T013 [US1] Unit test: long subject truncation in `tests/test_gmail_client.py`
- [X] T014 [US1] Integration test: CLI displays subjects in list output in `tests/test_cli.py`
- [X] T015 [US1] Integration test: end-to-end subject display with mocked Gmail API in `tests/test_cli.py`

---

## Phase 4: User Story 2 - Filter by Label (P2) _(Independently testable)_

**Goal**: Allow users to filter emails by Gmail label for focused workflows.

**Independent Test Criteria**:

- ✅ Can filter by label and see only emails with that label
- ✅ Non-existent label provides helpful error message
- ✅ Multiple labels on same email are handled correctly
- ✅ Default behavior (no label) shows INBOX emails

### Implementation Tasks

- [X] T016 [P] [US2] Add `label` parameter to `list_messages()` method in `src/gtool/clients/gmail.py`
- [X] T017 [P] [US2] Implement label-to-query conversion logic in `src/gtool/clients/gmail.py` (convert `label="Work"` to `label:Work`)
- [X] T018 [US2] Add `--label` option to `gmail list` command in `src/gtool/cli/main.py`
- [X] T019 [US2] Implement default INBOX filter when no label/query specified in `src/gtool/clients/gmail.py`
- [X] T020 [US2] Add user-friendly error handling for non-existent labels in `src/gtool/cli/main.py`

### Testing Tasks

- [X] T021 [US2] Unit test: label parameter converts to query syntax in `tests/test_gmail_client.py`
- [X] T022 [US2] Unit test: label and query are combined correctly in `tests/test_gmail_client.py`
- [X] T023 [US2] Unit test: default INBOX filter applied when no parameters in `tests/test_gmail_client.py`
- [X] T024 [US2] Unit test: multiple labels on single message in `tests/test_gmail_client.py`
- [X] T025 [US2] Integration test: CLI `--label Work` filters emails correctly in `tests/test_cli.py`
- [X] T026 [US2] Integration test: CLI `--label` with `--query` combines filters in `tests/test_cli.py`
- [X] T027 [US2] Integration test: error message for non-existent label in `tests/test_cli.py`

---

## Phase 5: Batch Size Controls (No Offset)

**Goal**: Allow users to request a configurable batch size (default 10) without offset-based pagination.

### Implementation Tasks

- [X] T028 Add `count` parameter handling to `list_messages()` in `src/gtool/clients/gmail.py` (default 10; no offset)
- [X] T029 Add `--count` option to `gmail list` command in `src/gtool/cli/main.py`
- [X] T030 Add validation for count >= 0 in `src/gtool/cli/main.py` (usage error if negative)

### Testing Tasks

- [X] T031 Unit test: count parameter limits results in `tests/test_gmail_client.py`
- [X] T032 Unit test: count=0 returns empty result in `tests/test_gmail_client.py`
- [X] T033 Integration test: CLI `--count 20` returns 20 emails in `tests/test_cli.py`

## Phase 5: (Removed) Pagination User Story

Pagination with offset is intentionally out of scope for this feature. Batch listing is achieved by re-running the command after processing a batch.

---

## Phase 6: Integration & Cross-Story Tests

Test combinations for subjects, labels, and backward compatibility.

- [ ] T046 [P] Integration test: subject display + label filter in `tests/test_cli.py`
- [ ] T050 Integration test: backward compatibility with existing `--query` parameter in `tests/test_cli.py`
- [ ] T051 Integration test: backward compatibility with legacy `--limit` parameter in `tests/test_cli.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

Final refinements and documentation.

- [ ] T052 Add comprehensive error messages for all edge cases in `src/gtool/cli/errors.py`
- [ ] T053 Update CLI help text and examples for `gmail list` command in `src/gtool/cli/main.py`
- [ ] T054 [P] Add docstring examples to `list_messages()` in `src/gtool/clients/gmail.py`
- [ ] T055 [P] Add docstring examples to `format_gmail_list_table()` in `src/gtool/cli/formatters.py`
- [ ] T056 Update README with Gmail list feature usage examples
- [ ] T057 Create migration guide for users switching from old list command

---

## Task Dependencies & Parallelization

### Critical Path (Sequential)

```
T001 → T003, T004 → (T006, T007, T008, T009) → (T016, T017, T018) → (T028, T029, T030)
       ↓
      T002
```

### Parallel Execution Groups

**Group 1: Setup (Days 1-2)** - _All in parallel_

- T001, T002

**Group 2: Foundations (Days 2-3)** - _T003, T004 in parallel_

- T003 (extract subjects)
- T004 (create formatter)

**Group 3: US1 Implementation (Days 3-4)** - _All tasks in parallel_

- T006, T007, T008, T009 (implementation)
- T010, T011, T012, T013, T014, T015 (tests)

**Group 4: US2 Implementation (Days 4-5)** - _All tasks in parallel_

- T016, T017, T018, T019, T020 (implementation)
- T021, T022, T023, T024, T025, T026, T027 (tests)

**Group 5: Batch Size (Days 5-6)** - _All tasks in parallel_

- T028, T029, T030 (implementation)
- T031, T032, T033 (tests)

**Group 6: Integration Testing (Days 6-7)** - _All in parallel_

- T046, T050, T051

**Group 7: Polish (Days 7-8)** - _All in parallel_

- T052, T053, T054, T055, T056, T057

### Estimated Timeline

- **Minimum (Parallel)**: 8 days (groups executed sequentially)
- **Realistic (with dependencies)**: 10-12 days (Groups 3, 4, 5 can overlap once foundations are done)
- **MVP (US1 only)**: 4 days (Phase 1 + Phase 3)

---

## User Story Completion Checklist

### ✅ User Story 1: View Email Titles (P1)

- [ ] T006, T007, T008, T009 (implementation)
- [ ] T010, T011, T012, T013, T014, T015 (testing)
- **Independent Test**: Run `gtool gmail list --count 5` and verify subjects display
- **MVP Criteria**: ✅ Delivers immediate value; can ship independently

### ✅ User Story 2: Filter by Label (P2)

- [ ] T016, T017, T018, T019, T020 (implementation)
- [ ] T021, T022, T023, T024, T025, T026, T027 (testing)
- **Independent Test**: Run `gtool gmail list --label Work` and verify filtering
- **Dependency**: Requires T006, T007 (US1) for proper subject display in results

### ✅ User Story 3: Pagination (P2)

- [ ] T028, T029, T030, T031, T032, T033, T034 (implementation)
- [ ] T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045 (testing)
- **Independent Test**: Run `gtool gmail list --count 10 --offset 20` and verify pagination
- **Dependency**: Requires T006, T007 (US1) for proper subject display in results

---

## MVP Scope

**Recommended MVP** (Ship after 4 days):

- ✅ Phase 1: Setup & Validation (T001, T002)
- ✅ Phase 2: Foundations (T003, T004)
- ✅ Phase 3: US1 - View Email Titles (T006-T015)

This delivers core value (email identification by subject) immediately, allowing US2 and US3 to ship as follow-up releases without blocking end users.

---

## Files Modified/Created

| File                          | Action | Phase      | Task                                    |
| ----------------------------- | ------ | ---------- | --------------------------------------- |
| `src/gtool/clients/gmail.py`  | Modify | 2, 3, 4, 5 | T003, T006, T016, T028                  |
| `src/gtool/cli/formatters.py` | Modify | 2, 3       | T004, T007                              |
| `src/gtool/cli/main.py`       | Modify | 3, 4, 5    | T009, T018, T020, T029, T030            |
| `src/gtool/cli/decorators.py` | Modify | 1          | T002                                    |
| `src/gtool/cli/errors.py`     | Modify | 7          | T052                                    |
| `tests/conftest.py`           | Modify | 1          | T001                                    |
| `tests/test_gmail_client.py`  | Modify | 3, 4, 5    | T010-T015, T021-T024, T031-T032         |
| `tests/test_cli.py`           | Modify | 3, 4, 5, 6 | T014, T025-T027, T033, T046, T050, T051 |
| `README.md`                   | Modify | 7          | T056                                    |

---

## Success Criteria Mapping

| Success Criterion                          | Task(s)               | Story |
| ------------------------------------------ | --------------------- | ----- |
| SC-001: 80% improvement in email scanning  | T006, T007, T010-T015 | US1   |
| SC-002: Retrieve next batch without offset | T028-T033             | US2   |
| SC-003: Unicode support in subjects        | T012, T013            | US1   |

---

## Notes for Implementers

1. **Backward Compatibility**: Tests T050-T051 ensure existing `--query` and legacy `--limit` parameters work unchanged
2. **Constitution Compliance**: All code changes must include type hints and docstrings (see Constitution Principle III)
3. **Test-First**: Implement unit tests before client/CLI code (Constitution Principle II)
4. **Mocking**: All Gmail API calls use mocks; no real API calls in tests (Constitution Principle II)
5. **Subject Extraction**: May require fetching full message metadata (headers) vs. snippet only

---

**Version**: 1.0.0
**Last Updated**: January 19, 2026
**Branch**: `007-gmail-list-enhancements`
