from data.market_data import calculate_metrics, calculate_rsi, normalize_symbol


def make_bars(count: int = 25) -> list[dict]:
    bars = []
    for index in range(count):
        close = 100 + index
        bars.append(
            {
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1_000_000 + (index * 10_000),
            }
        )
    return bars


def test_normalize_symbol_accepts_common_tickers():
    assert normalize_symbol(" aapl ") == "AAPL"
    assert normalize_symbol("brk.b") == "BRK.B"


def test_calculate_rsi_returns_bounded_value():
    rsi = calculate_rsi([100, 101, 100, 102, 103, 102, 104, 105, 106, 104, 105, 107, 108, 109, 110])

    assert 0 <= rsi <= 100


def test_calculate_metrics_includes_research_fields():
    metrics = calculate_metrics(
        price=126,
        bars=make_bars(),
        quote={"bid_price": 125.95, "ask_price": 126.05},
    )

    assert metrics["current_price"] == 126
    assert metrics["volume"] > 0
    assert metrics["sma_5"] > metrics["sma_20"]
    assert metrics["bid_ask_spread_percent"] > 0
