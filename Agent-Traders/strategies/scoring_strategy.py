def get_latest_metric(metrics: dict, name: str, default=None):
    """
    Get a metric value from the metrics dictionary.

    This helper supports both simple numbers and pandas Series.
    If a metric is a Series, it returns the newest value.
    """
    value = metrics.get(name, default)

    if hasattr(value, "iloc"):
        return value.iloc[-1]

    return value


def is_missing(value) -> bool:
    """Check for None or NaN values without adding extra dependencies."""
    return value is None or value != value


def calculate_risk_reward(metrics: dict, signal: str) -> dict:
    """
    Calculate stop loss, take profit, risk, reward, and risk/reward ratio.

    For BUY:
    - stop_loss = support - (0.25 * atr)
    - take_profit = resistance
    - risk = current_price - stop_loss
    - reward = take_profit - current_price

    For SELL:
    - stop_loss = resistance + (0.25 * atr)
    - take_profit = support
    - risk = stop_loss - current_price
    - reward = current_price - take_profit
    """
    current_price = get_latest_metric(metrics, "current_price")
    support = get_latest_metric(metrics, "support")
    resistance = get_latest_metric(metrics, "resistance")
    atr = get_latest_metric(metrics, "atr_14", 0)

    if signal == "BUY":
        stop_loss = support - (0.25 * atr)
        take_profit = resistance
        risk = current_price - stop_loss
        reward = take_profit - current_price
    elif signal == "SELL":
        stop_loss = resistance + (0.25 * atr)
        take_profit = support
        risk = stop_loss - current_price
        reward = current_price - take_profit
    else:
        return {
            "stop_loss": None,
            "take_profit": None,
            "risk": 0,
            "reward": 0,
            "risk_reward_ratio": None,
        }

    if risk <= 0 or reward <= 0:
        risk_reward_ratio = None
    else:
        risk_reward_ratio = reward / risk

    return {
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk": risk,
        "reward": reward,
        "risk_reward_ratio": risk_reward_ratio,
    }


def determine_confidence(score_difference: int) -> str:
    """Turn the distance between buy and sell scores into a confidence label."""
    if score_difference >= 4:
        return "HIGH"
    if score_difference >= 2:
        return "MEDIUM"

    return "LOW"


def explain_signal(metrics: dict, signal: str, reasons: list[str]) -> str:
    """Create a beginner-friendly explanation of the final signal."""
    if signal == "HOLD":
        return "HOLD because " + ", ".join(reasons) + "."

    return signal + " because " + ", ".join(reasons) + "."


def price_is_trapped_between_levels(current_price: float, support: float, resistance: float) -> bool:
    """
    Check whether price is sitting in the middle of support and resistance.

    This is a simple way to avoid weak trades where price has no clear breakout.
    """
    price_range = resistance - support

    if price_range <= 0:
        return True

    position_in_range = (current_price - support) / price_range
    return 0.35 <= position_in_range <= 0.65


