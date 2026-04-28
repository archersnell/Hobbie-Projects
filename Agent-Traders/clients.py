from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient

from config import BotConfig


def create_market_data_client(config: BotConfig) -> StockHistoricalDataClient:
    return StockHistoricalDataClient(config.api_key, config.secret_key)


def create_trading_client(config: BotConfig) -> TradingClient:
    return TradingClient(config.api_key, config.secret_key, paper=config.paper)
