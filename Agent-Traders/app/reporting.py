from app.config import BotConfig


def is_missing(value) -> bool:
    return value is None or value != value


def format_price(value) -> str:
    if is_missing(value):
        return "n/a"

    return f"${value:.2f}"


def format_number(value, decimals: int = 2) -> str:
    if is_missing(value):
        return "n/a"

    return f"{value:.{decimals}f}"


def format_ratio(value) -> str:
    if is_missing(value):
        return "n/a"

    return f"{value:.2f}:1"


def print_research_report(config: BotConfig, analysis: dict) -> None:
    strategy_result = analysis["strategy_result"]
    research_result = analysis["research_result"]
    score_difference = strategy_result["buy_score"] - strategy_result["sell_score"]

    print(f"{config.symbol} research")
    print(
        f"Signal: {strategy_result['strategy_signal']} "
        f"| Trade: {strategy_result['decision'].upper()} "
        f"({strategy_result['confidence']}) | "
        f"Score: BUY {strategy_result['buy_score']} / SELL {strategy_result['sell_score']} "
        f"(net {score_difference:+})"
    )
    print(
        f"Price: {format_price(strategy_result['current_price'])} | "
        f"VWAP: {format_price(strategy_result['vwap'])} | "
        f"SMA: {format_price(strategy_result['sma'])}"
    )
    print(
        f"Trend: EMA9 {format_price(strategy_result['ema_9'])} / "
        f"EMA20 {format_price(strategy_result['ema_20'])} | "
        f"RSI: {format_number(strategy_result['rsi_14'])}"
    )
    print(
        f"Momentum: MACD {format_number(strategy_result['macd'])} / "
        f"Signal {format_number(strategy_result['macd_signal'])} | "
        f"RVOL: {format_number(strategy_result['relative_volume'])} | "
        f"ATR: {format_number(strategy_result['atr_14'])}"
    )
    print(
        f"Levels: Support {format_price(strategy_result['support'])} | "
        f"Resistance {format_price(strategy_result['resistance'])} | "
        f"OR {format_price(strategy_result['opening_range_low'])}-"
        f"{format_price(strategy_result['opening_range_high'])}"
    )
    print(
        f"Risk: Stop {format_price(strategy_result['stop_loss'])} | "
        f"Target {format_price(strategy_result['take_profit'])} | "
        f"R/R {format_ratio(strategy_result['risk_reward_ratio'])}"
    )
    print(f"Reason: {strategy_result['reason']}")
    print(f"Research: {research_result['action']} ({research_result['conviction']})")


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


def print_scan_report(
    candidates: list[dict],
    scanned_count: int,
    universe: str,
    scan_offset: int,
    next_offset: int,
    session_trades_used: int,
    max_session_trades: int,
    max_session_value: float,
    session_value_used: float,
    min_price: float,
    max_price: float,
    min_atr_pct: float,
    min_rvol: float,
    min_risk_reward: float,
    skipped_counts: dict,
    execute_paper: bool,
    paper_side: str = "buy",
    market_status: dict | None = None,
) -> None:
    print(
        f"Scan complete: {len(candidates)} candidate(s) from "
        f"{scanned_count} symbol(s) in {universe}"
    )
    print(f"Universe slice: offset {scan_offset} -> next {next_offset}")
    print(
        f"Focus: {format_price(min_price)}-{format_price(max_price)} | "
        f"ATR >= {format_number(min_atr_pct)}% | "
        f"RVOL >= {format_number(min_rvol)} | "
        f"R/R >= {format_number(min_risk_reward)}"
    )
    print(
        f"Session limits: {session_trades_used}/{max_session_trades} trades | "
        f"{format_price(session_value_used)}/{format_price(max_session_value)} used"
    )
    print(
        "Execution: "
        + (f"paper {paper_side} orders enabled" if execute_paper else "scan only")
    )
    if market_status:
        print(f"Market: {market_status['message']}")
        if execute_paper and market_status["is_open"] is False:
            print("Execution note: paper orders will not be submitted while the market is closed.")
    skipped_parts = [
        f"hold={skipped_counts.get('hold_signal', 0)}",
        f"focus={skipped_counts.get('outside_focus', 0)}",
    ]
    if execute_paper:
        skipped_parts.append(f"wrong-side={skipped_counts.get('wrong_side', 0)}")
    skipped_parts.extend(
        [
            f"seen={skipped_counts.get('already_seen', 0)}",
            f"value={skipped_counts.get('session_value', 0)}",
        ]
    )
    print("Skipped: " + " | ".join(skipped_parts))

    if not candidates:
        print("No paper-eligible setups found." if execute_paper else "No strong setups found.")
        return

    for index, candidate in enumerate(candidates, start=1):
        strategy_result = candidate["strategy_result"]
        score_difference = strategy_result["buy_score"] - strategy_result["sell_score"]

        print(
            f"{index:>2}. {candidate['symbol']:<6} "
            f"{strategy_result['strategy_signal']:<4} "
            f"trade={strategy_result['decision'].upper():<4} "
            f"score={score_difference:+} "
            f"price={format_price(strategy_result['current_price'])} "
            f"rvol={format_number(strategy_result['relative_volume'])} "
            f"atr={format_number(candidate['atr_pct'])}% "
            f"rr={format_ratio(strategy_result['risk_reward_ratio'])} "
            f"est={format_price(candidate['estimated_trade_value'])} "
            f"qty={candidate['quantity']}"
        )
        if execute_paper:
            print(f"    Execution: {candidate['execution_status']}")
        print(f"    {strategy_result['reason']}")
