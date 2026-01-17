# Tasks: Layer Separation Enforcement

**Feature**: Layer Separation Enforcement
**Branch**: `006-layer-separation`
**Input**: Design documents from `/specs/006-layer-separation/`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline and prepare exception infrastructure

- [ ] T001 Run full test suite to establish baseline (all tests must pass)
- [ ] T002 [P] Add ConfigError base class to src/gtool/infrastructure/exceptions.py
- [ ] T003 [P] Document exception hierarchy in src/gtool/infrastructure/exceptions.py docstrings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core exception infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Verify AuthError and ServiceError exist in src/gtool/infrastructure/exceptions.py
- [ ] T005 [P] Search codebase for all `import click` usage in infrastructure and config layers
- [ ] T006 [P] Search codebase for all `from gtool.cli` imports in infrastructure and config layers
- [ ] T007 Document all callsites that will need updates in implementation notes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Infrastructure Reusability (Priority: P1) 🎯 MVP

**Goal**: Remove CLI dependencies from infrastructure layer enabling reuse in non-CLI contexts

**Independent Test**: Import `gtool.infrastructure.auth` and `gtool.infrastructure.retry` without `click` installed

### Implementation for User Story 1

- [ ] T008 [US1] Remove `import click` from src/gtool/infrastructure/auth.py
- [ ] T009 [US1] Remove CLI error references from docstrings in src/gtool/infrastructure/auth.py
- [ ] T010 [US1] Verify AuthError is used consistently in src/gtool/infrastructure/auth.py
- [ ] T011 [US1] Update src/gtool/infrastructure/retry.py to import AuthError instead of CLI AuthenticationError
- [ ] T012 [US1] Replace AuthenticationError with AuthError in src/gtool/infrastructure/retry.py exception handling
- [ ] T013 [US1] Update error messages in src/gtool/infrastructure/retry.py to be CLI-agnostic
- [ ] T014 [US1] Update tests/test_google_auth.py to expect AuthError instead of CLI exceptions
- [ ] T015 [US1] Update tests/test_retry_policy.py to expect AuthError instead of CLI exceptions
- [ ] T016 [US1] Add test in tests/test_google_auth.py verifying infrastructure imports without click
- [ ] T017 [US1] Create demonstration test in tests/test_non_cli_usage.py showing API server usage pattern
- [ ] T018 [US1] Run infrastructure tests to verify US1 complete (uv run pytest tests/test_google_auth.py tests/test_retry_policy.py)

**Checkpoint**: Infrastructure layer is CLI-independent and reusable

---

## Phase 4: User Story 2 - Config Layer Testability (Priority: P2)

**Goal**: Remove CLI dependencies from config layer enabling programmatic testing

**Independent Test**: Create and validate Config object without `click` imports

### Implementation for User Story 2

- [ ] T019 [US2] Add ConfigValidationError class inheriting from ConfigError in src/gtool/config/settings.py
- [ ] T020 [US2] Remove `import click` from src/gtool/config/settings.py
- [ ] T021 [US2] Replace all `raise click.UsageError` with `raise ConfigValidationError` in src/gtool/config/settings.py
- [ ] T022 [US2] Remove Config.prompt() method from src/gtool/config/settings.py
- [ ] T023 [US2] Update src/gtool/config/settings.py docstrings to remove click references
- [ ] T024 [US2] Update tests/test_config.py to import ConfigValidationError
- [ ] T025 [US2] Update tests/test_config.py to expect ConfigValidationError instead of click.UsageError
- [ ] T026 [US2] Remove click.prompt mocking from tests/test_config.py if present
- [ ] T027 [US2] Add test in tests/test_config.py verifying config imports without click
- [ ] T028 [US2] Add test in tests/test_config.py for programmatic config validation
- [ ] T029 [US2] Run config tests to verify US2 complete (uv run pytest tests/test_config.py)

**Checkpoint**: Config layer is CLI-independent and testable

---

## Phase 5: User Story 3 - CLI Error Mapping (Priority: P3)

**Goal**: Add exception translation in CLI layer for user-friendly error messages

**Independent Test**: Trigger infrastructure errors and verify CLI translates to user-friendly messages

### Implementation for User Story 3

