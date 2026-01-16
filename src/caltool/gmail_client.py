"""Gmail API client.

This module provides GMailClient for interacting with the Gmail API.
It inherits from GoogleAPIClient to leverage shared patterns for authentication,
error handling, and retry logic.
"""

import json
import logging
from typing import Any, Optional

from googleapiclient.errors import HttpError

from .google_client import GoogleAPIClient
from .errors import CLIError

logger = logging.getLogger(__name__)


class GMailClient(GoogleAPIClient):
    """Client for Gmail API operations.

    Inherits common authentication, error handling, and retry patterns from
    GoogleAPIClient. Provides Gmail-specific methods for listing and retrieving
    messages, managing labels, and more.
    """

    API_NAME = "gmail"
    API_VERSION = "v1"

    def __init__(self, config, service: Optional[Any] = None):
        """Initialize GMailClient for Gmail API.

        Args:
            config: Config object with credentials and settings
            service: Optional pre-built service object (for testing)
        """
        super().__init__(config, self.API_NAME, self.API_VERSION, service)

    def _validate_config(self):
        """Validate Gmail-specific configuration.

        Ensures that Gmail scope is configured when Gmail client is used.
        """
        # Base validation covers CREDENTIALS_FILE, TOKEN_FILE, SCOPES
        super()._validate_config()

        # Verify Gmail scope is present

        if not self._has_gmail_scope():
            raise CLIError(
                "Gmail scope not configured.\n\n"
                "To use Gmail features:\n"
                "1. Run 'caltool config' to add Gmail scopes to your configuration\n"
                "2. Ensure the Gmail API is enabled in Google Cloud Console:\n"
                "   https://console.cloud.google.com/apis/library/gmail.googleapis.com\n"
                "3. Add Gmail scopes to your OAuth consent screen:\n"
                "   - Go to https://console.cloud.google.com/apis/credentials\n"
                "   - Navigate to 'OAuth consent screen'\n"
                "   - Click 'Edit App' → 'Scopes' → Add:\n"
                "     • https://www.googleapis.com/auth/gmail.readonly (view messages)\n"
                "     • https://www.googleapis.com/auth/gmail.modify (delete messages)\n"
                "4. Delete token.json and re-authenticate after configuration"
            )

    def _has_gmail_scope(self) -> bool:
        """Check if Gmail scope is configured.

        Returns:
            True if any Gmail scope is in the configured scopes
        """
        scopes = self.config.get("SCOPES", [])
        return any("gmail" in scope.lower() for scope in scopes)

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def list_messages(self, query: str = "", max_results: int = 10) -> list:
        """List messages matching the query.

        Args:
            query: Gmail query string (e.g., "is:unread", "from:user@example.com")
            max_results: Maximum number of results to return

        Returns:
            List of message objects from Gmail API

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Listing messages with query: {query}")
        results = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        logger.info(
            json.dumps({"component": "GMailClient", "event": "list_messages", "query": query, "count": len(messages)})
        )
        return messages

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_message(self, message_id: str, format_: str = "full") -> dict:
        """Get a specific message by ID.

        Args:
            message_id: The ID of the message to retrieve
            format_: Format of the message ('full', 'minimal', 'raw', 'metadata')

        Returns:
            Message object from Gmail API with details

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Retrieving message {message_id}")
        message = self.service.users().messages().get(userId="me", id=message_id, format=format_).execute()
        logger.info(
            json.dumps(
                {"component": "GMailClient", "event": "get_message", "message_id": message_id, "format": format_}
            )
        )
        return message

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def delete_message(self, message_id: str) -> None:
        """Delete a specific message by ID.

        Args:
            message_id: The ID of the message to delete

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Deleting message {message_id}")
        self.service.users().messages().delete(userId="me", id=message_id).execute()
        logger.info(
            json.dumps(
                {"component": "GMailClient", "event": "delete_message", "message_id": message_id, "status": "success"}
            )
        )
