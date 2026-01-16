# Implementation Plan: DRY/SOLID Code Cleanup

**Branch**: `002-dry-solid-cleanup` | **Date**: January 15, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-dry-solid-cleanup/spec.md`

## Summary

Refactor the calendarcli codebase to eliminate duplicate code (DRY), remove dead code (YAGNI), simplify abstractions (KISS), and fix SOLID principle violations. This is a pure refactoring effort with no user-facing changes—all existing tests must continue to pass.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: click, google-api-python-client, google-auth-oauthlib  
**Storage**: JSON config files (~/.config/caltool/)  
**Testing**: pytest with mocks for Google API  
**Target Platform**: Linux/macOS/Windows CLI  
**Project Type**: Single project (CLI application)  
**Performance Goals**: N/A (refactoring only)  
**Constraints**: All existing tests must pass; no breaking changes to CLI interface  
**Scale/Scope**: ~1500 LOC across 10 source modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Separation of Concerns | ✅ PASS | Refactoring maintains module boundaries |
| II. Test-First Development | ✅ PASS | Existing tests validate refactoring; no new features |
| III. Type Safety & Documentation | ✅ PASS | Preserved during refactoring |
| IV. CLI-First Design | ✅ PASS | No CLI interface changes |
| V. PEP8 & Best Practices | ✅ PASS | Refactoring improves compliance (import organization) |

**Error Handling**: Refactoring CLI exception handlers to catch specific exceptions (CLIError, GoogleAuthError) improves compliance with constitution's error handling requirements.

## Project Structure

### Documentation (this feature)

```text
specs/002-dry-solid-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal - straightforward refactor)
├── tasks.md             # Phase 2 output
└── checklists/
    └── requirements.md  # Spec validation checklist
```

### Source Code (existing structure - no changes)

```text
src/caltool/
├── __init__.py
├── cli.py               # FR-005, FR-006: Exception handling changes
├── config.py            # FR-002: Remove duplicate methods (lines 63-99)
├── datetime_utils.py    # No changes
├── errors.py            # FR-003: Remove unused cli_error()
├── format.py            # FR-007: Move import to module level
├── gcal_client.py       # FR-009: Remove unnecessary _validate_config override
├── gmail_client.py      # FR-007: Remove local CLIError import
├── google_auth.py       # No changes
├── google_client.py     # FR-001, FR-004, FR-008: Remove duplicate retry, fix abstractmethod
└── scheduler.py         # No changes

tests/
├── test_cli.py          # Verify exception handling still works
├── test_config.py       # Verify Gmail scope methods work
├── test_errors.py       # Verify CLIError still works (cli_error removed)
├── test_google_client.py # Verify retry decorator still works
└── [other test files]   # Must continue passing
```

## Files Changed Summary

| File | Changes | Requirements |
|------|---------|--------------|
| `config.py` | Remove lines 63-99 (duplicate methods) | FR-002 |
| `errors.py` | Remove `cli_error()` function | FR-003 |
| `google_client.py` | Remove `retry_on_exception()` method; remove `@abstractmethod` from `_validate_config` | FR-001, FR-004, FR-008 |
| `gcal_client.py` | Remove `_validate_config()` override | FR-009 |
| `gmail_client.py` | Remove local `from .errors import CLIError` import | FR-007 |
| `format.py` | Move `from collections import defaultdict` to module level | FR-007 |
| `cli.py` | Change `except Exception` to `except (CLIError, google.auth.exceptions.GoogleAuthError)` | FR-005, FR-006 |

## Complexity Tracking

No constitution violations. This refactoring reduces complexity.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Removing duplicate breaks some code path | Low | Medium | Run full test suite after each change |
| Exception handling change breaks CLI UX | Low | High | Test each CLI command manually; preserve user-friendly messages |
| Circular import from moving imports | Low | Low | Test imports in isolation; revert if needed |

## Phase 0: Research Summary

**No NEEDS CLARIFICATION items.** This is a straightforward refactoring task with clear targets:

1. **Duplicate code locations**: Confirmed via grep search
   - `config.py`: Lines 63-99 duplicate lines 215-256
   - `google_client.py`: `retry_on_exception()` duplicates `@retry` decorator

2. **Dead code confirmed unused**:
   - `cli_error()` in errors.py: Zero usages in codebase
   - `retry_on_exception()`: Zero usages in codebase

3. **Import patterns confirmed**:
   - `format.py:116`: Local import of `defaultdict`
   - `gmail_client.py:48`: Local import of `CLIError`

4. **Exception handling locations**: 8 instances in cli.py (lines 40, 95, 106, 136, 147, 174, 190, 209)

## Phase 1: Design (N/A for refactoring)

This feature involves no new data models, APIs, or contracts. It's pure code cleanup.

## Implementation Order

Execute in this order to minimize risk:

1. **P3: Dead code removal** (lowest risk, immediate cleanup)
   - Remove `cli_error()` from errors.py
   - Remove `retry_on_exception()` from google_client.py

2. **P1: Duplicate method removal** (medium risk, careful verification)
   - Remove duplicate methods from config.py (lines 63-99)
   - Remove `@abstractmethod` from `_validate_config()` in google_client.py
   - Remove unnecessary `_validate_config()` override from gcal_client.py

3. **P4: Import cleanup** (low risk, style only)
   - Move `defaultdict` import to top of format.py
   - Remove local `CLIError` import from gmail_client.py

4. **P2: Exception handling** (highest risk, test thoroughly)
   - Update all 8 `except Exception` blocks in cli.py
   - Add `import google.auth.exceptions` to cli.py

5. **Final verification**
   - Run full test suite
   - Manual CLI smoke test
