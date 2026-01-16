# Task Breakdown: Composition-Based Architecture Migration

**Feature**: `003-composition-refactor`
**Branch**: `003-composition-refactor`
**Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)
**Total Tasks**: 48 | **Phases**: 6 | **Test-First**: Yes

## Phase 1: Setup (Infrastructure & Testing Foundation)

Goal: Prepare test infrastructure and project structure for composition refactoring.
Independent Test: All tests pass; project structure ready for feature implementation.

- [ ] T001 Create project structure and documentation skeleton for feature 003
- [ ] T002 Set up test utilities for composition-based testing (no @patch decorators)
- [ ] T003 Create mock factories for Google Auth, Service, and HttpError instances
- [ ] T004 Document testing strategy: constructor injection, mock dependencies, assertions
- [ ] T005 Verify all 88 existing tests still pass with fresh environment

## Phase 2: Foundational - User Story 1 (P1) - Extract Reusable Components

Goal: Extract three standalone, reusable components from GoogleAPIClient for independent testing and use.
Independent Test: Each component tested directly; zero @patch decorators; >95% coverage per component.
Tests: FR-001, FR-002, FR-003, SC-001, SC-002

**Components to Extract**:
1. `ErrorCategorizer`: Categorizes HttpError into "AUTH", "QUOTA", "TRANSIENT", "CLIENT"
2. `RetryPolicy`: Manages retry logic with smart categorization
3. `ServiceFactory`: Builds Google API service instances

### Component 1: ErrorCategorizer

- [ ] T006 [P] Create test suite for ErrorCategorizer in `tests/test_error_categorizer.py`
  - Tests for 401 → "AUTH" (FR-001)
  - Tests for 429 → "QUOTA" (FR-001)
  - Tests for 500 → "TRANSIENT" (FR-001)
  - Tests for 400 → "CLIENT" (FR-001)
  - Performance test: <1ms per call (SC-001)
- [ ] T007 [P] Implement ErrorCategorizer class in `src/caltool/error_categorizer.py`
  - `categorize(error: HttpError) -> str` method
  - Handle all error types: AUTH, QUOTA, TRANSIENT, CLIENT
  - Type hints and docstrings
- [ ] T008 Verify ErrorCategorizer 95%+ coverage in test suite

### Component 2: RetryPolicy

- [ ] T009 [P] Create test suite for RetryPolicy in `tests/test_retry_policy.py`
  - Tests for initialization with max_retries, delay, ErrorCategorizer
  - Tests for `should_retry()` returning False for AUTH errors (FR-002)
  - Tests for `should_retry()` returning True for QUOTA errors (FR-002)
  - Tests for `execute()` with successful retry (FR-002, SC-002)
  - Tests for `execute()` with max_retries exceeded
  - Tests for exponential backoff behavior
- [ ] T010 [P] Implement RetryPolicy class in `src/caltool/retry_policy.py`
  - `__init__(max_retries: int, delay: float, error_categorizer: ErrorCategorizer)`
  - `should_retry(error_category: str) -> bool` method
  - `execute(func: Callable, *args, **kwargs) -> Any` method with retry loop
  - Exponential backoff: delay * (2 ** attempt)
  - Type hints and docstrings
- [ ] T011 Verify RetryPolicy 95%+ coverage in test suite

### Component 3: ServiceFactory

- [ ] T012 [P] Create test suite for ServiceFactory in `tests/test_service_factory.py`
  - Tests for initialization with GoogleAuth instance
  - Tests for `build_service("calendar", "v3")` returns working service (FR-003)
  - Tests for `build_service("gmail", "v1")` returns working service
  - Tests for error handling when auth fails
  - Mock google_auth.service_account and googleapiclient.discovery
- [ ] T013 [P] Implement ServiceFactory class in `src/caltool/service_factory.py`
  - `__init__(auth: GoogleAuth)`
  - `build_service(api_name: str, api_version: str) -> Any` method
  - Uses `googleapiclient.discovery.build()`
  - Type hints and docstrings
