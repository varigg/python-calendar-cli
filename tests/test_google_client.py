"""Tests for GoogleAPIClient base class.

Per Constitution Principle II (Test-First Development), tests are written
BEFORE implementation. These tests MUST FAIL initially, and implementation
is driven by making tests pass.

Test Strategy:
1. Test initialization with config and service building
2. Test service building with GoogleAuth
3. Test error categorization (AUTH, QUOTA, TRANSIENT, CLIENT)
4. Test error handling with user-friendly messages
5. Test retry logic with smart category-based decisions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
import httplib2

from caltool.google_client import GoogleAPIClient
from caltool.config import Config
from caltool.errors import CLIError


class ConcreteGoogleAPIClient(GoogleAPIClient):
    """Concrete implementation for testing abstract base class."""
    
    API_NAME = "test"
    API_VERSION = "v1"
    
    def _validate_config(self):
        """No-op for testing."""
        pass


class TestGoogleAPIClientInitialization:
    """Test GoogleAPIClient.__init__() method."""
    
    @patch('caltool.google_client.GoogleAuth')
    @patch('caltool.google_client.build')
    def test_init_builds_service_from_config(self, mock_build, mock_google_auth, mock_config):
        """GoogleAPIClient should build service from GoogleAuth."""
        # Mock GoogleAuth
        mock_auth = Mock()
        mock_creds = Mock()
        mock_auth.get_credentials.return_value = mock_creds
        mock_google_auth.return_value = mock_auth
        
        # Mock build
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1")
        assert client.config == mock_config
        assert client.service == mock_service
    
    def test_init_accepts_injected_service(self, mock_config):
        """GoogleAPIClient should accept pre-built service for testing."""
        mock_service = Mock()
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1", service=mock_service)
        assert client.service == mock_service


class TestGoogleAPIClientServiceBuilding:
    """Test GoogleAPIClient._build_service() method."""
    
    @patch('caltool.google_client.build')
    @patch('caltool.google_client.GoogleAuth')
    def test_build_service_uses_google_auth(self, mock_google_auth, mock_build, mock_config):
        """_build_service should use GoogleAuth to get credentials."""
        mock_auth = Mock()
        mock_creds = Mock()
        mock_auth.get_credentials.return_value = mock_creds
        mock_google_auth.return_value = mock_auth
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        client = ConcreteGoogleAPIClient(mock_config, "calendar", "v3")
        service = client._build_service("calendar", "v3")
        
        assert service == mock_service
        mock_build.assert_called()


class TestGoogleAPIClientErrorCategorization:
    """Test GoogleAPIClient.categorize_error() method."""
    
    def test_categorize_401_as_auth_error(self):
        """401 Unauthorized should be categorized as AUTH."""
        resp = httplib2.Response({"status": "401"})
        content = b'{"error": {"code": 401, "message": "Invalid credentials"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "AUTH"
    
    def test_categorize_403_scope_as_auth_error(self):
        """403 Forbidden with scope issues should be categorized as AUTH."""
        resp = httplib2.Response({"status": "403"})
        content = b'{"error": {"code": 403, "message": "Insufficient permissions"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "AUTH"
    
    def test_categorize_429_as_quota_error(self):
        """429 Too Many Requests should be categorized as QUOTA."""
        resp = httplib2.Response({"status": "429"})
        content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "QUOTA"
    
    def test_categorize_403_quota_as_quota_error(self):
        """403 with quota message should be categorized as QUOTA."""
        resp = httplib2.Response({"status": "403"})
        content = b'{"error": {"code": 403, "message": "Quota exceeded"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "QUOTA"
    
    def test_categorize_500_as_transient_error(self):
        """500 Internal Server Error should be categorized as TRANSIENT."""
        resp = httplib2.Response({"status": "500"})
        content = b'{"error": {"code": 500, "message": "Internal server error"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "TRANSIENT"
    
    def test_categorize_404_as_client_error(self):
        """404 Not Found should be categorized as CLIENT."""
        resp = httplib2.Response({"status": "404"})
        content = b'{"error": {"code": 404, "message": "Not found"}}'
        error = HttpError(resp, content)
        
        category = ConcreteGoogleAPIClient.categorize_error(error)
        assert category == "CLIENT"


class TestGoogleAPIClientErrorHandling:
    """Test GoogleAPIClient.handle_api_error() method."""
    
    def test_handle_auth_error_raises_cli_error(self, mock_config):
        """handle_api_error should raise CLIError for AUTH errors."""
        mock_service = Mock()
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1", service=mock_service)
        
        resp = httplib2.Response({"status": "401"})
        content = b'{"error": {"code": 401, "message": "Invalid credentials"}}'
        error = HttpError(resp, content)
        
        with pytest.raises(CLIError):
            client.handle_api_error(error)
    
    def test_handle_quota_error_raises_cli_error(self, mock_config):
        """handle_api_error should raise CLIError for QUOTA errors."""
        mock_service = Mock()
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1", service=mock_service)
        
        resp = httplib2.Response({"status": "429"})
        content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
        error = HttpError(resp, content)
        
        with pytest.raises(CLIError):
            client.handle_api_error(error)


class TestGoogleAPIClientRetryLogic:
    """Test GoogleAPIClient.retry_on_exception() method - research decision #3."""
    
    def test_retry_does_not_retry_auth_errors(self, mock_config):
        """Retry logic should NOT retry AUTH errors (user action required)."""
        mock_service = Mock()
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1", service=mock_service)
        
        resp = httplib2.Response({"status": "401"})
        content = b'{"error": {"code": 401, "message": "Invalid credentials"}}'
        error = HttpError(resp, content)
        
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise error
        
        wrapped = client.retry_on_exception(failing_func)
        
        with pytest.raises(HttpError):
            wrapped()
        
        # Should fail immediately without retries
        assert call_count == 1
    
    @patch('caltool.google_client.time.sleep')
    def test_retry_does_retry_quota_errors(self, mock_sleep, mock_config):
        """Retry logic SHOULD retry QUOTA errors (temporary)."""
        mock_service = Mock()
        client = ConcreteGoogleAPIClient(mock_config, "test", "v1", service=mock_service)
        
        resp = httplib2.Response({"status": "429"})
        content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
        error = HttpError(resp, content)
        
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise error
            return "success"
        
        wrapped = client.retry_on_exception(failing_func, max_retries=3, delay=0)
        result = wrapped()
        
        # Should retry and eventually succeed
        assert result == "success"
        assert call_count >= 2

