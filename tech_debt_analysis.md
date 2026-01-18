# YAGNI/KISS Analysis: Overengineering Review

**Date**: January 17, 2026
**Scope**: Full codebase review for signs of overengineering
**Reviewer**: Code review following feature 006-layer-separation

---

## Executive Summary

The codebase shows signs of **moderate overengineering**, particularly from recent refactoring efforts. For a CLI tool with **2 API clients** (Calendar, Gmail) and **~5 commands**, the architecture has grown to **6 layers** with **22 source files** and **2,336 lines of production code**.

While the layer separation achieves its goal of removing click dependencies from lower layers, some abstractions exist that add complexity without proportional benefit.

---

## Codebase Metrics

| Metric                 | Value       | Assessment             |
| ---------------------- | ----------- | ---------------------- |
| Production code        | 2,336 lines | High for scope         |
| Test code              | 1,794 lines | Reasonable (77% ratio) |
| Source files           | 22          | Fragmented             |
| Exception types        | 4+          | More than needed       |
| Architectural layers   | 6           | Excessive for CLI      |
| Largest file (auth.py) | 627 lines   | 27% of codebase        |
| Tests                  | 114         | Good coverage          |
| Test execution time    | 4.34s       | Acceptable             |

### Layer Size Breakdown

```
CLI Layer:           456 lines (cli/main.py, errors.py, decorators.py, formatters.py)
Config Layer:        150 lines (config/settings.py, __init__.py)
Infrastructure:      948 lines (auth.py, retry.py, service_factory.py, error_categorizer.py, exceptions.py)
Clients:             315 lines (calendar.py, gmail.py)
Core:                139 lines (scheduler.py, models.py)
Utils:               142 lines (datetime.py)
```

**Observation**: Infrastructure layer (948 lines) is larger than all business logic combined (Clients + Core = 454 lines).

---

## High-Priority Issues (Clear YAGNI/KISS Violations)

### 1. ErrorCategorizer as a Separate Class

**Location**: `src/gtool/infrastructure/error_categorizer.py` (55 lines)

**Current State**:

```python
class ErrorCategorizer:
    """Categorizes HTTP errors from Google API calls."""

    def categorize(self, error: HttpError) -> str:
        if not isinstance(error, HttpError):
            raise TypeError(f"Expected HttpError, got {type(error)}")

        status_code = error.resp.status
        if status_code == 401:
            return "AUTH"
        elif status_code == 403:
            return "QUOTA"
        # ... ~20 lines of simple conditionals
```

**Problem**:

- A 55-line class with a single method called from exactly one place (`RetryPolicy.execute()`)
- Created as a "component for composition-based architecture" but there's only one categorization strategy
- No need for swappable categorizers - the HTTP status → category mapping is fixed

**YAGNI Violation**: Abstracted for extensibility that will never be needed.

**Recommendation**:

```
Merge ErrorCategorizer into RetryPolicy as a private _categorize_error() method.
Delete infrastructure/error_categorizer.py. The categorization logic is ~20 lines
and is inherently coupled to the retry decision logic.
```

---

### 2. ServiceFactory Caching

**Location**: `src/gtool/infrastructure/service_factory.py` (66 lines)

**Current State**:

```python
class ServiceFactory:
    def __init__(self, auth: GoogleAuth) -> None:
        self._auth = auth
        self._services: Dict[tuple, Any] = {}  # Cache

    def build_service(self, api_name: str, api_version: str) -> Any:
        cache_key = (api_name, api_version)
        if cache_key not in self._services:
            self._services[cache_key] = discovery.build(...)
        return self._services[cache_key]
```

**Problem**:

- CLI tool pattern: `create client → call API → exit`
- Each command creates a new `ServiceFactory` instance
- The cache is never reused - the process exits before any second call
- Premature optimization for a scenario that doesn't exist

**YAGNI Violation**: Caching designed for long-running services, not CLI tools.

**Recommendation**:

```
Remove the _services cache dictionary from ServiceFactory. Simplify to:

def build_service(self, api_name: str, api_version: str) -> Any:
    return discovery.build(api_name, api_version,
                          credentials=self._auth.get_credentials())

Or consider if ServiceFactory itself is needed - could be a simple function.
```

---

### 3. Excessive Exception Hierarchy

**Location**: `src/gtool/infrastructure/exceptions.py` (81 lines)

**Current State**:

