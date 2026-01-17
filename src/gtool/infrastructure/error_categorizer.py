"""ErrorCategorizer component for composition-based architecture.

Categorizes Google API errors into actionable categories for retry policy.
Separates error handling logic from API client implementation.
"""

from googleapiclient.errors import HttpError


class ErrorCategorizer:
    """Categorizes HTTP errors from Google API calls.

    Maps HTTP status codes to retry-relevant categories:
    - AUTH: Authentication/authorization errors (401, 403 with auth scope)
    - QUOTA: Rate limiting or quota errors (429, 403 with quota)
    - TRANSIENT: Temporary server errors (5xx)
    - CLIENT: Client errors that won't resolve with retries (4xx except above)

    Example:
        >>> categorizer = ErrorCategorizer()
        >>> # With actual HttpError from googleapiclient
        >>> category = categorizer.categorize(http_error)
        >>> print(category)  # "AUTH" or "QUOTA" or "TRANSIENT" or "CLIENT"
    """

    def categorize(self, error: HttpError) -> str:
        """Categorize an HTTP error from Google API.

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
