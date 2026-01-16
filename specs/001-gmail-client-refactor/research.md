# Research Findings: Gmail Client Integration & Google Auth Refactoring

**Date**: 2026-01-15
**Phase**: Phase 0 Research
**Feature**: [spec.md](spec.md) | [plan.md](plan.md)

## Overview

This document captures findings from Phase 0 research investigations. All 5 research tasks have been completed with concrete decisions and rationale.

---

## Research Task 1: Google OAuth Scope Management Patterns

### Question

How should scopes be managed when users add Gmail to existing Calendar setup? Does adding scopes require full re-authentication or can we use incremental authorization?

### Investigation

**Current Implementation** (from `gcal_client.py:authenticate()`):

```python
creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh existing scopes
    else:
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
        creds = flow.run_local_server(port=0)  # OAuth flow for new scopes
```

**Key Findings**:

1. **Token file stores scopes**: The `Credentials.from_authorized_user_file()` accepts scopes parameter but validates against stored scopes in token
2. **Scope mismatch triggers re-auth**: If requested scopes differ from token scopes, `creds.valid` will be False, triggering OAuth flow
3. **Incremental auth supported**: Google OAuth2 allows incremental authorization where new scopes can be added by re-running OAuth flow with expanded scope list
4. **No automatic scope merge**: The library does NOT automatically merge scopes; developer must handle scope union logic

### Decision

**Approach**: **Explicit Scope Union with User Notification**

When Gmail scopes are added:

1. **Detect scope change**: Compare requested scopes with existing token scopes
2. **Notify user**: Display clear message: "New Gmail scopes detected. You'll be prompted to authorize additional permissions."
3. **Run OAuth flow**: Use `InstalledAppFlow` with complete scope list (Calendar + Gmail)
4. **Update token**: Save new credentials with all scopes to token file

**Implementation Pattern**:

```python
# In GoogleAuth.authenticate()
stored_scopes = self._load_token_scopes()  # Read from existing token
requested_scopes = set(self.config.get("SCOPES"))
new_scopes = requested_scopes - stored_scopes

if new_scopes:
    logger.info(f"New scopes detected: {new_scopes}. Re-authorization required.")
    # Force OAuth flow with full scope list
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, list(requested_scopes))
    creds = flow.run_local_server(port=0)
```

**Rationale**:

- Explicit and transparent to user (no silent auth failures)
- Works with Google's incremental authorization model
- Simple to implement and test
- Clear error messages if authorization fails

**Alternatives Considered**:

- **Silent scope addition**: Rejected because auth errors would be confusing
- **Separate token files per API**: Rejected because it complicates credential management and doesn't match Google's model

---

## Research Task 2: Token File Management for Multiple APIs

### Question

Can one token file contain credentials for multiple Google APIs (Calendar + Gmail)? How does token refresh work across multiple scopes?

### Investigation

**Token File Format** (JSON structure):

```json
{
  "token": "ya29.a0...",
  "refresh_token": "1//0...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "...",
  "client_secret": "...",
  "scopes": [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly"
  ]
}
```

**Key Findings**:

1. **Single token, multiple scopes**: One token file CAN and SHOULD contain all authorized scopes
2. **Unified refresh**: `creds.refresh(Request())` refreshes ALL scopes at once (not per-API)
3. **Scope validation on load**: When loading credentials, google-auth validates requested scopes against stored scopes
4. **Service independence**: Multiple services (Calendar v3, Gmail v1) can share same credentials object

**From existing code**:

```python
# Current pattern (works for multiple APIs)
creds = Credentials.from_authorized_user_file(token_file, scopes)  # scopes = all APIs
service1 = build("calendar", "v3", credentials=creds)
service2 = build("gmail", "v1", credentials=creds)  # Same creds, different service
```

### Decision

**Approach**: **Single Shared Token File**

- **One token file** (`~/.config/caltool/token.json`) for all Google API clients
- **All scopes stored together** in the token's `scopes` array
- **All clients share credentials**: GoogleAuth module provides credentials to all clients
- **Single refresh point**: Only GoogleAuth handles token refresh; clients just use credentials

**Implementation Pattern**:

```python
# google_auth.py
class GoogleAuth:
    def __init__(self, config):
        self.token_file = config.get("TOKEN_FILE")
        self.credentials_file = config.get("CREDENTIALS_FILE")
        self.scopes = config.get("SCOPES")  # Full list: Calendar + Gmail + future

    def get_credentials(self) -> Credentials:
        """Return valid credentials for all configured scopes."""
        # Single auth flow, multiple services use result
        return self._authenticate()
```

