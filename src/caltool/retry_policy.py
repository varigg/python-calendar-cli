"""RetryPolicy component for composition-based architecture.

Manages retry logic with smart categorization using ErrorCategorizer.
Separates retry policy from API client implementation.
"""

import time
from typing import Any, Callable, Optional

from caltool.error_categorizer import ErrorCategorizer


class RetryPolicy:
    """Manages retry logic for Google API calls with smart error categorization.

    Retries transient errors (QUOTA, TRANSIENT) with exponential backoff.
    Does not retry permanent errors (AUTH, CLIENT).

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay in seconds before first retry (default: 1.0)
        error_categorizer: ErrorCategorizer instance for error classification

    Example:
        >>> categorizer = ErrorCategorizer()
        >>> policy = RetryPolicy(max_retries=3, delay=1.0, error_categorizer=categorizer)
        >>> result = policy.execute(api_call, arg1, arg2)
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        error_categorizer: Optional[ErrorCategorizer] = None,
    ) -> None:
        """Initialize RetryPolicy.

        Args:
            max_retries: Maximum retry attempts
            delay: Initial delay between retries in seconds
            error_categorizer: ErrorCategorizer for error classification
        """
        self.max_retries = max_retries
        self.delay = delay
        self.error_categorizer = error_categorizer or ErrorCategorizer()

    def should_retry(self, error_category: str) -> bool:
        """Determine if an error should be retried.

        Args:
            error_category: Error category from ErrorCategorizer

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
            Exception: Original exception if retries exhausted or error not retryable
        """
        attempt = 0

        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                attempt += 1

                # Try to categorize the error
                error_category = "TRANSIENT"
                try:
                    error_category = self.error_categorizer.categorize(exc)
                except (TypeError, AttributeError):
                    # If categorizer fails (not an HttpError), treat as TRANSIENT
                    error_category = "TRANSIENT"

                # Check if we should retry
                if not self.should_retry(error_category) or attempt > self.max_retries:
                    raise

                # Exponential backoff: delay * (2 ** (attempt - 1))
                wait_time = self.delay * (2 ** (attempt - 1))
                time.sleep(wait_time)
