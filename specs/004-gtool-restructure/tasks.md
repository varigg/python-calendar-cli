# Tasks: gtool Restructure

**Feature**: `004-gtool-restructure`
**Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)
**Total Tasks**: 49 | **Phases**: 8

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1/US2/US3]**: User story reference

---

## Phase 1: Setup

**Purpose**: Create new directory structure and package scaffolding

- [x] T001 Create `src/gtool/` directory structure with all layer packages
- [x] T002 [P] Create `src/gtool/__init__.py` with package exports
- [x] T003 [P] Create `src/gtool/infrastructure/__init__.py`
- [x] T004 [P] Create `src/gtool/config/__init__.py`
- [x] T005 [P] Create `src/gtool/utils/__init__.py`
- [x] T006 [P] Create `src/gtool/clients/__init__.py`
- [x] T007 [P] Create `src/gtool/core/__init__.py`
- [x] T008 [P] Create `src/gtool/cli/__init__.py`

**Checkpoint**: ✅ Empty package structure ready for file migration

---

## Phase 2: Config & Utils Layers (US2)

**Purpose**: Migrate configuration and utility modules (required before Infrastructure)

- [x] T009 [P] [US2] Copy `config.py` → `gtool/config/settings.py`, update imports
- [x] T010 [P] [US2] Copy `datetime_utils.py` → `gtool/utils/datetime.py`, update imports
- [x] T011 [US2] Update `gtool/config/__init__.py` with public exports
- [x] T012 [US2] Update `gtool/utils/__init__.py` with public exports

**Checkpoint**: ✅ Config and utils layers complete (required for Infrastructure phase)

---

## Phase 3: Infrastructure Layer (US2 - Layered Structure)

**Purpose**: Migrate infrastructure components (depends on Config being available)

- [x] T013 [P] [US2] Copy `error_categorizer.py` → `gtool/infrastructure/error_categorizer.py`, update imports
- [x] T014 [P] [US2] Copy `retry_policy.py` → `gtool/infrastructure/retry.py`, update imports
- [x] T015 [P] [US2] Copy `service_factory.py` → `gtool/infrastructure/service_factory.py`, update imports
- [x] T016 [US2] Copy `google_auth.py` → `gtool/infrastructure/auth.py`, update imports (now Config is available)
- [x] T017 [US2] Update `gtool/infrastructure/__init__.py` with public exports

**Checkpoint**: ✅ Infrastructure layer complete, can be imported as `gtool.infrastructure`

---

## Phase 4: Clients Layer (US2 + US3 - Class Renames)

**Purpose**: Migrate API clients with class renames

- [x] T018 [P] [US2] [US3] Copy `gcal_client_v2.py` → `gtool/clients/calendar.py`
  - Rename class `GCalClientV2` → `CalendarClient`
  - Update all internal imports to `gtool.*`
- [x] T019 [P] [US2] [US3] Copy `gmail_client_v2.py` → `gtool/clients/gmail.py`
  - Rename class `GMailClientV2` → `GmailClient`
  - Update all internal imports to `gtool.*`
- [x] T020 [US2] Update `gtool/clients/__init__.py` with public exports

**Checkpoint**: ✅ Clients layer complete with new class names

---

## Phase 5: Core Layer (US2)

**Purpose**: Migrate business logic, extract SearchParameters

- [ ] T021 [P] [US2] Create `gtool/core/models.py` with `SearchParameters` dataclass (extracted from scheduler)
- [ ] T022 [US2] Copy `scheduler.py` → `gtool/core/scheduler.py`
  - Import `SearchParameters` from `gtool.core.models`
  - Update all internal imports to `gtool.*`
- [ ] T023 [US2] Update `gtool/core/__init__.py` with public exports

**Checkpoint**: Core layer complete

---

## Phase 6: CLI Layer (US1 + US2)

**Purpose**: Migrate CLI module, this is the entry point

- [ ] T024 [P] [US2] Copy `errors.py` → `gtool/cli/errors.py`, update imports
- [ ] T025 [P] [US2] Copy `format.py` → `gtool/cli/formatters.py`, update imports
- [ ] T026 [US1] [US2] Copy `cli.py` → `gtool/cli/main.py`
  - Update all internal imports to use `gtool.*` layer packages
  - Update factory functions to use new client class names
