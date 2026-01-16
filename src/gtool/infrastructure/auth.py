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

import json
import logging
import os
import socket
from typing import Optional, cast

import click
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from gtool.config.settings import Config
from gtool.cli.errors import CLIError

logger = logging.getLogger(__name__)


class GoogleAuth:
    """Manages Google OAuth authentication and credential lifecycle.

    This class is responsible for:
    - Managing the OAuth flow for initial authentication
    - Loading and saving credentials/tokens
    - Detecting and handling scope changes
    - Refreshing expired credentials

    All Google API clients (CalendarClient, GmailClient, etc.) use this class
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
        self._oauth_client_type: Optional[str] = None

        raw_credentials_file = config.get("CREDENTIALS_FILE")
        if not raw_credentials_file or not isinstance(raw_credentials_file, str):
            raise CLIError("CREDENTIALS_FILE not configured")
        self.credentials_file = os.path.expanduser(raw_credentials_file)

        raw_token_file = config.get("TOKEN_FILE")
        if not raw_token_file or not isinstance(raw_token_file, str):
            raise CLIError("TOKEN_FILE not configured")
        self.token_file = os.path.expanduser(raw_token_file)

        raw_scopes = config.get("SCOPES")
        if raw_scopes is None:
            self.scopes = []
        elif isinstance(raw_scopes, list):
            self.scopes = [str(s) for s in raw_scopes]
        elif isinstance(raw_scopes, str):
            # Allow accidental string config; treat as comma-separated.
            self.scopes = [s.strip() for s in raw_scopes.split(",") if s.strip()]
        else:
            self.scopes = []

        logger.debug(
            json.dumps(
                {
                    "component": "GoogleAuth",
                    "event": "init",
                    "credentials_file": self.credentials_file,
                    "token_file": self.token_file,
                    "scopes": self.scopes,
                }
            )
        )

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
        logger.debug(json.dumps({"component": "GoogleAuth", "event": "get_credentials:start"}))

        # Step 1: Try to load existing token
        creds = self._load_token_from_file()

        # Step 2: Validate and potentially refresh
        if creds:
            logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:existing"}))
            if self._validate_credentials(creds):
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:valid"}))
                # Check for scope changes
                stored_scopes = self._load_token_scopes()
                if self._detect_scope_changes(self.scopes, stored_scopes):
                    self._notify_scope_change(self.scopes, stored_scopes)
                    # Refresh with new scopes
                    creds = self._refresh_token(creds)
                return creds
            elif creds.refresh_token:
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:expired_refreshing"}))
                creds = self._refresh_token(creds)
                self._save_token(creds)
                return creds

        # Step 3: No valid token, run OAuth flow
        logger.debug(json.dumps({"component": "GoogleAuth", "event": "oauth:start"}))
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
            logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:load", "path": self.token_file}))
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            return creds
        except Exception as e:
            logger.warning(json.dumps({"component": "GoogleAuth", "event": "token:load_failed", "error": str(e)}))
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
            with open(self.token_file, "r") as f:
                token_data = json.load(f)
                scopes = token_data.get("scopes", [])
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:scopes_loaded", "scopes": scopes}))
                return scopes
        except Exception as e:
            logger.warning(json.dumps({"component": "GoogleAuth", "event": "token:scopes_failed", "error": str(e)}))
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
        logger.debug(
            json.dumps(
                {
                    "component": "GoogleAuth",
                    "event": "scopes:compare",
                    "has_changes": has_changes,
                    "new": sorted(list(new_set)),
                    "stored": sorted(list(stored_set)),
                }
            )
        )
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

        logger.info(
            json.dumps(
                {
                    "component": "GoogleAuth",
                    "event": "scopes:change_detected",
                    "added_scopes": sorted(list(added_scopes)),
                    "message": "You will be prompted to grant these new permissions.",
                }
            )
        )

    def _run_oauth_flow(self) -> Credentials:
        """Initiate and complete OAuth flow for new authentication.

        This method guides the user through the Google OAuth consent flow
        to grant the application access to the requested scopes.

        Returns:
            New Credentials object after user completes OAuth flow

        Raises:
            CLIError: If OAuth flow fails
        """
        logger.debug(
            json.dumps({"component": "GoogleAuth", "event": "oauth:init", "credentials_file": self.credentials_file})
        )
        attempted_redirect_uri: Optional[str] = None

        try:
            flow = self._create_oauth_flow()

            # Allow forcing console-based OAuth to avoid callback hangs: set GTOOL_OAUTH_CONSOLE=1
            force_console = os.environ.get("GTOOL_OAUTH_CONSOLE", "").lower() in {"1", "true", "yes", "on"}
            if force_console:
                if self._oauth_client_type == "web":
                    raise CLIError(
                        "GTOOL_OAUTH_CONSOLE=1 is not supported for WEB OAuth clients.\n"
                        "Use the local-server redirect flow (http://localhost:<port>/) with Authorized redirect URIs, "
                        "or create an Installed/Desktop OAuth client if you need a console/manual flow."
                    )
                logger.info(json.dumps({"component": "GoogleAuth", "event": "oauth:force_console"}))
                creds = self._run_console_flow(flow)
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "oauth:success", "mode": "console"}))
                return creds

            try:
                host = self._get_oauth_host()
                ports = self._get_oauth_ports()
                chosen_port = self._choose_oauth_port(host, ports)
                redirect_uri = f"http://{host}:{chosen_port}/"
                attempted_redirect_uri = redirect_uri

                logger.debug(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:local_server_config",
                            "host": host,
                            "port": chosen_port,
                            "redirect_uri": redirect_uri,
                            "scopes": self.scopes,
                        }
                    )
                )

                # Ensure the redirect URI is deterministic and matches pre-registered URIs in Google Cloud.
                flow.redirect_uri = redirect_uri
                creds_any = flow.run_local_server(host=host, port=chosen_port, open_browser=True)
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "oauth:success", "mode": "local_server"}))
                return cast(Credentials, creds_any)
            except CLIError:
                raise
            except Exception as local_error:
                local_error_text = str(local_error)

                if "mismatching_state" in local_error_text or "State not equal" in local_error_text:
                    raise CLIError(
                        "OAuth local-server flow failed (mismatching_state).\n"
                        "This is a CSRF protection check: the 'state' returned to the callback does not match the state in the auth request.\n"
                        f"Attempted redirect URI: {attempted_redirect_uri or '<unknown>'}\n\n"
                        "Common causes:\n"
                        "- You opened an old/stale authorization URL from a previous run\n"
                        "- More than one OAuth flow is running at the same time\n"
                        "- The browser auto-reused a previous tab/session\n\n"
                        "Fix:\n"
                        "- Close all in-progress OAuth tabs/windows\n"
                        "- Ensure only one 'gtool' process is running\n"
                        "- Rerun the command and use the newly printed URL exactly once (prefer an incognito/private window)\n"
                        "- If it still happens, switch to a different registered port via GTOOL_OAUTH_PORTS"
                    )

                if "redirect_uri_mismatch" in str(local_error):
                    raise CLIError(
                        "OAuth failed: redirect_uri_mismatch\n"
                        f"Attempted redirect URI: {attempted_redirect_uri or '<unknown>'}\n"
                        "Add this exact URI to Authorized redirect URIs for your OAuth client OR adjust "
                        "GTOOL_OAUTH_PORTS to a registered port."
                    )

                if self._oauth_client_type == "web":
                    raise CLIError(
                        "OAuth local-server flow failed.\n"
                        f"Attempted redirect URI: {attempted_redirect_uri or '<unknown>'}\n"
                        f"Error: {local_error}\n"
                        "Console/OOB fallback is not allowed for WEB OAuth clients.\n"
                        "Fix by registering additional redirect URIs (http://localhost:<port>/) and setting "
                        "GTOOL_OAUTH_PORTS to a registered, free port."
                    )
                # Fallback to console flow if the local server callback fails (e.g., browser/redirect issues)
                logger.warning(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:local_server_failed",
                            "error": str(local_error),
                        }
                    )
                )
                creds = self._run_console_flow(flow)
                logger.debug(json.dumps({"component": "GoogleAuth", "event": "oauth:success", "mode": "console"}))
                return cast(Credentials, creds)
        except FileNotFoundError:
            logger.error(
                json.dumps(
                    {"component": "GoogleAuth", "event": "oauth:credentials_missing", "path": self.credentials_file}
                )
            )
            raise CLIError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please download your credentials.json from Google Cloud Console and place it in the configured location."
            )
        except CLIError:
            raise
        except Exception as e:
            logger.error(json.dumps({"component": "GoogleAuth", "event": "oauth:failed", "error": str(e)}))
            raise CLIError(
                "Authentication failed. If the browser redirect did not complete, rerun with '--debug' "
                "and ensure your credentials.json matches the configured scopes. You can also set GTOOL_OAUTH_CONSOLE=1 "
                "to use console-based OAuth."
            )

    def _get_oauth_host(self) -> str:
        """Return the host used for the OAuth local server redirect."""
        return os.environ.get("GTOOL_OAUTH_HOST", "localhost").strip() or "localhost"

    def _get_oauth_ports(self) -> list[int]:
        """Return the list of allowed OAuth redirect ports.

        The ports must be pre-registered in Google Cloud Console for web OAuth clients.
        """
        default_ports = [8401]
        raw = os.environ.get("GTOOL_OAUTH_PORTS")
        if not raw:
            return default_ports

        ports: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ports.append(int(part))
            except ValueError:
                continue
        return ports or default_ports

    def _choose_oauth_port(self, host: str, ports: list[int]) -> int:
        """Pick the first available port from the allowlist by attempting to bind."""
        last_error: Optional[str] = None
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.bind((host, port))
                finally:
                    sock.close()

                logger.debug(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:port_available",
                            "host": host,
                            "port": port,
                        }
                    )
                )
                return port
            except OSError as e:
                last_error = str(e)
                logger.debug(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:port_in_use",
                            "host": host,
                            "port": port,
                            "error": str(e),
                        }
                    )
                )
                continue

        logger.error(
            json.dumps(
                {
                    "component": "GoogleAuth",
                    "event": "oauth:no_available_ports",
                    "host": host,
                    "ports": ports,
                    "error": last_error,
                }
            )
        )
        raise CLIError(
            "No available OAuth redirect ports found.\n"
            "Free a port or change GTOOL_OAUTH_PORTS to a different allowlist.\n"
            "Also ensure the matching redirect URIs (http://<host>:<port>/) are registered in Google Cloud Console."
        )

    def _create_oauth_flow(self) -> InstalledAppFlow:
        """Create an OAuth flow from either 'installed' or 'web' client secrets JSON."""
        client_config: Optional[dict] = None
        try:
            with open(self.credentials_file, "r") as f:
                client_config = json.load(f)
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.warning(
                json.dumps(
                    {
                        "component": "GoogleAuth",
                        "event": "oauth:credentials_read_failed",
                        "error": str(e),
                    }
                )
            )

        def _normalize_auth_uri(config: dict, key: str) -> dict:
            if key not in config or not isinstance(config.get(key), dict):
                return config
            normalized = dict(config)
            block = dict(normalized[key])
            auth_uri = block.get("auth_uri")
            if auth_uri == "https://accounts.google.com/o/oauth2/auth":
                block["auth_uri"] = "https://accounts.google.com/o/oauth2/v2/auth"
                logger.debug(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:auth_uri_normalized",
                            "type": key,
                            "from": auth_uri,
                            "to": block["auth_uri"],
                        }
                    )
                )
            normalized[key] = block
            return normalized

        if client_config and "web" in client_config:
            self._oauth_client_type = "web"
            logger.debug(json.dumps({"component": "GoogleAuth", "event": "oauth:client_type_detected", "type": "web"}))
            client_config = _normalize_auth_uri(client_config, "web")
            return InstalledAppFlow.from_client_config(client_config, self.scopes)

        if client_config and "installed" in client_config:
            self._oauth_client_type = "installed"
            logger.debug(
                json.dumps({"component": "GoogleAuth", "event": "oauth:client_type_detected", "type": "installed"})
            )
            client_config = _normalize_auth_uri(client_config, "installed")
            try:
                return InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
            except Exception as e:
                logger.warning(
                    json.dumps(
                        {
                            "component": "GoogleAuth",
                            "event": "oauth:from_client_secrets_failed",
                            "error": str(e),
                        }
                    )
                )
                return InstalledAppFlow.from_client_config(client_config, self.scopes)

        raise CLIError(
            "Invalid credentials file format. Expected an OAuth client secrets JSON with a top-level 'installed' or 'web' key."
        )

    def _run_console_flow(self, flow: InstalledAppFlow) -> Credentials:
        """Perform a console-based OAuth flow (no local server)."""
        # Use urn:ietf:wg:oauth:2.0:oob for out-of-band/manual copy-paste flow
        flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        click.echo("Please visit this URL to authorize access:")
        click.echo(auth_url)
        code = click.prompt("Enter the authorization code here")
        flow.fetch_token(code=code)
        return cast(Credentials, flow.credentials)

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
        logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:refresh:start"}))
        try:
            credentials.refresh(Request())
            logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:refresh:success"}))
            return credentials
        except Exception as e:
            error_str = str(e)
            logger.error(json.dumps({"component": "GoogleAuth", "event": "token:refresh:failed", "error": error_str}))

            # Detect invalid_scope error - means the scope is not configured in GCP OAuth consent screen
            if "invalid_scope" in error_str.lower():
                # Extract the problematic scopes from configured scopes
                gmail_scopes = [s for s in self.scopes if "gmail" in s.lower()]

                if gmail_scopes:
                    raise CLIError(
                        "Token refresh failed: invalid_scope\n\n"
                        "The Gmail API scopes are not configured in your Google Cloud Project.\n\n"
                        "To fix this:\n"
                        "1. Go to https://console.cloud.google.com/apis/credentials\n"
                        "2. Click on your OAuth 2.0 Client ID\n"
                        "3. Under 'OAuth consent screen', ensure Gmail API is enabled:\n"
                        "   - Navigate to 'OAuth consent screen' in the left sidebar\n"
                        "   - Click 'Edit App'\n"
                        "   - In the 'Scopes' section, add these Gmail scopes:\n"
                        f"     {', '.join(gmail_scopes)}\n"
                        "4. Save the changes\n"
                        "5. Delete your token.json file and re-authenticate:\n"
                        f"   rm {self.token_file}\n"
                        "   Then run your command again\n\n"
                        "Note: You may also need to enable the Gmail API:\n"
                        "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
                    )
                else:
                    raise CLIError(
                        "Token refresh failed: invalid_scope\n\n"
                        f"One or more configured scopes are not valid for your OAuth client:\n{self.scopes}\n\n"
                        "To fix this:\n"
                        "1. Go to https://console.cloud.google.com/apis/credentials\n"
                        "2. Click on your OAuth 2.0 Client ID\n"
                        "3. Under 'OAuth consent screen', add the required scopes\n"
                        "4. Enable the corresponding APIs in the Google Cloud Console\n"
                        "5. Delete your token.json and re-authenticate:\n"
                        f"   rm {self.token_file}\n"
                        "   Then run 'gtool config' to reconfigure"
                    )

            raise CLIError("Token refresh failed. Please run 'gtool config' to re-authenticate.")

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

            logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:save", "path": self.token_file}))
            with open(self.token_file, "w") as f:
                f.write(credentials.to_json())
            logger.debug(json.dumps({"component": "GoogleAuth", "event": "token:save_success"}))
        except Exception as e:
            logger.error(json.dumps({"component": "GoogleAuth", "event": "token:save_failed", "error": str(e)}))
            raise CLIError(f"Failed to save authentication token: {e}")

    def _validate_credentials(self, credentials: Credentials) -> bool:
        """Check if credentials are valid.

        Args:
            credentials: Credentials object to validate

        Returns:
            True if credentials are valid, False otherwise
        """
        valid = bool(credentials.valid)
        expired = bool(credentials.expired)
        logger.debug(
            json.dumps({"component": "GoogleAuth", "event": "token:validate", "valid": valid, "expired": expired})
        )
        return valid and not expired
