"""
Command-line tool for managing your stock watchlist.
Usage:
  python manage.py list
  python manage.py add TSLA "Tesla Inc."
  python manage.py remove TSLA
  python manage.py test-notification
  python manage.py set-key pushover_user YOUR_KEY
  python manage.py set-key pushover_token YOUR_TOKEN
  python manage.py set-key finnhub YOUR_KEY
"""

import sys
from datetime import date
from config import load_config, save_config
from notifier import test_notification


def cmd_list(config: dict) -> None:
    """Prints all stocks currently on the watchlist."""
    watchlist = config["watchlist"]

    if not watchlist:
        print("Your watchlist is empty.")
        return

    print(f"\n{'Ticker':<8} {'Name':<30} {'Added'}")
    print("-" * 52)
    for stock in watchlist:
        print(f"{stock['ticker']:<8} {stock['name']:<30} {stock['added']}")
    print(f"\nTotal: {len(watchlist)} stock(s)\n")


def cmd_add(config: dict, ticker: str, name: str = None) -> None:
    """Adds a stock to the watchlist by ticker symbol."""
    ticker = ticker.upper()

    # Check for duplicates
    existing = [s["ticker"] for s in config["watchlist"]]
    if ticker in existing:
        print(f"⚠️  {ticker} is already on your watchlist.")
        return

    config["watchlist"].append({
        "ticker": ticker,
        "name": name or ticker,
        "added": str(date.today()),
    })

    save_config(config)
    print(f"✅ Added {ticker} ({name or ticker}) to your watchlist.")


def cmd_remove(config: dict, ticker: str) -> None:
    """Removes a stock from the watchlist by ticker symbol."""
    ticker = ticker.upper()
    original_count = len(config["watchlist"])

    config["watchlist"] = [
        s for s in config["watchlist"] if s["ticker"] != ticker
    ]

    if len(config["watchlist"]) == original_count:
        print(f"⚠️  {ticker} was not found on your watchlist.")
        return

    save_config(config)
    print(f"🗑️  Removed {ticker} from your watchlist.")


def cmd_set_key(config: dict, key_name: str, value: str) -> None:
    """Sets an API key or credential in config.json."""
    key_map = {
        "pushover_user":  ("pushover",  "user_key"),
        "pushover_token": ("pushover",  "api_token"),
        "finnhub":        ("finnhub",   "api_key"),
    }

    if key_name not in key_map:
        print(f"❌ Unknown key '{key_name}'. Valid options: {', '.join(key_map.keys())}")
        return

    section, field = key_map[key_name]
    config[section][field] = value
    save_config(config)
    print(f"✅ Updated {section}.{field}")


def print_help() -> None:
    """Prints usage instructions."""
    print(__doc__)


def main():
    config = load_config()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "list":
        cmd_list(config)

    elif command == "add":
        if len(sys.argv) < 3:
            print("Usage: python manage.py add TICKER \"Company Name\"")
            return
        ticker = sys.argv[2]
        name   = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_add(config, ticker, name)

    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: python manage.py remove TICKER")
            return
        cmd_remove(config, sys.argv[2])

    elif command == "test-notification":
        print("Sending test notification to your iPhone...")
        test_notification()

    elif command == "set-key":
        if len(sys.argv) < 4:
            print("Usage: python manage.py set-key [pushover_user|pushover_token|finnhub] VALUE")
            return
        cmd_set_key(config, sys.argv[2], sys.argv[3])

    else:
        print(f"❌ Unknown command '{command}'")
        print_help()


if __name__ == "__main__":
    main()