- [ ] T027 [US2] Update `gtool/cli/__init__.py` with public exports (cli group)

**Checkpoint**: CLI layer complete, all source files migrated

---

## Phase 7: Package Configuration (US1)

**Purpose**: Update pyproject.toml and finalize package

- [ ] T028 [US1] Update `pyproject.toml`:
  - Change package name from `caltool` to `gtool`
  - Update `[project.scripts]` entry point: `gtool = "gtool.cli.main:cli"`
  - Update package discovery to `src/gtool`
- [ ] T029 [US1] Run `uv sync` to reinstall package with new name
- [ ] T030 [US1] Verify `gtool --help` works from command line

**Checkpoint**: CLI renamed and installable as `gtool`

---

## Phase 8: Test Migration & Cleanup

**Purpose**: Update all tests and remove old package

### Test Import Updates

- [ ] T031 [P] Update `tests/conftest.py` imports to `gtool.*`
- [ ] T032 [P] Rename `tests/test_error_categorizer.py` imports to `gtool.infrastructure.error_categorizer`
- [ ] T033 [P] Rename `tests/test_retry_policy.py` imports to `gtool.infrastructure.retry`
- [ ] T034 [P] Rename `tests/test_service_factory.py` imports to `gtool.infrastructure.service_factory`
- [ ] T035 [P] Rename `tests/test_google_auth.py` imports to `gtool.infrastructure.auth`
- [ ] T036 [P] Rename `tests/test_config.py` imports to `gtool.config.settings`
- [ ] T037 [P] Rename `tests/test_env_config.py` imports to `gtool.config.settings`
- [ ] T038 [P] Rename `tests/test_datetime_utils.py` imports to `gtool.utils.datetime`
- [ ] T039 [P] Rename `tests/test_gcal_client_v2.py` → `tests/test_calendar_client.py`, update imports and class refs
- [ ] T040 [P] Rename `tests/test_gmail_client_v2.py` → `tests/test_gmail_client.py`, update imports and class refs
- [ ] T041 [P] Rename `tests/test_scheduler.py` imports to `gtool.core.scheduler`
- [ ] T042 [P] Rename `tests/test_cli.py` imports to `gtool.cli.main`
- [ ] T043 [P] Rename `tests/test_format.py` imports to `gtool.cli.formatters`
- [ ] T044 [P] Rename `tests/test_errors.py` imports to `gtool.cli.errors`

### Verification & Cleanup

- [ ] T045 Run full test suite: `uv run pytest tests/ -v`
- [ ] T046 Run coverage check: `uv run pytest --cov=src/gtool tests/`
- [ ] T047 Delete old `src/caltool/` directory
- [ ] T048 Verify no references to `caltool` remain: `grep -r "caltool" src/ tests/`
- [ ] T049 Final verification: `gtool --help`, `gtool free today`, `gtool gmail list`

**Checkpoint**: Migration complete, all tests pass, old package removed

---

## Dependencies & Execution Order

### Critical Path

```
Phase 1 (Setup) → Phase 2 (Config/Utils) → Phase 3 (Infrastructure) → Phase 4 (Clients) → Phase 5 (Core) → Phase 6 (CLI) → Phase 7 (Package) → Phase 8 (Tests)
```

### Parallelizable Tasks

| Phase | Parallel Tasks                                        |
| ----- | ----------------------------------------------------- |
| 1     | T002-T008 (all **init**.py files)                     |
| 2     | T009-T010 (config and datetime utils)                 |
| 3     | T013-T015 (error categorizer, retry, service factory) |
| 4     | T018-T019 (both clients)                              |
| 5     | T021 can start immediately                            |
| 6     | T024-T025 (errors and formatters)                     |
| 8     | T031-T044 (all test updates)                          |

---

## Success Criteria

- [ ] SC-001: `gtool --help` displays all commands
- [ ] SC-002: 95+ tests pass
- [ ] SC-003: Coverage ≥ 81%
- [ ] SC-004: No circular imports
- [ ] SC-005: No references to `caltool` in codebase
- [ ] SC-006: All imports use layered structure (`gtool.cli`, `gtool.core`, etc.)
