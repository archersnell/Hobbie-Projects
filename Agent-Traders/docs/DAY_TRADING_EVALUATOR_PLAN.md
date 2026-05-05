# Historical Day Trading Stock Evaluator Plan

This document is an older planning note. The active beginner-friendly code now
lives in `data/market_data.py` and `strategies/simple_momentum.py`.

This project is a planning document and code scaffold for evaluating intraday stock metrics.
It does not connect to APIs, place trades, or decide what to buy or sell.

The expected input is a pandas DataFrame named `df` with intraday candles.
At minimum, it should include these columns:

```text
open, high, low, close, volume
```

Rows should be sorted from oldest candle to newest candle.

## Trend Indicators

### VWAP

1. Name: Volume Weighted Average Price
2. What it measures: VWAP shows the average price paid during the day, weighted by trading volume.
3. Calculation logic:
   - Typical price = `(high + low + close) / 3`
   - Price-volume = `typical_price * volume`
   - VWAP = `cumulative(price-volume) / cumulative(volume)`
   - VWAP resets each trading day.
4. Required inputs: `high`, `low`, `close`, `volume`
5. Typical parameters: Intraday calculation from market open to current candle.

### EMA 9

1. Name: 9-period Exponential Moving Average
2. What it measures: EMA 9 shows short-term trend direction with more weight on recent prices.
3. Calculation logic:
   - `k = 2 / (period + 1)`
   - `EMA_today = (Price_today * k) + (EMA_yesterday * (1 - k))`
4. Required inputs: `close`
5. Typical parameters: `period = 9`

### EMA 20

1. Name: 20-period Exponential Moving Average
2. What it measures: EMA 20 shows a smoother intraday trend than EMA 9.
3. Calculation logic:
   - `k = 2 / (period + 1)`
   - `EMA_today = (Price_today * k) + (EMA_yesterday * (1 - k))`
4. Required inputs: `close`
5. Typical parameters: `period = 20`

### SMA

1. Name: Simple Moving Average
2. What it measures: SMA shows the average closing price over a fixed number of candles.
3. Calculation logic:
   - SMA = `sum(close prices over period) / period`
4. Required inputs: `close`
5. Typical parameters: `period = 20`

## Momentum Indicators

### RSI 14

1. Name: 14-period Relative Strength Index
2. What it measures: RSI estimates whether price momentum is strong, weak, overbought, or oversold.
3. Calculation logic:
   - Price change = `close_today - close_yesterday`
   - Gain = positive changes, otherwise `0`
   - Loss = absolute value of negative changes, otherwise `0`
   - Average gain = rolling average of gains over `14` periods
   - Average loss = rolling average of losses over `14` periods
   - `RS = average_gain / average_loss`
   - `RSI = 100 - (100 / (1 + RS))`
4. Required inputs: `close`
5. Typical parameters: `period = 14`

### MACD

1. Name: Moving Average Convergence Divergence
2. What it measures: MACD compares fast and slow EMAs to show trend momentum.
3. Calculation logic:
   - `MACD = EMA(12) - EMA(26)`
   - Signal line = `EMA(9) of MACD`
   - Histogram = `MACD - Signal line`
4. Required inputs: `close`
5. Typical parameters: Fast EMA `12`, slow EMA `26`, signal EMA `9`

## Volume Indicators

### Volume

1. Name: Candle Volume
2. What it measures: Volume shows how many shares traded during each candle.
3. Calculation logic:
   - Use the raw `volume` value from each candle.
4. Required inputs: `volume`
5. Typical parameters: None.

### Relative Volume

1. Name: Relative Volume
2. What it measures: Relative volume compares current volume against recent average volume.
3. Calculation logic:
   - Average volume = rolling average of `volume` over the chosen period
   - Relative volume = `current_volume / average_volume`
4. Required inputs: `volume`
5. Typical parameters: `period = 20`

## Volatility Indicators

### ATR

1. Name: Average True Range
2. What it measures: ATR estimates how much price is moving over recent candles.
3. Calculation logic:
   - True range is the largest of:
   - `high - low`
   - `abs(high - previous_close)`
   - `abs(low - previous_close)`
   - ATR = rolling average of true range over the chosen period.
4. Required inputs: `high`, `low`, `close`
5. Typical parameters: `period = 14`

### Bollinger Bands

1. Name: Bollinger Bands
2. What it measures: Bollinger Bands show whether price is high or low compared with recent volatility.
3. Calculation logic:
   - Middle band = SMA over the chosen period
   - Standard deviation = rolling standard deviation of `close`
   - Upper band = `middle_band + (standard_deviation * num_std)`
   - Lower band = `middle_band - (standard_deviation * num_std)`
4. Required inputs: `close`
5. Typical parameters: `period = 20`, `num_std = 2`

## Price Levels

### Support

1. Name: Rolling Support
2. What it measures: Support estimates a recent low-price area where buyers may have appeared.
3. Calculation logic:
   - Support = rolling minimum of `low` over the chosen period.
4. Required inputs: `low`
5. Typical parameters: `period = 20`

### Resistance

1. Name: Rolling Resistance
2. What it measures: Resistance estimates a recent high-price area where sellers may have appeared.
3. Calculation logic:
   - Resistance = rolling maximum of `high` over the chosen period.
4. Required inputs: `high`
5. Typical parameters: `period = 20`

### Opening Range High

1. Name: Opening Range High
2. What it measures: Opening range high is the highest price during the first candles after market open.
3. Calculation logic:
   - Choose the opening range window, such as first `15` minutes.
   - Opening range high = highest `high` inside that window.
4. Required inputs: `high`
5. Typical parameters: First `15` minutes, or first `15` one-minute candles.

### Opening Range Low

1. Name: Opening Range Low
2. What it measures: Opening range low is the lowest price during the first candles after market open.
3. Calculation logic:
   - Choose the opening range window, such as first `15` minutes.
   - Opening range low = lowest `low` inside that window.
4. Required inputs: `low`
5. Typical parameters: First `15` minutes, or first `15` one-minute candles.

## Code Scaffold

The original code scaffold lived in:

```text
indicators/intraday_indicators.py
```

Main function:

```python
evaluate_indicators(df)
```

It returns a dictionary containing all calculated metric series and opening range levels.
