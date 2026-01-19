"""GmailClient - composition-based Gmail API client.

Refactored to use composition pattern with dependency injection.
Provides Gmail operations: list messages, get message, delete message, etc.
"""

from typing import Any, List, Optional

from gtool.infrastructure.retry import RetryPolicy
from gtool.infrastructure.service_factory import ServiceFactory


def extract_subject_from_headers(message: dict) -> str:
    """Extract subject line from Gmail message headers.

    Extracts the Subject header from a Gmail message payload. If the subject
    is missing or blank, returns "(No Subject)" as per FR-006.

    Args:
        message: Gmail message dict with 'payload' containing 'headers'

    Returns:
        Subject string, or "(No Subject)" if missing/blank

    Raises:
        KeyError: If message structure is invalid (missing 'payload')

    Example:
        >>> msg = {
        ...     "id": "123",
        ...     "payload": {
        ...         "headers": [
        ...             {"name": "Subject", "value": "Hello World"},
        ...             {"name": "From", "value": "user@example.com"}
        ...         ]
        ...     }
        ... }
        >>> extract_subject_from_headers(msg)
        'Hello World'

        >>> msg_no_subject = {
        ...     "id": "456",
        ...     "payload": {
        ...         "headers": [{"name": "From", "value": "user@example.com"}]
        ...     }
        ... }
        >>> extract_subject_from_headers(msg_no_subject)
        '(No Subject)'
    """
    # Get headers from message payload
    headers = message.get("payload", {}).get("headers", [])

    # Find Subject header
    for header in headers:
        if header.get("name", "").lower() == "subject":
            subject = header.get("value", "").strip()
            # Return "(No Subject)" if blank (FR-006)
            return subject if subject else "(No Subject)"

    # No Subject header found
    return "(No Subject)"


class GmailClient:
    """Gmail API client using composition pattern.

    This client manages Gmail API operations using composition for dependency
    injection instead of inheritance. Dependencies include ServiceFactory
    for building API services and RetryPolicy for handling transient errors.

    Args:
        service_factory: ServiceFactory instance for building API services.
        retry_policy: Optional RetryPolicy for automatic retry handling.
        service: Optional pre-built Gmail API service instance.

    Attributes:
        _service_factory: ServiceFactory for building services.
        _retry_policy: RetryPolicy for retry handling.
        _service: Gmail API service instance.
    """

    def __init__(
        self,
        service_factory: Optional[ServiceFactory] = None,
        retry_policy: Optional[RetryPolicy] = None,
        service: Optional[Any] = None,
    ) -> None:
        """Initialize the GmailClient with composition dependencies.

        Args:
            service_factory: ServiceFactory to build Gmail API services.
            retry_policy: Optional RetryPolicy for automatic retries.
            service: Optional pre-built service (for testing or injection).
        """
        self._service_factory = service_factory
        self._retry_policy = retry_policy
        self._service = service

        # Lazy-load service if not provided
        if self._service is None and self._service_factory is not None:
            self._service = self._service_factory.build_service("gmail", "v1")

    def list_messages(self, query: str = "", limit: int = 10, max_results: int = None) -> List[dict]:
        """List Gmail messages matching a query.

        Returns a list of message metadata matching the specified query.
        Each message includes id, threadId, snippet, and subject (extracted from headers).

        Common query examples:
        - "is:unread" - unread messages
        - "from:user@example.com" - messages from specific sender
        - "has:attachment" - messages with attachments

        Args:
            query: Gmail search query (default: all messages).
            limit: Maximum number of messages to return (new parameter).
            max_results: Maximum number of messages to return (old parameter, for compatibility).

        Returns:
            List of message dictionaries with id, threadId, snippet, and subject.

        Raises:
            CLIError: If Gmail scope missing, authentication fails, or API call fails.

        Example:
            >>> client = GmailClient(service_factory=factory)
            >>> unread = client.list_messages("is:unread", limit=20)
            >>> for msg in unread:
            ...     print(f"{msg['subject']}: {msg['snippet']}")
        """
        # Support both old (max_results) and new (limit) parameter names
        actual_limit = max_results if max_results is not None else limit

        def fetch_messages():
            return self._service.users().messages().list(userId="me", q=query, maxResults=actual_limit).execute()

        if self._retry_policy is not None:
            result = self._retry_policy.execute(fetch_messages)
        else:
            result = fetch_messages()

        messages = result.get("messages", [])

        # Enrich messages with subject lines (T006 [US1])
        # Fetch full message metadata to get headers including subject
        enriched_messages = []
        for msg in messages:
            msg_id = msg.get("id")
            if msg_id:
                # Fetch message with metadata format to get headers
                def fetch_full_message():
                    return (
                        self._service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject", "From", "Date"])
                        .execute()
                    )

                if self._retry_policy is not None:
                    full_msg = self._retry_policy.execute(fetch_full_message)
                else:
                    full_msg = fetch_full_message()

                # Extract subject from headers
                subject = extract_subject_from_headers(full_msg)

                # Merge subject into message dict
                enriched_msg = {**msg, "subject": subject}

                # Also include snippet if available from full message
                if "snippet" in full_msg:
                    enriched_msg["snippet"] = full_msg["snippet"]

                enriched_messages.append(enriched_msg)
            else:
                # Fallback if message has no ID
                enriched_messages.append({**msg, "subject": "(No Subject)"})

        return enriched_messages

    def get_message(self, message_id: str, format_: str = "full") -> dict:
        """Get full message details including headers and body.

        Args:
            message_id: Gmail message ID.
            format_: Message format ("full", "minimal", "raw", "metadata").

        Returns:
            Message dictionary with full details (headers, body, payload, etc).

        Raises:
            CLIError: If Gmail scope missing, message not found, or API call fails.
        """

        def fetch_message():
            return self._service.users().messages().get(userId="me", id=message_id, format=format_).execute()

        if self._retry_policy is not None:
            return self._retry_policy.execute(fetch_message)
        return fetch_message()

    def delete_message(self, message_id: str) -> None:
        """Delete a message permanently.

        Args:
            message_id: Gmail message ID to delete.

        Returns:
            None on success.

        Raises:
            CLIError: If Gmail scope missing, message not found, or API call fails.
        """

        def delete_msg():
            self._service.users().messages().delete(userId="me", id=message_id).execute()

        if self._retry_policy is not None:
            self._retry_policy.execute(delete_msg)
        else:
            delete_msg()
        return None
