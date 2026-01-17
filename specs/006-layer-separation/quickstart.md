# Quickstart: Layer Separation Implementation

**Feature**: Layer Separation Enforcement
**Date**: 2026-01-17
**For**: Developers implementing this refactoring

## Purpose

This quickstart guide helps developers understand and implement the layer separation refactoring. Follow this guide to ensure consistent implementation across all phases.

---

## Prerequisites

Before starting implementation:

1. **Read required documents**:
   - [spec.md](spec.md) — User stories and requirements
   - [plan.md](plan.md) — Technical approach and structure
   - [research.md](research.md) — Design decisions and patterns
   - [data-model.md](data-model.md) — Exception hierarchy
   - [contracts/exception-contracts.md](contracts/exception-contracts.md) — Exception contracts

2. **Understand current state**:
   - Review [analysis.md](../../../analysis.md) for violation details
   - Examine current exception usage in codebase
   - Run existing tests to establish baseline

3. **Set up development environment**:
   ```bash
   cd /path/to/calendarcli
   git checkout 006-layer-separation
   uv sync
   uv run pytest  # Verify all tests pass
   ```

---

## Implementation Phases

### Phase 0: Validate Current State

**Before making any changes**, verify the baseline:

```bash
# Run all tests
uv run pytest

# Verify infrastructure currently imports click
grep -r "import click" src/gtool/infrastructure/

# Verify config currently imports click
grep -r "import click" src/gtool/config/

# Expected results:
# - src/gtool/infrastructure/auth.py:import click
# - src/gtool/config/settings.py:import click
```

**Checkpoint**: All tests pass, violations confirmed.

---

### Phase 1: Infrastructure Layer (Priority P1)

**Goal**: Remove CLI dependencies from infrastructure layer.

#### Step 1.1: Add ConfigError to infrastructure exceptions

**File**: `src/gtool/infrastructure/exceptions.py`

**Changes**:

```python
class ConfigError(Exception):
    """Base exception for configuration-related failures."""
    pass
```

**Test**:

```bash
# Verify exception can be imported
python -c "from gtool.infrastructure.exceptions import ConfigError; print('✓ ConfigError defined')"
```

#### Step 1.2: Remove click from auth.py

**File**: `src/gtool/infrastructure/auth.py`

**Find and remove**:

```python
import click  # REMOVE THIS LINE
```

**Update docstrings**: Remove any CLI/CLIError references.

**Test**:

```bash
# Verify no click import
grep "import click" src/gtool/infrastructure/auth.py  # Should return nothing

# Verify module imports without click
python -c "from gtool.infrastructure.auth import GoogleAuth; print('✓ Auth imports without click')"
```

#### Step 1.3: Update retry.py to use AuthError

**File**: `src/gtool/infrastructure/retry.py`

**Find**:

```python
from gtool.cli.errors import AuthenticationError
```

**Replace with**:

```python
from gtool.infrastructure.exceptions import AuthError
```

**Find where AuthenticationError is raised and replace with AuthError**:

```python
# OLD (incorrect)
raise AuthenticationError("...")

# NEW (correct)
raise AuthError("...")
```

**Test**:

```bash
# Verify no CLI error import
grep "from gtool.cli" src/gtool/infrastructure/retry.py  # Should return nothing

# Verify AuthError imported
grep "from gtool.infrastructure.exceptions import AuthError" src/gtool/infrastructure/retry.py

# Run retry tests
uv run pytest tests/test_retry_policy.py -v
```

#### Step 1.4: Update infrastructure tests

**Files**: `tests/test_google_auth.py`, `tests/test_retry_policy.py`

**Changes needed**:

- Update assertions expecting CLI exceptions to expect infrastructure exceptions
- Add test verifying infrastructure imports without click

**Example test**:

```python
def test_infrastructure_imports_without_click():
    """Verify infrastructure can be imported without click installed."""
    # This test ensures infrastructure is CLI-independent
    from gtool.infrastructure.auth import GoogleAuth
    from gtool.infrastructure.retry import RetryPolicy
    from gtool.infrastructure.exceptions import AuthError, ServiceError

    # If we got here, imports succeeded
    assert True


def test_auth_raises_auth_error_not_cli_error():
    """Verify GoogleAuth raises AuthError, not CLI exceptions."""
    from gtool.infrastructure.auth import GoogleAuth
    from gtool.infrastructure.exceptions import AuthError

    # Test that auth failures raise AuthError
    # (specific test implementation depends on mock setup)
    with pytest.raises(AuthError):
        # Trigger auth failure
        pass
```

**Checkpoint Phase 1**:

