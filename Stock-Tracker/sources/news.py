"""
Polls Finnhub company news, scores urgency, and sends breaking news alerts.
"""

from datetime import date, datetime

import finnhub

from config import get_finnhub_key, get_tickers, get_urgency_keywords
from notifier import send_breaking_alert, send_normal_alert
from sources.state import has_seen_item, mark_item_seen
from sources.time_utils import is_weekend


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

            headline = item.get("headline", "Stock news")
            source = item.get("source") or ticker
            summary = item.get("summary") or "New article detected."
            published_at = item.get("datetime")
            if published_at:
                try:
                    published_at = datetime.fromtimestamp(published_at).strftime("%Y-%m-%d %H:%M")
                    summary = f"{summary}\n\nPublished: {published_at}"
                except (TypeError, ValueError, OSError):
                    pass

            title = f"{ticker}: {headline[:80]}"
            message = f"{source}\n\n{summary[:700]}"
            url = item.get("url")

            sent = send_breaking_alert(title, message, url) if urgent else send_normal_alert(title, message, url)
            if sent:
                mark_item_seen(item_id)
