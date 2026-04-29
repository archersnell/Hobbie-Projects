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
MAX_SYMBOL_QUANTITY=3
MAX_TRADES_PER_DAY=5
LOSS_TOLERANCE_PCT=5
MIN_BUY_SCORE=6
BOT_INTERVAL_SECONDS=300
```

## CLI Commands

Start here to see the available commands:

```powershell
python main.py --help
python main.py buy --help
python main.py sell --help
python main.py research --help
python main.py auto-buy --help
python main.py monitor --help
python main.py run-bot --help
```

Base command format:

```powershell
python main.py buy SYMBOL
python main.py sell SYMBOL
python main.py research SYMBOL
python main.py research SYMBOL SYMBOL SYMBOL
python main.py research --market all --limit # --top #
python main.py auto-buy --market all --limit # --candidates # --min-score #
python main.py monitor --loss-tolerance #
python main.py run-bot --market all --interval #
```

## Project Structure

```text
Agent-Traders/
|-- main.py
|-- cli.py
|-- config.py
|-- broker/
|   `-- alpaca_client.py
|-- bot/
|   |-- state.py
|   `-- trading_loop.py
|-- commands/
|   |-- auto_buy.py
|   |-- buy.py
|   |-- monitor.py
|   |-- run_bot.py
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
|   |-- test_auto_buy.py
|   |-- test_bot_state.py
|   |-- test_market_discovery.py
|   |-- test_market_data.py
|   |-- test_monitor.py
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

## Auto Buy

The `auto-buy` command is paper-only. It searches market movers, researches the strongest daily movers, prints the research report, and submits at most one paper buy order when it finds a `possible buy candidate` at or above `--min-score`.

Example:

```powershell
python main.py auto-buy --market all --limit 500 --candidates 10 --min-score 6
```

Safety rules:

- Live trading is blocked.
- Only one paper order can be submitted per run.
- Order size is capped by `MAX_TRADE_VALUE`.
- If no candidate meets the score threshold, no order is placed.

## Position Monitor

The `monitor` command is paper-only. It researches your open paper positions and submits sell orders when either:

- unrealized loss is at or below `--loss-tolerance`
- research says `avoid`

Run one monitor cycle:

```powershell
python main.py monitor --loss-tolerance 5
```

Keep monitoring every 5 minutes:

```powershell
python main.py monitor --loss-tolerance 5 --loop --interval 300
```

More aggressive mode, where `watch` also exits:

```powershell
python main.py monitor --loss-tolerance 5 --sell-on-watch
```

## Continuous Bot

The `run-bot` command is the first continuous paper-trading milestone. It loops forever unless you pass `--once` or stop it with `Ctrl+C`.

Each cycle:

1. Reads current paper positions.
2. Researches holdings and sells weak/risky positions.
3. Checks per-symbol quantity and daily trade limits.
4. Searches market movers.
5. Researches the strongest movers.
6. Buys at most one paper order if a candidate qualifies and that symbol is below its quantity cap.
7. Sleeps until the next cycle.

Run one test cycle:

```powershell
python main.py run-bot --once
```

Run continuously every 5 minutes:

```powershell
python main.py run-bot --market all --interval 300
```

Conservative example:

```powershell
python main.py run-bot --market all --limit 500 --candidates 10 --max-symbol-quantity 3 --max-trades-per-day 5 --loss-tolerance 5 --min-score 6 --interval 300
```

The same values can be controlled from `.env`:

```env
MAX_SYMBOL_QUANTITY=3
MAX_TRADES_PER_DAY=5
LOSS_TOLERANCE_PCT=5
MIN_BUY_SCORE=6
BOT_INTERVAL_SECONDS=300
```

`MAX_SYMBOL_QUANTITY` is not a limit on how many different stocks the bot can hold. It is the maximum whole-share quantity allowed for each individual symbol. For example, if `MAX_SYMBOL_QUANTITY=3` and you already hold 3 shares of `AAPL`, the bot can still buy `MSFT`, but it will not add more `AAPL`.

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
