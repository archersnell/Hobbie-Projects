# Refactor Report

## Current Project Structure

Before the cleanup, the project had a working Alpaca bot split across `app/`, `agents/`, `brokers/`, `indicators/`, and `strategies/`. The entry point was `main.py`, which delegated to `app.cli` and `app.workflows`.

The repo also contained generated files such as `__pycache__/` folders and `data/trading_bot.log`. Those are runtime artifacts and are not part of the core source code.

After the refactor, the active source tree is:

```text
main.py                  # tiny entry point
cli.py                   # command-line parsing only
config.py                # environment variables and settings
broker/alpaca_client.py  # Alpaca SDK wrapper
commands/                # buy, sell, research command logic
agents/                  # simple research agent
strategies/              # strategy interface and simple momentum rules
data/market_data.py      # market data metrics
tests/                   # lightweight unit tests
```

## Existing Trading Functionality

The original version could:

- Load Alpaca credentials from environment variables.
- Connect to Alpaca trading and market data clients.
- Validate stock symbols through Alpaca.
- Research a symbol with price, SMA, VWAP, EMA, RSI, MACD, relative volume, ATR, support, and resistance metrics.
- Scan a universe of symbols for volatile setups.
- Submit paper orders from scan or trade workflows.
- Apply risk checks such as max trade value and one trade per run.

## Overly Complex Parts

The main complexity came from the large `app.workflows` file and the multi-agent chain. The old flow combined CLI behavior, scanning, research, risk checks, order execution, watch mode, session limits, and reporting in one place.

That made the project harder to study as a college hobby project because there were many knobs before the basic loop was clear:

1. Read config.
2. Fetch market data.
3. Evaluate a simple strategy.
4. Buy or sell safely through Alpaca.

## Keep, Simplify, Remove, Rewrite

Keep:

- Alpaca integration.
- Environment-variable based secrets.
- Symbol validation.
- Simple technical metrics like percent change, volume, relative volume, volatility, SMA, RSI, momentum, and bid/ask spread.
- A strategy interface for future ML.

Simplify:

- CLI commands are now only `buy`, `sell`, and `research`.
- Research scans a small configurable watchlist instead of the full active market.
- Strategy logic is a simple score with beginner-readable reasons.
- Order sizing uses `MAX_TRADE_VALUE`.

Removed or isolated:

- The old `app/` workflow package was removed.
- The old `brokers/` package was replaced by `broker/alpaca_client.py`.
- The advanced indicator module was removed from the active beginner path.
- The old execution, risk, news, and strategy agent files were removed from the active source tree.
- Generated `__pycache__/` folders and logs are now ignored by `.gitignore`.

Rewrite:

- `main.py` and `cli.py` now form the simple command entry point.
- `broker/alpaca_client.py` wraps Alpaca SDK calls.
- `commands/` contains one file per CLI action.
- `data/market_data.py` contains readable metric helpers.
- `strategies/base.py` and `strategies/simple_momentum.py` provide a small future-proof strategy shape.
- `agents/research_agent.py` now has one job: turn market data into research results.
