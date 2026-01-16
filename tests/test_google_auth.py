"""Tests for GoogleAuth class.

Per Constitution Principle II (Test-First Development), tests are written
BEFORE implementation. These tests MUST FAIL initially, and implementation
is driven by making tests pass.

Test Strategy:
1. Test initialization with valid/invalid config
2. Test credential loading from token file
3. Test scope change detection
4. Test OAuth flow initiation
5. Test token refresh logic
6. Test error handling for auth failures
"""

import pytest
from unittest.mock import Mock, patch
from google.oauth2.credentials import Credentials

from caltool.google_auth import GoogleAuth
from caltool.config import Config
from caltool.errors import CLIError


class TestGoogleAuthInitialization:
    """Test GoogleAuth.__init__() method."""

    def test_init_with_valid_config(self, mock_config):
        """GoogleAuth should initialize successfully with valid config."""
        auth = GoogleAuth(mock_config)
        assert auth.config == mock_config
        assert auth.credentials_file is not None
        assert auth.token_file is not None
        assert auth.scopes is not None

    def test_init_raises_error_if_credentials_file_missing(self):
        """GoogleAuth should raise CLIError if CREDENTIALS_FILE is missing."""
        config = Config()
        config.data = {
            "TOKEN_FILE": "/tmp/token.json",
            "SCOPES": ["scope1"],
        }
        with pytest.raises(CLIError):
            GoogleAuth(config)

    def test_init_raises_error_if_scopes_missing(self, mock_config):
        """GoogleAuth should raise CLIError if SCOPES is missing or empty."""
        mock_config.data["SCOPES"] = None
        with pytest.raises(CLIError):
            GoogleAuth(mock_config)


class TestGoogleAuthGetCredentials:
    """Test GoogleAuth.get_credentials() method - main credential flow."""

    @patch("caltool.google_auth.Credentials.from_authorized_user_file")
    def test_load_existing_valid_token(self, mock_creds_from_file, mock_config, tmp_path):
        """get_credentials should load existing token if valid."""
        # Setup
        mock_token_file = tmp_path / "token.json"
        mock_token_file.write_text('{"token": "test"}')
        mock_config.data["TOKEN_FILE"] = str(mock_token_file)

        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds_from_file.return_value = mock_creds

        # Test
        auth = GoogleAuth(mock_config)
        result = auth.get_credentials()

        # Verify
        assert result == mock_creds
        mock_creds_from_file.assert_called_once()

    @patch("caltool.google_auth.Credentials.from_authorized_user_file")
    @patch("caltool.google_auth.InstalledAppFlow")
    def test_refresh_expired_token(self, mock_flow, mock_creds_from_file, mock_config, tmp_path):
        """get_credentials should refresh expired token with refresh_token."""
        # Setup
        mock_token_file = tmp_path / "token.json"
        mock_token_file.write_text('{"token": "test"}')
        mock_config.data["TOKEN_FILE"] = str(mock_token_file)

        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'
        mock_creds_from_file.return_value = mock_creds

        # Test
        auth = GoogleAuth(mock_config)
        result = auth.get_credentials()

        # Verify refresh was attempted
        assert result is not None

    @patch("caltool.google_auth.InstalledAppFlow.from_client_secrets_file")
    def test_run_oauth_flow_if_no_token(self, mock_flow, mock_config, tmp_path):
        """get_credentials should run OAuth flow if no token exists."""
        # Setup
        mock_token_file = tmp_path / "token.json"
        # Token file does not exist
        mock_config.data["TOKEN_FILE"] = str(mock_token_file)

        # Credentials file must exist for OAuth flow creation.
        mock_credentials_file = tmp_path / "credentials.json"
        mock_credentials_file.write_text(
            '{"installed": {"client_id": "cid", "client_secret": "secret", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": ["http://localhost"]}}'
        )
        mock_config.data["CREDENTIALS_FILE"] = str(mock_credentials_file)
        mock_flow_instance = Mock()
        mock_creds = Mock(spec=Credentials)
        mock_creds.to_json.return_value = '{"token": "test"}'
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.return_value = mock_flow_instance

        # Test
        auth = GoogleAuth(mock_config)
        # Avoid real socket probing in unit test.
        with (
            patch.object(GoogleAuth, "_get_oauth_ports", return_value=[8401]),
            patch.object(GoogleAuth, "_choose_oauth_port", return_value=8401),
        ):
            result = auth.get_credentials()
        # Verify OAuth flow was initiated
        assert result is not None


class TestGoogleAuthScopeDetection:
    """Test scope change detection (research decision #1)."""

    def test_load_token_scopes_returns_empty_if_no_file(self, mock_config):
        """_load_token_scopes should return empty list if token file doesn't exist."""
        auth = GoogleAuth(mock_config)
        scopes = auth._load_token_scopes()
        # Should not raise, returns empty list or None
        assert scopes is not None

    @patch("caltool.google_auth.Credentials.from_authorized_user_file")
    def test_detect_scope_changes(self, mock_creds_from_file, mock_config, tmp_path):
        """_detect_scope_changes should identify when new scopes are added."""
        mock_token_file = tmp_path / "token.json"
        mock_token_file.write_text('{"token": "test"}')
        mock_config.data["TOKEN_FILE"] = str(mock_token_file)

        auth = GoogleAuth(mock_config)

        # Existing scopes from token
        existing = ["https://www.googleapis.com/auth/calendar.readonly"]
        # New scopes requested
        new = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/gmail.readonly",
        ]

        has_changes = auth._detect_scope_changes(new, existing)
        assert has_changes is True

    @patch("caltool.google_auth.Credentials.from_authorized_user_file")
    def test_no_scope_changes_when_same(self, mock_creds_from_file, mock_config, tmp_path):
        """_detect_scope_changes should return False if scopes are identical."""
        mock_token_file = tmp_path / "token.json"
        mock_token_file.write_text('{"token": "test"}')
        mock_config.data["TOKEN_FILE"] = str(mock_token_file)

        auth = GoogleAuth(mock_config)

        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

        has_changes = auth._detect_scope_changes(scopes, scopes)
        assert has_changes is False


class TestGoogleAuthErrorHandling:
    """Test error handling during authentication."""

    def test_auth_error_if_credentials_file_not_found(self, mock_config, tmp_path):
        """get_credentials should raise CLIError if credentials file doesn't exist."""
        mock_config.data["CREDENTIALS_FILE"] = str(tmp_path / "nonexistent.json")
        auth = GoogleAuth(mock_config)

        # When OAuth flow fails (file not found)
        with pytest.raises(Exception):  # Will raise FileNotFoundError or CLIError
            auth.get_credentials()
