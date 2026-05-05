import time

from agents.research_agent import ResearchAgent
from broker.alpaca_client import AlpacaClient
from commands.research import research_symbols
from config import AppConfig


def position_unrealized_plpc(position) -> float:
    """Return unrealized P/L percent from Alpaca's decimal string as a percent."""
    return float(position.unrealized_plpc) * 100


def whole_share_quantity(position) -> int:
    return int(float(position.qty))


def should_sell_position(result: dict, loss_tolerance_pct: float, sell_on_watch: bool) -> tuple[bool, str]:
    metrics = result["metrics"]
    recommendation = result["recommendation"]
    unrealized_plpc = metrics["unrealized_plpc"]
    sell_labels = {"avoid"}

    if sell_on_watch:
        sell_labels.add("watch")

    if unrealized_plpc <= -abs(loss_tolerance_pct):
        return True, f"loss tolerance hit ({unrealized_plpc:.2f}% <= -{abs(loss_tolerance_pct):.2f}%)"

    if recommendation["label"] in sell_labels:
        return True, f"research label is {recommendation['label']}"

    return False, "holding remains within tolerance"


def research_positions(positions: list, client: AlpacaClient, research_agent: ResearchAgent) -> list[dict]:
    symbols = [position.symbol for position in positions]
    results = research_symbols(symbols, client, research_agent)
    position_by_symbol = {position.symbol: position for position in positions}

    for result in results:
        position = position_by_symbol[result["symbol"]]
        result["position"] = position
        result["metrics"]["unrealized_plpc"] = position_unrealized_plpc(position)
        result["metrics"]["quantity"] = whole_share_quantity(position)

    return results


def print_monitor_report(results: list[dict], loss_tolerance_pct: float, sell_on_watch: bool) -> None:
    if not results:
        print("No open paper positions found.")
        return

    print("Position monitor report")
    print(
        f"{'Symbol':<6} {'Qty':>5} {'P/L%':>8} {'Recommendation':<22} "
        f"{'Score':>5} {'Action':<8} Reason"
    )
    print("-" * 96)

    for result in results:
        metrics = result["metrics"]
        recommendation = result["recommendation"]
        should_sell, reason = should_sell_position(
            result=result,
            loss_tolerance_pct=loss_tolerance_pct,
            sell_on_watch=sell_on_watch,
        )
        action = "SELL" if should_sell else "HOLD"
        print(
            f"{result['symbol']:<6} "
            f"{metrics['quantity']:>5} "
            f"{metrics['unrealized_plpc']:>7.2f}% "
            f"{recommendation['label']:<22} "
            f"{recommendation['score']:>5} "
            f"{action:<8} {reason}"
        )


def run_monitor(
    loss_tolerance_pct: float,
    sell_on_watch: bool,
    loop: bool,
    interval_seconds: int,
    config: AppConfig,
) -> None:
    if config.is_live_trading:
        raise ValueError(
            "Live trading is enabled. Automated monitoring sells are blocked. "
            "Set ALPACA_TRADING_MODE=paper before using monitor."
        )
    if loss_tolerance_pct <= 0:
        raise ValueError("--loss-tolerance must be greater than 0.")
    if interval_seconds < 30:
        raise ValueError("--interval must be at least 30 seconds.")

    client = AlpacaClient(config)
    research_agent = ResearchAgent()

    print("Monitor mode: PAPER ONLY")
    print("Open positions will be researched and may be sold based on tolerance rules.")

    try:
        while True:
            positions = client.get_positions()
            results = research_positions(positions, client, research_agent)
            print_monitor_report(results, loss_tolerance_pct, sell_on_watch)

            for result in results:
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
                print(
                    f"SELL submitted in PAPER mode for {result['symbol']} "
                    f"({quantity} share(s)): {reason}. Order ID: {order.id}"
                )

            if not loop:
                return

            print(f"Sleeping {interval_seconds} seconds before next monitor cycle.")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Monitor stopped.")
