"""
Checks earnings calendars and sends report-day reminders and summaries.
"""

from datetime import date

import finnhub

from config import get_finnhub_key, get_tickers
from notifier import send_digest_alert, send_normal_alert
from sources.state import has_seen_item, mark_item_seen
from sources.summarizer import summarize_earnings
from sources.time_utils import is_market_day


# Builds a Finnhub client using the configured API key.
def get_client() -> finnhub.Client:
    return finnhub.Client(api_key=get_finnhub_key())


# Safely fetches today's earnings calendar from Finnhub.
def fetch_earnings_calendar(client: finnhub.Client) -> list[dict]:
    today = date.today().isoformat()
    try:
        response = client.earnings_calendar(_from=today, to=today)
        return response.get("earningsCalendar", []) if isinstance(response, dict) else []
    except Exception as exc:
        print(f"[earnings] Error fetching earnings calendar: {exc}")
        return []


# Sends a morning reminder for watched stocks reporting today.
def check_earnings_calendar() -> None:
    if not is_market_day():
        return

    client = get_client()
    watched = set(get_tickers())

    for item in fetch_earnings_calendar(client):
        ticker = item.get("symbol")
        if ticker not in watched:
            continue

        item_id = f"earnings-reminder:{ticker}:{item.get('date')}"
        if has_seen_item(item_id):
            continue

        hour = item.get("hour", "unknown time")
        title = f"{ticker} earnings today"
        message = f"{ticker} reports earnings today ({hour})."
        if send_normal_alert(title, message):
            mark_item_seen(item_id)


# Sends a Claude-generated summary when today's watched earnings data is available.
def check_earnings_results() -> None:
    if not is_market_day():
        return

    client = get_client()
    watched = set(get_tickers())

    for item in fetch_earnings_calendar(client):
        ticker = item.get("symbol")
        if ticker not in watched:
            continue

        if item.get("epsActual") is None and item.get("revenueActual") is None:
            continue

        item_id = f"earnings-summary:{ticker}:{item.get('date')}"
        if has_seen_item(item_id):
            continue

        summary = summarize_earnings(ticker, item)
        if not summary:
            summary = f"Earnings data posted for {ticker}: {item}"

        if send_digest_alert(f"{ticker} earnings summary", summary):
            mark_item_seen(item_id)
