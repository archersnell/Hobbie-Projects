import pandas as pd


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate intraday VWAP from high, low, close, and volume."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    price_times_volume = typical_price * df["volume"]

    cumulative_price_volume = price_times_volume.cumsum()
    cumulative_volume = df["volume"].cumsum()

    return cumulative_price_volume / cumulative_volume


def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate an exponential moving average of the close price."""
    return df["close"].ewm(span=period, adjust=False).mean()


def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate a simple moving average of the close price."""
    return df["close"].rolling(window=period).mean()


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI using average gains and losses."""
    price_change = df["close"].diff()

    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    average_gain = gains.rolling(window=period).mean()
    average_loss = losses.rolling(window=period).mean()

    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict:
    """Calculate MACD, signal line, and histogram."""
    fast_ema = calculate_ema(df, fast_period)
    slow_ema = calculate_ema(df, slow_period)

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_histogram": histogram,
    }


def calculate_volume(df: pd.DataFrame) -> pd.Series:
    """Return raw candle volume."""
    return df["volume"]


def calculate_relative_volume(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Compare current volume to recent average volume."""
    average_volume = df["volume"].rolling(window=period).mean()
    return df["volume"] / average_volume


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    previous_close = df["close"].shift(1)

    high_low = df["high"] - df["low"]
    high_previous_close = (df["high"] - previous_close).abs()
    low_previous_close = (df["low"] - previous_close).abs()

    true_range = pd.concat(
        [high_low, high_previous_close, low_previous_close],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(window=period).mean()


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2,
) -> dict:
    """Calculate Bollinger Bands around a moving average."""
    middle_band = calculate_sma(df, period)
    standard_deviation = df["close"].rolling(window=period).std()

    upper_band = middle_band + (standard_deviation * num_std)
    lower_band = middle_band - (standard_deviation * num_std)

    return {
        "bollinger_upper": upper_band,
        "bollinger_middle": middle_band,
        "bollinger_lower": lower_band,
    }


def calculate_support_resistance(df: pd.DataFrame, period: int = 20) -> dict:
    """Calculate simple rolling support and resistance levels."""
    support = df["low"].rolling(window=period).min()
    resistance = df["high"].rolling(window=period).max()

    return {
        "support": support,
        "resistance": resistance,
    }


def calculate_opening_range(df: pd.DataFrame, opening_range_periods: int = 15) -> dict:
    """
    Calculate opening range high and low.

    For one-minute candles, opening_range_periods=15 means the first 15 minutes.
    For five-minute candles, opening_range_periods=3 also means the first 15 minutes.
    """
    opening_candles = df.head(opening_range_periods)

    return {
        "opening_range_high": opening_candles["high"].max(),
        "opening_range_low": opening_candles["low"].min(),
    }


def evaluate_indicators(df: pd.DataFrame) -> dict:
    """
    Calculate all day trading metrics and return them in one dictionary.

    This function expects df to contain:
    open, high, low, close, volume
    """
    vwap = calculate_vwap(df)
    ema_9 = calculate_ema(df, period=9)
    ema_20 = calculate_ema(df, period=20)
    sma_20 = calculate_sma(df, period=20)
    rsi_14 = calculate_rsi(df, period=14)
    macd_values = calculate_macd(df)
    volume = calculate_volume(df)
    relative_volume = calculate_relative_volume(df, period=20)
    atr_14 = calculate_atr(df, period=14)
    bollinger_bands = calculate_bollinger_bands(df, period=20, num_std=2)
    support_resistance = calculate_support_resistance(df, period=20)
    opening_range = calculate_opening_range(df, opening_range_periods=15)

    return {
        "vwap": vwap,
        "ema_9": ema_9,
        "ema_20": ema_20,
        "sma_20": sma_20,
        "rsi_14": rsi_14,
        "macd": macd_values["macd"],
        "macd_signal": macd_values["macd_signal"],
        "macd_histogram": macd_values["macd_histogram"],
        "volume": volume,
        "relative_volume": relative_volume,
        "atr_14": atr_14,
        "bollinger_upper": bollinger_bands["bollinger_upper"],
        "bollinger_middle": bollinger_bands["bollinger_middle"],
        "bollinger_lower": bollinger_bands["bollinger_lower"],
        "support": support_resistance["support"],
        "resistance": support_resistance["resistance"],
        "opening_range_high": opening_range["opening_range_high"],
        "opening_range_low": opening_range["opening_range_low"],
    }
