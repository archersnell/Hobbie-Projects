"""
Polls Finnhub company news, scores urgency, and sends breaking news alerts.
"""

from datetime import date, datetime

import finnhub

from config import get_finnhub_key, get_tickers, get_urgency_keywords
from notifier import send_breaking_alert, send_normal_alert
from sources.state import has_seen_item, mark_item_seen
from sources.time_utils import is_weekend


MAX_SUMMARY_LENGTH = 360


# Builds a Finnhub client using the configured API key.
def get_client() -> finnhub.Client:
    return finnhub.Client(api_key=get_finnhub_key())


# Returns True when a headline or summary contains an urgent keyword.
def is_urgent_news(item: dict) -> bool:
    searchable_text = " ".join([
        str(item.get("headline", "")),
        str(item.get("summary", "")),
    ]).lower()
    return any(keyword.lower() in searchable_text for keyword in get_urgency_keywords())


# Returns the first urgency keyword found in a news item.
def get_matched_keyword(item: dict) -> str | None:
    searchable_text = " ".join([
        str(item.get("headline", "")),
        str(item.get("summary", "")),
    ]).lower()

    for keyword in get_urgency_keywords():
        if keyword.lower() in searchable_text:
            return keyword

    return None


# Produces a stable ID for a news article across app restarts.
def get_news_id(ticker: str, item: dict) -> str:
    return f"news:{ticker}:{item.get('id') or item.get('url') or item.get('headline')}"


# Fetches recent company news for a ticker from Finnhub.
def fetch_company_news(client: finnhub.Client, ticker: str) -> list[dict]:
    today = date.today().isoformat()
    try:
        return client.company_news(ticker, _from=today, to=today) or []
    except Exception as exc:
        print(f"[news] Error fetching news for {ticker}: {exc}")
        return []


# Shortens long notification fields without cutting words mid-stream.
def shorten_text(text: str, max_length: int) -> str:
    clean_text = " ".join(str(text or "").split())
    if len(clean_text) <= max_length:
        return clean_text

    return clean_text[:max_length].rsplit(" ", 1)[0] + "..."


# Converts a Finnhub timestamp into a compact display value.
def format_published_at(timestamp) -> str:
    if not timestamp:
        return "unknown"

    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "unknown"


# Builds a categorized phone-friendly news alert.
def format_news_alert(ticker: str, item: dict) -> tuple[str, str, str | None, bool]:
    urgent = is_urgent_news(item)
    category = "Urgent news" if urgent else "Stock news"
    headline = shorten_text(item.get("headline", "Stock news"), 72)
    source = item.get("source") or ticker
    summary = shorten_text(item.get("summary") or "New article detected.", MAX_SUMMARY_LENGTH)
    published_at = format_published_at(item.get("datetime"))
    matched_keyword = get_matched_keyword(item)

    title = f"{category}: {ticker} - {headline}"
    message_parts = [
        f"Category: {category}",
        f"Source: {source}",
        f"Why it matters: {summary}",
        f"Published: {published_at}",
    ]

    if matched_keyword:
        message_parts.insert(2, f"Trigger: {matched_keyword}")

    return title, "\n".join(message_parts), item.get("url"), urgent


# Checks watched tickers for new urgent or important news.
def check_breaking_news() -> None:
    client = get_client()

    for ticker in get_tickers():
        for item in fetch_company_news(client, ticker):
            item_id = get_news_id(ticker, item)
            if has_seen_item(item_id):
                continue

            urgent = is_urgent_news(item)
            if is_weekend() and not urgent:
                continue

            title, message, url, urgent = format_news_alert(ticker, item)

            sent = send_breaking_alert(title, message, url) if urgent else send_normal_alert(title, message, url)
            if sent:
                mark_item_seen(item_id)
