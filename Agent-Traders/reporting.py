from config import BotConfig


def print_research_report(config: BotConfig, analysis: dict) -> None:
    strategy_result = analysis["strategy_result"]
    research_result = analysis["research_result"]

    print(f"{config.symbol} research")
    print(f"Action: {research_result['action']} ({research_result['conviction']})")
    print(
        f"Price: ${strategy_result['current_price']:.2f} | "
        f"{config.sma_period}-day SMA: ${strategy_result['sma']:.2f}"
    )
    print(
        f"Trend: {strategy_result['price_vs_sma_pct']:.2f}% vs SMA | "
        f"Momentum: {strategy_result['recent_change_pct']:.2f}%"
    )
    print(f"Summary: {research_result['summary']}")


def print_trade_outcome(config: BotConfig, risk_result: dict, trading_mode: str) -> None:
    if not risk_result["approved"]:
        print(f"{config.symbol} trade")
        print("Status: skipped")
        print(f"Reason: {risk_result['message']}")
        return

    if risk_result["message"]:
        print(f"Note: {risk_result['message']}")

    print(f"{config.symbol} trade")
    print(f"Status: submitted ({trading_mode})")
    print(f"Size: {risk_result['quantity']} share(s)")


def print_top_performers_report(top_performers: list[dict]) -> None:
    print("Top 10 performers today")
    if not top_performers:
        print("No qualifying stocks found.")
        return

    for index, stock in enumerate(top_performers, start=1):
        print(
            f"{index:>2}. {stock['symbol']:<6} "
            f"{stock['percent_change']:>6.2f}%  "
            f"${stock['price']:.2f}"
        )
