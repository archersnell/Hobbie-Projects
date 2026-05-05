"""
Time helpers for market-day and scheduled alert behavior.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from config import get_alert_settings


# Returns the configured timezone as a ZoneInfo object.
def get_timezone() -> ZoneInfo:
    return ZoneInfo(get_alert_settings().get("timezone", "America/New_York"))


# Returns the current datetime in the configured market timezone.
def now_local() -> datetime:
    return datetime.now(get_timezone())


# Returns True on Saturday or Sunday in the configured timezone.
def is_weekend() -> bool:
    return now_local().weekday() >= 5


# Returns True on weekdays in the configured timezone.
def is_market_day() -> bool:
    return not is_weekend()


# Converts an HH:MM setting into a time object.
def parse_time_setting(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


# Returns True when the current local time is inside the configured window.
def is_within_time_window(start_time: str, end_time: str) -> bool:
    current_time = now_local().time()
    start = parse_time_setting(start_time)
    end = parse_time_setting(end_time)

    if start <= end:
        return start <= current_time <= end

    return current_time >= start or current_time <= end
