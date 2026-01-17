# Exception Contracts: Layer Separation

**Feature**: Layer Separation Enforcement
**Date**: 2026-01-17

## Purpose

This document defines the contracts (interfaces) for exception handling across layers. Since this is an architectural refactoring focused on exception boundaries, the "contracts" are the exception types and their translation rules.

---

## Contract 1: Infrastructure Exception Interface

### AuthError Contract

**Module**: `gtool.infrastructure.exceptions`

**Type**: Exception class

**Signature**:

```python
class AuthError(Exception):
    """Base exception for authentication and authorization failures.

    Raised when:
    - OAuth flow fails
    - Token refresh fails
    - Credentials are missing or invalid
    - Google Auth API returns errors

    This exception should NEVER be raised from CLI layer.
    CLI layer MUST catch this and translate to AuthenticationError.
    """
    pass
```

**Contract Rules**:

1. **MUST** be raised by infrastructure layer for auth failures
2. **MUST NOT** be raised by CLI or config layers
3. **MUST** include descriptive message in constructor
4. **MUST** be caught by CLI layer and translated to `AuthenticationError`

**Example Usage**:

```python
# Infrastructure layer (CORRECT)
try:
    credentials.refresh(Request())
except google.auth.exceptions.RefreshError as e:
    raise AuthError(f"Token refresh failed: {e}") from e

# CLI layer (CORRECT - translation)
try:
    auth.get_credentials()
except AuthError as e:
    raise AuthenticationError(str(e)) from e
```

---

### ServiceError Contract

**Module**: `gtool.infrastructure.exceptions`

**Type**: Exception class

**Signature**:

```python
class ServiceError(Exception):
    """Base exception for service/API failures.

    Raised when:
    - Google API returns 5xx errors
    - Network connectivity issues occur
    - API quota exceeded (after retries)
    - Service unavailable

    This exception should NEVER be raised from CLI layer.
    CLI layer MUST catch this and translate to CLIError.
    """
    pass
```

**Contract Rules**:

1. **MUST** be raised by infrastructure layer for service failures
2. **MUST NOT** be raised by CLI or config layers
3. **MUST** include service context (API name, status code) in message
4. **MUST** be caught by CLI layer and translated to `CLIError`

**Example Usage**:

```python
# Infrastructure layer (CORRECT)
if response.status_code >= 500:
    raise ServiceError(f"Google Calendar API returned {response.status_code}: {response.reason}")

# CLI layer (CORRECT - translation)
try:
    calendar_client.get_events(...)
except ServiceError as e:
    raise CLIError(f"Calendar service error: {e}") from e
```

---

### ConfigError Contract

**Module**: `gtool.infrastructure.exceptions`

**Type**: Exception class (base class)

**Signature**:

```python
class ConfigError(Exception):
    """Base exception for configuration-related failures.

    This is a base class for all config exceptions.
    Use subclasses (like ConfigValidationError) for specific failures.

    This exception hierarchy allows CLI to catch all config errors:
        try:
            config.validate()
        except ConfigError as e:
            # Handle any config issue
    """
    pass
```

**Contract Rules**:

1. **MUST** be base class for config exceptions
2. **MAY** be raised directly for general config errors
3. **SHOULD** be subclassed for specific config failures
4. **MUST** be caught by CLI layer for user presentation

---

## Contract 2: Config Exception Interface

### ConfigValidationError Contract

**Module**: `gtool.config.settings`

**Type**: Exception class (subclass of ConfigError)

**Signature**:

```python
class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails.

    Raised when:
    - Required configuration keys are missing
    - Configuration values are invalid
    - Gmail scopes are inconsistent
    - Configuration format is incorrect

    This exception should NEVER be click.UsageError.
    CLI layer MUST catch this and translate to click.UsageError.
    """
    pass
```

**Contract Rules**:

1. **MUST** be raised by config layer for validation failures
2. **MUST NOT** be `click.UsageError` (config layer is UI-agnostic)
3. **MUST** include specific validation failure in message
4. **SHOULD** include guidance on how to fix
5. **MUST** be caught by CLI layer and translated to `click.UsageError`

**Example Usage**:

```python
# Config layer (CORRECT)
def validate_gmail_scopes(self) -> None:
    if self.is_gmail_enabled() and not self.has_gmail_scope():
        raise ConfigValidationError(
            "Gmail enabled but gmail scopes not in SCOPES list. "
            "Run 'gtool config' to update configuration."
        )

# CLI layer (CORRECT - translation)
@cli.group()
def gmail():
    try:
        config.validate_gmail_scopes()
    except ConfigValidationError as e:
        raise click.UsageError(str(e))
```

---

## Contract 3: CLI Exception Translation Interface

### Exception Translation Decorator

**Module**: `gtool.cli.main` (or `gtool.cli.errors`)

**Type**: Function decorator

**Signature**:

```python
def handle_infrastructure_errors(func: Callable) -> Callable:
    """Decorator to translate infrastructure exceptions to CLI exceptions.

    Translates:
    - AuthError → AuthenticationError
    - ServiceError → CLIError
    - ConfigValidationError → click.UsageError

    Preserves exception chain using 'from e' for debugging.

    Usage:
        @cli.command()
        @handle_infrastructure_errors
        def my_command():
            # command implementation
    """
```

**Contract Rules**:

1. **MUST** be applied to all click commands that may raise infrastructure exceptions
2. **MUST** preserve exception chain (use `from e`)
3. **MUST** translate to appropriate CLI exception type
4. **MUST** maintain or improve error message clarity
5. **MUST NOT** let infrastructure exceptions leak to users

**Implementation Contract**:

