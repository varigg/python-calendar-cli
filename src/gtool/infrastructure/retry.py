"""RetryPolicy for handling transient failures with exponential backoff.

Manages retry logic with smart categorization of Google API errors.
Separates retry policy from API client implementation.
"""

import logging
import time
from typing import Any, Callable

import google.auth.exceptions
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class RetryPolicy:
    """Manages retry logic for Google API calls with smart error categorization.

    Retries transient errors (QUOTA, TRANSIENT) with exponential backoff.
    Does not retry permanent errors (AUTH, CLIENT).

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay in seconds before first retry (default: 1.0)

    Example:
        >>> policy = RetryPolicy(max_retries=3, delay=1.0)
        >>> result = policy.execute(api_call, arg1, arg2)
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
    ) -> None:
        """Initialize RetryPolicy.

        Args:
            max_retries: Maximum retry attempts
            delay: Initial delay between retries in seconds
        """
        self.max_retries = max_retries
        self.delay = delay

    def _categorize_error(self, error: HttpError) -> str:
        """Categorize an HTTP error from Google API.

        Maps HTTP status codes to retry-relevant categories:
        - AUTH: Authentication/authorization errors (401, 403 with auth scope)
        - QUOTA: Rate limiting or quota errors (429, 403 with quota)
        - TRANSIENT: Temporary server errors (5xx)
        - CLIENT: Client errors that won't resolve with retries (4xx except above)

        Args:
            error: HttpError from googleapiclient library

        Returns:
            str: One of "AUTH", "QUOTA", "TRANSIENT", or "CLIENT"

        Raises:
            TypeError: If error is not an HttpError instance
        """
        if not isinstance(error, HttpError):
            raise TypeError(f"Expected HttpError, got {type(error)}")

        status_code = error.resp.status

        # Map status codes to categories
        if status_code == 401:
            return "AUTH"
        elif status_code == 403:
            # 403 can be quota exhausted or permission denied
            # Treat as QUOTA for retry logic (most common case)
            return "QUOTA"
        elif status_code == 429:
            return "QUOTA"
        elif 500 <= status_code < 600:
            return "TRANSIENT"
        else:
            return "CLIENT"

    def should_retry(self, error_category: str) -> bool:
        """Determine if an error should be retried.

        Args:
            error_category: Error category string

        Returns:
            bool: True if error should be retried, False otherwise
        """
        retryable_categories = {"QUOTA", "TRANSIENT"}
        return error_category in retryable_categories

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function with retry logic.

        Args:
            func: Callable to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result of func execution

        Raises:
            AuthenticationError: If Google auth error occurs
            Exception: Original exception if retries exhausted or error not retryable
        """
        attempt = 0

        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except google.auth.exceptions.GoogleAuthError as exc:
                # Wrap Google auth exceptions as AuthError
                # CLI layer will translate this to AuthenticationError for user-facing messages
                from gtool.infrastructure.exceptions import AuthError

                logger.debug(f"Google auth error caught and wrapped: {exc}")
                raise AuthError(f"Authentication failed: {exc}") from exc
            except Exception as exc:
                attempt += 1

                # Try to categorize the error
                error_category = "TRANSIENT"
                try:
                    error_category = self._categorize_error(exc)
                except (TypeError, AttributeError):
                    # If categorization fails (not an HttpError), treat as TRANSIENT
                    error_category = "TRANSIENT"

                # Check if we should retry
                if not self.should_retry(error_category) or attempt > self.max_retries:
                    raise

                # Exponential backoff: delay * (2 ** (attempt - 1))
                wait_time = self.delay * (2 ** (attempt - 1))
                time.sleep(wait_time)
