"""Tests for GMailClientV2 - composition-based Gmail client.

Tests Gmail API operations using composition pattern.
No @patch decorators - all dependencies injected via constructor.
"""

from caltool.gmail_client_v2 import GMailClientV2


def test_gmail_client_v2_initialization(mock_service_factory, mock_retry_policy):
    """FR-005: GMailClientV2 should initialize with dependencies via constructor."""
    client = GMailClientV2(service_factory=mock_service_factory, retry_policy=mock_retry_policy)
    assert client._service_factory == mock_service_factory
    assert client._retry_policy == mock_retry_policy


def test_gmail_client_v2_list_messages(mock_google_service):
    """FR-005: GMailClientV2.list_messages() should return message list."""
    mock_google_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ],
        "resultSizeEstimate": 2,
    }

    client = GMailClientV2(service_factory=None, service=mock_google_service)
    messages = client.list_messages(query="is:unread", limit=10)

    assert len(messages) == 2
    assert messages[0]["id"] == "msg1"


def test_gmail_client_v2_get_message(mock_google_service):
    """FR-005: GMailClientV2.get_message() should return message details."""
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

    client = GMailClientV2(service_factory=None, service=mock_google_service)
    message = client.get_message("msg1")

    assert message["id"] == "msg1"
    assert message["snippet"] == "This is a test message"


def test_gmail_client_v2_delete_message(mock_google_service):
    """FR-005: GMailClientV2.delete_message() should delete a message."""
    mock_google_service.users.return_value.messages.return_value.delete.return_value.execute.return_value = None

    client = GMailClientV2(service_factory=None, service=mock_google_service)
    result = client.delete_message("msg1")

    # delete_message returns None on success
    assert result is None
    mock_google_service.users.return_value.messages.return_value.delete.assert_called_once()