**Rationale**:

- Matches Google OAuth2 design (token = sum of all authorized scopes)
- Simplifies credential management (one source of truth)
- Single refresh mechanism (no coordination needed between APIs)
- Users see unified permissions in Google Account settings

**Alternatives Considered**:

- **Separate token files per API**: Rejected — unnecessary complexity, violates DRY
- **Token file per scope**: Rejected — doesn't match Google's authorization model

---

## Research Task 3: Error Handling & Quota Management

### Question

How should rate limiting and quota errors be distinguished and handled? What error classification is needed?

### Investigation

**Current Error Handling** (from `gcal_client.py`):

```python
@retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
def get_calendar_list(self):
    try:
        # API call
    except HttpError as e:
        logger.error(f"Google API error: {e}")
        raise
```

**HttpError Status Codes** (from Google API documentation):

- **401 Unauthorized**: Invalid or expired credentials
- **403 Forbidden**:
  - Quota exceeded (`reason: "userRateLimitExceeded"` or `"quotaExceeded"`)
  - Insufficient permissions (`reason: "forbidden"`)
- **429 Too Many Requests**: Rate limit exceeded (retry with backoff)
- **500/502/503**: Transient server errors (safe to retry)
- **404 Not Found**: Resource doesn't exist (don't retry)

**Error Structure**:

```python
# HttpError has:
error.resp.status  # HTTP status code
error.error_details  # List of error details with 'reason' field
```

### Decision

**Approach**: **Categorized Error Handling with User-Friendly Messages**

Define 4 error categories:

1. **AUTH_ERROR**: 401, 403 forbidden — User needs to re-authenticate or fix scopes
2. **QUOTA_ERROR**: 403 quota exceeded, 429 — User needs to wait or request quota increase
3. **TRANSIENT_ERROR**: 500, 502, 503 — Automatic retry with exponential backoff
4. **CLIENT_ERROR**: 404, 400 — Don't retry; show clear message

**Implementation Pattern**:

```python
# google_client.py (base class)
class ErrorCategory(Enum):
    AUTH = "authentication"
    QUOTA = "quota_or_rate_limit"
    TRANSIENT = "temporary_server_error"
    CLIENT = "client_request_error"

def categorize_error(error: HttpError) -> ErrorCategory:
    """Classify HttpError for appropriate handling."""
    status = error.resp.status

    if status == 401:
        return ErrorCategory.AUTH

    if status == 403:
        # Check reason field
        details = getattr(error, 'error_details', [])
        for detail in details:
            reason = detail.get('reason', '')
            if reason in ['userRateLimitExceeded', 'quotaExceeded']:
                return ErrorCategory.QUOTA
        return ErrorCategory.AUTH  # Insufficient permissions

    if status == 429:
        return ErrorCategory.QUOTA

    if status in [500, 502, 503]:
        return ErrorCategory.TRANSIENT

    return ErrorCategory.CLIENT  # 404, 400, etc.

def handle_api_error(error: HttpError):
    """Provide user-friendly error messages."""
    category = categorize_error(error)

    if category == ErrorCategory.AUTH:
        raise click.UsageError(
            "Authentication failed. Run 'caltool config' to update credentials."
        )
    elif category == ErrorCategory.QUOTA:
        raise click.UsageError(
            "Google API quota exceeded. Please wait and try again later."
        )
    elif category == ErrorCategory.TRANSIENT:
        # Retry handled by decorator
        raise
    else:
        raise click.UsageError(f"API request failed: {error}")
```

**Retry Strategy**:

- **AUTH/CLIENT errors**: Don't retry (immediate user feedback)
- **QUOTA errors**: Retry with exponential backoff (3 attempts, 2/4/8 second delays)
- **TRANSIENT errors**: Retry with linear backoff (3 attempts, 2 second delays)

**Rationale**:

- Clear categorization enables appropriate handling per error type
- User-friendly messages direct users to solutions
- Retry logic matches Google API best practices
- Extensible for future API-specific error cases

**Alternatives Considered**:

- **Catch-all error handling**: Rejected — doesn't provide actionable user guidance
- **No categorization**: Rejected — retry logic would be inconsistent

---

## Research Task 4: Backward Compatibility Contract

### Question

What specific GCalClient behaviors must remain identical after refactoring?

### Investigation

**Current GCalClient Interface** (public methods):

```python
class GCalClient:
    def __init__(self, config, service: object | None = None)
    def authenticate(self) -> service
    def get_calendar_list(self) -> list
    def get_day_busy_times(calendar_ids, day_start, day_end, timezone) -> list
    def get_event_details(calendar_id, event_id) -> dict
    def get_events(calendar_id, start_time, end_time) -> list
```

