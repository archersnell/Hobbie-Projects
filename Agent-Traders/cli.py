import argparse

from commands.auto_buy import run_auto_buy
from commands.buy import run_buy
from commands.monitor import run_monitor
from commands.research import run_research
from commands.run_bot import run_bot_command
from commands.sell import run_sell
from config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simple Alpaca paper-trading helper for volatile stocks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    buy_parser = subparsers.add_parser("buy", help="Buy one symbol using a safe paper order.")
    buy_parser.add_argument("symbol", help="Ticker symbol, such as AAPL or TSLA.")

    sell_parser = subparsers.add_parser("sell", help="Sell your current position in one symbol.")
    sell_parser.add_argument("symbol", help="Ticker symbol, such as AAPL or TSLA.")

    research_parser = subparsers.add_parser(
        "research",
        help="Research symbols or search a market type for daily movers.",
    )
    research_parser.add_argument(
        "symbols",
        nargs="*",
        help="Optional ticker symbols, such as AAPL TSLA NVDA.",
    )
    research_parser.add_argument(
        "--market",
        choices=["stocks", "etfs", "all"],
        default="stocks",
        help="Market type to search when no symbols are provided. Default: stocks.",
    )
    research_parser.add_argument(
        "--limit",
        type=int,
        default=250,
        help="Maximum discovered assets to snapshot before ranking. Default: 250.",
    )
    research_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of researched movers to show. Default: 5.",
    )

    auto_buy_parser = subparsers.add_parser(
        "auto-buy",
        help="Search market movers and place one paper buy order if a strong candidate is found.",
    )
    auto_buy_parser.add_argument(
        "--market",
        choices=["stocks", "etfs", "all"],
        default="all",
        help="Market type to search. Default: all.",
    )
    auto_buy_parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum discovered assets to snapshot before ranking. Default: 500.",
    )
    auto_buy_parser.add_argument(
        "--candidates",
        type=int,
        default=10,
        help="Number of daily movers to fully research before choosing. Default: 10.",
    )
    auto_buy_parser.add_argument(
        "--min-score",
        type=int,
        default=6,
        help="Minimum strategy score required before buying. Default: 6.",
    )

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Research open paper positions and sell when risk rules say to exit.",
    )
    monitor_parser.add_argument(
        "--loss-tolerance",
        type=float,
        default=5.0,
        help="Sell when unrealized loss reaches this percent. Default: 5.0.",
    )
    monitor_parser.add_argument(
        "--sell-on-watch",
        action="store_true",
        help="Sell when research says WATCH as well as AVOID. Default only sells AVOID.",
    )
    monitor_parser.add_argument(
        "--loop",
        action="store_true",
        help="Keep monitoring until Ctrl+C. Default runs once.",
    )
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between monitor cycles when --loop is used. Default: 300.",
    )

    run_bot_parser = subparsers.add_parser(
        "run-bot",
        help="Continuously monitor holdings and buy one researched candidate when symbol caps allow.",
    )
    run_bot_parser.add_argument(
        "--market",
        choices=["stocks", "etfs", "all"],
        default="all",
        help="Market type to search for new buys. Default: all.",
    )
    run_bot_parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum discovered assets to snapshot before ranking. Default: 500.",
    )
    run_bot_parser.add_argument(
        "--candidates",
        type=int,
        default=10,
        help="Number of daily movers to fully research before choosing. Default: 10.",
    )
    run_bot_parser.add_argument(
        "--max-symbol-quantity",
        "--max-open-positions",
        type=int,
        default=None,
        dest="max_symbol_quantity",
        help="Maximum whole shares allowed per symbol. Defaults to MAX_SYMBOL_QUANTITY.",
    )
    run_bot_parser.add_argument(
        "--max-trades-per-day",
        type=int,
        default=None,
        help="Maximum buy/sell orders per day. Defaults to MAX_TRADES_PER_DAY.",
    )
    run_bot_parser.add_argument(
        "--loss-tolerance",
        type=float,
        default=None,
        help="Sell when unrealized loss reaches this percent. Defaults to LOSS_TOLERANCE_PCT.",
    )
    run_bot_parser.add_argument(
        "--min-score",
        type=int,
        default=None,
        help="Minimum strategy score required before buying. Defaults to MIN_BUY_SCORE.",
    )
    run_bot_parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Seconds between cycles. Defaults to BOT_INTERVAL_SECONDS.",
    )
    run_bot_parser.add_argument(
        "--sell-on-watch",
        action="store_true",
        help="Sell when research says WATCH as well as AVOID.",
    )
    run_bot_parser.add_argument(
        "--once",
        action="store_true",
        help="Run one bot cycle and exit. Useful for testing.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    try:
        if args.command == "buy":
            run_buy(args.symbol, config)
        elif args.command == "sell":
            run_sell(args.symbol, config)
        elif args.command == "research":
            run_research(
                symbols=args.symbols,
                market_type=args.market,
                limit=args.limit,
                top=args.top,
                config=config,
            )
        elif args.command == "auto-buy":
            run_auto_buy(
                market_type=args.market,
                limit=args.limit,
                candidates=args.candidates,
                min_score=args.min_score,
                config=config,
            )
        elif args.command == "monitor":
            run_monitor(
                loss_tolerance_pct=args.loss_tolerance,
                sell_on_watch=args.sell_on_watch,
                loop=args.loop,
                interval_seconds=args.interval,
                config=config,
            )
        elif args.command == "run-bot":
            run_bot_command(
                market_type=args.market,
                limit=args.limit,
                candidates=args.candidates,
                max_symbol_quantity=args.max_symbol_quantity,
                max_trades_per_day=args.max_trades_per_day,
                loss_tolerance_pct=args.loss_tolerance,
                min_buy_score=args.min_score,
                interval_seconds=args.interval,
                sell_on_watch=args.sell_on_watch,
                once=args.once,
                config=config,
            )
    except ValueError as error:
        print(f"Error: {error}")
