import config
import pandas as pd


def recommendation(score):
    if score > config.BUY_THRESHOLD:
        return "BUY"
    elif score > config.WATCH_THRESHOLD:
        return "WATCH"
    elif score > config.HOLD_THRESHOLD:
        return "HOLD"
    else:
        return "SELL"
    

def score(data: dict) -> dict:
    history = data["history"]
    current_price = data["current_price"]

    # calculate moving averages from history
    ma_50 = history["Close"].rolling(window=50).mean().iloc[-1]
    ma_200 = history["Close"].rolling(window=200).mean().iloc[-1]

    rsi = calculate_rsi(history)

    # call each scoring function
    rsi_score = score_rsi(rsi)
    ma_score = score_moving_avg(current_price, ma_50, ma_200)
    vol_score = score_volume(data.get("volume"),data.get("average_volume"))
    week_score = score_52_week_position(current_price, data.get("52_week_low"), data.get("52_week_high"))

    # add them up
    total = rsi_score + ma_score + vol_score + week_score

    return {
        "score": total,
        "recommendation": recommendation(total)
    }

def calculate_rsi(history: pd.DataFrame, period: int = 14) -> float:
    close = history["Close"]
    delta = close.diff()          # day over day change

    gains = delta.where(delta > 0, 0)   # keep gains, zero out losses
    losses = -delta.where(delta < 0, 0) # keep losses, make positive

    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]  # return the most recent RSI value

def score_rsi(rsi: float) -> int:
    if rsi > 70:
        score = 5
    elif rsi > 50:
        score = 10
    elif rsi > 30:
        score = 18
    else:
        score = 25

    
    return score

def score_moving_avg(current: float, ma_50: float, ma_200: float) -> int:
    if current > ma_200 and current > ma_50:
        score = 30
    elif current > ma_200 and current < ma_50:
        score = 15
    elif current < ma_200 and current > ma_50:
        score = 9
    else:
        score = 0

    return score

def score_52_week_position(current_price, week_low52, week_high52) -> int:
    price_range = week_high52 - week_low52
    if price_range ==0:
        return 10
    lower_range =  current_price - week_low52
    percent = lower_range/price_range

    score = percent * 20
    return score

def score_volume(volume: float, average_volume: float) -> int:
    if average_volume == 0:
        return 0
    ratio = volume / average_volume

    if ratio > 2.0:
        score = 25
    elif ratio > 1.5:
        score = 19
    elif ratio > 1.0:
        score =13
    else:
        score = 5
    
    return score
