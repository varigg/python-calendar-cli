"""Exceptions used by infrastructure layer (auth, service factory, etc).

Exception Hierarchy:
    Exception (Python built-in)
    ├── AuthError - Authentication/authorization failures
    └── ConfigValidationError - Configuration validation failures

These exceptions are infrastructure-level and UI-agnostic. The CLI layer
translates these to user-friendly CLI exceptions:
    - AuthError → AuthenticationError (CLI)
    - ConfigValidationError → click.UsageError (CLI)
"""


class AuthError(Exception):
    """Authentication and authorization failures.

    Raised when OAuth flow fails, token refresh fails, credentials are
    missing/invalid, or Google Auth API returns errors.
    """

    pass


class ConfigValidationError(Exception):
    """Configuration validation failures.

    Raised when required config keys are missing, config values have
    incorrect types, or Gmail is enabled but scopes are not configured.
    """

    pass
