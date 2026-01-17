---
description: "Implementation tasks for Gmail Client Integration & Google Auth Refactoring"
feature: "001-gmail-client-refactor"
---

# Tasks: Gmail Client Integration & Google Auth Refactoring

**Input**: Design documents from `specs/001-gmail-client-refactor/`
**Prerequisites**: [spec.md](spec.md) ✅, [plan.md](plan.md) ✅, [research.md](research.md) ✅

**User Stories**:

- **US1** (P1): Initialize Gmail with Shared Google Auth
- **US2** (P1): Unified Google Client Architecture
- **US3** (P2): Gmail Client MVP Implementation
- **US4** (P2): Configuration Schema Extension for Gmail
- **US5** (P1): Module Reorganization for Separation of Concerns

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3, US4, US5)
- File paths included in descriptions

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Verify environment and test infrastructure readiness

- [x] T001 Verify Python 3.12+ environment and all dependencies installed per pyproject.toml
- [x] T002 Run existing test suite to establish baseline (all tests must pass before refactoring)
- [x] T003 [P] Create backup branch for rollback safety

**Checkpoint**: Environment ready, baseline established

---

## Phase 2: Foundational (Blocking Prerequisites for ALL User Stories)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Test Infrastructure Setup

- [x] T004 [P] Create test file structure: tests/test_google_auth.py, tests/test_google_client.py, tests/test_gmail_client.py
- [x] T005 [P] Add mock fixtures for Google API responses in tests/conftest.py (Gmail message data, auth responses)

### Backward Compatibility Verification

- [x] T006 Document current GCalClient public API contract in tests/test_backward_compatibility.py (method signatures, return types, exception behavior)
- [x] T007 Create integration tests that verify Calendar functionality remains unchanged after refactoring

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 5 - Module Reorganization (Priority: P1) 🎯 ARCHITECTURAL

**Goal**: Establish clear separation of concerns by extracting auth and creating base client pattern

**Independent Test**: Module structure review confirms auth, service building, and client logic are isolated with clear contracts

### US5 Tasks - Module Structure

- [x] T008 [P] [US5] Create src/caltool/google_auth.py with GoogleAuth class skeleton (empty methods, type hints, docstrings)
- [x] T009 [P] [US5] Create src/caltool/google_client.py with GoogleAPIClient ABC skeleton (abstract base class definition)
- [x] T010 [US5] Write tests for GoogleAuth class initialization in tests/test_google_auth.py (TDD: tests fail initially)
- [x] T011 [US5] Write tests for GoogleAPIClient base class in tests/test_google_client.py (TDD: tests fail initially)

**Checkpoint US5**: Module structure established, ready for implementation

---

## Phase 4: User Story 1 - Shared Google Auth (Priority: P1) 🎯 MVP FOUNDATION

**Goal**: Extract authentication logic from GCalClient into reusable GoogleAuth module

**Independent Test**: Both GCalClient and a test Gmail client can authenticate using GoogleAuth without duplicating auth code

### US1 Tasks - Authentication Extraction

