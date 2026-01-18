"""Domain models for gtool - core data structures."""

import datetime
from dataclasses import dataclass


@dataclass
class SearchParameters:
    """Parameters for scheduling/free time search.

    Attributes:
        start_datetime: Start of search range (timezone-aware)
        end_datetime: End of search range (timezone-aware, inclusive)
        availability_start: Daily start time for availability window
        availability_end: Daily end time for availability window
        duration: Minimum slot duration in minutes
    """

    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    availability_start: datetime.time
    availability_end: datetime.time
    duration: int