- [ ] T014 Verify ServiceFactory 95%+ coverage in test suite

### Validation Tasks

- [ ] T015 Run all tests for Phase 2 components: pytest tests/test_error_categorizer.py tests/test_retry_policy.py tests/test_service_factory.py
- [ ] T016 Verify zero @patch decorators in Phase 2 tests
- [ ] T017 Verify all three components have >95% coverage
- [ ] T018 Verify all 88 existing tests still pass (baseline unchanged)

## Phase 3: User Story 2 (P2) - Create Composition-Based Calendar Client

Goal: Refactor GCalClient using composition pattern; validate pattern with Calendar API client.
Independent Test: GCalClientV2 fully testable with constructor injection; zero @patch decorators; >95% coverage.
Tests: FR-004, SC-003, SC-004

### GCalClientV2 Implementation

- [ ] T019 [P] [US2] Create test suite for GCalClientV2 in `tests/test_gcal_client_v2.py`
  - Tests for `__init__(service_factory: ServiceFactory, retry_policy: RetryPolicy = None, service: Any = None)`
  - Tests for `get_calendar_list()` returns calendars without @patch (FR-004, FR-007)
  - Tests for `get_events(calendar_id, date_range)` returns events
  - Tests for `get_day_busy_times(calendar_id, date)` returns busy times
  - Tests for `get_event_details(calendar_id, event_id)` returns event details
  - Tests for RetryPolicy.execute() invoked on HttpError (FR-004)
  - Verify each method testable in <10 lines of code (SC-004)
  - Mock service via constructor injection

- [ ] T020 [P] [US2] Extract public API contract from existing GCalClient
  - Document all public methods: get_calendar_list(), get_events(), etc.
  - Document all parameter types and return types
  - Ensure GCalClientV2 will have identical public API

- [ ] T021 [P] [US2] Implement GCalClientV2 class in `src/caltool/gcal_client_v2.py`
  - `__init__(service_factory: ServiceFactory, retry_policy: RetryPolicy = None, service: Any = None)`
  - `get_calendar_list() -> List[Dict]` method
  - `get_events(calendar_id: str, date_range: Tuple[date, date]) -> List[Event]` method
  - `get_day_busy_times(calendar_id: str, date: date) -> List[Tuple[time, time]]` method
  - `get_event_details(calendar_id: str, event_id: str) -> Dict` method
  - Use RetryPolicy.execute() for all API calls
  - Type hints and docstrings
  - Zero inheritance from GoogleAPIClient

- [ ] T022 [US2] Run test suite for GCalClientV2: pytest tests/test_gcal_client_v2.py
- [ ] T023 [US2] Verify zero @patch decorators in GCalClientV2 tests
- [ ] T024 [US2] Verify GCalClientV2 95%+ coverage

## Phase 4: User Story 3 (P3) - Create Composition-Based Gmail Client

Goal: Apply composition pattern to Gmail client; demonstrate pattern scalability.
Independent Test: GMailClientV2 fully testable with constructor injection; zero @patch decorators; >95% coverage.
Tests: FR-005, SC-003, SC-004

### GMailClientV2 Implementation

- [ ] T025 [P] [US3] Create test suite for GMailClientV2 in `tests/test_gmail_client_v2.py`
  - Tests for `__init__(service_factory: ServiceFactory, retry_policy: RetryPolicy = None, service: Any = None)`
  - Tests for `list_messages(query: str, limit: int)` returns messages without @patch (FR-005, FR-007)
  - Tests for `get_message(message_id: str)` returns message details
  - Tests for `delete_message(message_id: str)` returns success
  - Tests for missing Gmail scope raises CLIError (FR-005)
  - Tests for RetryPolicy.execute() invoked on HttpError
  - Verify each method testable in <10 lines of code (SC-004)
  - Mock service and scope validation via constructor injection

- [ ] T026 [P] [US3] Extract public API contract from existing GMailClient
  - Document all public methods: list_messages(), get_message(), delete_message()
  - Document all parameter types and return types
  - Document scope requirements
  - Ensure GMailClientV2 will have identical public API

