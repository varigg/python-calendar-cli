# Data Model: Layer Separation Enforcement

**Feature**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Research**: [research.md](research.md)
**Date**: 2026-01-17

## Purpose

This document defines the data entities (exception types) involved in the layer separation refactoring. While this is primarily an architectural refactoring, the exception hierarchy represents the core "data model" for error handling across layers.

---

## Entity: Infrastructure Exceptions

### AuthError

**Purpose**: Represents authentication and authorization failures at the infrastructure level.

**Location**: `src/gtool/infrastructure/exceptions.py`

**Attributes**:

- Inherits from `Exception`
- Message string describing the auth failure

**When Raised**:

- OAuth flow failures
- Token refresh failures
- Missing or invalid credentials
- Google auth API errors

**Used By**:

- `GoogleAuth` class in `auth.py`
- Any infrastructure code handling authentication

**Mapped To** (in CLI layer):

- `AuthenticationError` (CLI-friendly presentation)

**Example**:

```python
raise AuthError("Failed to refresh expired token: invalid_grant")
```

---

### ServiceError

**Purpose**: Represents Google API service failures at the infrastructure level.

**Location**: `src/gtool/infrastructure/exceptions.py`

**Attributes**:

- Inherits from `Exception`
- Message string describing the service failure

**When Raised**:

- Google API HTTP errors (5xx)
- Network connectivity issues
- API quota exceeded (after retries exhausted)
- Service unavailable errors

**Used By**:

- `RetryPolicy` class in `retry.py`
- Google API clients (Calendar, Gmail)

**Mapped To** (in CLI layer):

- `CLIError` (generic CLI error with context)

**Example**:

```python
raise ServiceError("Google Calendar API returned 503: Service Unavailable")
```

---

### ConfigError

**Purpose**: Base exception for configuration-related failures at the infrastructure level.

**Location**: `src/gtool/infrastructure/exceptions.py` (**NEW**)

**Attributes**:

- Inherits from `Exception`
- Message string describing the config failure

**When Raised**:

- Base class for config exceptions
- Not raised directly; used for catching multiple config error types

**Used By**:

- Config layer as base class
- CLI layer for catching all config errors

**Subclasses**:

- `ConfigValidationError`

**Example**:

```python
try:
    config.validate()
except ConfigError as e:
    # Handle any config-related error
    logger.error(f"Configuration error: {e}")
```

---

## Entity: Config Exceptions

### ConfigValidationError

**Purpose**: Represents validation failures in configuration data.

**Location**: `src/gtool/config/settings.py` (**NEW**)

**Attributes**:

- Inherits from `ConfigError`
- Message string describing the validation failure

**When Raised**:

- Missing required configuration keys
- Invalid configuration values
- Gmail scope validation failures
- Configuration format errors

**Used By**:

- `Config.validate()` method
- `Config.validate_gmail_scopes()` method
- Any config validation logic

**Mapped To** (in CLI layer):

- `click.UsageError` (indicates user input issue)

**Example**:

```python
raise ConfigValidationError("Gmail enabled but gmail scopes not in SCOPES list. Run 'gtool config'...")
```

---

## Entity: CLI Exceptions (No Changes)

These exceptions remain in `src/gtool/cli/errors.py` and are used for user-facing error presentation.

### CLIError

**Purpose**: Base exception for CLI-layer errors (existing).

**Attributes**:

- Inherits from `click.ClickException`
- User-friendly message

**When Used**:

- Generic CLI errors
- Wraps `ServiceError` from infrastructure

### AuthenticationError

**Purpose**: CLI-specific authentication error (existing).

**Attributes**:

- Inherits from `CLIError`
- User-friendly auth failure message

**When Used**:

- Wraps `AuthError` from infrastructure
- User-facing auth error presentation

---

## Exception Hierarchy (Complete)

