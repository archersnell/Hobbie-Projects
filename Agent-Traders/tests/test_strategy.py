from strategies.simple_momentum import SimpleMomentumStrategy


def test_simple_momentum_strategy_marks_strong_setup_as_candidate():
    market_data = {
        "current_price": 12.0,
        "daily_percent_change": 4.5,
        "volume": 2_000_000,
        "relative_volume": 2.0,
        "volatility_estimate": 4.0,
        "sma_5": 11.0,
        "sma_20": 10.0,
        "rsi_14": 62.0,
        "momentum": 5.0,
        "bid_ask_spread_percent": 0.2,
    }

    result = SimpleMomentumStrategy().evaluate("TEST", market_data)

    assert result["label"] == "possible buy candidate"
    assert result["score"] >= 6
