# Separation of Concerns Analysis (2026-01-17)

## Summary

This document records separation-of-concerns issues found during a layer-by-layer review of the gtool codebase.

## Findings

### 1) Infrastructure depends on CLI (UI layer)

**Issue:** Infrastructure layer imports UI dependencies and CLI-specific errors.

Evidence:

- `click` used in infrastructure auth module.
  - File: src/gtool/infrastructure/auth.py (import click)
- Retry policy wraps Google auth errors into CLI AuthenticationError.
  - File: src/gtool/infrastructure/retry.py (imports gtool.cli.errors.AuthenticationError)
- Auth docstrings still reference CLIError.
  - File: src/gtool/infrastructure/auth.py

**Risk:** Circular dependencies, harder reuse/testing of infrastructure without CLI.

**Recommended Fix (prompt):**

> Refactor infrastructure to be UI-agnostic. Replace `click` usage and CLI error references in `auth.py` and `retry.py` with infrastructure-level exceptions (e.g., `AuthError`/`ServiceError`). In the CLI layer, map these infra exceptions to `CLIError`/`AuthenticationError` with user-facing messages. Update docstrings accordingly.

---

### 2) Config layer depends on CLI (UI layer)

**Issue:** Configuration layer uses click prompts and prints directly.

Evidence:

- `click` imported in config settings module.
- `Config.prompt()` uses `click.prompt` and `click.echo`.
  - File: src/gtool/config/settings.py

**Risk:** Config layer cannot be reused in non-CLI contexts (e.g., tests, GUI, APIs).

**Recommended Fix (prompt):**

> Move interactive prompting out of the config layer into the CLI layer. Keep `Config` as pure data/validation and file IO. Create CLI helpers to collect input and then call `Config.set/save`. Remove `click` import from config.

---

### 3) Config validation raises click UsageError (UI layer)

**Issue:** Config validation raises CLI-specific exceptions.

Evidence:

- `validate_gmail_scopes()` raises `click.UsageError`.
  - File: src/gtool/config/settings.py
- CLI catches this in `gmail` command group.
  - File: src/gtool/cli/main.py

**Risk:** UI exceptions leak into core config layer.

**Recommended Fix (prompt):**

> Have config validation raise a domain/config exception instead of `click.UsageError`. Convert it to `CLIError` in `cli/main.py`. This keeps config UI-free.

---

## Non-Issues (separation respected)

- **Clients**: API-only logic (Calendar/Gmail) uses infrastructure services without CLI/UI code.
- **Core**: `scheduler` and `models` are pure domain logic.
- **Utils**: datetime parsing/formatting is UI-agnostic.

## Scope

Findings are based on direct inspection of the following key modules:

- CLI: src/gtool/cli/main.py, src/gtool/cli/errors.py
- Clients: src/gtool/clients/calendar.py, src/gtool/clients/gmail.py
- Config: src/gtool/config/settings.py
- Core: src/gtool/core/scheduler.py, src/gtool/core/models.py
- Infrastructure: src/gtool/infrastructure/auth.py, retry.py, service_factory.py, error_categorizer.py
- Utils: src/gtool/utils/datetime.py