- [x] T012 [US1] Implement GoogleAuth.**init**(config) in src/caltool/google_auth.py (store credentials_file, token_file, scopes)
- [x] T013 [US1] Implement GoogleAuth.get_credentials() method with OAuth flow logic (extracted from GCalClient.authenticate)
- [x] T014 [US1] Implement GoogleAuth.\_load_token_scopes() helper to read existing scopes from token file
- [x] T015 [US1] Implement GoogleAuth.\_detect_scope_changes() to compare requested vs stored scopes
- [x] T016 [US1] Add scope change notification logic (log message when new scopes detected, per research decision #1)
- [x] T017 [US1] Implement token refresh logic in GoogleAuth with incremental scope authorization support
- [x] T018 [US1] Run tests in tests/test_google_auth.py and verify all pass (TDD green phase)
- [x] T019 [US1] Add error handling for auth failures (categorize AUTH errors per research decision #3)

**Checkpoint US1**: GoogleAuth module complete and tested; ready to integrate with clients

---

## Phase 5: User Story 2 - Unified Client Architecture (Priority: P1) 🎯 MVP FOUNDATION

**Goal**: Create GoogleAPIClient base class with shared retry, error handling, and service building logic

**Independent Test**: Base class can initialize services for Calendar and Gmail with consistent behavior

### US2 Tasks - Base Client Implementation

- [x] T020 [US2] Implement GoogleAPIClient.**init**(config, api_name, api_version, service) in src/caltool/google_client.py
- [x] T021 [US2] Implement GoogleAPIClient.\_build_service(api_name, api_version) using GoogleAuth for credentials
- [x] T022 [P] [US2] Extract retry_on_exception decorator from gcal_client.py to google_client.py (make it a base class method)
- [x] T023 [P] [US2] Implement GoogleAPIClient.categorize_error(HttpError) per research decision #3 (AUTH/QUOTA/TRANSIENT/CLIENT)
- [x] T024 [US2] Implement GoogleAPIClient.handle_api_error(HttpError) with user-friendly messages per error category
- [x] T025 [US2] Add @retry_on_exception decorator to base class with smart retry logic (don't retry AUTH/CLIENT, do retry QUOTA/TRANSIENT)
- [x] T026 [US2] Run tests in tests/test_google_client.py and verify all pass (TDD green phase)

**Checkpoint US2**: Base client complete; ready to refactor GCalClient and implement GMailClient

---

## Phase 6: User Story 1 & 2 Integration - GCalClient Refactoring (Priority: P1) 🎯 CRITICAL

**Goal**: Refactor GCalClient to use GoogleAuth and inherit from GoogleAPIClient WITHOUT breaking changes

**Independent Test**: All existing Calendar tests pass; no changes to public API or behavior

### GCalClient Refactoring Tasks

- [x] T027 [US1] [US2] Modify GCalClient.**init** to call super().**init**(config, "calendar", "v3", service) in src/caltool/gcal_client.py
- [x] T028 [US1] [US2] Remove authenticate() method from GCalClient (now handled by base class via GoogleAuth)
- [x] T029 [US1] [US2] Remove retry_on_exception decorator from GCalClient (now inherited from base class)
- [x] T030 [US1] [US2] Update GCalClient error handling to use base class handle_api_error() method
- [x] T031 [US1] [US2] Run ALL existing tests in tests/test_cli.py and verify 100% pass (backward compatibility check)
- [x] T032 [US1] [US2] Run tests/test_backward_compatibility.py to verify contract preservation
- [x] T033 [US1] [US2] Verify Calendar CLI commands work unchanged: `caltool get-calendars`, `caltool free today+1`

**Checkpoint P1 Stories (US1, US2, US5)**: Architectural foundation complete; Calendar functionality unchanged; ready for Gmail implementation

---

## Phase 7: User Story 3 - Gmail Client MVP (Priority: P2) 🎯 FEATURE DELIVERY

**Goal**: Implement Gmail client with list messages functionality using shared auth and base client pattern

**Independent Test**: `caltool gmail list` retrieves and displays Gmail messages successfully

### US3 Tasks - Gmail Client Implementation

- [x] T034 [P] [US3] Create src/caltool/gmail_client.py with GMailClient class inheriting from GoogleAPIClient
- [x] T035 [US3] Implement GMailClient.**init**(config, service) calling super().**init**(config, "gmail", "v1", service)
- [x] T036 [US3] Write tests for GMailClient initialization in tests/test_gmail_client.py (TDD: tests fail initially)
- [x] T037 [US3] Implement GMailClient.list_messages(query, max_results) method with Gmail API messages().list() call
- [x] T038 [US3] Add error handling to list_messages using base class categorize_error() and handle_api_error()
- [x] T039 [US3] Implement GMailClient.get_message(message_id) for retrieving individual message details
- [x] T040 [US3] Add retry decorator to Gmail API methods (inherited from base class)
- [x] T041 [US3] Run tests in tests/test_gmail_client.py and verify all pass (TDD green phase)
- [x] T042 [US3] Test Gmail client with mock API responses (rate limit 429, quota exceeded 403, success 200)

### US3 Tasks - CLI Integration

- [x] T043 [US3] Add `gmail` command group to src/caltool/cli.py using click.group()
- [x] T044 [US3] Implement `caltool gmail list` command with --limit and --query options
- [x] T045 [US3] Add --format option to gmail commands (json, pretty) using existing format.py helpers
- [x] T046 [US3] Implement message formatting in src/caltool/format.py for human-readable Gmail output
- [x] T047 [US3] Add error handling to gmail CLI commands using handle_cli_exception from errors.py
- [x] T048 [US3] Test gmail list command end-to-end with real Google account (manual testing)

**Checkpoint US3**: Gmail client MVP complete; `caltool gmail list` works end-to-end

---

## Phase 8: User Story 4 - Configuration Extension (Priority: P2) 🎯 UX POLISH

**Goal**: Extend configuration system to support Gmail scopes and settings interactively

**Independent Test**: `caltool config` allows users to add/edit Gmail scopes and shows Gmail-specific options

### US4 Tasks - Config Schema Extension

- [x] T049 [P] [US4] Extend DEFAULTS in src/caltool/config.py to include gmail.readonly scope example (commented out by default)
- [x] T050 [US4] Add Gmail scope options to Config.prompt() method with clear descriptions
- [x] T051 [US4] Update Config.validate() to check for Gmail scopes when Gmail commands are used
- [x] T052 [P] [US4] Add Gmail-specific config options (e.g., DEFAULT_LABEL, MAX_MESSAGES) to config schema
- [x] T053 [US4] Implement scope selection menu in config command (checkboxes for Calendar, Gmail, Drive, etc.)
- [x] T054 [US4] Test config command interactively: add Gmail scope, verify token refresh triggered
- [x] T055 [US4] Update tests/test_config.py to cover Gmail scope validation and prompting

### US4 Tasks - Scope Error Handling

- [x] T056 [US4] Add scope validation check in gmail commands (error if Gmail scope missing)
- [x] T057 [US4] Implement user-friendly error message: "Gmail scope not configured. Run 'caltool config' to add Gmail permissions."
- [x] T058 [US4] Test error flow: remove Gmail scope, run `caltool gmail list`, verify clear error message

**Checkpoint US4**: Configuration UX complete; users can self-serve Gmail setup

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Documentation, logging enhancements, edge case handling, and final validation

### Documentation

- [x] T059 [P] Update README.md with Gmail functionality examples (`caltool gmail list`, scope configuration)
- [x] T060 [P] Update .github/copilot-instructions.md with new module responsibilities (google_auth, google_client, gmail_client)
- [x] T061 [P] Add docstrings to all new public methods (GoogleAuth, GoogleAPIClient, GMailClient) per constitution

### Logging & Observability

- [x] T062 [P] Add structured logging to GoogleAuth (auth flow steps, scope changes, token refresh)
- [x] T063 [P] Add structured logging to GMailClient (API calls, message counts, errors)
- [x] T064 Verify all error messages are user-friendly and non-technical (no stack traces exposed)

### Edge Case Handling

- [x] T065 Test offline behavior: disconnect internet, run gmail command, verify graceful error
- [x] T066 Test account switching: delete token file, re-authenticate with different account, verify works
- [x] T067 Test scope revocation: revoke Gmail scope in Google Account settings, run command, verify clear re-auth guidance
- [x] T068 Test missing credentials file: delete credentials.json, run command, verify helpful error message

### Final Validation

- [x] T069 Run full test suite: `uv run pytest` (all tests must pass)
- [x] T070 Verify test coverage >80% for new modules (google_auth, google_client, gmail_client)
- [x] T071 Run type checking: `mypy src/caltool/` (no type errors)
- [x] T072 Run linting: `ruff check src/` (no violations)
- [x] T073 Verify all 5 constitution principles satisfied (separation, TDD, types, CLI, PEP8)
- [x] T074 Test all Calendar commands still work: get-calendars, free, show-events (regression check)

**Checkpoint**: Feature complete, tested, documented, and ready for release

---

## Dependency Graph

### Story Completion Order

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation)
    ↓
Phase 3 (US5: Module Organization) ← ARCHITECTURAL
    ↓
Phase 4 (US1: Shared Auth) ← FOUNDATION ←┐
    ↓                                      │
Phase 5 (US2: Base Client) ← FOUNDATION ←┤ P1 (parallel after US5)
    ↓                                      │
Phase 6 (US1+US2: GCalClient Refactor) ←┘ CRITICAL (must verify backward compat)
    ↓
Phase 7 (US3: Gmail Client MVP) ← P2 (depends on P1 complete)
    ↓
Phase 8 (US4: Config Extension) ← P2 (parallel with US3 after foundation)
    ↓
Phase 9 (Polish & Validation)
```

### Parallel Execution Opportunities

**After Phase 3 (US5 complete)**:

- US1 tasks (T012-T019) and US2 tasks (T020-T026) can run in parallel
- Both build on US5 module structure but are independent

**After Phase 6 (P1 complete)**:

- US3 Gmail implementation (T034-T048) and US4 Config extension (T049-T058) can run in parallel
- Both depend on P1 foundation but are independent features

**During Phase 9**:

- Documentation tasks (T059-T061), logging tasks (T062-T064), and edge case tests (T065-T068) can all run in parallel

---

## Task Summary

- **Total Tasks**: 74 tasks
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundation)**: 4 tasks
- **Phase 3 (US5 - Module Org)**: 4 tasks
- **Phase 4 (US1 - Shared Auth)**: 8 tasks
- **Phase 5 (US2 - Base Client)**: 7 tasks
- **Phase 6 (US1+US2 Integration)**: 7 tasks
- **Phase 7 (US3 - Gmail MVP)**: 15 tasks
- **Phase 8 (US4 - Config)**: 10 tasks
- **Phase 9 (Polish)**: 16 tasks

**Parallelizable Tasks**: 18 tasks marked with [P]

**Critical Path**: Setup → Foundation → US5 → US1 → US2 → GCalClient Refactor → US3 → US4 → Polish

**Suggested MVP Scope** (minimum viable product):

- Phase 1-6 only (US1, US2, US5 - architectural foundation + GCalClient refactored)
- Delivers: Clean architecture, backward compatible, ready for Gmail
- Defers: Gmail client (US3) and config UX (US4) to iteration 2

**Full Feature Scope**:

- All 9 phases (includes Gmail functionality and polished config UX)

---

## Implementation Strategy

### TDD Workflow (Per Constitution Principle II)

For each user story:

1. **Write tests first** (T010, T011, T018, T026, T036, T041) - tests MUST fail initially
2. **Implement to pass tests** (T012-T017, T020-T025, T034-T041)
3. **Refactor** while keeping tests green
4. **Validate** backward compatibility (T031-T033, T074)

### Backward Compatibility Gates

**CRITICAL**: Tasks T031-T033 are BLOCKING for Phase 7+

- If ANY existing Calendar test fails after GCalClient refactoring → STOP
- Root cause and fix before proceeding to Gmail implementation
- Success Criterion SC-002 requires 100% Calendar functionality preserved

### Constitution Compliance Checklist

- ✅ **Separation of Concerns** (Principle I): US5 enforces module isolation
- ✅ **Test-First Development** (Principle II): TDD tasks in every phase
- ✅ **Type Safety** (Principle III): T061 ensures docstrings, T071 validates types
- ✅ **CLI-First** (Principle IV): T043-T048 deliver CLI interface
- ✅ **PEP8** (Principle V): T072 validates style compliance

---

**Tasks Ready for Implementation** ✅
**Start with**: Phase 1 (T001-T003) to establish baseline
