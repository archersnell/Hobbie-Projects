from cli import build_parser
from config import load_config, setup_logging
from workflows import run_research, run_trade


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
        elif args.command == "trade":
            run_trade(config)
    except ValueError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
