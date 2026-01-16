"""Abstract base class for Google API clients.

This module provides common patterns and functionality shared by all Google API
clients (Calendar, Gmail, Drive, etc.). It establishes consistent error handling,
retry logic, and service building patterns across the application.

Key Responsibilities:
- Building Google API service instances
- Categorizing API errors (AUTH, QUOTA, TRANSIENT, CLIENT)
- Implementing smart retry logic
- Providing error handling utilities
"""

import logging
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Config
from .errors import CLIError
from .google_auth import GoogleAuth

logger = logging.getLogger(__name__)


class GoogleAPIClient(ABC):
    """Abstract base class for Google API clients.

    This class provides:
    - Common initialization pattern (config, service building)
    - Error categorization and handling
    - Retry decorator with smart logic
    - Service building with proper credential management

    All Google API clients (GCalClient, GMailClient, etc.) should inherit
    from this class to ensure consistent behavior across the application.
    """

    # Subclasses must define these
    API_NAME: str = None  # e.g., "calendar", "gmail", "drive"
    API_VERSION: str = None  # e.g., "v3", "v1"

    @staticmethod
    def retry(max_retries: int = 3, delay: int = 2, allowed_exceptions: tuple = (HttpError,)):
        """Static decorator to retry a function with smart logic.

        Per research decision #3: Smart retry logic based on error category.
        - Do NOT retry AUTH errors (user action required)
        - Do NOT retry CLIENT errors (code is wrong)
        - DO retry QUOTA and TRANSIENT errors (temporary issues)

        Args:
            max_retries: Maximum number of attempts
            delay: Delay between retries in seconds
            allowed_exceptions: Tuple of exceptions to catch and retry

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(self, *args, **kwargs)
                    except HttpError as e:
                        category = self.categorize_error(e)

                        # Do not retry AUTH or CLIENT errors
                        if category in ("AUTH", "CLIENT"):
                            logger.warning(f"Non-retryable error ({category}): {e}")
                            self.handle_api_error(e)  # Convert to CLIError with friendly message
                            return  # Unreachable, but satisfies type checker

                        # Retry QUOTA and TRANSIENT errors
                        if attempt == max_retries - 1:
                            logger.error(f"All {max_retries} attempts failed")
                            self.handle_api_error(e)  # Convert to CLIError after exhausting retries
                            return  # Unreachable, but satisfies type checker

                        logger.warning(f"Attempt {attempt + 1} failed ({category}), retrying in {delay}s...")
                        time.sleep(delay)
                    except allowed_exceptions as e:
                        if attempt == max_retries - 1:
                            logger.error(f"All {max_retries} attempts failed")
                            raise

                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                        time.sleep(delay)

            return wrapper

        return decorator

    def __init__(self, config: Config, api_name: str, api_version: str, service: Optional[Any] = None):
        """Initialize Google API client.

        Args:
            config: Config object with credentials and settings
            api_name: Google API name (e.g., "calendar", "gmail")
            api_version: API version (e.g., "v3", "v1")
            service: Optional pre-built service object (for testing/injection)

        Raises:
            CLIError: If authentication fails
        """
        self.config = config
        self.api_name = api_name
        self.api_version = api_version

        # Validate config before attempting to build service
        self._validate_config()

        # Build or use injected service
        self.service = service or self._build_service(api_name, api_version)

        logger.debug(f"{self.__class__.__name__} initialized with {api_name}/{api_version}")

    def _build_service(self, api_name: str, api_version: str) -> Any:
        """Build and return a Google API service object.

        Uses GoogleAuth to obtain valid credentials, then builds the
        service using the Google API discovery service.

        Args:
            api_name: Google API name (e.g., "calendar", "gmail")
            api_version: API version (e.g., "v3", "v1")

        Returns:
            Service object ready for API calls

        Raises:
            CLIError: If service building fails
        """
        logger.debug(f"Building service for {api_name}/{api_version}")
        try:
            auth = GoogleAuth(self.config)
            credentials = auth.get_credentials()
            service = build(api_name, api_version, credentials=credentials)
            logger.debug(f"Service built successfully for {api_name}/{api_version}")
            return service
        except CLIError:
            raise
        except Exception as e:
            logger.error(f"Failed to build service: {e}")
            raise CLIError(f"Failed to connect to Google API: {e}")

    @staticmethod
    def categorize_error(error: HttpError) -> str:
        """Categorize an HttpError for smart handling.

        Per research decision #3: Categorized error handling.
        Maps HTTP error codes to business categories:
        - AUTH: Authentication/authorization failures (401, 403 scope issues)
        - QUOTA: Rate limit/quota exceeded (429, 403 quota)
        - TRANSIENT: Temporary network failures (5xx)
        - CLIENT: Client errors (4xx excluding above)

        Args:
            error: HttpError from Google API

        Returns:
            One of: "AUTH", "QUOTA", "TRANSIENT", "CLIENT"
        """
        status_code = error.resp.status
        content = error.content.decode("utf-8") if isinstance(error.content, bytes) else error.content

        # AUTH errors: 401, or 403 with permission/scope issues
        if status_code == 401:
            return "AUTH"
        elif status_code == 403 and ("permission" in content.lower() or "scope" in content.lower()):
            return "AUTH"

        # QUOTA errors: 429, or 403 with quota issues
        elif status_code == 429:
            return "QUOTA"
        elif status_code == 403 and "quota" in content.lower():
            return "QUOTA"

        # TRANSIENT errors: 5xx server errors
        elif 500 <= status_code < 600:
            return "TRANSIENT"

        # CLIENT errors: everything else (4xx)
        else:
            return "CLIENT"

    def handle_api_error(self, error: HttpError) -> None:
        """Handle an API error with categorized, user-friendly messaging.

        Categorizes the error, logs appropriately, and raises a CLIError
        with a user-friendly message (no stack traces).

        Args:
            error: HttpError from Google API

        Raises:
            CLIError: With user-friendly message based on error category
        """
        category = self.categorize_error(error)
        logger.error(f"API error ({category}): {error}")

        if category == "AUTH":
            raise CLIError("Authentication failed. Please run 'caltool config' to re-authenticate.")
        elif category == "QUOTA":
            raise CLIError("Rate limit exceeded. Please wait a few moments and try again.")
        elif category == "TRANSIENT":
            raise CLIError("Temporary connection error. Please try again in a moment.")
        else:  # CLIENT
            raise CLIError("API request failed. Please check your request and try again.")

    @abstractmethod
    def _validate_config(self):
        """Validate that required config values are present.

        Subclasses should override to check for any client-specific config.

        Raises:
            CLIError: If required config is missing
        """
        # Base implementation checks core config
        if not self.config.get("CREDENTIALS_FILE"):
            raise CLIError("CREDENTIALS_FILE not configured")
        if not self.config.get("TOKEN_FILE"):
            raise CLIError("TOKEN_FILE not configured")
        if not self.config.get("SCOPES"):
            raise CLIError("SCOPES not configured")
