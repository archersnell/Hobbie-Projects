"""
Checks Finnhub insider transactions and alerts on meaningful executive trades.
"""

from datetime import date, timedelta

import finnhub

from config import get_finnhub_key, get_tickers
from notifier import send_normal_alert
from sources.state import has_seen_item, mark_item_seen
from sources.time_utils import is_market_day


MIN_TRADE_VALUE = 100_000

TRANSACTION_ACTIONS = {
    "P": "Buy",
    "S": "Sell",
    "A": "Award/grant",
    "D": "Disposition",
    "M": "Option exercise",
}


# Builds a Finnhub client using the configured API key.
def get_client() -> finnhub.Client:
    return finnhub.Client(api_key=get_finnhub_key())


# Fetches recent insider transactions for a ticker.
def fetch_insider_transactions(client: finnhub.Client, ticker: str) -> list[dict]:
    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()

    try:
        response = client.stock_insider_transactions(ticker, _from=start, to=end)
        return response.get("data", []) if isinstance(response, dict) else []
    except Exception as exc:
        print(f"[insider] Error fetching insider transactions for {ticker}: {exc}")
        return []


# Calculates the approximate dollar value of an insider transaction.
def get_transaction_value(item: dict) -> float:
    try:
        shares = abs(float(item.get("share", 0) or 0))
        price = abs(float(item.get("transactionPrice", 0) or 0))
        return shares * price
    except (TypeError, ValueError):
        return 0.0


# Produces a stable ID for an insider transaction.
def get_transaction_id(ticker: str, item: dict) -> str:
    filing_id = item.get("id") or item.get("accessionNumber")
    fallback = f"{item.get('name')}:{item.get('transactionDate')}:{item.get('share')}"
    return f"insider:{ticker}:{filing_id or fallback}"


# Describes an insider transaction code in plain English.
def get_transaction_action(code: str) -> str:
    clean_code = str(code or "").upper()
    return TRANSACTION_ACTIONS.get(clean_code, f"Trade {clean_code or 'unknown'}")


# Formats a share count for compact display.
def format_shares(shares) -> str:
    try:
        return f"{abs(float(shares)):,.0f}"
    except (TypeError, ValueError):
        return "unknown"


# Builds a categorized insider-trade alert.
def format_insider_alert(ticker: str, item: dict, value: float) -> tuple[str, str]:
    name = item.get("name", "Unknown insider")
    code = item.get("transactionCode", "")
    action = get_transaction_action(code)
    shares = format_shares(item.get("share"))
    date_text = item.get("transactionDate", "unknown date")
    try:
        price_text = f"${float(item.get('transactionPrice')):,.2f}"
    except (TypeError, ValueError):
        price_text = "not listed"

    title = f"Insider {action.lower()}: {ticker}"
    message = "\n".join([
        "Category: Insider trade",
        f"Insider: {name}",
        f"Action: {action}",
        f"Size: {shares} shares at {price_text}",
        f"Value/date: ${value:,.0f} on {date_text}",
    ])
    return title, message


# Checks watched tickers for large insider buys or sells.
def check_insider_trades() -> None:
    if not is_market_day():
        return

    client = get_client()

    for ticker in get_tickers():
        for item in fetch_insider_transactions(client, ticker):
            value = get_transaction_value(item)
            if value < MIN_TRADE_VALUE:
                continue

            item_id = get_transaction_id(ticker, item)
            if has_seen_item(item_id):
                continue

            title, message = format_insider_alert(ticker, item, value)

            if send_normal_alert(title, message):
                mark_item_seen(item_id)
