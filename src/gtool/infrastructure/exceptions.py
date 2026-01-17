"""Exceptions used by infrastructure layer (auth, service factory, etc).

Exception Hierarchy:
    Exception (Python built-in)
    ├── AuthError - Authentication/authorization failures
    ├── ServiceError - Google API service failures
    └── ConfigError - Configuration errors (base for config layer)
        └── ConfigValidationError (defined in config.settings)

These exceptions are infrastructure-level and UI-agnostic. The CLI layer
translates these to user-friendly CLI exceptions:
    - AuthError → AuthenticationError (CLI)
    - ServiceError → CLIError (CLI)
    - ConfigValidationError → click.UsageError (CLI)
"""


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


class ConfigValidationError(ConfigError):
    """Configuration validation error.

    Raised when:
    - Required config keys are missing
    - Config values have incorrect types (e.g., SCOPES is not a list)
    - Config values fail validation rules
    - Gmail is enabled but scopes are not configured

    This exception should NEVER be raised from CLI layer.
    CLI layer MUST catch this and translate to click.UsageError.
    """

    pass

    pass
