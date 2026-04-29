import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class AppConfig:
    alpaca_api_key: str
    alpaca_secret_key: str
    trading_mode: str
    data_feed: str
    max_trade_value: float
    max_symbol_quantity: int
    max_trades_per_day: int
    loss_tolerance_pct: float
    min_buy_score: int
    bot_interval_seconds: int

    @property
    def is_live_trading(self) -> bool:
        return self.trading_mode == "live"


def load_config() -> AppConfig:
    load_dotenv()

    trading_mode = os.getenv("ALPACA_TRADING_MODE", "paper").strip().lower()
    if trading_mode not in {"paper", "live"}:
        raise ValueError("ALPACA_TRADING_MODE must be either 'paper' or 'live'.")

    return AppConfig(
        alpaca_api_key=os.getenv("ALPACA_API_KEY", "").strip(),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", "").strip(),
        trading_mode=trading_mode,
        data_feed=os.getenv("ALPACA_DATA_FEED", "iex").strip().lower(),
        max_trade_value=float(os.getenv("MAX_TRADE_VALUE", "100")),
        max_symbol_quantity=int(
            os.getenv("MAX_SYMBOL_QUANTITY", os.getenv("MAX_OPEN_POSITIONS", "3"))
        ),
        max_trades_per_day=int(os.getenv("MAX_TRADES_PER_DAY", "5")),
        loss_tolerance_pct=float(os.getenv("LOSS_TOLERANCE_PCT", "5")),
        min_buy_score=int(os.getenv("MIN_BUY_SCORE", "6")),
        bot_interval_seconds=int(os.getenv("BOT_INTERVAL_SECONDS", "300")),
    )
