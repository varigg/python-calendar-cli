"""Tests for ServiceFactory component.

Tests Google API service building using composition pattern.
No @patch decorators - all dependencies injected via function arguments.
"""

from unittest.mock import MagicMock, patch


from caltool.service_factory import ServiceFactory


def test_service_factory_build_calendar_service(mock_google_auth):
    """FR-003: ServiceFactory should build a working Calendar service."""
    with patch("caltool.service_factory.discovery.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        factory = ServiceFactory(auth=mock_google_auth)
        result = factory.build_service("calendar", "v3")

        assert result == mock_service
        mock_build.assert_called_once()
        call_args = mock_build.call_args
        assert "calendar" in str(call_args) or call_args[0] == ("calendar", "v3")


def test_service_factory_build_gmail_service(mock_google_auth):
    """FR-003: ServiceFactory should build a working Gmail service."""
    with patch("caltool.service_factory.discovery.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        factory = ServiceFactory(auth=mock_google_auth)
        result = factory.build_service("gmail", "v1")

        assert result == mock_service
        mock_build.assert_called_once()
        call_args = mock_build.call_args
        assert "gmail" in str(call_args) or call_args[0] == ("gmail", "v1")


def test_service_factory_caches_services(mock_google_auth):
    """ServiceFactory should cache built services for performance."""
    with patch("caltool.service_factory.discovery.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        factory = ServiceFactory(auth=mock_google_auth)

        # Build same service twice
        result1 = factory.build_service("calendar", "v3")
        result2 = factory.build_service("calendar", "v3")

        # Both should be the same instance
        assert result1 is result2
        # But build should only be called once (cached)
        assert mock_build.call_count == 1


def test_service_factory_handles_different_apis(mock_google_auth):
    """ServiceFactory should handle different API types separately."""
    with patch("caltool.service_factory.discovery.build") as mock_build:
        mock_calendar = MagicMock()
        mock_gmail = MagicMock()
        mock_build.side_effect = [mock_calendar, mock_gmail]

        factory = ServiceFactory(auth=mock_google_auth)

        calendar_result = factory.build_service("calendar", "v3")
        gmail_result = factory.build_service("gmail", "v1")

        assert calendar_result == mock_calendar
        assert gmail_result == mock_gmail
        assert mock_build.call_count == 2
