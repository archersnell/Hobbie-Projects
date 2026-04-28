import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from alpaca.data.enums import DataFeed


@dataclass
class BotConfig:
    api_key: str
    secret_key: str
    paper: bool
    symbol: str
    max_trade_value: float
    sma_period: int
    data_feed: DataFeed
    log_file: str


def setup_logging(log_file: str) -> None:
    """Write detailed logs to a file while keeping terminal output concise."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8")],
    )


def parse_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_data_feed(value: str) -> DataFeed:
    feed_name = (value or "iex").strip().lower()
    if feed_name == "iex":
        return DataFeed.IEX
    if feed_name == "sip":
        return DataFeed.SIP
    raise ValueError("ALPACA_DATA_FEED must be either 'iex' or 'sip'.")


def load_config(
    symbol_override: str | None = None,
    allow_env_symbol: bool = True,
) -> BotConfig:
    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()

    if not api_key or not secret_key:
        raise ValueError(
            "Missing Alpaca API keys. Add ALPACA_API_KEY and ALPACA_SECRET_KEY to your .env file."
        )

    env_symbol = os.getenv("ALPACA_SYMBOL", "") if allow_env_symbol else ""
    symbol = symbol_override or env_symbol

    return BotConfig(
        api_key=api_key,
        secret_key=secret_key,
        paper=parse_bool(os.getenv("ALPACA_PAPER"), default=True),
        symbol=symbol.strip().upper(),
        max_trade_value=float(os.getenv("MAX_TRADE_VALUE", "500")),
        sma_period=int(os.getenv("SMA_PERIOD", "20")),
        data_feed=parse_data_feed(os.getenv("ALPACA_DATA_FEED", "iex")),
        log_file=os.path.join("data", "trading_bot.log"),
    )
