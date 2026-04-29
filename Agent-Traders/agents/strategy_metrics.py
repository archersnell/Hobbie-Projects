import pandas as pd

from alpaca.common.exceptions import APIError
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestTradeRequest
from alpaca.data.timeframe import TimeFrame
from indicators.intraday_indicators import evaluate_indicators


class StrategyMetrics:
    """Gather market data and calculate metrics used by the strategy."""

    def collect(
        self,
        market_data_client: StockHistoricalDataClient,
        symbol: str,
        sma_period: int,
        data_feed,
        history_start,
    ) -> dict:
        current_price = self._get_current_price(
            market_data_client=market_data_client,
            symbol=symbol,
            data_feed=data_feed,
        )
        price_bars = self._get_recent_price_bars(
            market_data_client=market_data_client,
            symbol=symbol,
            sma_period=sma_period,
            data_feed=data_feed,
            history_start=history_start,
        )
        closes = [bar["close"] for bar in price_bars]
        sma = self._calculate_sma(closes=closes, sma_period=sma_period)
        indicator_metrics = self._calculate_indicator_metrics(price_bars)

        return {
            "symbol": symbol,
            "current_price": current_price,
            "sma": sma,
            "price_vs_sma_pct": self._calculate_percent_change(
                current_value=current_price,
                previous_value=sma,
            ),
            "recent_change_pct": self._calculate_recent_change(
                current_price=current_price,
                closes=closes,
            ),
        } | indicator_metrics

    def _get_current_price(
        self,
        market_data_client: StockHistoricalDataClient,
        symbol: str,
        data_feed,
    ) -> float:
        latest_trade_request = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
            feed=data_feed,
        )

        try:
            latest_trades = market_data_client.get_stock_latest_trade(latest_trade_request)
        except APIError as error:
            message = getattr(error, "message", str(error))
            raise ValueError(f"Could not fetch latest trade for {symbol}: {message}") from error

        if symbol not in latest_trades:
            raise ValueError(
                f"No latest trade data was returned for {symbol}. Check that the symbol is valid."
            )

        latest_trade = latest_trades[symbol]
        return float(latest_trade.price)

    def _get_recent_price_bars(
        self,
        market_data_client: StockHistoricalDataClient,
        symbol: str,
        sma_period: int,
        data_feed,
        history_start,
    ) -> list[dict]:
        bars_request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=history_start,
            limit=sma_period,
            feed=data_feed,
        )
        try:
            bars = market_data_client.get_stock_bars(bars_request)
        except APIError as error:
            message = getattr(error, "message", str(error))
            raise ValueError(f"Could not fetch price history for {symbol}: {message}") from error

        symbol_bars = bars.data.get(symbol, [])

        if len(symbol_bars) < sma_period:
            raise ValueError(
                f"Not enough price history to calculate the {sma_period}-day SMA for {symbol}. "
                "Check that the symbol is valid and has recent market data."
            )

        return [
            {
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume or 0),
            }
            for bar in symbol_bars
        ]

    def _calculate_indicator_metrics(self, price_bars: list[dict]) -> dict:
        price_history = pd.DataFrame(price_bars)
        indicators = evaluate_indicators(price_history)

        return {
            name: self._get_latest_value(value)
            for name, value in indicators.items()
        }

    def _get_latest_value(self, value):
        if hasattr(value, "iloc"):
            return value.iloc[-1]

        return value

    def _calculate_sma(self, closes: list[float], sma_period: int) -> float:
        return float(pd.Series(closes).tail(sma_period).mean())

    def _calculate_recent_change(self, current_price: float, closes: list[float]) -> float:
        if len(closes) >= 5:
            return self._calculate_percent_change(
                current_value=current_price,
                previous_value=closes[-5],
            )

        return self._calculate_percent_change(
            current_value=current_price,
            previous_value=closes[0],
        )

    def _calculate_percent_change(self, current_value: float, previous_value: float) -> float:
        if previous_value == 0:
            return 0.0

        return ((current_value - previous_value) / previous_value) * 100
