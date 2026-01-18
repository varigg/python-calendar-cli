"""ServiceFactory - builds Google API service instances.

Uses composition pattern to inject authentication and build Google API
services on demand.
"""

from typing import Any

from googleapiclient import discovery

from gtool.infrastructure.auth import GoogleAuth


class ServiceFactory:
    """Builds Google API service instances.

    This factory manages the creation of Google API service clients
    using the google-api-python-client library.

    Args:
        auth: GoogleAuth instance providing authenticated credentials.

    Attributes:
        _auth: GoogleAuth instance.
    """

    def __init__(self, auth: GoogleAuth) -> None:
        """Initialize the ServiceFactory with authentication.

        Args:
            auth: GoogleAuth instance to use for service credentials.
        """
        self._auth = auth

    def build_service(self, api_name: str, api_version: str) -> Any:
        """Build a Google API service.

        Builds a Google API service for the specified API name and version
        using the authenticated credentials.

        Args:
            api_name: Name of the Google API (e.g., "calendar", "gmail").
            api_version: Version of the API (e.g., "v3", "v1").

        Returns:
            Built googleapiclient service instance.

        Example:
            >>> factory = ServiceFactory(auth)
            >>> calendar = factory.build_service("calendar", "v3")
            >>> gmail = factory.build_service("gmail", "v1")
        """
        return discovery.build(
            api_name,
            api_version,
            credentials=self._auth.get_credentials(),
        )
