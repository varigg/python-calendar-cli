# Test Performance Analysis

## Issue Summary

Test execution time regressed from **3.93s** to **18.29s** (365% slower) after implementing feature 006-layer-separation.

## Investigation Results

### Slowest Tests (Before Fix)
Using `pytest --durations=10`:
```
14.40s call     tests/test_layer_separation.py::TestGmailScopeValidation::test_gmail_command_fails_without_gmail_scope
0.03s call     tests/test_retry_policy.py::test_retry_policy_exponential_backoff
```

**One test was taking 14.4 seconds** - 81% of total test time!

### Root Cause Analysis

The slow test `test_gmail_command_fails_without_gmail_scope` was:
1. Setting `GMAIL_ENABLED = False` to test validation logic
2. The `gmail()` group function called `validate_gmail_scopes()` which only validates when `GMAIL_ENABLED = True`
3. With validation passing (incorrectly), the command proceeded to call the Gmail API
4. Gmail API returned 403 "Insufficient authentication scopes" error
5. Retry policy kicked in with exponential backoff: `max_retries=3`, `delay=2.0`
6. Each retry took ~2-5 seconds, totaling **~14 seconds**

### Additional Issue Discovered

When fixing the performance issue, discovered a critical bug in the CLI group initialization:

**Problem**: The `cli()` function was **unconditionally** creating a new `Config()` instance and assigning it to `ctx.obj`, even when tests passed a mock config via `runner.invoke(cli, [...], obj=mock_config)`.

**Impact**: All tests that relied on passing a mock config were actually running with a fresh Config instance, not their carefully prepared mock. This caused Gmail tests to fail because:
- Tests set `mock_config.data["SCOPES"].append("gmail.readonly")`
- But `cli()` replaced `ctx.obj` with a new `Config()` instance
- Gmail commands received the new config, which had no Gmail scopes
- Commands failed with "Gmail scope not configured" error

## Fixes Applied

### 1. Performance Fix: Direct Scope Validation

Changed `gmail()` group function from calling `validate_gmail_scopes()` to directly checking `has_gmail_scope()`:

**Before (buggy):**
```python
@cli.group("gmail", help="Manage Gmail messages (requires Gmail scope)")
@click.pass_obj
def gmail(config):
    """Gmail management commands."""
    config.validate_gmail_scopes()  # Only checks when GMAIL_ENABLED=True
```

**After (fixed):**
```python
@cli.group("gmail", help="Manage Gmail messages (requires Gmail scope)")
@click.pass_obj
def gmail(config):
    """Gmail management commands."""
    if not config.has_gmail_scope("readonly"):
        raise click.UsageError(
            "Gmail scope not configured. Run 'gtool config' to add Gmail permissions."
        )
```

### 2. Config Injection Fix: Respect Test Mocks

Changed `cli()` function to only create a new Config when one isn't already provided:

**Before (buggy):**
```python
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging for troubleshooting.")
@click.pass_context
def cli(ctx, debug):
    """Calendar CLI tool for managing Google Calendar availability and events."""
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    # Load config once and pass as obj
    config = Config()
    try:
        config.validate()
    except (CLIError, AuthError, ConfigValidationError) as e:
        handle_cli_exception(e)
    ctx.obj = config  # Always overwrites ctx.obj!
```

**After (fixed):**
```python
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging for troubleshooting.")
@click.pass_context
def cli(ctx, debug):
    """Calendar CLI tool for managing Google Calendar availability and events."""
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    # Load config once and pass as obj (unless already provided for testing)
    if ctx.obj is None:
        config = Config()
        try:
            config.validate()
        except (CLIError, AuthError, ConfigValidationError) as e:
            handle_cli_exception(e)
        ctx.obj = config
```

## Performance Results

### Before Fixes
- **Total time**: 18.29s
- **Slowest test**: 14.40s (test_gmail_command_fails_without_gmail_scope)
- **Test failures**: 0 (but tests were using wrong config!)

### After Performance Fix Only
- **Total time**: 8.32s (54% improvement)
- **Slowest test**: 0.03s (retry policy test)
- **Test failures**: 5 (Gmail tests failed due to config injection bug)

### After Both Fixes
- **Total time**: 4.34s (76% improvement from worst, 10% better than original baseline!)
- **Slowest test**: 0.03s (retry policy test)
- **Test failures**: 0
- **Tests passing**: 114/114

## Key Takeaways

1. **Validation Logic Gaps**: Methods that conditionally validate based on flags (like `GMAIL_ENABLED`) can create unexpected behavior when tests set those flags to control test scenarios.

2. **Retry Policy Impact**: Exponential backoff retry policies can dramatically increase test time when tests trigger real API calls that fail. Always mock external services properly.

3. **Test Isolation**: Click's context object injection must be handled carefully to support test mocking. Always check if `ctx.obj` is already set before overwriting it.

4. **Performance Debugging**: `pytest --durations` is invaluable for identifying performance bottlenecks. In this case, one test was responsible for 81% of total test time.

5. **Hidden Bugs**: Performance investigations can reveal deeper architectural issues. The config injection bug was hidden because tests were "passing" - they just weren't testing what we thought they were testing!

## Recommendations

1. ✅ **Applied**: Always validate critical scopes regardless of feature flags
2. ✅ **Applied**: Check for existing context objects before creating new ones in CLI groups
3. **Future**: Consider adding a test to verify that `runner.invoke(cli, obj=mock)` actually uses the mock
4. **Future**: Add performance regression tests to CI pipeline (e.g., fail if total test time > 10s)
