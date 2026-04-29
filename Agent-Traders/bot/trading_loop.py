import time

from agents.research_agent import ResearchAgent
from broker.alpaca_client import AlpacaClient
from bot.state import BotState
from commands.auto_buy import calculate_order_quantity, is_buy_candidate
from commands.monitor import print_monitor_report, research_positions, should_sell_position
from commands.research import discover_market_movers, print_ranked_results, research_symbols
from config import AppConfig


def _sell_positions(
    client: AlpacaClient,
    position_results: list[dict],
    loss_tolerance_pct: float,
    sell_on_watch: bool,
    state: BotState,
    max_trades_per_day: int,
) -> set[str]:
    sold_symbols = set()

    for result in position_results:
        if not state.can_trade(max_trades_per_day):
            print("Daily trade limit reached. No more sell orders this cycle.")
            return sold_symbols

        should_sell, reason = should_sell_position(
            result=result,
            loss_tolerance_pct=loss_tolerance_pct,
            sell_on_watch=sell_on_watch,
        )
        if not should_sell:
            continue

        quantity = result["metrics"]["quantity"]
        if quantity < 1:
            print(f"Skipping {result['symbol']}: position is smaller than one whole share.")
            continue

        order = client.place_market_order(
            symbol=result["symbol"],
            quantity=quantity,
            side="sell",
        )
        state.record_trade()
        sold_symbols.add(result["symbol"])
        print(
            f"SELL submitted in PAPER mode for {result['symbol']} "
            f"({quantity} share(s)): {reason}. Order ID: {order.id}"
        )

    return sold_symbols


def current_symbol_quantity(current_positions: dict, symbol: str) -> int:
    position = current_positions.get(symbol)
    if position is None:
        return 0
    return int(float(position.qty))


def _buy_one_candidate(
    client: AlpacaClient,
    research_agent: ResearchAgent,
    current_positions: dict,
    blocked_symbols: set[str],
    market_type: str,
    limit: int,
    candidates: int,
    min_buy_score: int,
    max_symbol_quantity: int,
    config: AppConfig,
    state: BotState,
    max_trades_per_day: int,
) -> bool:
    if not state.can_trade(max_trades_per_day):
        print("Daily trade limit reached. No buy order submitted.")
        return False

    mover_symbols = discover_market_movers(
        client=client,
        market_type=market_type,
        limit=limit,
        top=candidates,
    )
    print()
    print(f"Researching top {len(mover_symbols)} mover(s) for bot buy decision...")
    results = research_symbols(mover_symbols, client, research_agent)
    ranked_results = research_agent.rank_results(results)
    print_ranked_results("Bot buy research report", ranked_results)

    account = client.get_account()
    buying_power = float(account.buying_power)

    for result in ranked_results:
        if not is_buy_candidate(result, min_score=min_buy_score):
            continue

        symbol = result["symbol"]
        if symbol in blocked_symbols:
            print(f"Skipping {symbol}: sold earlier this cycle.")
            continue

        existing_quantity = current_symbol_quantity(current_positions, symbol)
        remaining_quantity = max_symbol_quantity - existing_quantity
        if remaining_quantity < 1:
            print(
                f"Skipping {symbol}: current quantity {existing_quantity} already meets "
                f"the per-symbol cap of {max_symbol_quantity}."
            )
            continue

        current_price = result["metrics"]["current_price"]
        affordable_quantity = calculate_order_quantity(
            current_price=current_price,
            buying_power=buying_power,
            max_trade_value=config.max_trade_value,
        )
        quantity = min(affordable_quantity, remaining_quantity)

        if quantity < 1:
            print(
                f"Skipping {symbol}: price ${current_price:.2f} is above the available "
                f"paper trade value (${min(config.max_trade_value, buying_power):.2f})."
            )
            continue

        order = client.place_market_order(symbol=symbol, quantity=quantity, side="buy")
        state.record_trade()
        print()
        print(f"BUY submitted in PAPER mode for {symbol}")
        print(f"Reason: {result['recommendation']['reason']}")
        print(f"Score: {result['recommendation']['score']}")
        print(f"Quantity: {quantity} share(s)")
        print(f"Estimated value: ${quantity * current_price:.2f}")
        print(f"Order ID: {order.id}")
        return True

    print(f"No buy submitted. No candidate met score >= {min_buy_score}.")
    return False


def run_trading_loop(
    config: AppConfig,
    market_type: str,
    limit: int,
    candidates: int,
    max_symbol_quantity: int,
    max_trades_per_day: int,
    loss_tolerance_pct: float,
    min_buy_score: int,
    interval_seconds: int,
    sell_on_watch: bool,
    once: bool,
) -> None:
    if config.is_live_trading:
        raise ValueError(
            "Live trading is enabled. The continuous bot is blocked. "
            "Set ALPACA_TRADING_MODE=paper before using run-bot."
        )
    if interval_seconds < 30:
        raise ValueError("--interval must be at least 30 seconds.")
    if max_symbol_quantity < 1:
        raise ValueError("--max-symbol-quantity must be at least 1.")
    if max_trades_per_day < 1:
        raise ValueError("--max-trades-per-day must be at least 1.")
    if candidates < 1:
        raise ValueError("--candidates must be at least 1.")
    if loss_tolerance_pct <= 0:
        raise ValueError("--loss-tolerance must be greater than 0.")
    if min_buy_score < 1:
        raise ValueError("--min-score must be at least 1.")

    client = AlpacaClient(config)
    research_agent = ResearchAgent()
    state = BotState()

    print("Trading loop: PAPER ONLY")
    print("Each cycle monitors current holdings, sells weak positions, then buys at most one candidate if it passes caps.")

    try:
        while True:
            state.reset_if_new_day()
            print()
            print(
                f"Cycle start | trades today {state.trades_today}/{max_trades_per_day} | "
                f"max quantity per symbol {max_symbol_quantity}"
            )

            positions = client.get_positions()
            position_results = research_positions(positions, client, research_agent)
            print_monitor_report(position_results, loss_tolerance_pct, sell_on_watch)
            sold_symbols = _sell_positions(
                client=client,
                position_results=position_results,
                loss_tolerance_pct=loss_tolerance_pct,
                sell_on_watch=sell_on_watch,
                state=state,
                max_trades_per_day=max_trades_per_day,
            )

            current_positions = {
                position.symbol: position
                for position in client.get_positions()
            }

            if state.can_trade(max_trades_per_day):
                _buy_one_candidate(
                    client=client,
                    research_agent=research_agent,
                    current_positions=current_positions,
                    blocked_symbols=sold_symbols,
                    market_type=market_type,
                    limit=limit,
                    candidates=candidates,
                    min_buy_score=min_buy_score,
                    max_symbol_quantity=max_symbol_quantity,
                    config=config,
                    state=state,
                    max_trades_per_day=max_trades_per_day,
                )
            else:
                print("Buy step skipped: daily trade limit reached.")

            if once:
                print("Run-bot completed one cycle.")
                return

            print(f"Sleeping {interval_seconds} seconds before next bot cycle.")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Trading loop stopped.")
