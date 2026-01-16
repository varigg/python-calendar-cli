"""Tests for Scheduler business logic.

Tests the core scheduling algorithms: finding free slots, merging busy times,
and validating slot durations.
"""

import datetime
from unittest.mock import Mock

import pytest

from caltool.scheduler import Scheduler, SearchParameters


@pytest.fixture
def scheduler_fixture():
    """Create a configured scheduler with mock client."""
    search_params = SearchParameters(
        start_date=datetime.date(2025, 5, 2),
        end_date=datetime.date(2025, 5, 2),
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
        duration=30,
        timezone="America/Los_Angeles",
    )
    return Scheduler(
        client=Mock(),
        search_params=search_params,
        calendar_ids=["primary"],
    )


# --- is_slot_long_enough tests ---


def test_is_slot_long_enough_exact_duration(scheduler_fixture):
    """Slot exactly matching duration should return True."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 8, 30)
    assert scheduler_fixture.is_slot_long_enough(start, end, 30) is True


def test_is_slot_long_enough_longer_than_duration(scheduler_fixture):
    """Slot longer than duration should return True."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 9, 0)
    assert scheduler_fixture.is_slot_long_enough(start, end, 30) is True


def test_is_slot_long_enough_shorter_than_duration(scheduler_fixture):
    """Slot shorter than duration should return False."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 8, 15)
    assert scheduler_fixture.is_slot_long_enough(start, end, 30) is False


def test_is_slot_long_enough_zero_duration(scheduler_fixture):
    """Zero duration should return False."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 9, 0)
    assert scheduler_fixture.is_slot_long_enough(start, end, 0) is False


def test_is_slot_long_enough_negative_duration(scheduler_fixture):
    """Negative duration should return False."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 9, 0)
    assert scheduler_fixture.is_slot_long_enough(start, end, -30) is False


def test_is_slot_long_enough_start_equals_end(scheduler_fixture):
    """Start == end should return False."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    assert scheduler_fixture.is_slot_long_enough(start, start, 30) is False


def test_is_slot_long_enough_start_after_end(scheduler_fixture):
    """Start after end should return False."""
    start = datetime.datetime(2025, 5, 2, 9, 0)
    end = datetime.datetime(2025, 5, 2, 8, 0)
    assert scheduler_fixture.is_slot_long_enough(start, end, 30) is False


# --- get_free_slots_for_day tests ---


def test_get_free_slots_for_day_no_busy_times(scheduler_fixture):
    """No busy times should return entire availability window."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    slots = scheduler_fixture.get_free_slots_for_day([], start, end, 30)
    assert len(slots) == 1
    assert slots[0] == (start, end)


def test_get_free_slots_for_day_one_busy_block(scheduler_fixture):
    """One busy block should create two free slots."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    busy = [{"start": "2025-05-02T10:00:00", "end": "2025-05-02T11:00:00"}]
    slots = scheduler_fixture.get_free_slots_for_day(busy, start, end, 30)
    assert len(slots) == 2
    # First free slot: 8:00 - 10:00
    assert slots[0][0] == start
    assert slots[0][1] == datetime.datetime(2025, 5, 2, 10, 0)
    # Second free slot: 11:00 - 18:00
    assert slots[1][0] == datetime.datetime(2025, 5, 2, 11, 0)
    assert slots[1][1] == end


def test_get_free_slots_for_day_overlapping_busy_times(scheduler_fixture):
    """Overlapping busy times should be merged."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    # Two overlapping meetings
    busy = [
        {"start": "2025-05-02T10:00:00", "end": "2025-05-02T11:00:00"},
        {"start": "2025-05-02T10:30:00", "end": "2025-05-02T12:00:00"},
    ]
    slots = scheduler_fixture.get_free_slots_for_day(busy, start, end, 30)
    assert len(slots) == 2
    # Free: 8:00-10:00 and 12:00-18:00 (merged busy: 10:00-12:00)
    assert slots[0][1] == datetime.datetime(2025, 5, 2, 10, 0)
    assert slots[1][0] == datetime.datetime(2025, 5, 2, 12, 0)


def test_get_free_slots_for_day_adjacent_busy_times(scheduler_fixture):
    """Adjacent busy times should be merged."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    busy = [
        {"start": "2025-05-02T10:00:00", "end": "2025-05-02T11:00:00"},
        {"start": "2025-05-02T11:00:00", "end": "2025-05-02T12:00:00"},
    ]
    slots = scheduler_fixture.get_free_slots_for_day(busy, start, end, 30)
    assert len(slots) == 2
    # Merged busy: 10:00-12:00
    assert slots[0][1] == datetime.datetime(2025, 5, 2, 10, 0)
    assert slots[1][0] == datetime.datetime(2025, 5, 2, 12, 0)


