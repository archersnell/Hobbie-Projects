from typing import Any

from config import AppConfig


class AlpacaClient:
    """Small wrapper around Alpaca so commands do not depend on SDK details."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._trading_client = None
        self._data_client = None

    def _require_keys(self) -> None:
        if not self.config.alpaca_api_key or not self.config.alpaca_secret_key:
            raise ValueError(
                "Missing Alpaca keys. Add ALPACA_API_KEY and ALPACA_SECRET_KEY to your .env file."
            )

    def _get_data_feed(self):
        from alpaca.data.enums import DataFeed

        if self.config.data_feed == "iex":
            return DataFeed.IEX
        if self.config.data_feed == "sip":
            return DataFeed.SIP
        raise ValueError("ALPACA_DATA_FEED must be either 'iex' or 'sip'.")

    @property
    def trading_client(self):
        if self._trading_client is None:
            from alpaca.trading.client import TradingClient

            self._require_keys()
            self._trading_client = TradingClient(
                self.config.alpaca_api_key,
                self.config.alpaca_secret_key,
                paper=not self.config.is_live_trading,
            )
        return self._trading_client

    @property
    def data_client(self):
        if self._data_client is None:
            from alpaca.data.historical import StockHistoricalDataClient

            self._require_keys()
            self._data_client = StockHistoricalDataClient(
                self.config.alpaca_api_key,
                self.config.alpaca_secret_key,
            )
        return self._data_client

    def validate_symbol(self, symbol: str) -> None:
        from alpaca.common.exceptions import APIError
        from alpaca.trading.enums import AssetStatus

        try:
            asset = self.trading_client.get_asset(symbol)
        except APIError as error:
            message = getattr(error, "message", str(error))
            raise ValueError(f"Alpaca could not validate {symbol}: {message}") from error

        if asset.status != AssetStatus.ACTIVE:
            raise ValueError(f"{symbol} is not active on Alpaca.")
        if not asset.tradable:
            raise ValueError(f"{symbol} is not tradable on Alpaca.")

    def get_account(self) -> Any:
        return self.trading_client.get_account()

    def get_position(self, symbol: str) -> Any | None:
        from alpaca.common.exceptions import APIError

        try:
            return self.trading_client.get_open_position(symbol)
        except APIError as error:
            message = getattr(error, "message", str(error)).lower()
            if "position does not exist" in message or getattr(error, "status_code", None) == 404:
                return None
            raise

    def get_positions(self) -> list[Any]:
        return self.trading_client.get_all_positions()

    def get_latest_price(self, symbol: str) -> float:
        from alpaca.data.requests import StockLatestTradeRequest

        request = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
            feed=self._get_data_feed(),
        )
        trades = self.data_client.get_stock_latest_trade(request)
        if symbol not in trades:
            raise ValueError(f"No latest trade data returned for {symbol}.")
        return float(trades[symbol].price)

    def get_latest_quote(self, symbol: str) -> dict:
        from alpaca.data.requests import StockLatestQuoteRequest

        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbol,
            feed=self._get_data_feed(),
        )
        quotes = self.data_client.get_stock_latest_quote(request)
        quote = quotes.get(symbol)
        if not quote:
            return {}
        return {
            "bid_price": float(quote.bid_price or 0),
            "ask_price": float(quote.ask_price or 0),
        }

    def get_daily_bars(self, symbol: str, limit: int = 60) -> list[dict]:
        from datetime import datetime, timedelta, timezone

        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=datetime.now(timezone.utc) - timedelta(days=120),
            limit=limit,
            feed=self._get_data_feed(),
        )
        bars = self.data_client.get_stock_bars(request).data.get(symbol, [])
        return [
            {
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume or 0),
            }
            for bar in bars
        ]

    def get_tradable_assets(self) -> list[Any]:
        from alpaca.trading.enums import AssetClass, AssetStatus
        from alpaca.trading.requests import GetAssetsRequest

        request = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
        assets = self.trading_client.get_all_assets(request)
        return [asset for asset in assets if asset.tradable]

    def get_stock_snapshots(self, symbols: list[str]) -> dict:
        from alpaca.data.requests import StockSnapshotRequest

        snapshots = {}
        for index in range(0, len(symbols), 200):
            symbol_chunk = symbols[index : index + 200]
            request = StockSnapshotRequest(
                symbol_or_symbols=symbol_chunk,
                feed=self._get_data_feed(),
            )
            snapshots.update(self.data_client.get_stock_snapshot(request))
        return snapshots

    def place_market_order(self, symbol: str, quantity: int, side: str) -> Any:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        return self.trading_client.submit_order(order_data=order_request)
