"""
Loads, saves, and provides access to all app configuration from config.json.
This is the single source of truth for settings and the watchlist.
"""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> dict:
    """Reads config.json and returns it as a dictionary."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Writes a config dictionary back to config.json, preserving formatting."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_watchlist() -> list[dict]:
    """Returns the current list of watched stocks as a list of dicts."""
    return load_config()["watchlist"]


def get_tickers() -> list[str]:
    """Returns just the ticker symbols from the watchlist (e.g. ['IONQ', 'QBTS'])."""
    return [stock["ticker"] for stock in get_watchlist()]


def get_pushover_credentials() -> dict:
    """Returns the Pushover user_key and api_token."""
    return load_config()["pushover"]


def get_finnhub_key() -> str:
    """Returns the Finnhub API key."""
    return load_config()["finnhub"]["api_key"]


def get_alert_settings() -> dict:
    """Returns timing and scheduling settings for alerts."""
    return load_config()["alert_settings"]


def get_urgency_keywords() -> list[str]:
    """Returns the list of keywords that trigger an immediate high-priority alert."""
    return load_config()["news_urgency"]["high_priority_keywords"]