- [ ] T027 [P] [US3] Implement GMailClientV2 class in `src/caltool/gmail_client_v2.py`
  - `__init__(service_factory: ServiceFactory, retry_policy: RetryPolicy = None, service: Any = None)`
  - `list_messages(query: str, limit: int) -> List[Message]` method
  - `get_message(message_id: str) -> Dict` method
  - `delete_message(message_id: str) -> None` method
  - Scope validation: Raise CLIError if Gmail scope missing
  - Use RetryPolicy.execute() for all API calls
  - Type hints and docstrings
  - Zero inheritance from GoogleAPIClient

- [ ] T028 [US3] Run test suite for GMailClientV2: pytest tests/test_gmail_client_v2.py
- [ ] T029 [US3] Verify zero @patch decorators in GMailClientV2 tests
- [ ] T030 [US3] Verify GMailClientV2 95%+ coverage

## Phase 5: User Story 4 (P4) - Update CLI to Use Composed Clients

Goal: Integrate composed clients into CLI with zero breaking changes; maintain 100% backward compatibility.
Independent Test: All 88 existing CLI tests pass without modification; backward compatibility verified.
Tests: FR-008, SC-005

### CLI Integration

- [ ] T031 [P] [US4] Create instantiation factories for composed clients in `src/caltool/cli.py`
  - Factory function to create GCalClientV2 with proper dependencies
  - Factory function to create GMailClientV2 with proper dependencies
  - Ensure factories use same authentication flow as before

- [ ] T032 [P] [US4] Refactor CLI calendar commands to use GCalClientV2
  - Replace GCalClient usage with GCalClientV2 in `free` command
  - Replace GCalClient usage in `show-events` command
  - Replace GCalClient usage in `get-calendars` command
  - Verify public API identical (no parameter changes)

- [ ] T033 [P] [US4] Refactor CLI Gmail commands to use GMailClientV2
  - Replace GMailClient usage with GMailClientV2 in `gmail list` command
  - Replace GMailClient usage in `gmail show-message` command
  - Replace GMailClient usage in `gmail delete` command
  - Verify public API identical (no parameter changes)

- [ ] T034 [US4] Run all existing CLI tests: pytest tests/test_cli.py
- [ ] T035 [US4] Verify all 88 tests pass without modification (SC-005)
- [ ] T036 [US4] Verify backward compatibility: no breaking changes to CLI commands

### Performance Validation

- [ ] T037 [US4] Benchmark test suite execution time before/after refactoring
  - Measure existing test suite execution time (baseline)
  - Measure refactored test suite execution time
  - Verify 30%+ speedup due to eliminated @patch overhead (SC-006)

## Phase 6: Polish & Cross-Cutting Concerns

Goal: Clean up, deprecate old clients, finalize documentation, ensure code quality.

### Deprecation & Cleanup

- [ ] T038 Add deprecation warnings to GoogleAPIClient in `src/caltool/google_client.py`
  - Document that GoogleAPIClient is deprecated in favor of composition
  - Document migration path to GCalClientV2 and GMailClientV2
  - Deprecation warning will be raised when GoogleAPIClient methods are called

- [ ] T039 Add deprecation warnings to GCalClient in `src/caltool/gcal_client.py`
  - Document that GCalClient is deprecated in favor of GCalClientV2
  - Keep GCalClient functional for backward compatibility during transition period

- [ ] T040 Add deprecation warnings to GMailClient in `src/caltool/gmail_client.py`
  - Document that GMailClient is deprecated in favor of GMailClientV2
  - Keep GMailClient functional for backward compatibility during transition period

### Documentation & Type Safety

- [ ] T041 Add comprehensive docstrings to all three components
  - ErrorCategorizer: Document error categorization strategy
  - RetryPolicy: Document retry logic and backoff strategy
  - ServiceFactory: Document Google API service building
  - Include type hints for all parameters and return types

