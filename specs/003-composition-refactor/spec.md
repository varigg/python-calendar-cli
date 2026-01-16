# Feature Specification: Composition-Based Architecture Migration

**Feature Branch**: `003-composition-refactor`
**Created**: January 15, 2026
**Status**: ✅ COMPLETE
**Input**: User description: "Migrate Google API clients from inheritance to composition-based architecture for better testability and separation of concerns"

## User Scenarios & Testing

### User Story 1 - Extract Reusable Components (Priority: P1) ✅

As a developer, I want error categorization, retry logic, and service building to be standalone components so that I can test, reuse, and modify them independently without affecting the entire client hierarchy.

**Why this priority**: Foundation for all other changes. These components are needed before we can refactor clients. Delivers immediate value by making core logic testable in isolation.

**Independent Test**: Can be fully tested by creating ErrorCategorizer, RetryPolicy, and ServiceFactory instances directly, calling their methods with various inputs, and asserting outputs without any Google API client instances.

**Acceptance Scenarios**:

1. Given an HTTP 401 error, When ErrorCategorizer.categorize() is called, Then it returns "AUTH"
2. Given an HTTP 429 error, When ErrorCategorizer.categorize() is called, Then it returns "QUOTA"
3. Given an HTTP 500 error, When ErrorCategorizer.categorize() is called, Then it returns "TRANSIENT"
4. Given a function that fails twice then succeeds, When RetryPolicy.execute() is called with max_retries=3, Then the function succeeds on third attempt
5. Given an AUTH error, When RetryPolicy.should_retry() is called, Then it returns False
6. Given valid GoogleAuth, When ServiceFactory.build_service() is called with "calendar" and "v3", Then it returns a working Calendar service

### User Story 2 - Create Composition-Based Calendar Client (Priority: P2) ✅

As a developer, I want a composition-based GCalClient that accepts ServiceFactory and RetryPolicy as dependencies so that I can test it with constructor injection instead of monkey patching.

**Why this priority**: Calendar is the core feature. Refactoring it validates the composition pattern.

**Acceptance Scenarios**:

1. Given a mock service, When GCalClientV2.get_calendar_list() is called, Then it returns calendars without @patch
2. Given a mock service that raises HttpError, When GCalClientV2 method is called, Then RetryPolicy.execute() is invoked

### User Story 3 - Create Composition-Based Gmail Client (Priority: P3) ✅

As a developer, I want a composition-based GMailClient following the same pattern.

**Acceptance Scenarios**:

1. Given a mock service, When GMailClientV2.list_messages() is called, Then it returns messages without @patch
2. Given missing Gmail scope, When GMailClientV2 is instantiated, Then it raises CLIError

### User Story 4 - Update CLI to Use Composed Clients (Priority: P4) ✅

As a CLI user, I want the application to continue working exactly as before.

**Acceptance Scenarios**:

1. Given CLI uses composed clients, When CLI commands are executed, Then behavior is identical to before (same arguments, same output)
2. Given old internal tests deleted, When new behavioral tests run, Then all tests pass

## Functional Requirements

### Core Components

**FR-001**: ✅ System MUST provide an ErrorCategorizer class with categorize(error: HttpError) -> str method returning "AUTH", "QUOTA", "TRANSIENT", or "CLIENT"

**FR-002**: ✅ System MUST provide a RetryPolicy class that accepts max_retries, delay, and optional ErrorCategorizer; provides should_retry() and execute() methods; does NOT retry AUTH/CLIENT errors; DOES retry QUOTA/TRANSIENT errors

**FR-003**: ✅ System MUST provide a ServiceFactory class that accepts GoogleAuth and provides build_service(api_name, api_version) method

### Composed Clients

**FR-004**: ✅ System MUST provide GCalClientV2 that accepts ServiceFactory, optional RetryPolicy, optional service; does NOT inherit from GoogleAPIClient; provides same public API as GCalClient

**FR-005**: ✅ System MUST provide GMailClientV2 following same pattern as GCalClientV2

**FR-006**: ✅ All component classes MUST be testable without mock.patch decorators

**FR-007**: ✅ Composed clients MUST be testable by injecting mock dependencies via constructor

**FR-008**: ✅ System MUST maintain backward compatibility - CLI commands, arguments, and output unchanged; internal test structure may change

**FR-009**: ✅ All tests MUST use module-level imports; MUST NOT use test classes unless necessary; MUST use dependency injection over monkeypatch; MUST focus on high-value code paths (no testing constants or Python behavior)

## Success Criteria

**SC-001**: ✅ ErrorCategorizer correctly categorizes 100% of error types in under 1ms per call

**SC-002**: ✅ RetryPolicy successfully retries QUOTA/TRANSIENT errors up to max_retries

**SC-003**: ✅ New test suites require zero @patch decorators and focus on high-value code paths (no testing constants or Python built-in behavior)

**SC-004**: ✅ Composed clients testable in under 10 lines of test code per method

**SC-005**: ✅ CLI commands work unchanged; old internal-structure tests deleted/replaced; behavioral tests verified

**SC-006**: ✅ Test execution faster (2.30s for 95 tests vs previous baseline)
