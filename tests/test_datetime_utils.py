"""
Unit tests for parse_date_range in datetime_utils.py
"""
import datetime

import pytest

from src.caltool.datetime_utils import parse_date_range


def test_today_plus_1():
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    assert parse_date_range("today+1") == (today, tomorrow)

def test_tomorrow_plus_2():
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    day_after = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    assert parse_date_range("tomorrow+2") == (tomorrow, day_after)

def test_weekday_plus_0():
    # Find next Thursday from today
    today = datetime.date.today()
    thursday = today + datetime.timedelta((3 - today.weekday() + 7) % 7)
    assert parse_date_range("thursday") == (thursday.isoformat(), thursday.isoformat())

def test_weekday_plus_1():
    today = datetime.date.today()
    thursday = today + datetime.timedelta((3 - today.weekday() + 7) % 7)
    friday = thursday + datetime.timedelta(days=1)
    assert parse_date_range("thursday+1") == (thursday.isoformat(), friday.isoformat())

def test_invalid_range():
    with pytest.raises(ValueError):
        parse_date_range("noday+1")
