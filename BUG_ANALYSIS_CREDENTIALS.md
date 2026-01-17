# Gmail Command Error Analysis and Fix

## Issue

Running `uv run gtool gmail list` produces:

```
AttributeError: 'GoogleAuth' object has no attribute 'credentials'. Did you mean: 'get_credentials'?
```

## Root Cause

The bug is in [service_factory.py](service_factory.py#L52). The code attempted to access `credentials` as a property on the `GoogleAuth` object:

```python
# BUGGY CODE (line 52 in service_factory.py)
credentials=self._auth.credentials
```

However, `GoogleAuth` doesn't expose `credentials` as a property. Instead, it provides a **method** `get_credentials()` that returns valid credentials.

### Why This Bug Existed

The discrepancy is due to a refactoring where:

- **Expected interface**: `auth.credentials` (property)
- **Actual interface**: `auth.get_credentials()` (method)

The refactoring updated `GoogleAuth` to use a method, but `ServiceFactory` was not updated to call it.

## Evidence from Code

**GoogleAuth class** ([auth.py](auth.py#L92-L135)):

```python
def get_credentials(self) -> Credentials:
    """Get valid Google API credentials.

    This method implements the complete credential acquisition flow:
    1. Load existing token if present
    2. Check if token is valid
    3. If expired, attempt refresh
    4. If no token or refresh fails, initiate new OAuth flow
    5. Save token to file
    """
    # ... implementation
    return creds
```

**ServiceFactory class** (BEFORE - [service_factory.py](service_factory.py#L42-L56)):

```python
def build_service(self, api_name: str, api_version: str) -> Any:
    cache_key = (api_name, api_version)
    if cache_key not in self._services:
        self._services[cache_key] = discovery.build(
            api_name,
            api_version,
            credentials=self._auth.credentials,  # ❌ BUG: should call get_credentials()
        )
    return self._services[cache_key]
```

## Test Reproduction

Created [tests/test_credentials_bug.py](test_credentials_bug.py) with two tests:

1. **test_service_factory_calls_get_credentials_method**: Verifies that `get_credentials()` is called
2. **test_service_factory_build_service_with_strict_auth_mock**: Verifies the fix works with a strict mock that only has `get_credentials()`

Run the tests:

```bash
uv run pytest tests/test_credentials_bug.py -v
```

## Fix Applied

Changed [service_factory.py](service_factory.py#L63) line 63 from:

```python
credentials=self._auth.credentials,
```

To:

```python
credentials=self._auth.get_credentials(),
```

**Updated Code**:

```python
def build_service(self, api_name: str, api_version: str) -> Any:
    cache_key = (api_name, api_version)
    if cache_key not in self._services:
        self._services[cache_key] = discovery.build(
            api_name,
            api_version,
            credentials=self._auth.get_credentials(),  # ✅ FIXED: Call the method
        )
    return self._services[cache_key]
```

## Results

- ✅ New tests now pass
- ✅ Existing `test_service_factory.py` tests still pass
- ✅ The AttributeError is resolved
