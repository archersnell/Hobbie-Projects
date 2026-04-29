# Agent Traders

A beginner-friendly Alpaca paper-trading helper for researching volatile stocks and placing simple paper buy/sell orders.

This project is intentionally small. It is meant to be easy to read, easy to run from VS Code, and easy to extend later with better strategies or machine learning.

## Safety First

The default mode is paper trading:

```env
ALPACA_TRADING_MODE=paper
```

The CLI blocks live buy and sell orders by default. Do not add live trading until you understand the code, Alpaca order behavior, and the financial risk.

Never hardcode API keys. Put them in `.env`, which should stay private.

## Setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create your local `.env` file from `.env.example` and add your Alpaca paper keys:

```env
ALPACA_API_KEY=your_paper_key_here
ALPACA_SECRET_KEY=your_paper_secret_here
ALPACA_TRADING_MODE=paper
ALPACA_DATA_FEED=iex
MAX_TRADE_VALUE=100
```

## CLI Commands

Start here to see the available commands:

```powershell
python main.py --help
python main.py buy --help
python main.py sell --help
python main.py research --help
```

Base command format:

```powershell
python main.py buy SYMBOL
python main.py sell SYMBOL
python main.py research SYMBOL
python main.py research SYMBOL SYMBOL SYMBOL
python main.py research --market stocks
python main.py research --market etfs
python main.py research --market all --limit # --top #
```

## Project Structure

```text
Agent-Traders/
|-- main.py
|-- cli.py
|-- config.py
|-- broker/
|   `-- alpaca_client.py
|-- commands/
|   |-- buy.py
|   |-- sell.py
|   `-- research.py
|-- agents/
|   `-- research_agent.py
|-- strategies/
|   |-- base.py
|   `-- simple_momentum.py
|-- data/
|   |-- market_data.py
|   `-- market_discovery.py
|-- tests/
|   |-- test_market_discovery.py
|   |-- test_market_data.py
|   `-- test_strategy.py
|-- docs/
|   `-- REFACTOR_REPORT.md
|-- .env.example
|-- requirements.txt
`-- README.md
```

## How Research Works

The research command can work in two ways:

- If you provide symbols, it researches those exact symbols.
- If you provide `--market stocks`, `--market etfs`, or `--market all`, it discovers active tradable Alpaca assets in that market type, ranks them by daily percent move, and researches the top movers.

For each researched symbol, it fetches daily bars, latest trade price, and latest quote data from Alpaca. It calculates:

- current price
- daily percent change
- volume
- relative volume
- volatility estimate
- 5-day and 20-day simple moving averages
- RSI 14
- recent momentum
- bid/ask spread

The default strategy returns:

- `possible buy candidate`
- `watch`
- `avoid`

This is not financial advice. It is a learning tool for organizing market data and practicing safe paper trading.

## Market Search

The market search mode uses Alpaca assets and snapshots instead of a fixed symbol list.

Examples:

```powershell
python main.py research --market stocks
python main.py research --market etfs
python main.py research --market all --limit 500 --top 10
```

The ETF filter uses Alpaca asset names to identify funds, trusts, and ETF-style products. Leveraged and inverse ETFs can move fast and decay over time, so treat this as research only unless you are paper trading.

## Future ML Hook

Strategies use this interface:

```python
class Strategy:
    def evaluate(self, symbol: str, market_data: dict) -> dict:
        ...
```

Later, you can add a machine learning strategy by creating another class with the same `evaluate` method and swapping it into `ResearchAgent`.

Good future upgrades:

- Save research snapshots to CSV for model training.
- Add a trained model that predicts next-day or intraday movement.
- Blend model confidence with the simple momentum score.
- Add stricter risk rules before enabling any live behavior.

## Tests

Run the lightweight unit tests with:

```powershell
python -m pytest
```
