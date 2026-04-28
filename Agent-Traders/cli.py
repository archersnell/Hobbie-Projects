import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run research or trade workflows for the Alpaca trading bot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research_parser = subparsers.add_parser(
        "research",
        help="Run market research only. No trades will be placed.",
    )
    research_parser.add_argument(
        "--symbol",
        help="Optional stock symbol override, such as AAPL or MSFT.",
    )
    research_parser.add_argument(
        "symbol_arg",
        nargs="?",
        help="Optional stock symbol override as a positional value, such as AAPL or MSFT.",
    )

    trade_parser = subparsers.add_parser(
        "trade",
        help="Run research, risk checks, and place a trade if approved.",
    )
    trade_parser.add_argument(
        "--symbol",
        help="Optional stock symbol override, such as AAPL or MSFT.",
    )
    trade_parser.add_argument(
        "symbol_arg",
        nargs="?",
        help="Optional stock symbol override as a positional value, such as AAPL or MSFT.",
    )

    return parser