**Current Usage Patterns** (from tests):

1. **Dependency injection**: `GCalClient(config, service=mock_service)` — tests inject mock service
2. **Config-based init**: `GCalClient(config)` — production uses config to build service
3. **Direct method calls**: `client.get_events(calendar_id, start_time, end_time)`
4. **Error propagation**: HttpError exceptions are raised (not swallowed)
5. **Retry behavior**: All methods decorated with `@retry_on_exception`

**CLI Integration** (from `cli.py`):

```python
@click.command()
def get_calendars(config):
    client = GCalClient(config)  # Must work unchanged
    calendars = client.get_calendar_list()  # Method signature unchanged
    # ... format and display
```

### Decision

**Backward Compatibility Contract**:

**MUST preserve**:

1. ✅ **Constructor signature**: `GCalClient(config, service=None)` — no changes
2. ✅ **Method signatures**: All 5 public methods keep exact signatures (params, return types)
3. ✅ **Method names**: No renames (get_calendar_list, get_day_busy_times, etc.)
4. ✅ **Exception types**: HttpError still raised from failed API calls
5. ✅ **Retry behavior**: Methods still decorated with retry logic (3 attempts, 2s delay)
6. ✅ **Service injection**: Tests can still inject mock service via constructor
7. ✅ **Return value formats**: Lists, dicts, and data structures unchanged

**MAY change** (internal implementation):

- ✅ Inheritance: GCalClient can inherit from GoogleAPIClient base class
- ✅ Authentication logic: Extracted to GoogleAuth module (called internally)
- ✅ Retry decorator: Moved to base class (behavior identical)
- ✅ Logging: Enhanced logging is acceptable

**Verification Strategy**:

```python
# All existing tests MUST pass without modification
# Example: tests/test_cli.py::test_gcalclient_injection
def test_gcalclient_injection(mock_config):
    mock_service = Mock()
    client = GCalClient(mock_config, service=mock_service)  # Must work
    assert client.service is mock_service  # Must pass
```

**Refactoring Pattern**:

```python
# Before (current)
class GCalClient:
    def __init__(self, config, service=None):
        self.service = service or self.authenticate()

    def authenticate(self):
        # 60 lines of auth logic here
        return build("calendar", "v3", credentials=creds)

# After (refactored)
class GCalClient(GoogleAPIClient):  # Inherit from base
    def __init__(self, config, service=None):
        super().__init__(config, "calendar", "v3", service)  # Base handles auth

    # All public methods unchanged (signatures, behavior, return types)
```

**Rationale**:

- Preserves all existing tests and CLI code
- Users experience zero breaking changes
- Inheritance is backward-compatible (Liskov substitution principle)
- Internal refactoring invisible to callers

**Alternatives Considered**:

- **Rename methods**: Rejected — breaks existing code
- **Change constructor**: Rejected — breaks dependency injection in tests
- **Modify return types**: Rejected — breaks downstream formatting logic

---

## Research Task 5: Base Class vs. Protocol Design Decision

### Question

Should we use inheritance (ABC) or Python protocol (structural typing) for GoogleAPIClient?

### Investigation

**Option A: Abstract Base Class (ABC)**

```python
from abc import ABC, abstractmethod

class GoogleAPIClient(ABC):
    def __init__(self, config, api_name, api_version, service=None):
        self.config = config
        self.auth = GoogleAuth(config)
        self.service = service or self._build_service(api_name, api_version)

    def _build_service(self, api_name, api_version):
        creds = self.auth.get_credentials()
        return build(api_name, api_version, credentials=creds)

    @abstractmethod
    def _handle_api_specific_error(self, error):
        """Subclasses can override for API-specific error handling."""
        pass

# Usage
class GCalClient(GoogleAPIClient):
    def __init__(self, config, service=None):
        super().__init__(config, "calendar", "v3", service)
```

**Option B: Protocol (Structural Typing)**

```python
from typing import Protocol

class GoogleAPIClient(Protocol):
    service: object
    config: Config

    def _build_service(self, api_name: str, api_version: str) -> object: ...
    def _handle_error(self, error: HttpError) -> None: ...

# Usage
class GCalClient:  # No inheritance
    service: object
    config: Config

    def __init__(self, config, service=None):
        self.config = config
        self.auth = GoogleAuth(config)  # Composition
        self.service = service or self._build_service("calendar", "v3")
```

**Comparison**:

