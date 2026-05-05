import re


SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def normalize_symbol(symbol: str) -> str:
    clean_symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(clean_symbol):
        raise ValueError(f"Invalid symbol '{symbol}'. Use a ticker like AAPL or BRK.B.")
    return clean_symbol


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _percent_change(current_value: float, previous_value: float) -> float:
    if previous_value == 0:
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100


def calculate_sma(values: list[float], period: int) -> float:
    return _average(values[-period:])


def calculate_rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) <= period:
        return 50.0

    changes = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    recent_changes = changes[-period:]
    gains = [change for change in recent_changes if change > 0]
    losses = [-change for change in recent_changes if change < 0]
    average_gain = _average(gains)
    average_loss = _average(losses)

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def estimate_volatility(bars: list[dict], period: int = 14) -> float:
    recent_bars = bars[-period:]
    ranges = []
    for bar in recent_bars:
        close = bar["close"]
        if close > 0:
            ranges.append(((bar["high"] - bar["low"]) / close) * 100)
    return _average(ranges)


def calculate_metrics(price: float, bars: list[dict], quote: dict) -> dict:
    if len(bars) < 20:
        raise ValueError("At least 20 daily bars are needed for research metrics.")

    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]
    previous_close = closes[-2]
    latest_volume = volumes[-1]
    average_volume = _average(volumes[-21:-1])
    bid_price = quote.get("bid_price", 0)
    ask_price = quote.get("ask_price", 0)
    spread = ask_price - bid_price if ask_price and bid_price else 0

    return {
        "current_price": price,
        "daily_percent_change": _percent_change(price, previous_close),
        "volume": latest_volume,
        "relative_volume": latest_volume / average_volume if average_volume else 0.0,
        "volatility_estimate": estimate_volatility(bars),
        "sma_5": calculate_sma(closes, 5),
        "sma_20": calculate_sma(closes, 20),
        "rsi_14": calculate_rsi(closes),
        "momentum": _percent_change(price, closes[-6]),
        "bid_ask_spread_percent": (spread / price) * 100 if price > 0 else 0.0,
    }


def get_market_snapshot(client, symbol: str) -> dict:
    price = client.get_latest_price(symbol)
    bars = client.get_daily_bars(symbol, limit=60)
    quote = client.get_latest_quote(symbol)
    return calculate_metrics(price=price, bars=bars, quote=quote)