- [ ] T030 [US3] Create handle_infrastructure_errors decorator in src/gtool/cli/main.py
- [ ] T031 [US3] Implement AuthError → AuthenticationError translation in decorator
- [ ] T032 [US3] Implement ServiceError → CLIError translation in decorator
- [ ] T033 [US3] Implement ConfigValidationError → click.UsageError translation in decorator
- [ ] T034 [US3] Apply @handle_infrastructure_errors decorator to all calendar commands in src/gtool/cli/main.py
- [ ] T035 [US3] Apply @handle_infrastructure_errors decorator to all gmail commands in src/gtool/cli/main.py
- [ ] T036 [US3] Apply @handle_infrastructure_errors decorator to config command in src/gtool/cli/main.py
- [ ] T037 [US3] Create prompt_config_interactive() function in src/gtool/cli/main.py
- [ ] T038 [US3] Implement user input prompting logic in prompt_config_interactive() using click.prompt
- [ ] T039 [US3] Implement config.set() calls for each config value in prompt_config_interactive()
- [ ] T040 [US3] Add validation and save logic in prompt_config_interactive() with ConfigValidationError handling
- [ ] T041 [US3] Update config command in src/gtool/cli/main.py to call prompt_config_interactive()
- [ ] T042 [US3] Add test in tests/test_cli.py for AuthError → AuthenticationError translation
- [ ] T043 [US3] Add test in tests/test_cli.py for ServiceError → CLIError translation
- [ ] T044 [US3] Add test in tests/test_cli.py for ConfigValidationError → click.UsageError translation
- [ ] T045 [US3] Add test in tests/test_cli.py for prompt_config_interactive() function
- [ ] T046 [US3] Run CLI tests to verify US3 complete (uv run pytest tests/test_cli.py)

**Checkpoint**: All user stories independently functional, exceptions properly mapped

---

## Phase 6: Integration Testing (High-Value Tests Only)

**Purpose**: Add targeted integration tests that catch real bugs (like ServiceFactory credentials issue)

**Testing Philosophy**: Mock only external Google API calls, test internal integration

- [ ] T047 [P] [INT] Add integration test in tests/test_google_auth.py for missing credentials file raising AuthError
- [ ] T048 [P] [INT] Add integration test in tests/test_service_factory.py verifying get_credentials() is called (not credentials property)
- [ ] T049 [P] [INT] Add integration test in tests/test_config.py for scope validation with missing Gmail scopes
- [ ] T050 [INT] Add integration test verifying Config → GoogleAuth → ServiceFactory initialization flow
- [ ] T051 [INT] Add integration test for exception propagation from infrastructure through CLI translation
- [ ] T052 [INT] Add integration test verifying token refresh failure raises AuthError (not CLI exception)
- [ ] T053 [INT] Run integration tests to ensure they catch real bugs (uv run pytest tests/test\__integration_.py -v)

**Checkpoint**: Integration tests verify real flows, catching bugs that mocks hide

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [ ] T054 [P] Run full test suite and verify 100% pass rate (uv run pytest)
- [ ] T055 [P] Verify zero click imports in infrastructure (grep -r "import click" src/gtool/infrastructure/)
- [ ] T056 [P] Verify zero click imports in config (grep -r "import click" src/gtool/config/)
- [ ] T057 [P] Verify zero CLI imports in infrastructure (grep -r "from gtool.cli" src/gtool/infrastructure/)
- [ ] T058 [P] Verify zero CLI imports in config (grep -r "from gtool.cli" src/gtool/config/)
- [ ] T059 Manual test: Run gtool config command and verify interactive prompting works
- [ ] T060 Manual test: Run gtool get-calendars and verify auth error handling works
- [ ] T061 Manual test: Run gtool gmail list and verify error handling works
- [ ] T062 [P] Update project documentation if needed (README.md) with exception architecture
- [ ] T063 Run quickstart.md validation to ensure developer onboarding guide is accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run parallel with US1)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion (needs infrastructure exceptions available)
- **Integration Testing (Phase 6)**: Depends on all user stories being complete
- **Polish (Phase 7)**: Depends on integration tests passing

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run parallel with US1
- **User Story 3 (P3)**: MUST complete after US1 and US2 - Depends on infrastructure exceptions being established

### Within Each User Story

**User Story 1**:

1. Remove click imports first (T008-T009)
2. Verify AuthError usage (T010)
3. Update retry module (T011-T013)
4. Update tests (T014-T017)
5. Validate (T018)

**User Story 2**:

1. Add ConfigValidationError (T019)
2. Remove click (T020-T023)
3. Update tests (T024-T028)
4. Validate (T029)

**User Story 3**:

1. Create decorator (T030-T033)
2. Apply to commands (T034-T036)
3. Implement prompting (T037-T041)
4. Add tests (T042-T045)
5. Validate (T046)

### Parallel Opportunities

