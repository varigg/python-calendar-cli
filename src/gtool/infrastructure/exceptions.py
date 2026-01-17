"""Exceptions used by infrastructure layer (auth, service factory, etc)."""


class AuthError(Exception):
    """Base exception for authentication and authorization failures."""

    pass


class ServiceError(Exception):
    """Base exception for service/API failures."""

    pass