| Aspect           | ABC (Inheritance)                     | Protocol (Structural)             |
| ---------------- | ------------------------------------- | --------------------------------- |
| Code reuse       | ✅ Excellent (shared methods in base) | ⚠️ Requires mixin or duplication  |
| Testability      | ✅ Easy to mock base class            | ✅ Easy to mock protocol          |
| Type checking    | ✅ Runtime + static (mypy)            | ✅ Static only (mypy)             |
| Flexibility      | ⚠️ Single inheritance limit           | ✅ Multiple protocols possible    |
| Backward compat  | ✅ Transparent (Liskov)               | ⚠️ Requires adding protocol attrs |
| Learning curve   | ✅ Familiar OOP pattern               | ⚠️ Advanced Python feature        |
| Refactoring ease | ✅ Move code to base class            | ⚠️ Must update all clients        |

### Decision

**Approach**: **Abstract Base Class (ABC) with Composition**

Use ABC for shared implementation and composition for dependency injection:

```python
# google_client.py
from abc import ABC
from googleapiclient.discovery import build

class GoogleAPIClient(ABC):
    """Base class for all Google API clients."""

    def __init__(self, config: Config, api_name: str, api_version: str, service: object | None = None):
        self.config = config
        self.service = service or self._build_service(api_name, api_version)

    def _build_service(self, api_name: str, api_version: str) -> object:
        """Build Google API service with authenticated credentials."""
        auth = GoogleAuth(self.config)  # Composition: Auth is injected
        creds = auth.get_credentials()
        return build(api_name, api_version, credentials=creds)

    @retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def _api_call_with_retry(self, func):
        """Shared retry wrapper for API calls."""
        try:
            return func()
        except HttpError as e:
            handle_api_error(e)  # Shared error handling
            raise

# gcal_client.py
class GCalClient(GoogleAPIClient):
    def __init__(self, config: Config, service: object | None = None):
        super().__init__(config, "calendar", "v3", service)

    # All existing methods unchanged

# gmail_client.py (new)
class GMailClient(GoogleAPIClient):
    def __init__(self, config: Config, service: object | None = None):
        super().__init__(config, "gmail", "v1", service)

    def list_messages(self, query: str = "", max_results: int = 10):
        # Gmail-specific implementation
```

**Rationale**:

1. **Code reuse**: Auth logic, service building, retry decorator all shared via inheritance
2. **Backward compatibility**: GCalClient inherits base behavior, existing interface preserved
3. **Familiar pattern**: Team already uses OOP; ABC is well-understood
4. **Easy testing**: Base class easily mocked; service injection still works
5. **Maintainability**: Shared logic in one place; changes propagate to all clients
6. **Future-proof**: Adding Drive, Sheets, etc. follows same pattern

**Why not Protocol**:

- Protocol is more advanced/abstract (steeper learning curve)
- Would require duplicating auth/retry logic across clients (DRY violation)
- Doesn't provide implementation reuse (only type checking)
- Refactoring existing GCalClient would be more invasive

**Alternatives Considered**:

- **Pure Protocol**: Rejected — loses code reuse benefits
- **Mixin classes**: Rejected — more complex than ABC, unclear composition rules
- **No base class**: Rejected — duplicates auth/retry logic across clients

---

## Summary of Decisions

| Research Task                 | Decision                                                                                 | Key Rationale                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **1. OAuth Scope Management** | Explicit scope union with user notification; re-run OAuth when new scopes detected       | Transparent, matches Google's incremental auth model            |
| **2. Token File Management**  | Single shared token file for all APIs; all scopes stored together                        | Simplifies credential management; matches Google OAuth2 design  |
| **3. Error Handling**         | Categorize errors (AUTH/QUOTA/TRANSIENT/CLIENT); user-friendly messages with retry logic | Actionable guidance for users; appropriate retry per error type |
| **4. Backward Compatibility** | Preserve all GCalClient public methods, signatures, and behaviors                        | Zero breaking changes; all existing tests pass unchanged        |
| **5. Base Class Design**      | Abstract Base Class (ABC) with composition                                               | Code reuse, familiar OOP pattern, easy testing                  |

---

## Next Steps

**Phase 1: Design & Contracts**

- Create `data-model.md` with entity definitions (GoogleAuth, GoogleAPIClient, GMailClient, Config)
- Define contracts in `contracts/` directory (interfaces, schemas)
- Write `quickstart.md` for developer onboarding
- Update agent context with new patterns

All research unknowns have been resolved. Ready to proceed to Phase 1 design.

---

**Research Complete**: 2026-01-15
**No blocking issues identified**
**Constitution compliance: ✅ PASS (all 5 principles satisfied)**
