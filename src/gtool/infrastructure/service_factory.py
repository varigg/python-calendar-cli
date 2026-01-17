"""ServiceFactory - builds Google API service instances.

Uses composition pattern to inject authentication and build Google API
services on demand with caching for performance.
"""

from typing import Any, Dict

from googleapiclient import discovery

from gtool.infrastructure.auth import GoogleAuth


class ServiceFactory:
    """Builds and caches Google API service instances.

    This factory manages the creation of Google API service clients
    using the google-api-python-client library. Services are cached
    to avoid rebuilding the same service multiple times.

    Args:
        auth: GoogleAuth instance providing authenticated credentials.

    Attributes:
        _auth: GoogleAuth instance.
        _services: Cache of built service instances keyed by (api_name, version).
    """

    def __init__(self, auth: GoogleAuth) -> None:
        """Initialize the ServiceFactory with authentication.

        Args:
            auth: GoogleAuth instance to use for service credentials.
        """
        self._auth = auth
        self._services: Dict[tuple, Any] = {}

    def build_service(self, api_name: str, api_version: str) -> Any:
        """Build or retrieve a cached Google API service.

        Builds a Google API service for the specified API name and version
        using the authenticated credentials. Services are cached by (api_name, version)
        key to avoid rebuilding the same service multiple times.

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
        cache_key = (api_name, api_version)

        if cache_key not in self._services:
            self._services[cache_key] = discovery.build(
                api_name,
                api_version,
                credentials=self._auth.get_credentials(),
            )

        return self._services[cache_key]
