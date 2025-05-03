import datetime
import unittest
from zoneinfo import ZoneInfo

from click.testing import CliRunner

from caltool.cli import (
    cli,
    find_free_slots,
    is_slot_long_enough,
    is_within_availability,
)

# class TestWeather:
#     def test_cli(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ["temperature"])
#         assert result.exit_code == 0
#         assert -90.0 <= float(result.output) <= 60.0


class TestCalendarCLI(unittest.TestCase):
    def setUp(self):
        """Set up common variables for the tests."""
        self.availability_start = datetime.time(8, 0)  # 8:00 AM
        self.availability_end = datetime.time(18, 0)  # 6:00 PM
        self.duration_minutes = 30
        self.time_zone = ZoneInfo("America/Los_Angeles")

    def test_is_slot_long_enough(self):
        """Test if a slot is long enough for the specified duration."""
        start = datetime.datetime(2025, 5, 2, 8, 0)
        end = datetime.datetime(2025, 5, 2, 8, 30)
        self.assertTrue(is_slot_long_enough(start, end, self.duration_minutes))

        end = datetime.datetime(2025, 5, 2, 8, 15)
        self.assertFalse(is_slot_long_enough(start, end, self.duration_minutes))

    def test_is_within_availability(self):
        """Test if a time is within availability hours."""
        time = datetime.time(9, 0)  # 9:00 AM
        self.assertTrue(
            is_within_availability(
                time,
                self.duration_minutes,
                self.availability_start,
                self.availability_end,
            )
        )

        time = datetime.time(17, 45)  # 5:45 PM
        self.assertFalse(
            is_within_availability(
                time,
                self.duration_minutes,
                self.availability_start,
                self.availability_end,
            )
        )

        time = datetime.time(7, 30)  # 7:30 AM
        self.assertFalse(
            is_within_availability(
                time,
                self.duration_minutes,
                self.availability_start,
                self.availability_end,
            )
        )

    def test_find_free_slots(self):
        """Test finding free slots."""
        busy = [
            {"start": "2025-05-02T08:30:00Z", "end": "2025-05-02T09:30:00Z"},
            {"start": "2025-05-02T10:00:00Z", "end": "2025-05-02T11:00:00Z"},
        ]
        start_time = datetime.datetime(2025, 5, 2, 8, 0, tzinfo=ZoneInfo("UTC"))
        end_time = datetime.datetime(2025, 5, 2, 12, 0, tzinfo=ZoneInfo("UTC"))

        free_slots = find_free_slots(
            busy,
            start_time,
            end_time,
            self.duration_minutes,
            availability_start=self.availability_start,
            availability_end=self.availability_end,
        )

        expected_slots = [
            (
                datetime.datetime(2025, 5, 2, 8, 0, tzinfo=ZoneInfo("UTC")),
                datetime.datetime(2025, 5, 2, 8, 30, tzinfo=ZoneInfo("UTC")),
                "",
            ),
            (
                datetime.datetime(2025, 5, 2, 9, 30, tzinfo=ZoneInfo("UTC")),
                datetime.datetime(2025, 5, 2, 10, 0, tzinfo=ZoneInfo("UTC")),
                "",
            ),
            (
                datetime.datetime(2025, 5, 2, 11, 0, tzinfo=ZoneInfo("UTC")),
                datetime.datetime(2025, 5, 2, 12, 0, tzinfo=ZoneInfo("UTC")),
                "",
            ),
        ]

        self.assertEqual(free_slots, expected_slots)


if __name__ == "__main__":
    unittest.main()
