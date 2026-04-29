import argparse

from commands.buy import run_buy
from commands.research import run_research
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
    except ValueError as error:
        print(f"Error: {error}")