```python
class AuthError(Exception):
    """Base exception for authentication and authorization failures."""
    pass

class ServiceError(Exception):
    """Base exception for service/API failures."""
    pass

class ConfigError(Exception):
    """Base exception for configuration-related failures."""
    pass

class ConfigValidationError(ConfigError):
    """Configuration validation error."""
    pass
    pass  # ← Duplicate pass statement (bug)
```

**Problems**:

1. `ServiceError` is **never raised** anywhere in the codebase
2. `ConfigError` base class is never caught separately from `ConfigValidationError`
3. 81 lines of docstrings for 4 exception classes with no logic
4. Duplicate `pass` statement at end of `ConfigValidationError`

**KISS Violation**: More exception types than actual error handling paths.

**Recommendation**:

```
1. Remove ServiceError - it's defined but never used
2. Remove ConfigError base class - only ConfigValidationError is used
3. Keep only AuthError and ConfigValidationError
4. Fix the duplicate 'pass' statement bug
5. Reduce docstrings to essential information

After cleanup, file should be ~20 lines instead of 81.
```

---

### 4. Dead Code: validate_gmail_scopes()

**Location**: `src/gtool/config/settings.py` lines 128-139

**Current State**:

```python
def validate_gmail_scopes(self) -> None:
    """Validate that Gmail scopes are configured when Gmail is enabled."""
    if self.is_gmail_enabled() and not self.has_gmail_scope("readonly"):
        logger.error("Gmail enabled but no Gmail scope configured")
        raise ConfigValidationError(
            "Gmail is enabled but no Gmail scope is configured..."
        )
```

**Problem**:

- The performance fix (commit 1776ced) changed `gmail()` group to call `has_gmail_scope()` directly
- `validate_gmail_scopes()` is now **only called from tests**
- Production code path: `gmail()` → `has_gmail_scope()` (direct)

**YAGNI Violation**: Method exists but isn't used in production.

**Recommendation**:

```
Either:
A) Remove validate_gmail_scopes() entirely - update tests to use has_gmail_scope()
B) Keep it but mark as deprecated with comment explaining it's for testing only
C) Restore usage in gmail() group if the validation logic should be centralized
```

---

### 5. OAuth Host/Port Configuration Complexity

**Location**: `src/gtool/infrastructure/auth.py` lines 350-450 (~100 lines)

**Current State**:

```python
def _get_oauth_host(self) -> str:
    return os.environ.get("GTOOL_OAUTH_HOST", "localhost").strip() or "localhost"

def _get_oauth_ports(self) -> list[int]:
    default_ports = [8401]
    raw = os.environ.get("GTOOL_OAUTH_PORTS")
    # ... 15 lines of parsing logic

def _choose_oauth_port(self, host: str, ports: list[int]) -> int:
    # ... 30 lines of port availability checking
```

**Problem**:

- ~100 lines of infrastructure for edge cases
- Default (`localhost:8401`) works for 99% of users
- Port conflicts are rare and recoverable with simple documentation

**YAGNI Violation**: Built for hypothetical enterprise deployment scenarios.

**Recommendation**:

```
Simplify to single hardcoded port with clear error message:

PORT = 8401
try:
    creds = flow.run_local_server(port=PORT)
except OSError:
    raise AuthError(f"Port {PORT} in use. Kill process or set GTOOL_OAUTH_PORT=XXXX")

Remove multi-port allowlist, port probing, and host configuration.
Document the single env var for the rare case someone needs it.
```

---

## Medium-Priority Issues (Borderline Overengineering)

### 6. Six-Layer Architecture for Five Commands

**Current Layers**:

```
1. CLI Layer (click commands, formatters)
2. Config Layer (settings, validation)
3. Infrastructure Layer (auth, retry, service factory, exceptions)
4. Clients Layer (calendar, gmail API wrappers)
5. Core Layer (scheduler, models)
6. Utils Layer (datetime parsing)
```

**Problem**:

- Each layer has 1-4 files averaging 100-150 lines
- Many inter-layer dependencies with thin wrappers
- Feature changes require touching 3+ layers

**Trade-off**: Layer separation was intentional (feature 006) to remove click from lower layers. The architecture is correct for a larger project but may be excessive for current scope.

**Recommendation**:

```
No immediate action needed, but consider:
- If project doesn't grow significantly, consolidate in future
- Infrastructure layer (948 lines) could be simplified
- Core layer (139 lines) could merge into clients
```

---

### 7. RetryPolicy Class-Based Design

**Location**: `src/gtool/infrastructure/retry.py` (108 lines)

**Current State**:

