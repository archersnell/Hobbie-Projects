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


MAX_FALLBACK_SUMMARY_LENGTH = 500


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


# Formats a number as compact money text.
def format_money(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "not listed"

    if abs(number) >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if abs(number) >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"

    return f"${number:,.0f}"


# Formats an earnings field for compact display.
def format_metric(value) -> str:
    if value is None:
        return "not listed"

    return str(value)


# Builds a categorized earnings-day reminder.
def format_earnings_reminder(ticker: str, item: dict) -> tuple[str, str]:
    report_time = item.get("hour") or "unknown time"
    estimate = format_metric(item.get("epsEstimate"))
    revenue_estimate = format_money(item.get("revenueEstimate"))

    title = f"Earnings due: {ticker}"
    message = "\n".join([
        "Category: Earnings reminder",
        f"Report time: {report_time}",
        f"EPS estimate: {estimate}",
        f"Revenue estimate: {revenue_estimate}",
        "Watch for: EPS/revenue surprise and guidance.",
    ])
    return title, message


# Builds a compact fallback earnings summary without AI.
def format_earnings_fallback(ticker: str, item: dict) -> str:
    eps_actual = format_metric(item.get("epsActual"))
    eps_estimate = format_metric(item.get("epsEstimate"))
    revenue_actual = format_money(item.get("revenueActual"))
    revenue_estimate = format_money(item.get("revenueEstimate"))

    message = "\n".join([
        "Category: Earnings results",
        f"EPS: {eps_actual} actual vs {eps_estimate} est.",
        f"Revenue: {revenue_actual} actual vs {revenue_estimate} est.",
        "Watch for: price reaction, guidance, and analyst revisions.",
    ])
    return message[:MAX_FALLBACK_SUMMARY_LENGTH]


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

        title, message = format_earnings_reminder(ticker, item)
        if send_normal_alert(title, message):
            mark_item_seen(item_id)


# Sends an OpenAI-generated summary when today's watched earnings data is available.
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
            summary = format_earnings_fallback(ticker, item)

        if send_digest_alert(f"Earnings results: {ticker}", summary):
            mark_item_seen(item_id)
