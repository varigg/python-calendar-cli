"""Tests for ErrorCategorizer component.

Tests error categorization for Google API errors using composition pattern.
No @patch decorators - all dependencies injected via function arguments.
"""

from caltool.error_categorizer import ErrorCategorizer


def test_error_categorizer_returns_auth_for_401(mock_http_error_401):
    """FR-001: 401 Unauthorized error should categorize as AUTH."""
    categorizer = ErrorCategorizer()
    result = categorizer.categorize(mock_http_error_401)
    assert result == "AUTH"


def test_error_categorizer_returns_quota_for_429(mock_http_error_429):
    """FR-001: 429 Too Many Requests error should categorize as QUOTA."""
    categorizer = ErrorCategorizer()
    result = categorizer.categorize(mock_http_error_429)
    assert result == "QUOTA"


def test_error_categorizer_returns_transient_for_500(mock_http_error_500):
    """FR-001: 500 Internal Server Error should categorize as TRANSIENT."""
    categorizer = ErrorCategorizer()
    result = categorizer.categorize(mock_http_error_500)
    assert result == "TRANSIENT"


def test_error_categorizer_returns_client_for_400(mock_http_error_400):
    """FR-001: 400 Bad Request error should categorize as CLIENT."""
    categorizer = ErrorCategorizer()
    result = categorizer.categorize(mock_http_error_400)
    assert result == "CLIENT"


def test_error_categorizer_returns_quota_for_403(mock_http_error_403):
    """FR-001: 403 Forbidden (quota exceeded) should categorize as QUOTA."""
    categorizer = ErrorCategorizer()
    result = categorizer.categorize(mock_http_error_403)
    assert result == "QUOTA"