- ✅ No `import click` in infrastructure
- ✅ No `from gtool.cli` in infrastructure
- ✅ Infrastructure tests pass
- ✅ Infrastructure raises AuthError/ServiceError (not CLI exceptions)

---

### Phase 2: Config Layer (Priority P2)

**Goal**: Remove CLI dependencies from config layer.

#### Step 2.1: Add ConfigValidationError to config

**File**: `src/gtool/config/settings.py`

**Add at top (after imports)**:

```python
from gtool.infrastructure.exceptions import ConfigError


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass
```

#### Step 2.2: Remove click import

**File**: `src/gtool/config/settings.py`

**Remove**:

```python
import click  # REMOVE THIS LINE
```

#### Step 2.3: Replace click.UsageError with ConfigValidationError

**File**: `src/gtool/config/settings.py`

**Find all instances**:

```python
raise click.UsageError("...")
```

**Replace with**:

```python
raise ConfigValidationError("...")
```

**Example locations**:

- `validate_gmail_scopes()` method
- Any other validation methods

#### Step 2.4: Remove Config.prompt() method

**File**: `src/gtool/config/settings.py`

**Find and DELETE the entire `Config.prompt()` method**.

**Rationale**: Interactive prompting moves to CLI layer (Phase 3).

#### Step 2.5: Update config tests

**File**: `tests/test_config.py`

**Changes needed**:

- Remove `import click` if present
- Remove mocking of `click.prompt` if present
- Update assertions expecting `click.UsageError` to expect `ConfigValidationError`

**Example**:

```python
# OLD (incorrect)
with pytest.raises(click.UsageError):
    config.validate_gmail_scopes()

# NEW (correct)
from gtool.config.settings import ConfigValidationError

with pytest.raises(ConfigValidationError):
    config.validate_gmail_scopes()
```

**Test**:

```bash
# Verify no click import
grep "import click" src/gtool/config/settings.py  # Should return nothing

# Verify ConfigValidationError defined
python -c "from gtool.config.settings import ConfigValidationError; print('✓ ConfigValidationError defined')"

# Run config tests
uv run pytest tests/test_config.py -v
```

**Checkpoint Phase 2**:

- ✅ No `import click` in config
- ✅ ConfigValidationError defined and used
- ✅ Config.prompt() removed
- ✅ Config tests pass

---

### Phase 3: CLI Layer (Priority P3)

**Goal**: Add exception translation and interactive prompting to CLI layer.

#### Step 3.1: Add exception translation decorator

**File**: `src/gtool/cli/main.py` (or create `src/gtool/cli/error_handlers.py`)

**Add decorator**:

```python
import functools
import click
from gtool.infrastructure.exceptions import AuthError, ServiceError, ConfigError
from gtool.config.settings import ConfigValidationError
from gtool.cli.errors import AuthenticationError, CLIError


def handle_infrastructure_errors(func):
    """Decorator to translate infrastructure exceptions to CLI exceptions.

    Translates:
    - AuthError → AuthenticationError
    - ServiceError → CLIError
    - ConfigValidationError → click.UsageError

    Preserves exception chain using 'from e' for debugging.
    """
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

#### Step 3.2: Apply decorator to commands

**File**: `src/gtool/cli/main.py`

**Apply to commands that may raise infrastructure exceptions**:

```python
@cli.command()
@handle_infrastructure_errors
def get_calendars():
    """List available calendars."""
    # ... implementation


@cli.group()
@handle_infrastructure_errors
def gmail():
    """Gmail commands."""
    # ... implementation
```

**Apply to all relevant commands**.

#### Step 3.3: Create interactive config prompting function

**File**: `src/gtool/cli/main.py`

**Add function**:

```python
def prompt_config_interactive(config: Config) -> None:
    """Prompt user interactively to configure application settings.

    Replaces Config.prompt() method. Interactive UI logic belongs in CLI layer.

    Args:
        config: Config object to update

    Raises:
        click.UsageError: If validation fails during save
    """
    click.echo("Let's configure gtool...")
    click.echo()

    # Collect user input
    credentials = click.prompt(
        "Path to credentials.json",
        default=config.get("CREDENTIALS_FILE")
    )
    credentials = os.path.expanduser(credentials)

    token = click.prompt(
        "Path to token.json",
        default=config.get("TOKEN_FILE")
    )
    token = os.path.expanduser(token)

    time_zone = click.prompt(
        "Default time zone",
        default=config.get("TIME_ZONE")
    )

    # ... more prompts as needed

    # Update config (config layer has no click dependency)
    config.set("CREDENTIALS_FILE", credentials)
    config.set("TOKEN_FILE", token)
    config.set("TIME_ZONE", time_zone)

    # Validate and save
    try:
        config.validate()
        config.save()
    except ConfigValidationError as e:
        raise click.UsageError(str(e))

    click.echo()
    click.echo("✓ Configuration saved successfully!")