def test_get_free_slots_for_day_slot_too_short(scheduler_fixture):
    """Short gaps between busy times should be excluded."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    # Gap of only 15 minutes (less than 30 min duration)
    busy = [
        {"start": "2025-05-02T09:00:00", "end": "2025-05-02T10:00:00"},
        {"start": "2025-05-02T10:15:00", "end": "2025-05-02T11:00:00"},
    ]
    slots = scheduler_fixture.get_free_slots_for_day(busy, start, end, 30)
    # Should have: 8:00-9:00 (60min) and 11:00-18:00 (7hrs)
    # Should NOT have: 10:00-10:15 (15min < 30min required)
    assert len(slots) == 2
    assert slots[0] == (start, datetime.datetime(2025, 5, 2, 9, 0))
    assert slots[1] == (datetime.datetime(2025, 5, 2, 11, 0), end)


def test_get_free_slots_for_day_busy_all_day(scheduler_fixture):
    """Busy for entire availability window should return no slots."""
    start = datetime.datetime(2025, 5, 2, 8, 0)
    end = datetime.datetime(2025, 5, 2, 18, 0)
    busy = [{"start": "2025-05-02T08:00:00", "end": "2025-05-02T18:00:00"}]
    slots = scheduler_fixture.get_free_slots_for_day(busy, start, end, 30)
    assert len(slots) == 0


# --- Scheduler initialization tests ---


def test_scheduler_rejects_zero_duration():
    """Scheduler should reject zero duration."""
    search_params = SearchParameters(
        start_date=datetime.date(2025, 5, 2),
        end_date=datetime.date(2025, 5, 2),
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
        duration=0,
        timezone="America/Los_Angeles",
    )
    with pytest.raises(ValueError, match="Duration must be a positive integer"):
        Scheduler(client=Mock(), search_params=search_params, calendar_ids=["primary"])


def test_scheduler_rejects_negative_duration():
    """Scheduler should reject negative duration."""
    search_params = SearchParameters(
        start_date=datetime.date(2025, 5, 2),
        end_date=datetime.date(2025, 5, 2),
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
        duration=-30,
        timezone="America/Los_Angeles",
    )
    with pytest.raises(ValueError, match="Duration must be a positive integer"):
        Scheduler(client=Mock(), search_params=search_params, calendar_ids=["primary"])


def test_scheduler_rejects_invalid_calendar_ids():
    """Scheduler should reject non-list calendar_ids."""
    search_params = SearchParameters(
        start_date=datetime.date(2025, 5, 2),
        end_date=datetime.date(2025, 5, 2),
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
        duration=30,
        timezone="America/Los_Angeles",
    )
    with pytest.raises(ValueError, match="calendar_ids must be a list"):
        Scheduler(client=Mock(), search_params=search_params, calendar_ids="primary")


# --- get_free_slots integration test ---


def test_get_free_slots_calls_client_for_each_day():
    """get_free_slots should call client for each day in range."""
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []

    search_params = SearchParameters(
        start_date=datetime.date(2025, 5, 2),
        end_date=datetime.date(2025, 5, 4),  # 3 days
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
        duration=30,
        timezone="America/Los_Angeles",
    )
    scheduler = Scheduler(
        client=mock_client,
        search_params=search_params,
        calendar_ids=["primary"],
    )

    slots = scheduler.get_free_slots()

    # Should call client 3 times (one per day)
    assert mock_client.get_day_busy_times.call_count == 3
    # Should return 3 full-day slots (no busy times)
    assert len(slots) == 3
