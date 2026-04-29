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

    scan_parser = subparsers.add_parser(
        "scan",
        help="Automatically scan top movers and show the best trade setups. Use --execute-paper to submit paper orders.",
    )
    scan_parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="How many symbols to analyze from the selected universe. Default: 25.",
    )
    scan_parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="How many symbols to skip before scanning. Watch mode advances this automatically.",
    )
    scan_parser.add_argument(
        "--universe",
        choices=["movers", "volatile-tech", "custom"],
        default="movers",
        help="Which symbol universe to scan. Default: movers.",
    )
    scan_parser.add_argument(
        "--symbols",
        help="Comma-separated symbols to scan when using --universe custom.",
    )
    scan_parser.add_argument(
        "--candidates",
        type=int,
        default=5,
        help="How many final candidates to show. Default: 5.",
    )
    scan_parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep scanning every 300 seconds until you press Ctrl+C.",
    )
    scan_parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Seconds between scans. Providing this automatically enables watch mode.",
    )
    scan_parser.add_argument(
        "--min-price",
        type=float,
        default=1.0,
        help="Minimum stock price for scan candidates. Default: 1.00.",
    )
    scan_parser.add_argument(
        "--max-price",
        type=float,
        default=10.0,
        help="Maximum stock price for scan candidates. Default: 10.00.",
    )
    scan_parser.add_argument(
        "--min-atr-pct",
        type=float,
        default=3.0,
        help="Minimum ATR as a percent of price. Default: 3.0.",
    )
    scan_parser.add_argument(
        "--min-rvol",
        type=float,
        default=0.75,
        help="Minimum relative volume for scan candidates. Default: 0.75.",
    )
    scan_parser.add_argument(
        "--min-risk-reward",
        type=float,
        default=1.5,
        help="Minimum reward/risk ratio required before paper BUY orders can be submitted. Default: 1.5.",
    )
    scan_parser.add_argument(
        "--min-score-gap",
        type=int,
        default=2,
        help="Minimum gap between BUY and SELL scores before the strategy can signal. Default: 2.",
    )
    scan_parser.add_argument(
        "--allow-range-trades",
        action="store_true",
        help="Allow signals even when price is between support and resistance.",
    )
    scan_parser.add_argument(
        "--max-session-trades",
        type=int,
        default=3,
        help="Maximum candidate trades allowed in one automated session. Default: 3.",
    )
    scan_parser.add_argument(
        "--max-session-value",
        type=float,
        default=1000.0,
        help="Maximum total dollars allowed in one automated session. Default: 1000.",
    )
    scan_parser.add_argument(
        "--execute-paper",
        action="store_true",
        help="Submit paper orders for scan candidates that pass all trade checks.",
    )
    scan_parser.add_argument(
        "--paper-side",
        choices=["buy", "sell", "both"],
        default="buy",
        help="Which paper signals can be executed: buy, sell, or both. Default: buy.",
    )

    return parser
