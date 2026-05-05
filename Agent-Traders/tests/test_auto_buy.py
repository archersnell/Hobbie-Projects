from commands.auto_buy import calculate_order_quantity, find_buy_candidate, is_buy_candidate


def test_find_buy_candidate_returns_first_candidate_at_min_score():
    results = [
        {
            "symbol": "AAA",
            "recommendation": {
                "label": "watch",
                "score": 5,
            },
        },
        {
            "symbol": "BBB",
            "recommendation": {
                "label": "possible buy candidate",
                "score": 7,
            },
        },
    ]

    assert find_buy_candidate(results, min_score=6)["symbol"] == "BBB"


def test_find_buy_candidate_returns_none_when_score_is_too_low():
    results = [
        {
            "symbol": "AAA",
            "recommendation": {
                "label": "possible buy candidate",
                "score": 5,
            },
        },
    ]

    assert find_buy_candidate(results, min_score=6) is None


def test_calculate_order_quantity_uses_smaller_of_buying_power_and_trade_limit():
    assert calculate_order_quantity(
        current_price=25,
        buying_power=1_000,
        max_trade_value=120,
    ) == 4


def test_is_buy_candidate_checks_label_and_score():
    assert is_buy_candidate(
        {
            "recommendation": {
                "label": "possible buy candidate",
                "score": 6,
            },
        },
        min_score=6,
    )
    assert not is_buy_candidate(
        {
            "recommendation": {
                "label": "watch",
                "score": 9,
            },
        },
        min_score=6,
    )