- **Phase 1**: All tasks marked [P] can run in parallel (T002, T003)
- **Phase 2**: All tasks marked [P] can run in parallel (T005, T006)
- **User Story 1 & 2**: Can be implemented in parallel by different developers (after Phase 2)
- **Phase 6**: All tasks marked [P] and [INT] can run in parallel (T047-T049)
- **Phase 7**: All tasks marked [P] can run in parallel (T054-T058, T062)

---

## Parallel Example: User Story 1 & 2

```bash
# Developer A works on User Story 1 (Infrastructure):
Task T008: Remove click from auth.py
Task T011: Update retry.py imports
Task T014: Update test_google_auth.py

# Developer B works on User Story 2 (Config) in parallel:
Task T019: Add ConfigValidationError
Task T020: Remove click from settings.py
Task T024: Update test_config.py

# Both stories complete independently, then merge for User Story 3
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (establish baseline)
2. Complete Phase 2: Foundational (verify exception infrastructure)
3. Complete Phase 3: User Story 1 (infrastructure reusability)
4. **STOP and VALIDATE**: Test US1 independently
5. Demonstrate infrastructure usage in non-CLI context

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Infrastructure reusable! (MVP)
3. Add User Story 2 → Test independently → Config testable!
4. Add User Story 3 → Test independently → Complete feature with error mapping!
5. Polish phase → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T007)
2. Once Foundational is done:
   - Developer A: User Story 1 (T008-T018)
   - Developer B: User Story 2 (T019-T029)
3. After US1 and US2 complete:
   - Developer C or A+B: User Story 3 (T030-T046)
4. All developers: Polish phase (T047-T056)

---

## Validation Checkpoints

### After User Story 1 (T018)

```bash
# Verify infrastructure independence
python -c "from gtool.infrastructure.auth import GoogleAuth; print('✓')"
python -c "from gtool.infrastructure.retry import RetryPolicy; print('✓')"

# Verify no click required
grep -r "import click" src/gtool/infrastructure/  # Should be empty

# Verify tests pass
uv run pytest tests/test_google_auth.py tests/test_retry_policy.py -v
```

### After User Story 2 (T029)

```bash
# Verify config independence
python -c "from gtool.config.settings import Config, ConfigValidationError; print('✓')"

# Verify no click required
grep -r "import click" src/gtool/config/  # Should be empty

# Verify tests pass
uv run pytest tests/test_config.py -v
```

### After User Story 3 (T046)

```bash
# Verify CLI exception translation
uv run pytest tests/test_cli.py -v

# Manual verification
uv run gtool config  # Should prompt interactively
uv run gtool get-calendars  # Should handle auth errors gracefully
```

### Final Validation (Phase 7)

```bash
# Full test suite
uv run pytest -v

# Import checks
grep -r "import click" src/gtool/infrastructure/ src/gtool/config/

# Success: No results from grep, all tests pass
```

---

## Success Criteria Validation

Each success criterion from spec.md maps to specific tasks:

| Success Criterion                         | Validation Tasks             |
| ----------------------------------------- | ---------------------------- |
| SC-001: 0 click imports in infrastructure | T055, T057                   |
| SC-002: Config testable without click     | T027, T028, T029, T056, T058 |
| SC-003: All existing tests pass           | T001, T054                   |
| SC-004: Non-CLI reuse demonstrated        | T017                         |
| SC-005: Exception flow documented         | T003, T062                   |
| SC-006: Integration tests catch real bugs | T047-T053                    |

---

## Notes

- [P] tasks = different files, no dependencies between them
- [INT] tasks = integration tests (mock only Google API, test internal flows)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each logical group of tasks (e.g., after each US checkpoint)
- Stop at any checkpoint to validate story independently
- Tests focus on high-value scenarios that catch real bugs (like ServiceFactory credentials issue)
- Integration tests mock only external dependencies (Google API), not internal components
- Tests are optional per spec, but included here for proper TDD workflow
- Maintain backward compatibility throughout - no user-facing changes

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (User Story 1)**: 11 tasks
- **Phase 4 (User Story 2)**: 11 tasks
- **Phase 5 (User Story 3)**: 17 tasks
- **Phase 6 (Integration Testing)**: 7 tasks
- **Phase 7 (Polish)**: 10 tasks

**Total**: 63 tasks

**Parallel opportunities**: 11 tasks can run in parallel
**Independent user stories**: US1 and US2 can be developed in parallel
**Estimated MVP**: Phases 1-3 (18 tasks) delivers infrastructure reusability
**High-value integration tests**: 7 targeted tests (Phase 6) catch real bugs without over-testing
