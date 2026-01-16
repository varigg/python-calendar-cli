"""Domain models for gtool - core data structures."""

import datetime
from dataclasses import dataclass


@dataclass
class SearchParameters:
    """Parameters for scheduling/free time search.

    Attributes:
        start_date: Date to begin search
        end_date: Date to end search (inclusive)
        start_time: Daily start time for availability window
        end_time: Daily end time for availability window
        duration: Minimum slot duration in minutes
        timezone: Timezone for all time calculations
    """

    start_date: datetime.date
    end_date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    duration: int
    timezone: str
