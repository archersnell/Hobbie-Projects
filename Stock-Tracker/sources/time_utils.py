"""
Time helpers for market-day and scheduled alert behavior.
"""

from datetime import datetime
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