```python
def handle_infrastructure_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AuthError as e:
            # Auth failures → user-friendly auth error
            raise AuthenticationError(str(e)) from e
        except ServiceError as e:
            # Service failures → generic CLI error with context
            raise CLIError(f"Service error: {e}") from e
        except ConfigValidationError as e:
            # Config validation → usage error (user input issue)
            raise click.UsageError(str(e))
    return wrapper
```

---

## Contract 4: Config Interactive Prompting Interface

### Interactive Config Prompting Function

**Module**: `gtool.cli.main`

**Type**: Function

**Signature**:

```python
def prompt_config_interactive(config: Config) -> None:
    """Prompt user interactively to configure application settings.

    This function replaces Config.prompt() method, moving interactive
    UI logic to CLI layer where it belongs.

    Args:
        config: Config object to update

    Behavior:
        - Uses click.prompt() for user input
        - Uses click.echo() for messages
        - Calls config.set() to update values (no click dependency)
        - Calls config.save() to persist (no click dependency)
        - Validates input before saving

    Raises:
        click.UsageError: If validation fails during save
    """
```

**Contract Rules**:

1. **MUST** be in CLI layer (not config layer)
2. **MUST** use click.prompt() for user input
3. **MUST** use click.echo() for messages
4. **MUST** call config.set() to update values (config has no click)
5. **MUST** call config.save() to persist (config has no click)
6. **MUST** handle ConfigValidationError and translate to click.UsageError

**Implementation Contract**:

```python
def prompt_config_interactive(config: Config) -> None:
    """Interactive configuration prompting (CLI layer)."""
    click.echo("Let's configure gtool...")

    # Collect user input (CLI layer responsibility)
    credentials = click.prompt(
        "Path to credentials.json",
        default=config.get("CREDENTIALS_FILE")
    )
    token = click.prompt(
        "Path to token.json",
        default=config.get("TOKEN_FILE")
    )
    # ... more prompts

    # Update config (config layer responsibility - no click)
    config.set("CREDENTIALS_FILE", credentials)
    config.set("TOKEN_FILE", token)

    # Validate and save (config layer - may raise ConfigValidationError)
    try:
        config.validate()
        config.save()
    except ConfigValidationError as e:
        raise click.UsageError(str(e))

    click.echo("✓ Configuration saved successfully!")
```

---

## Contract 5: Import Independence

### Infrastructure Import Contract

**Rule**: Infrastructure modules MUST be importable without CLI dependencies.

**Verification**:

```python
# This MUST work without click installed
from gtool.infrastructure.auth import GoogleAuth
from gtool.infrastructure.retry import RetryPolicy
from gtool.infrastructure.exceptions import AuthError, ServiceError

# This MUST raise AuthError (not CLI exception)
try:
    auth = GoogleAuth(config)
    auth.get_credentials()
except AuthError:
    # Handle infrastructure error
    pass
```

**Contract Rules**:

1. **MUST NOT** import `click` in infrastructure modules
2. **MUST NOT** import `gtool.cli.*` in infrastructure modules
3. **MUST** raise infrastructure exceptions (not CLI exceptions)
4. **MUST** work in non-CLI contexts (e.g., API server, batch script)

### Config Import Contract

**Rule**: Config modules MUST be importable without CLI dependencies.

**Verification**:

```python
# This MUST work without click installed
from gtool.config.settings import Config

# This MUST work programmatically (no prompts)
config = Config()
config.set("TIME_ZONE", "UTC")
config.save()

# This MUST raise ConfigValidationError (not click.UsageError)
try:
    config.validate()
except ConfigValidationError:
    # Handle validation error
    pass
```

**Contract Rules**:

1. **MUST NOT** import `click` in config modules
2. **MUST NOT** import `gtool.cli.*` in config modules
3. **MUST** raise config exceptions (not click exceptions)
4. **MUST** work programmatically without interactive prompts

---

## Contract Validation

### Test Contracts

Each contract MUST have corresponding tests:

1. **Infrastructure Exception Contract Tests**:
   - Verify AuthError raised (not CLI exception)
   - Verify ServiceError raised (not CLI exception)
   - Verify infrastructure imports without click

2. **Config Exception Contract Tests**:
   - Verify ConfigValidationError raised (not click.UsageError)
   - Verify config works programmatically
   - Verify config imports without click

3. **CLI Translation Contract Tests**:
   - Verify AuthError → AuthenticationError
   - Verify ServiceError → CLIError
   - Verify ConfigValidationError → click.UsageError
   - Verify exception chain preserved

4. **Import Independence Contract Tests**:
   - Test infrastructure import without click
   - Test config import without click
   - Test non-CLI usage scenarios

---

## Breaking Changes (None Expected)

This refactoring maintains **100% backward compatibility** for CLI users:

- ✅ Same error messages to users
- ✅ Same command behavior
- ✅ Same configuration file format
- ✅ Same exit codes

**Internal changes only**:

- Exception types raised internally change
- Exception translation added in CLI layer
- Interactive prompting moved to CLI layer

**CLI contract unchanged**:

- Commands work identically
- Options work identically
- Help messages unchanged
- User experience unchanged

---

## Summary

**New Contracts Introduced**:

1. Infrastructure exceptions (AuthError, ServiceError, ConfigError)
2. Config exceptions (ConfigValidationError)
3. Exception translation decorator
4. Interactive prompting function

**Contracts Maintained**:

1. CLI command interface (unchanged)
2. Configuration file format (unchanged)
3. User experience (unchanged)

**Contract Benefits**:

1. Infrastructure reusable in non-CLI contexts
2. Config testable without interactive prompts
3. Clear exception boundaries
4. Improved maintainability
