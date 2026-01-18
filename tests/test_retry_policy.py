"""Tests for RetryPolicy component.

Tests retry logic with smart error categorization.
No @patch decorators - all dependencies injected via function arguments.
"""

import time

import pytest

from gtool.infrastructure.retry import RetryPolicy


@pytest.mark.parametrize(
    "category,expected",
    [
        ("AUTH", False),
        ("CLIENT", False),
        ("QUOTA", True),
        ("TRANSIENT", True),
    ],
)
def test_retry_policy_should_retry_categories(category, expected):
    """FR-002: Verify retry behavior for each error category."""
    policy = RetryPolicy(max_retries=3, delay=0.01)
    assert policy.should_retry(category) is expected


def test_retry_policy_execute_succeeds_on_retry():
    """FR-002, SC-002: Function failing twice then succeeding should succeed after retries."""
    call_count = 0

    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"

    policy = RetryPolicy(max_retries=3, delay=0.001)

    result = policy.execute(failing_function)

    assert result == "success"
    assert call_count == 3


def test_retry_policy_execute_respects_max_retries():
    """FR-002: Execution should fail when max_retries exceeded."""

    def always_fails():
        raise ValueError("Persistent failure")

    policy = RetryPolicy(max_retries=2, delay=0.001)

    with pytest.raises(ValueError):
        policy.execute(always_fails)


def test_retry_policy_execute_with_args_and_kwargs():
    """FR-002: Execute should pass through args and kwargs to function."""

    def add_numbers(a, b, multiplier=1):
        return (a + b) * multiplier

    policy = RetryPolicy(max_retries=1, delay=0.001)

    result = policy.execute(add_numbers, 2, 3, multiplier=5)

    assert result == 25


def test_retry_policy_exponential_backoff():
    """FR-002: Delay should increase exponentially on each retry attempt."""
    call_times = []

    def track_calls():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise ValueError("Retry me")
        return "success"

    policy = RetryPolicy(max_retries=3, delay=0.01)

    result = policy.execute(track_calls)

    assert result == "success"
    assert len(call_times) == 3

    # Check that delays increase exponentially (roughly)
    if len(call_times) >= 3:
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        # Second delay should be roughly 2x the first (exponential: delay * 2^attempt)
        assert delay2 >= delay1 * 1.5  # Allow some tolerance for system variation