```python
class RetryPolicy:
    def __init__(self, max_retries=3, delay=1.0, error_categorizer=None):
        self.max_retries = max_retries
        self.delay = delay
        self.error_categorizer = error_categorizer or ErrorCategorizer()

    def should_retry(self, error_category: str) -> bool:
        return error_category in {"QUOTA", "TRANSIENT"}

    def execute(self, func, *args, **kwargs):
        # ... 40 lines of retry loop
```

**Problem**:

- Class with dependency injection for a simple retry loop
- `error_categorizer` is always `ErrorCategorizer()` - never injected with alternatives
- More appropriate for long-running services than CLI tools

**KISS Alternative**:

```python
@retry(max_attempts=3, delay=1.0, on=(QUOTA_ERRORS, TRANSIENT_ERRORS))
def fetch_calendars():
    return service.calendarList().list().execute()
```

**Recommendation**:

```
Consider replacing class-based RetryPolicy with a decorator:

def retry(max_attempts=3, delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (QuotaError, TransientError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

This is simpler and more Pythonic for CLI use.
```

---

### 8. translate_exceptions Decorator Indirection

**Location**: `src/gtool/cli/decorators.py` lines 23-55

**Current State**:

```python
def translate_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigValidationError as e:
            raise click.UsageError(str(e)) from e
        except ConfigError as e:
            raise click.UsageError(str(e)) from e  # Same as above
        except AuthError as e:
            raise AuthenticationError(str(e)) from e  # Just renames
        except ServiceError as e:
            raise CLIError(str(e)) from e  # Never happens
    return wrapper
```

**Problem**:

- `AuthError` → `AuthenticationError` is just a rename (both are Exception subclasses)
- `ServiceError` translation never executes (ServiceError is never raised)
- `ConfigError` and `ConfigValidationError` have identical handling
- Adds cognitive overhead without meaningful transformation

**Recommendation**:

```
Simplify to catch fewer exceptions with more meaningful handling:

def translate_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigValidationError as e:
            raise click.UsageError(str(e)) from e
        except AuthError as e:
            raise click.ClickException(f"Authentication failed: {e}") from e
    return wrapper

Remove: ConfigError (unused), ServiceError (never raised), AuthenticationError class.
```

---

## Appropriate Complexity (Not Overengineered)

These components are well-designed for their purpose:

1. **CalendarClient/GmailClient** - Clean, focused, appropriate abstraction
2. **Scheduler** - Necessary business logic, well-tested
3. **Config settings** - Appropriate for configuration management
4. **CLI commands** - Well-structured Click groups
5. **datetime utils** - Genuinely useful parsing logic
6. **GoogleAuth core flow** - OAuth complexity is inherent to the problem

---

## Recommended Simplification Roadmap

### Phase 1: Quick Wins (Low Risk, High Impact)

| Task                                   | Files Affected               | Lines Removed | Effort |
| -------------------------------------- | ---------------------------- | ------------- | ------ |
| Fix duplicate `pass` bug               | exceptions.py                | 1             | 5 min  |
| Remove unused ServiceError             | exceptions.py, decorators.py | ~30           | 15 min |
| Remove ServiceFactory cache            | service_factory.py           | ~10           | 10 min |
| Remove/deprecate validate_gmail_scopes | settings.py                  | ~12           | 10 min |

**Estimated total**: ~50 lines removed, 40 minutes work

### Phase 2: Consolidation (Medium Risk)

| Task                                    | Files Affected                 | Lines Removed | Effort |
| --------------------------------------- | ------------------------------ | ------------- | ------ |
| Merge ErrorCategorizer into RetryPolicy | error_categorizer.py, retry.py | ~40           | 30 min |
| Simplify exception hierarchy            | exceptions.py, decorators.py   | ~40           | 30 min |
| Simplify OAuth port handling            | auth.py                        | ~60           | 45 min |

**Estimated total**: ~140 lines removed, 2 hours work

### Phase 3: Future Consideration (Higher Risk)

- Convert RetryPolicy to decorator pattern
- Merge Core layer into Clients
- Consider if ServiceFactory is needed at all

---

## Conclusion

The codebase is **functional and well-tested** but has accumulated complexity beyond what a CLI tool of this scope requires. The recommended Phase 1 changes are low-risk improvements that can be done immediately. Phase 2 requires more careful refactoring. Phase 3 should be deferred until the project's growth trajectory is clearer.

**Key Principle**: A CLI tool that runs, does one thing, and exits doesn't need the architectural patterns of a long-running service.
