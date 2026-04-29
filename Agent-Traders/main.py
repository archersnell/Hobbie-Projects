from app.cli import build_parser
from app.config import load_config, setup_logging
from app.workflows import run_research, run_scan, run_trade


def main() -> None:
    try:
        parser = build_parser()
        args = parser.parse_args()
        symbol_override = getattr(args, "symbol", None) or getattr(args, "symbol_arg", None)

        if args.command == "trade":
            config = load_config(symbol_override=symbol_override, allow_env_symbol=False)
        else:
            config = load_config(symbol_override=symbol_override)

        setup_logging(config.log_file)

        if args.command == "research":
            run_research(config, symbol_override=symbol_override)
        elif args.command == "scan":
            watch = args.watch or args.interval is not None
            run_scan(
                config=config,
                scan_limit=args.limit,
                scan_offset=args.offset,
                universe=args.universe,
                symbols=args.symbols,
                candidate_count=args.candidates,
                watch=watch,
                interval_seconds=args.interval or 300,
                min_price=args.min_price,
                max_price=args.max_price,
                min_atr_pct=args.min_atr_pct,
                min_rvol=args.min_rvol,
                min_risk_reward=args.min_risk_reward,
                min_score_gap=args.min_score_gap,
                allow_range_trades=args.allow_range_trades,
                max_session_trades=args.max_session_trades,
                max_session_value=args.max_session_value,
                execute_paper=args.execute_paper,
                paper_side=args.paper_side,
            )
        elif args.command == "trade":
            run_trade(config)
    except ValueError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
