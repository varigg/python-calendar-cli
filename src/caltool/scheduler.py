import datetime
import logging
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

@dataclass
class SearchParameters:
    start_date: datetime.date
    end_date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    duration: int
    timezone: str

class Scheduler:
    """
    A class to manage scheduling and finding free time slots in Google Calendar.
    """

    def __init__(
        self,
        client: Any,
        search_params: SearchParameters,
        calendar_ids: list[str],
    ):
        """
        Initialize the Scheduler with configuration.
        Raises ValueError for invalid arguments.
        """
        self.start_date = search_params.start_date
        self.end_date = search_params.end_date
        self.start_time = search_params.start_time
        self.end_time = search_params.end_time

        if not isinstance(search_params.duration, int) or search_params.duration <= 0:
            raise ValueError("Duration must be a positive integer.")
        if not isinstance(calendar_ids, list) or not all(isinstance(cid, str) for cid in calendar_ids):
            raise ValueError("calendar_ids must be a list of strings.")
        self.client = client
        self.duration = search_params.duration
        self.timezone = search_params.timezone
        self.calendar_ids = calendar_ids
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Scheduler initialized with config: {self.__dict__}")

    def is_slot_long_enough(self, start: datetime.datetime, end: datetime.datetime, duration_minutes: int) -> bool:
        """
        Check if the time slot is long enough for the specified duration.

        Example:
            >>> s = datetime.datetime(2025, 5, 2, 8, 0)
            >>> e = datetime.datetime(2025, 5, 2, 8, 30)
            >>> Scheduler(...).is_slot_long_enough(s, e, 30)
            True
        Edge cases:
            - Zero or negative duration returns False
            - start == end returns False

        """
        if duration_minutes <= 0 or start >= end:
            return False
        return (end - start).total_seconds() >= duration_minutes * 60

    def get_free_slots_for_day(
        self,
        busy_times: list[dict],
        start: datetime.datetime,
        end: datetime.datetime,
        duration_minutes: int,
    ) -> list[tuple]:
        """
        Get free slots for a specific day, handling overlapping and adjacent busy times.
        Returns a list of (start, end) tuples.
        """
        free_slots = []
        cursor = start
        # Sort and merge overlapping/adjacent busy times
        busy_sorted = sorted(busy_times, key=lambda b: b["start"])
        merged_busy = []
        for b in busy_sorted:
            b_start = datetime.datetime.fromisoformat(b["start"])
            b_end = datetime.datetime.fromisoformat(b["end"])
            if not merged_busy:
                merged_busy.append({"start": b_start, "end": b_end})
            else:
                last = merged_busy[-1]
                if b_start <= last["end"]:  # Overlapping or adjacent
                    last["end"] = max(last["end"], b_end)
                else:
                    merged_busy.append({"start": b_start, "end": b_end})
        for busy in merged_busy:
            if self.is_slot_long_enough(cursor, busy["start"], duration_minutes):
                free_slots.append((cursor, busy["start"]))
            cursor = max(cursor, busy["end"])
        if cursor < end and self.is_slot_long_enough(cursor, end, duration_minutes):
            free_slots.append((cursor, end))
        return free_slots

    def get_free_slots(self) -> list[tuple]:
        """
        Get all free slots between start_date and end_date (inclusive).
        Handles errors and logs a summary for each day.
        """
        current_date = self.start_date
        free_slots = []
        while current_date <= self.end_date:
            try:
                self.logger.debug(f"Processing date: {current_date}")
                day_start = datetime.datetime.combine(current_date, self.start_time, tzinfo=ZoneInfo(self.timezone))
                day_end = datetime.datetime.combine(current_date, self.end_time, tzinfo=ZoneInfo(self.timezone))
                busy_times = self.client.get_day_busy_times(self.calendar_ids, day_start, day_end, self.timezone)
                slots = self.get_free_slots_for_day(busy_times, day_start, day_end, self.duration)
                free_slots.extend(slots)
                self.logger.info(f"{current_date}: Found {len(slots)} free slots.")
            except Exception as e:
                self.logger.error(f"Error processing {current_date}: {e}")
            current_date += datetime.timedelta(days=1)
        return free_slots
