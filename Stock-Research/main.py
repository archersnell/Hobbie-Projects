import argparse
from research import analyzer, scanner
from research import portfolio

def main():
    parser = argparse.ArgumentParser(description="Stock Research Tool")
    subparsers = parser.add_subparsers(dest="command")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("ticker")  # what argument does analyze need?

    # scan command
    subparsers.add_parser("scan")  # no arguments needed

    # portfolio command
    portfolio_parser = subparsers.add_parser("portfolio")
    portfolio_parser.add_argument("tickers")  # what argument does portfolio need?

    args = parser.parse_args()

    if args.command == "analyze":
        stock = analyzer.analyse(args.ticker)
        print(f"{stock['symbol']} | Price: {stock['current_price']} | Score: {stock['score']} | {stock['recommendation']}")
    elif args.command == "scan":
        scanner.start()
    elif args.command == "portfolio":
        with open(args.tickers) as f:
            tickers = [line.strip() for line in f.readlines()]
            results = portfolio.research_portfolio(tickers)
            for stock in results:
                print(f"{stock['symbol']} | Price: {stock['current_price']} | Score: {stock['score']} | {stock['recommendation']}")

if __name__ == "__main__":
    main()