```
Exception (Python built-in)
│
├── AuthError (infrastructure.exceptions - EXISTING)
│   Purpose: Infrastructure auth failures
│   Used by: GoogleAuth, retry logic
│
├── ServiceError (infrastructure.exceptions - EXISTING)
│   Purpose: Infrastructure service failures
│   Used by: RetryPolicy, API clients
│
├── ConfigError (infrastructure.exceptions - NEW)
│   Purpose: Base for config failures
│   Used by: Config layer
│   │
│   └── ConfigValidationError (config.settings - NEW)
│       Purpose: Config validation failures
│       Used by: Config.validate(), validate_gmail_scopes()
│
└── click.ClickException
    │
    └── CLIError (cli.errors - EXISTING)
        Purpose: Base CLI error
        Used by: CLI commands
        │
        └── AuthenticationError (cli.errors - EXISTING)
            Purpose: CLI auth error presentation
            Used by: CLI commands with auth
```

---

## Exception Flow Diagram

```
Infrastructure Layer          Config Layer              CLI Layer
─────────────────────────────────────────────────────────────────

[GoogleAuth]                [Config]                 [CLI Commands]
     │                           │                          │
     │ Auth fails                │ Validation fails         │
     ├─> AuthError               ├─> ConfigValidationError │
     │                           │                          │
     │                           │                          ▼
     │                           │                    [@decorator]
     │                           │                     catch & translate
     │                           │                          │
     └───────────────────────────┴──────────────────────────┤
                                                             │
                              Exception Translation          │
                              ─────────────────────          │
                              AuthError → AuthenticationError│
                              ServiceError → CLIError        │
                              ConfigValidationError → UsageError
                                                             │
                                                             ▼
                                                      [User sees error]
```

---

## State Transitions

### Authentication State Machine

```
[No Credentials]
     │
     ├─> Attempt auth
     │
     ├─> Success: [Valid Credentials]
     │
     └─> Failure: raise AuthError
              │
              └─> CLI catches → raise AuthenticationError
                       │
                       └─> User sees friendly message
```

### Configuration State Machine

```
[Empty/Invalid Config]
     │
     ├─> Validate config
     │
     ├─> Valid: [Ready to Use]
     │
     └─> Invalid: raise ConfigValidationError
              │
              └─> CLI catches → raise click.UsageError
                       │
                       └─> User sees validation message + guidance
```

---

## Validation Rules

### AuthError Validation

- **MUST** be raised for auth failures, never CLI errors
- **MUST** include descriptive message about failure cause
- **MUST** be raised from infrastructure layer only

### ServiceError Validation

- **MUST** be raised for service failures, never CLI errors
- **MUST** include API context (status code, service name)
- **MUST** be raised from infrastructure layer only

### ConfigValidationError Validation

- **MUST** be raised for validation failures, never `click.UsageError`
- **MUST** include specific validation failure (which key/value failed)
- **SHOULD** include guidance on how to fix
- **MUST** be raised from config layer only

### CLI Exception Mapping Validation

- **MUST** preserve exception chain (use `from e`)
- **MUST** maintain or improve error message clarity
- **MUST** catch infrastructure exceptions and translate to CLI
- **MUST NOT** let infrastructure exceptions leak to users

---

## Relationships

### Infrastructure → Config

- Config layer can raise `ConfigError` and subclasses
- Config layer does NOT raise infrastructure exceptions
- Config layer does NOT raise CLI exceptions

### Infrastructure → CLI

- CLI layer catches infrastructure exceptions
- CLI layer translates to CLI exceptions
- CLI layer adds user-friendly context

### Config → CLI

- CLI layer catches config exceptions
- CLI layer translates to `click.UsageError`
- CLI layer adds interactive prompting

---

## Data Model Summary

This refactoring introduces **two new exception types**:

1. **ConfigError** (base class in infrastructure.exceptions)
   - Enables catching all config errors
   - Maintains infrastructure independence

2. **ConfigValidationError** (in config.settings)
   - Replaces `click.UsageError` for validation
   - Enables config testing without CLI

**No existing exceptions are modified**, only usage patterns change:

- Infrastructure raises `AuthError` consistently (no CLI errors)
- CLI catches and translates to user-friendly presentation
- Config raises domain exceptions (no UI exceptions)

**Impact**: Clear exception boundaries enable layer independence and reusability.