def generate_strategy_signal(
    metrics: dict,
    min_volume_for_signal: float = 0.75,
    min_score_gap: int = 2,
    avoid_range_trades: bool = True,
) -> dict:
    """
    Generate a BUY, SELL, or HOLD signal from calculated stock metrics.

    This uses a scoring system. One bullish condition adds to the buy score.
    One bearish condition adds to the sell score.
    """
    buy_score = 0
    sell_score = 0
    buy_reasons = []
    sell_reasons = []
    hold_reasons = []

    current_price = get_latest_metric(metrics, "current_price")
    vwap = get_latest_metric(metrics, "vwap")
    ema_9 = get_latest_metric(metrics, "ema_9")
    ema_20 = get_latest_metric(metrics, "ema_20")
    rsi = get_latest_metric(metrics, "rsi_14")
    macd = get_latest_metric(metrics, "macd")
    macd_signal = get_latest_metric(metrics, "macd_signal")
    relative_volume = get_latest_metric(metrics, "relative_volume")
    support = get_latest_metric(metrics, "support")
    resistance = get_latest_metric(metrics, "resistance")
    opening_range_high = get_latest_metric(metrics, "opening_range_high")
    opening_range_low = get_latest_metric(metrics, "opening_range_low")

    # BUY score conditions.
    if current_price > vwap:
        buy_score += 1
        buy_reasons.append("price is above VWAP")

    if ema_9 > ema_20:
        buy_score += 1
        buy_reasons.append("EMA 9 is above EMA 20")

    if 40 <= rsi <= 70:
        buy_score += 1
        buy_reasons.append("RSI is in a healthy bullish range")

    if macd > macd_signal:
        buy_score += 1
        buy_reasons.append("MACD is above the signal line")

    if relative_volume > 1.5:
        buy_score += 1
        buy_reasons.append("relative volume is strong")

    if current_price > opening_range_high:
        buy_score += 1
        buy_reasons.append("price broke above the opening range high")

    if current_price > support * 1.005:
        buy_score += 1
        buy_reasons.append("price is safely above support")

    if current_price < resistance * 0.995:
        buy_score += 1
        buy_reasons.append("price is not too close to resistance")

    # SELL score conditions.
    if current_price < vwap:
        sell_score += 1
        sell_reasons.append("price is below VWAP")

    if ema_9 < ema_20:
        sell_score += 1
        sell_reasons.append("EMA 9 is below EMA 20")

    if 30 <= rsi <= 60:
        sell_score += 1
        sell_reasons.append("RSI is in a bearish range")

    if macd < macd_signal:
        sell_score += 1
        sell_reasons.append("MACD is below the signal line")

    if relative_volume > 1.5:
        sell_score += 1
        sell_reasons.append("relative volume is strong")

    if current_price < opening_range_low:
        sell_score += 1
        sell_reasons.append("price broke below the opening range low")

    if current_price < resistance * 0.995:
        sell_score += 1
        sell_reasons.append("price is safely below resistance")

    if current_price > support * 1.005:
        sell_score += 1
        sell_reasons.append("price is not too close to support")

    score_difference = abs(buy_score - sell_score)

    if buy_score > sell_score:
        signal = "BUY"
        reasons = buy_reasons
    elif sell_score > buy_score:
        signal = "SELL"
        reasons = sell_reasons
    else:
        signal = "HOLD"
        reasons = ["there is no clear score advantage"]

    has_enough_volume = not is_missing(relative_volume) and relative_volume >= 1
    has_some_volume = not is_missing(relative_volume) and relative_volume >= min_volume_for_signal
    has_strong_volume = not is_missing(relative_volume) and relative_volume > 1.5
    has_opening_range_breakout = (
        current_price > opening_range_high
        or current_price < opening_range_low
    )

    if has_some_volume and not has_enough_volume:
        if signal == "BUY":
            reasons.append("relative volume is acceptable but not strong")
        elif signal == "SELL":
            reasons.append("relative volume is acceptable but not strong")

    # HOLD filters. These protect against low-quality or unclear setups.
    if score_difference < min_score_gap:
        hold_reasons.append("buy and sell scores are too close")

    if not has_some_volume:
        hold_reasons.append("relative volume is too low")

    # Only force HOLD for a trapped price when there is no strong volume.
    # Strong volume can be the thing that starts a real breakout.
    if (
        avoid_range_trades
        and price_is_trapped_between_levels(current_price, support, resistance)
        and not has_opening_range_breakout
        and not has_strong_volume
    ):
        hold_reasons.append("price is trapped between support and resistance")

    if signal == "BUY" and rsi > 80:
        hold_reasons.append("RSI is extremely overbought for a buy")

    if signal == "SELL" and rsi < 20:
        hold_reasons.append("RSI is extremely oversold for a sell")

    if hold_reasons:
        return {
            "signal": "HOLD",
            "buy_score": buy_score,
            "sell_score": sell_score,
            "confidence": "LOW",
            "stop_loss": None,
            "take_profit": None,
            "risk_reward_ratio": None,
            "explanation": explain_signal(metrics, "HOLD", hold_reasons),
        }

    risk_reward = calculate_risk_reward(metrics, signal)
    risk_reward_ratio = risk_reward["risk_reward_ratio"]

    # Only block BUY or SELL when risk/reward is clearly invalid.
    # A weak ratio stays visible in the output so you can review the setup.
    if signal in {"BUY", "SELL"} and (
        risk_reward["risk"] <= 0
        or risk_reward["reward"] <= 0
        or risk_reward_ratio is None
    ):
        return {
            "signal": "HOLD",
            "buy_score": buy_score,
            "sell_score": sell_score,
            "confidence": "LOW",
            "stop_loss": None,
            "take_profit": None,
            "risk_reward_ratio": risk_reward_ratio,
            "explanation": explain_signal(
                metrics,
                "HOLD",
                ["risk/reward is poor for the stronger setup"],
            ),
        }

    return {
        "signal": signal,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "confidence": determine_confidence(score_difference),
        "stop_loss": risk_reward["stop_loss"],
        "take_profit": risk_reward["take_profit"],
        "risk_reward_ratio": risk_reward_ratio,
        "explanation": explain_signal(metrics, signal, reasons),
    }


if __name__ == "__main__":
    # Fake example metrics so you can run:
    # python -m strategies.scoring_strategy
    example_metrics = {
        "current_price": 105.00,
        "vwap": 102.50,
        "ema_9": 104.20,
        "ema_20": 101.80,
        "rsi_14": 58.00,
        "macd": 1.20,
        "macd_signal": 0.75,
        "relative_volume": 1.80,
        "atr_14": 1.50,
        "support": 101.00,
        "resistance": 112.00,
        "opening_range_high": 104.50,
        "opening_range_low": 99.50,
    }

    result = generate_strategy_signal(example_metrics)
    print(result)
