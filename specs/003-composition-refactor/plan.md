# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Migrate Google API clients from inheritance-based architecture to composition-based architecture to improve testability, separation of concerns, and code reuse. The migration extracts three reusable components (ErrorCategorizer, RetryPolicy, ServiceFactory) and refactors GCalClient and GMailClient to use constructor injection instead of abstract base class inheritance. This eliminates the need for `@patch` decorators in tests, improves code clarity, and enables independent testing of each concern.

**Technical Approach**:

- Phase 1: Extract ErrorCategorizer, RetryPolicy, and ServiceFactory as standalone components
- Phase 2: Create GCalClientV2 with composition pattern, test without @patch
- Phase 3: Create GMailClientV2 with composition pattern, test without @patch
- Phase 4: Update CLI to use composed clients, maintain 100% backward compatibility
- Phase 5: Deprecate GoogleAPIClient inheritance pattern, remove old clients

## Technical Context

**Language/Version**: Python 3.12.11
**Primary Dependencies**: google-auth, google-auth-oauthlib, google-api-python-client, click 8.x, pytest 8.3.5
**Storage**: N/A (token persistence via google_auth)
**Testing**: pytest with 88 existing tests, 72% coverage, mocks for Google APIs
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single Python CLI application
**Performance Goals**: API calls <1s each; test suite <10s; no degradation from refactoring
**Constraints**: Must maintain 100% backward compatibility with CLI behavior (commands, arguments, output); zero breaking changes to public API; internal test structure may change
**Scale/Scope**: ~2500 LOC across 10 modules; 88 tests; two Google API clients (Calendar, Gmail)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

✅ **Separation of Concerns**: Composition pattern directly addresses SoC violation in GoogleAPIClient inheritance. ErrorCategorizer, RetryPolicy, and ServiceFactory separate error handling, retry logic, and service building from client logic.

✅ **Test-First Development**: Feature spec includes 18 acceptance scenarios (6 per P1 user story). Implementation will use TDD—tests written before code. All new components testable without @patch decorators.

✅ **Type Safety & Documentation**: Python 3.12.11 with type hints. All three new components will have full docstrings and type annotations. Composed clients will maintain type safety of original clients.

✅ **CLI-First Design**: CLI behavior unchanged—refactoring is internal only. CLI commands, arguments, and output preserved. Internal tests updated to match new architecture.

✅ **PEP8 & Best Practices**: Code follows existing project style. New modules will be added to `src/caltool/`. All imports absolute, no circular dependencies.

**Gate Status**: ✅ PASS - Feature aligns with all five core principles. Composition pattern strengthens SoC principle.

## Project Structure

### Documentation (this feature)

```text
specs/003-composition-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 research (if needed)
├── data-model.md        # Phase 1 design (if needed)
├── quickstart.md        # Phase 1 quickstart (if needed)
├── contracts/           # Phase 1 API contracts (if needed)
└── tasks.md             # Phase 2 task breakdown (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/caltool/
├── google_client.py        # DEPRECATED: Will remain for backward compatibility
├── gcal_client.py          # DEPRECATED: Will remain after GCalClientV2 complete
├── gmail_client.py         # DEPRECATED: Will remain after GMailClientV2 complete
├── error_categorizer.py    # NEW: Phase 1 - Extract from google_client.py
├── retry_policy.py         # NEW: Phase 1 - Extract from google_client.py
├── service_factory.py       # NEW: Phase 1 - Extract from google_client.py
├── gcal_client_v2.py       # NEW: Phase 2 - Composition-based calendar client
├── gmail_client_v2.py      # NEW: Phase 3 - Composition-based Gmail client
└── cli.py                  # MODIFIED: Phase 4 - Use composed clients (no breaking changes)

tests/
├── test_google_client.py    # DELETED: Tests old inheritance internals
├── test_gcal_client.py      # DELETED: Tests old inheritance internals
├── test_gmail_client.py     # DELETED: Tests old inheritance internals
├── test_error_categorizer.py     # NEW: Phase 1
├── test_retry_policy.py          # NEW: Phase 1
├── test_service_factory.py       # NEW: Phase 1
├── test_gcal_client_v2.py        # NEW: Phase 2
├── test_gmail_client_v2.py       # NEW: Phase 3
└── test_cli.py              # MODIFIED: Replace old @patch-based tests, keep behavioral tests
```

**Structure Decision**: Single Python CLI application (Option 1). Composition refactoring adds 3 new standalone components (`error_categorizer.py`, `retry_policy.py`, `service_factory.py`) and 2 new client implementations (`gcal_client_v2.py`, `gmail_client_v2.py`). Old inheritance-based clients remain for backward compatibility during migration phase. CLI uses composed clients transparently; no breaking changes to public API.

## Complexity Tracking

> **All Constitution Check gates passed. No violations to justify.**

✅ Feature aligns with all core principles. Composition pattern actually _improves_ adherence to Separation of Concerns principle by breaking monolithic GoogleAPIClient into discrete, single-purpose components. No complexity trade-offs needed.
