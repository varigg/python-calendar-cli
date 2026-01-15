"""Google authentication and credential management module.

This module handles OAuth flow, token management, and credential refresh
for all Google API clients (Calendar, Gmail, etc.). It is the single source
of truth for Google authentication logic.

Key Responsibilities:
- OAuth flow initiation and completion
- Token file management (loading, saving, refreshing)
- Scope detection and change notification
- Credential validation and refresh
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Config
from .errors import CLIError

logger = logging.getLogger(__name__)


class GoogleAuth:
    """Manages Google OAuth authentication and credential lifecycle.
    
    This class is responsible for:
    - Managing the OAuth flow for initial authentication
    - Loading and saving credentials/tokens
    - Detecting and handling scope changes
    - Refreshing expired credentials
    
    All Google API clients (GCalClient, GMailClient, etc.) use this class
    to obtain valid credentials, ensuring consistent auth behavior across the application.
    """
    
    def __init__(self, config: Config):
        """Initialize GoogleAuth with configuration.
        
        Args:
            config: Config object containing CREDENTIALS_FILE, TOKEN_FILE, and SCOPES
            
        Raises:
            CLIError: If required config values are missing
        """
        self.config = config
        self.credentials_file = os.path.expanduser(config.get("CREDENTIALS_FILE") or "")
        self.token_file = os.path.expanduser(config.get("TOKEN_FILE") or "")
        self.scopes = config.get("SCOPES") or []
        
        logger.debug(
            f"GoogleAuth initialized: credentials_file={self.credentials_file}, "
            f"token_file={self.token_file}, scopes={self.scopes}"
        )
        
        if not self.credentials_file:
            raise CLIError("CREDENTIALS_FILE not configured")
        if not self.scopes:
            raise CLIError("SCOPES not configured")
    
    def get_credentials(self) -> Credentials:
        """Get valid Google API credentials.
        
        This method implements the complete credential acquisition flow:
        1. Load existing token if present
        2. Check if token is valid
        3. If expired, attempt refresh
        4. If no token or refresh fails, initiate new OAuth flow
        5. Save token to file
        
        Returns:
            Credentials object ready for use with Google API clients
            
        Raises:
            CLIError: If authentication fails
        """
        logger.debug("Starting credential acquisition flow")
        
        # Step 1: Try to load existing token
        creds = self._load_token_from_file()
        
        # Step 2: Validate and potentially refresh
        if creds:
            logger.debug("Existing credentials found")
            if self._validate_credentials(creds):
                logger.debug("Credentials are valid")
                # Check for scope changes
                stored_scopes = self._load_token_scopes()
                if self._detect_scope_changes(self.scopes, stored_scopes):
                    self._notify_scope_change(self.scopes, stored_scopes)
                    # Refresh with new scopes
                    creds = self._refresh_token(creds)
                return creds
            elif creds.refresh_token:
                logger.debug("Credentials expired but refresh token available, refreshing")
                creds = self._refresh_token(creds)
                self._save_token(creds)
                return creds
        
        # Step 3: No valid token, run OAuth flow
        logger.debug("No valid credentials found, initiating OAuth flow")
        creds = self._run_oauth_flow()
        self._save_token(creds)
        return creds
    
    def _load_token_from_file(self) -> Optional[Credentials]:
        """Load existing token from file.
        
        Returns:
            Credentials object if token file exists, None otherwise
        """
        if not os.path.exists(self.token_file):
            logger.debug(f"Token file does not exist: {self.token_file}")
            return None
        
        try:
            logger.debug(f"Loading token from {self.token_file}")
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            return creds
        except Exception as e:
            logger.warning(f"Failed to load token: {e}")
            return None
    
    def _load_token_scopes(self) -> list[str]:
        """Read existing scopes from token file.
        
        Per research decision #1: Detect scope changes to notify users
        when new permissions are requested.
        
        Returns:
            List of scopes stored in token file, or empty list if file doesn't exist
        """
        if not os.path.exists(self.token_file):
            logger.debug(f"Token file does not exist: {self.token_file}")
            return []
        
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                scopes = token_data.get('scopes', [])
                logger.debug(f"Loaded scopes from token: {scopes}")
                return scopes
        except Exception as e:
            logger.warning(f"Failed to read token scopes: {e}")
            return []
    
    def _detect_scope_changes(self, new_scopes: list[str], stored_scopes: list[str]) -> bool:
        """Compare requested scopes with scopes in existing token.
        
        Per research decision #1: Explicit scope union approach.
        When new scopes are detected, notify user via log message.
        
        Args:
            new_scopes: Scopes requested by current session
            stored_scopes: Scopes from existing token file
            
        Returns:
            True if new scopes detected, False otherwise
        """
        new_set = set(new_scopes)
        stored_set = set(stored_scopes)
        
        has_changes = not new_set.issubset(stored_set)
        logger.debug(f"Scope change detected: {has_changes} (new={new_set}, stored={stored_set})")
        return has_changes
    
    def _notify_scope_change(self, new_scopes: list[str], stored_scopes: list[str]):
        """Notify user that new scopes are being requested.
        
        Per research decision #1: Log a message indicating scope change.
        
        Args:
            new_scopes: New scopes being requested
            stored_scopes: Previously stored scopes
        """
        new_set = set(new_scopes)
        stored_set = set(stored_scopes)
        added_scopes = new_set - stored_set
        
        logger.info(f"Scope change detected. Adding new permissions: {added_scopes}")
        logger.info("You will be prompted to grant these new permissions.")
    
    def _run_oauth_flow(self) -> Credentials:
        """Initiate and complete OAuth flow for new authentication.
        
        This method guides the user through the Google OAuth consent flow
        to grant the application access to the requested scopes.
        
        Returns:
            New Credentials object after user completes OAuth flow
            
        Raises:
            CLIError: If OAuth flow fails
        """
        logger.debug(f"Starting OAuth flow with {self.credentials_file}")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes
            )
            creds = flow.run_local_server(port=0)
            logger.debug("OAuth flow completed successfully")
            return creds
        except FileNotFoundError as e:
            logger.error(f"Credentials file not found: {self.credentials_file}")
            raise CLIError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please download your credentials.json from Google Cloud Console and place it in the configured location."
            )
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            raise CLIError(f"Authentication failed: {e}")
    
    def _refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh expired credentials using refresh token.
        
        Per research decision #2: Single token file approach.
        Credentials are refreshed in-place and token file is updated.
        
        Args:
            credentials: Credentials object to refresh
            
        Returns:
            Refreshed credentials object
            
        Raises:
            CLIError: If refresh fails (e.g., refresh token revoked)
        """
        logger.debug("Refreshing expired credentials")
        try:
            credentials.refresh(Request())
            logger.debug("Credentials refreshed successfully")
            return credentials
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise CLIError(
                f"Token refresh failed. Please run 'caltool config' to re-authenticate."
            )
    
    def _save_token(self, credentials: Credentials):
        """Save credentials to token file.
        
        Args:
            credentials: Credentials object to save
            
        Raises:
            CLIError: If file write fails
        """
        try:
            # Ensure directory exists
            token_dir = os.path.dirname(self.token_file)
            if token_dir:
                os.makedirs(token_dir, exist_ok=True)
            
            logger.debug(f"Saving credentials to {self.token_file}")
            with open(self.token_file, "w") as f:
                f.write(credentials.to_json())
            logger.debug("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            raise CLIError(f"Failed to save authentication token: {e}")
    
    def _validate_credentials(self, credentials: Credentials) -> bool:
        """Check if credentials are valid.
        
        Args:
            credentials: Credentials object to validate
            
        Returns:
            True if credentials are valid, False otherwise
        """
        logger.debug(f"Validating credentials: valid={credentials.valid}, expired={credentials.expired}")
        return credentials.valid and not credentials.expired