```

#### Step 3.4: Update config command

**File**: `src/gtool/cli/main.py`

**Find the `config` command and update**:

```python
@cli.command()
@click.pass_context
def config(ctx):
    """Configure gtool settings interactively."""
    cfg = ctx.obj["config"]

    # Use new CLI-layer prompting function
    prompt_config_interactive(cfg)
```

#### Step 3.5: Add CLI exception translation tests

**File**: `tests/test_cli.py`

**Add tests**:

```python
from gtool.infrastructure.exceptions import AuthError, ServiceError
from gtool.config.settings import ConfigValidationError
from gtool.cli.errors import AuthenticationError, CLIError


def test_auth_error_translated_to_authentication_error(mocker):
    """Verify AuthError is translated to AuthenticationError in CLI."""
    # Mock infrastructure to raise AuthError
    mocker.patch('gtool.infrastructure.auth.GoogleAuth.get_credentials',
                 side_effect=AuthError("Auth failed"))

    # CLI command should translate to AuthenticationError
    with pytest.raises(AuthenticationError, match="Auth failed"):
        # Invoke CLI command that triggers auth
        pass


def test_service_error_translated_to_cli_error(mocker):
    """Verify ServiceError is translated to CLIError in CLI."""
    # Mock to raise ServiceError
    mocker.patch('gtool.clients.calendar.CalendarClient.get_events',
                 side_effect=ServiceError("API unavailable"))

    # CLI should translate to CLIError
    with pytest.raises(CLIError, match="Service error: API unavailable"):
        # Invoke CLI command
        pass


def test_config_validation_error_translated_to_usage_error(mocker):
    """Verify ConfigValidationError translated to click.UsageError in CLI."""
    # Mock config to raise validation error
    mocker.patch('gtool.config.settings.Config.validate_gmail_scopes',
                 side_effect=ConfigValidationError("Gmail scopes missing"))

    # CLI should translate to UsageError
    with pytest.raises(click.UsageError, match="Gmail scopes missing"):
        # Invoke command that validates config
        pass
```

**Test**:

```bash
# Run CLI tests
uv run pytest tests/test_cli.py -v

# Run all tests
uv run pytest
```

**Checkpoint Phase 3**:

- ✅ Exception translation decorator added
- ✅ Decorator applied to all relevant commands
- ✅ Interactive prompting moved to CLI
- ✅ Config command uses new prompting
- ✅ CLI tests pass
- ✅ Exception translation tests pass

---

### Phase 4: Integration & Validation

**Goal**: Verify complete implementation and backward compatibility.

#### Step 4.1: Run full test suite

```bash
# Run all tests
uv run pytest -v

# Expected: All tests pass (100% success)
```

#### Step 4.2: Verify import independence

```bash
# Test infrastructure imports without click
python -c "
from gtool.infrastructure.auth import GoogleAuth
from gtool.infrastructure.retry import RetryPolicy
from gtool.infrastructure.exceptions import AuthError, ServiceError
print('✓ Infrastructure imports without click')
"

# Test config imports without click
python -c "
from gtool.config.settings import Config, ConfigValidationError
print('✓ Config imports without click')
"
```

#### Step 4.3: Manual testing

Test the CLI to ensure backward compatibility:

```bash
# Test config command (interactive prompting)
uv run gtool config

# Test calendar commands (auth translation)
uv run gtool get-calendars

# Test gmail commands (exception handling)
uv run gtool gmail list --limit 5

# Verify error messages are user-friendly
# (Manually trigger errors to check)
```

#### Step 4.4: Create non-CLI usage demonstration

**File**: `tests/test_non_cli_usage.py` or similar

**Create example**:

```python
"""Demonstration that infrastructure can be used in non-CLI context."""

def test_infrastructure_in_api_server_context():
    """Simulate using gtool infrastructure in a web API server."""
    from gtool.infrastructure.auth import GoogleAuth
    from gtool.infrastructure.exceptions import AuthError
    from gtool.config.settings import Config

    # This would work in a FastAPI/Flask app without click
    config = Config()
    auth = GoogleAuth(config)

    try:
        credentials = auth.get_credentials()
        # Use credentials in API server
        assert credentials is not None
    except AuthError as e:
        # API server catches and returns HTTP 401
        # (no CLI error types involved)
        error_response = {"error": "Authentication failed", "detail": str(e)}
        assert error_response is not None
