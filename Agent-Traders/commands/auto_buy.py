from agents.research_agent import ResearchAgent
from broker.alpaca_client import AlpacaClient
from commands.research import (
    discover_market_movers,
    print_ranked_results,
    research_symbols,
)
from config import AppConfig


def find_buy_candidate(results: list[dict], min_score: int) -> dict | None:
    for result in results:
        recommendation = result["recommendation"]
        if (
            recommendation["label"] == "possible buy candidate"
            and recommendation["score"] >= min_score
        ):
            return result
    return None


def is_buy_candidate(result: dict, min_score: int) -> bool:
    recommendation = result["recommendation"]
    return (
        recommendation["label"] == "possible buy candidate"
        and recommendation["score"] >= min_score
    )


def calculate_order_quantity(current_price: float, buying_power: float, max_trade_value: float) -> int:
    trade_value = min(max_trade_value, buying_power)
    return int(trade_value // current_price)


def run_auto_buy(
    market_type: str,
    limit: int,
    candidates: int,
    min_score: int,
    config: AppConfig,
) -> None:
    if config.is_live_trading:
        raise ValueError(
            "Live trading is enabled. Automated buying is blocked. "
            "Set ALPACA_TRADING_MODE=paper before using auto-buy."
        )
    if candidates < 1:
        raise ValueError("--candidates must be at least 1.")
    if min_score < 1:
        raise ValueError("--min-score must be at least 1.")

    client = AlpacaClient(config)
    research_agent = ResearchAgent()

    print("Auto-buy mode: PAPER ONLY")
    print("Searching market movers, researching candidates, then placing at most one paper buy order.")

    mover_symbols = discover_market_movers(
        client=client,
        market_type=market_type,
        limit=limit,
        top=candidates,
    )
    print()
    print(f"Researching top {len(mover_symbols)} mover(s)...")
    results = research_symbols(mover_symbols, client, research_agent)
    ranked_results = research_agent.rank_results(results)
    print_ranked_results("Auto-buy research report", ranked_results)

    account = client.get_account()
    buying_power = float(account.buying_power)

    for candidate in ranked_results:
        if not is_buy_candidate(candidate, min_score=min_score):
            continue

        symbol = candidate["symbol"]
        if client.get_position(symbol) is not None:
            print(f"Skipping {symbol}: paper position already exists.")
            continue

        metrics = candidate["metrics"]
        recommendation = candidate["recommendation"]
        current_price = metrics["current_price"]
        quantity = calculate_order_quantity(
            current_price=current_price,
            buying_power=buying_power,
            max_trade_value=config.max_trade_value,
        )

        if quantity < 1:
            print(
                f"Skipping {symbol}: price ${current_price:.2f} is above the available "
                f"paper trade value (${min(config.max_trade_value, buying_power):.2f})."
            )
            continue

        order = client.place_market_order(symbol=symbol, quantity=quantity, side="buy")

        print()
        print(f"BUY submitted in PAPER mode for {symbol}")
        print(f"Reason: {recommendation['reason']}")
        print(f"Score: {recommendation['score']}")
        print(f"Quantity: {quantity} share(s)")
        print(f"Estimated value: ${quantity * current_price:.2f}")
        print(f"Order ID: {order.id}")
        return

    print()
    print(
        f"No paper order submitted. No researched candidate met score >= {min_score}, "
        "was affordable, and was not already held."
    )
