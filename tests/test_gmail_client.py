"""Tests for GmailClient - composition-based Gmail client.

Tests Gmail API operations using composition pattern.
No @patch decorators - all dependencies injected via constructor.
"""

from gtool.clients.gmail import GmailClient


def test_gmail_client_initialization(mock_service_factory, mock_retry_policy):
    """FR-005: GmailClient should initialize with dependencies via constructor."""
    client = GmailClient(service_factory=mock_service_factory, retry_policy=mock_retry_policy)
    assert client._service_factory == mock_service_factory
    assert client._retry_policy == mock_retry_policy


def test_gmail_client_list_messages(mock_google_service):
    """FR-005: GmailClient.list_messages() should return message list."""
    mock_google_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ],
        "resultSizeEstimate": 2,
    }

    client = GmailClient(service_factory=None, service=mock_google_service)
    messages = client.list_messages(query="is:unread", limit=10)

    assert len(messages) == 2
    assert messages[0]["id"] == "msg1"


def test_gmail_client_get_message(mock_google_service):
    """FR-005: GmailClient.get_message() should return message details."""
    mock_google_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "msg1",
        "threadId": "thread1",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "This is a test message",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"},
            ]
        },
    }

    client = GmailClient(service_factory=None, service=mock_google_service)
    message = client.get_message("msg1")

    assert message["id"] == "msg1"
    assert message["snippet"] == "This is a test message"


def test_gmail_client_delete_message(mock_google_service):
    """FR-005: GmailClient.delete_message() should delete a message."""
    mock_google_service.users.return_value.messages.return_value.delete.return_value.execute.return_value = None

    client = GmailClient(service_factory=None, service=mock_google_service)
    result = client.delete_message("msg1")

    # delete_message returns None on success
    assert result is None
    mock_google_service.users.return_value.messages.return_value.delete.assert_called_once()
