"""Tests for GmailClient - composition-based Gmail client.

Tests Gmail API operations using composition pattern.
No @patch decorators - all dependencies injected via constructor.
"""

from gtool.clients.gmail import GmailClient, extract_subject_from_headers


def test_gmail_client_list_messages(mock_google_service):
    """FR-005: GmailClient.list_messages() should return message list."""
    # Mock list() API call
    mock_google_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ],
        "resultSizeEstimate": 2,
    }

    # Mock get() API calls for each message to fetch headers
    mock_google_service.users.return_value.messages.return_value.get.return_value.execute.side_effect = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "First message preview",
            "payload": {"headers": [{"name": "Subject", "value": "First Subject"}]},
        },
        {
            "id": "msg2",
            "threadId": "thread2",
            "snippet": "Second message preview",
            "payload": {"headers": [{"name": "Subject", "value": "Second Subject"}]},
        },
    ]

    client = GmailClient(service_factory=None, service=mock_google_service)
    messages = client.list_messages(query="is:unread", limit=10)

    assert len(messages) == 2
    assert messages[0]["id"] == "msg1"
    assert messages[0]["subject"] == "First Subject"
    assert messages[1]["subject"] == "Second Subject"


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


# ============================================================================
# Phase 3 Tests: User Story 1 - View Email Titles
# ============================================================================


def test_extract_subject_from_headers_normal(gmail_message_with_subject):
    """T010 [US1]: Extract subject from message with normal subject header."""
    subject = extract_subject_from_headers(gmail_message_with_subject)
    assert subject == "Test Email Subject"


def test_extract_subject_from_headers_blank(gmail_message_no_subject):
    """T011 [US1]: Handle blank/missing subject as (No Subject)."""
    subject = extract_subject_from_headers(gmail_message_no_subject)
    assert subject == "(No Subject)"


def test_extract_subject_from_headers_unicode(gmail_message_unicode_subject):
    """T012 [US1]: Handle Unicode, emoji, and special characters in subject."""
    subject = extract_subject_from_headers(gmail_message_unicode_subject)
    assert subject == "🎉 Test Email with émoji & spëcial chars!"
    # Verify Unicode characters are preserved
    assert "🎉" in subject
    assert "émoji" in subject
    assert "spëcial" in subject


def test_extract_subject_from_headers_long_subject(gmail_message_long_subject):
    """T013 [US1]: Extract long subject without modification (truncation happens at display layer)."""
    subject = extract_subject_from_headers(gmail_message_long_subject)
    # Subject extraction should not truncate - that's the formatter's job
    assert len(subject) == 150
    assert subject == "A" * 150


def test_gmail_list_includes_subjects(mock_google_service, gmail_message_with_subject, gmail_message_unicode_subject):
    """T014 [US1]: Integration test - list_messages returns messages with subjects."""
    # Mock list() API call
    mock_google_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg123", "threadId": "thread456"},
            {"id": "msg999", "threadId": "thread888"},
        ],
        "resultSizeEstimate": 2,
    }

    # Mock get() API calls for headers
    mock_google_service.users.return_value.messages.return_value.get.return_value.execute.side_effect = [
        gmail_message_with_subject,
        gmail_message_unicode_subject,
    ]

    client = GmailClient(service_factory=None, service=mock_google_service)
    messages = client.list_messages(query="", limit=10)

    # Verify subjects are included in response
    assert len(messages) == 2
    assert messages[0]["subject"] == "Test Email Subject"
    assert messages[1]["subject"] == "🎉 Test Email with émoji & spëcial chars!"

    # Verify other fields are preserved
    assert messages[0]["id"] == "msg123"
    assert messages[1]["id"] == "msg999"