- [ ] T042 Add comprehensive docstrings to GCalClientV2 and GMailClientV2
  - Document constructor dependencies and optional parameters
  - Document all public methods with parameters and return types
  - Include usage examples in docstrings

- [ ] T043 Update project README.md with architecture section
  - Document composition-based architecture
  - Provide migration guide from old clients to new composed clients
  - Document benefits: testability, separation of concerns, code reuse

### Final Validation

- [ ] T044 Run all tests with coverage: pytest --cov=src/caltool tests/
  - Verify overall project coverage maintained or improved
  - Verify Phase 2, 3, 4 components all >95% coverage
  - Verify no coverage regression in existing modules

- [ ] T045 Run pre-commit hooks: pre-commit run --all-files
  - Verify ruff linting passes
  - Verify ruff formatting passes
  - Verify all other hooks pass

- [ ] T046 Run integration test: full CLI workflow
  - Test `calendarcli get-calendars` works end-to-end
  - Test `calendarcli free today` works end-to-end
  - Test `calendarcli gmail list` works end-to-end (if Gmail enabled)

- [ ] T047 Create MIGRATION.md guide for future contributors
  - Document composition pattern used in project
  - Document how to add new composed clients
  - Document testing strategy without @patch decorators

- [ ] T048 Final verification: Ensure all 88 existing tests pass
  - Run full test suite: pytest tests/
  - Verify no new failures or warnings
  - Verify feature 003 complete and ready for review

## Dependencies & Execution Order

### Critical Path (Blocking Order)
```
Phase 1 (Setup) → Phase 2 (Components) → Phase 3 (Calendar) → Phase 4 (Gmail) → Phase 5 (CLI) → Phase 6 (Polish)
```

### Parallelizable Tasks by Phase

**Phase 2 (Components)**: T006-T014 can run in parallel
- Three components: ErrorCategorizer, RetryPolicy, ServiceFactory
- T006+T007 (ErrorCategorizer) independent
- T009+T010 (RetryPolicy) independent
- T012+T013 (ServiceFactory) independent

**Phase 3 (Calendar)**: T019-T024 parallelizable (single client)
- T019 (tests) can start immediately
- T020 (API contract) can start immediately
- T021 (implementation) depends on T020

**Phase 4 (Gmail)**: T025-T030 parallelizable (single client, same pattern as Phase 3)
- T025 (tests) can start immediately
- T026 (API contract) can start immediately
- T027 (implementation) depends on T026

**Phase 5 (CLI)**: T031-T037 parallelizable (independent command groups)
- T031 (factories) prerequisite for all others
- T032 (calendar commands) independent of T033 (Gmail commands)

## Success Criteria Mapping

| Success Criteria | Validation Task |
|-----------------|-----------------|
| SC-001: <1ms per ErrorCategorizer call | T006 (performance test) |
| SC-002: Retry succeeds within max_retries | T009 (execute test) |
| SC-003: Zero @patch decorators, 95%+ coverage | T016, T023, T029 |
| SC-004: Methods testable in <10 lines | T019, T025 |
| SC-005: All 88 existing tests pass | T035, T048 |
| SC-006: 30%+ test execution speedup | T037 (benchmark) |

## Implementation Notes

### Testing Strategy (TDD Approach)
1. **Write tests first** for each component (T006, T009, T012)
2. **Implement component** to pass tests (T007, T010, T013)
3. **Verify coverage** >95% (T008, T011, T014)
4. **Repeat for clients** (phases 3-4)
5. **Integrate with CLI** (phase 5)
6. **Polish and finalize** (phase 6)

### No @patch Decorators
All new tests use constructor injection for dependencies:
```python
# Instead of:
@patch('google_client.build_service')
def test_client(mock_build):
    client = GCalClient()

# Use:
def test_client(mock_service_factory):
    client = GCalClientV2(service_factory=mock_service_factory)
```

### Backward Compatibility
- Old clients (GCalClient, GMailClient) remain functional
- CLI transparently uses new composed clients
- No changes to CLI commands, arguments, or output
- All 88 existing tests pass without modification
