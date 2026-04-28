import pandas as pd

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestTradeRequest
from alpaca.data.timeframe import TimeFrame


class StrategyAgent:
    """
    Strategy agent for a simple price-vs-SMA rule.

    This is intentionally small so you can later swap the decision logic with
    AI prompts, model predictions, or a more advanced technical strategy.
    """

    def evaluate(
        self,
        market_data_client: StockHistoricalDataClient,
        symbol: str,
        sma_period: int,
        data_feed,
        history_start,
    ) -> dict:
        latest_trade_request = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
            feed=data_feed,
        )
        latest_trade = market_data_client.get_stock_latest_trade(latest_trade_request)[symbol]
        current_price = float(latest_trade.price)

        bars_request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=history_start,
            limit=sma_period,
            feed=data_feed,
        )
        bars = market_data_client.get_stock_bars(bars_request)
        symbol_bars = bars.data.get(symbol, [])

        if len(symbol_bars) < sma_period:
            raise ValueError(
                f"Not enough price history to calculate the {sma_period}-day SMA for {symbol}."
            )

        closes = [bar.close for bar in symbol_bars]
        sma = float(pd.Series(closes).tail(sma_period).mean())
        price_vs_sma_pct = ((current_price - sma) / sma) * 100 if sma else 0.0

        if len(closes) >= 5:
            recent_change_pct = ((current_price - closes[-5]) / closes[-5]) * 100
        else:
            recent_change_pct = ((current_price - closes[0]) / closes[0]) * 100

        decision = "buy" if current_price > sma else "hold"
        reason = (
            f"Price is above the SMA ({current_price:.2f} > {sma:.2f})."
            if decision == "buy"
            else f"Price is not above the SMA ({current_price:.2f} <= {sma:.2f})."
        )

        return {
            "symbol": symbol,
            "current_price": current_price,
            "sma": sma,
            "price_vs_sma_pct": price_vs_sma_pct,
            "recent_change_pct": recent_change_pct,
            "decision": decision,
            "reason": reason,
        }