```

**Test**:

```bash
uv run pytest tests/test_non_cli_usage.py -v
```

**Checkpoint Phase 4**:

- ✅ All tests pass (100%)
- ✅ Infrastructure imports without click
- ✅ Config imports without click
- ✅ CLI works identically to before
- ✅ Non-CLI usage demonstrated

---

## Verification Checklist

Before marking implementation complete:

### Code Changes

- [ ] No `import click` in `src/gtool/infrastructure/`
- [ ] No `import click` in `src/gtool/config/`
- [ ] No `from gtool.cli` in `src/gtool/infrastructure/`
- [ ] No `from gtool.cli` in `src/gtool/config/`
- [ ] `ConfigError` added to `infrastructure/exceptions.py`
- [ ] `ConfigValidationError` added to `config/settings.py`
- [ ] `Config.prompt()` removed from `config/settings.py`
- [ ] `handle_infrastructure_errors` decorator added to CLI
- [ ] `prompt_config_interactive()` function added to CLI
- [ ] Exception translation decorator applied to commands

### Tests

- [ ] All existing tests pass
- [ ] Infrastructure tests expect `AuthError` (not CLI exceptions)
- [ ] Config tests expect `ConfigValidationError` (not `click.UsageError`)
- [ ] CLI tests verify exception translation
- [ ] Non-CLI usage test added

### Documentation

- [ ] Docstrings updated (no CLI references in infrastructure/config)
- [ ] Exception hierarchy documented
- [ ] Quickstart validated

### Manual Verification

- [ ] `gtool config` command works
- [ ] `gtool get-calendars` command works
- [ ] `gtool gmail list` command works
- [ ] Error messages are user-friendly
- [ ] Import independence verified

---

## Common Issues & Solutions

### Issue 1: Circular Import

**Symptom**: ImportError about circular dependencies

**Solution**: Ensure dependency direction is correct:

- CLI can import infrastructure ✅
- CLI can import config ✅
- Infrastructure CANNOT import CLI ❌
- Config CANNOT import CLI ❌

### Issue 2: Tests Failing After Exception Changes

**Symptom**: Tests expecting old exception types fail

**Solution**: Update test assertions:

```python
# Before
with pytest.raises(click.UsageError):

# After
from gtool.config.settings import ConfigValidationError
with pytest.raises(ConfigValidationError):
```

### Issue 3: CLI Command Missing Exception Translation

**Symptom**: Infrastructure exceptions leak to users

**Solution**: Apply decorator to command:

```python
@cli.command()
@handle_infrastructure_errors  # Add this
def my_command():
    pass
```

### Issue 4: Config.prompt() Removed But Still Called

**Symptom**: AttributeError: 'Config' object has no attribute 'prompt'

**Solution**: Replace with CLI-layer prompting:

```python
# Before
config.prompt()

# After
prompt_config_interactive(config)
```

---

## Success Criteria Validation

Verify each success criterion from [spec.md](spec.md):

1. **SC-001**: Infrastructure imports without click

   ```bash
   python -c "from gtool.infrastructure.auth import GoogleAuth" # No click required
   ```

2. **SC-002**: Config testable without click mocking

   ```bash
   uv run pytest tests/test_config.py -v  # No click mocks
   ```

3. **SC-003**: All existing CLI tests pass

   ```bash
   uv run pytest tests/test_cli.py -v  # 100% pass
   ```

4. **SC-004**: Non-CLI reuse demonstrated

   ```bash
   uv run pytest tests/test_non_cli_usage.py -v
   ```

5. **SC-005**: Exception flow documented
   - See [data-model.md](data-model.md) and [contracts/exception-contracts.md](contracts/exception-contracts.md)

---

## Next Steps

After completing this implementation:

1. **Code Review**: Request review focusing on:
   - Exception handling correctness
   - Import independence
   - Backward compatibility
   - Test coverage

2. **Merge Strategy**:
   - Merge to main after approval
   - Tag with version if needed
   - Update main README if exception handling changed

3. **Future Work**:
   - Consider implementing non-CLI interfaces (GUI, API)
   - Document architecture for future contributors
   - Monitor for new CLI dependencies creeping back in

---

## Getting Help

If stuck during implementation:

1. Review [research.md](research.md) for design decisions
2. Check [contracts/exception-contracts.md](contracts/exception-contracts.md) for exception rules
3. Look at similar refactoring in [specs/001-gmail-client-refactor/](../../001-gmail-client-refactor/)
4. Ask for clarification in code review

---

**Happy refactoring! 🚀**
