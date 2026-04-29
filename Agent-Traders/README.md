# Alpaca Trading Bot

This project is a beginner-friendly trading bot built with `alpaca-py`. It connects to Alpaca, reads your account, evaluates stock indicators, scores the setup, and places a paper trade only when the strategy and risk checks allow it.

The code is also organized so you can grow it into a multi-agent trading system later. Each agent has one job:

- `news_agent` prepares market context
- `research_agent` turns signals into plain-English trade ideas
- `strategy_agent` decides whether to buy
- `risk_agent` checks whether the trade is safe enough to place
- `execution_agent` sends the order to Alpaca

## Project Structure

```text
Agent-Traders/
|-- app/
|   |-- cli.py
|   |-- config.py
|   |-- reporting.py
|   `-- workflows.py
|-- agents/
|   |-- __init__.py
|   |-- execution_agent.py
|   |-- news_agent.py
|   |-- research_agent.py
|   |-- risk_agent.py
|   |-- strategy_metrics.py
|   `-- strategy_agent.py
|-- brokers/
|   `-- alpaca_clients.py
|-- docs/
|   `-- DAY_TRADING_EVALUATOR_PLAN.md
|-- indicators/
|   `-- intraday_indicators.py
|-- strategies/
|   `-- scoring_strategy.py
|-- data/
|   `-- trading_bot.log
|-- .env
|-- main.py
|-- README.md
`-- requirements.txt
```

## What the Bot Does

1. Loads your Alpaca API keys from `.env`
2. Connects to Alpaca using `TradingClient`
3. Fetches account information
4. Fetches the latest stock price for `AAPL` by default
5. Calculates stock metrics and intraday-style indicators
6. Scores the setup with strategy rules
7. Builds a research summary with trend and momentum context
8. Runs risk checks before execution
9. Limits each trade to a maximum dollar amount
10. Prevents more than one trade per run

## Setup

1. Open the `.env` file
2. Add your Alpaca paper trading API key and secret key:

```env
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
```

3. Make sure your virtual environment is activated
4. Run research only:

```powershell
python main.py research
```

Without a symbol, this now shows the top 10 performing tradable US stocks of the day.

If your virtual environment is not already active on Windows:

```powershell
.\.venv\Scripts\activate
python main.py research
```

5. Run the trading workflow when you want the bot to be allowed to place a trade:

```powershell
python main.py trade
```

You can also override the default symbol from `.env` on the command line:

```powershell
python main.py research --symbol MSFT
python main.py trade --symbol NVDA
python main.py research SPY
python main.py trade TSLA
```

## Paper Trading vs Live Trading

This bot starts in paper mode by default:

```env
ALPACA_PAPER=true
```

To switch to live trading:

1. Replace your paper API keys with your live Alpaca keys
2. Change this line in `.env`:

```env
ALPACA_PAPER=false
```

Be careful with live trading. Real money will be at risk once you switch.

## Config Options

You can change these values in `.env`:

```env
MAX_TRADE_VALUE=500
SMA_PERIOD=20
ALPACA_DATA_FEED=iex
```

## Research Agent

The `research_agent` is an advisor, not an execution engine. It looks at:

- current price
- simple moving average
- percent difference between price and SMA
- recent price change
- news sentiment from `news_agent`

Then it returns a beginner-friendly opinion like:

- `research for a possible buy`
- `keep on watch`
- `wait`

This makes it a good place to add symbol ranking, AI summaries, or LLM-based trade notes later.

## CLI Commands

Use separate commands depending on what you want to do:

- `python main.py research`
  Shows the top 10 performing tradable US stocks of the day.

- `python main.py scan`
  Automatically scans top movers and shows the best trade setups. No trades are placed.
- `python main.py scan --watch --interval 300`
  Keeps scanning every 5 minutes until you press `Ctrl+C`.
- `python main.py scan --max-price 10 --min-atr-pct 3 --max-session-trades 3 --max-session-value 1000`
  Focuses on low-priced volatile stocks and caps the automated session.
- `python main.py trade`
  Runs research, checks risk rules, and places a trade only if the setup is approved.
  This command requires a symbol from the CLI.
- `python main.py research --symbol TSLA`
  Runs research for a different symbol without changing `.env`.
- `python main.py trade --symbol AMZN`
  Trades a different symbol without changing `.env`.
- `python main.py research SPY`
  Same as `--symbol SPY`, but faster to type.
- `python main.py trade QQQ`
  Same as `--symbol QQQ`, but faster to type.

## Scan Options

The `scan` command looks for low-priced, volatile trade setups without placing trades.

```powershell
python main.py scan [options]
```

The scan report also checks Alpaca's market clock. Intraday indicators are most reliable during regular market hours. If `--execute-paper` is enabled while the market is closed, the bot will show matching setups but will not submit paper orders.

Available scan options:

| Option | Default | What it does |
| --- | ---: | --- |
| `--limit` | `25` | Number of symbols to analyze from the selected universe. |
| `--offset` | `0` | Number of symbols to skip before scanning. Watch mode advances this when no candidates are found. |
| `--universe` | `movers` | Symbol source to scan: `movers`, `volatile-tech`, or `custom`. |
| `--symbols` | none | Comma-separated symbols to scan when using `--universe custom`. |
| `--candidates` | `5` | Number of final scan candidates to print. |
| `--watch` | off | Keeps scanning repeatedly until you press `Ctrl+C` or a session limit is reached. |
| `--interval` | `300` in watch mode | Seconds between scans. Providing this automatically enables watch mode. Minimum is `30`. |
| `--min-price` | `1.00` | Lowest stock price allowed in scan results. |
| `--max-price` | `10.00` | Highest stock price allowed in scan results. |
| `--min-atr-pct` | `3.0` | Minimum ATR as a percent of price. Higher means more volatile stocks. |
| `--min-rvol` | `0.75` | Minimum relative volume. Higher means more active stocks. |
| `--min-risk-reward` | `1.5` | Minimum reward/risk ratio required before a paper BUY order can be submitted. Lower values make the bot less strict. |
| `--min-score-gap` | `2` | Minimum gap between BUY and SELL scores before the strategy can signal. Use `1` for a more aggressive paper scan. |
| `--allow-range-trades` | off | Allows signals even when price is between support and resistance. Useful for testing, but riskier. |
| `--max-session-trades` | `3` | Maximum number of candidate trades allowed during one automated scan session. |
| `--max-session-value` | `1000.00` | Maximum total estimated dollars allowed during one automated scan session. |
| `--execute-paper` | off | Submits paper orders for scan candidates that pass all trade checks. Requires `ALPACA_PAPER=true`. |
| `--paper-side` | `buy` | Which paper signals can execute: `buy`, `sell`, or `both`. SELL paper orders may open short positions. |

Example low-price volatility scan:

```powershell
python main.py scan --min-price 1 --max-price 10 --min-atr-pct 3 --min-rvol 0.75
```

Example volatile tech universe scan:

```powershell
python main.py scan --universe volatile-tech --max-price 50 --min-atr-pct 3
```

Example scan starting deeper in the universe:

```powershell
python main.py scan --universe volatile-tech --offset 25 --limit 25 --max-price 50
```

Example custom symbol scan:

```powershell
python main.py scan --universe custom --symbols NVDA,AMD,SOXL,TQQQ,PLTR
```

Example watch session with trade and dollar caps:

```powershell
python main.py scan --watch --interval 300 --max-session-trades 3 --max-session-value 1000
```

Example paper auto-trading session:

```powershell
python main.py scan --execute-paper --interval 30 --max-price 10 --min-atr-pct 3 --max-session-trades 3 --max-session-value 1000
```

Example paper session that can execute bearish setups too:

```powershell
python main.py scan --execute-paper --paper-side both --universe volatile-tech --interval 30 --max-price 50 --min-atr-pct 1.5 --min-rvol 0.5 --min-risk-reward 1.0 --min-score-gap 1 --allow-range-trades --max-session-trades 5 --max-session-value 1000
```

Less strict paper scan for testing:

```powershell
python main.py scan --execute-paper --universe volatile-tech --interval 30 --max-price 50 --min-atr-pct 1.5 --min-rvol 0.5 --min-risk-reward 1.0 --min-score-gap 1 --allow-range-trades --max-session-trades 5 --max-session-value 1000
```

## Future AI Agent Ideas

This project is already structured for future upgrades:

- Upgrade `agents/research_agent.py` to compare multiple symbols and rank opportunities
- Add real headline or sentiment data inside `agents/news_agent.py`
- Improve the scoring logic inside `strategies/scoring_strategy.py`
- Add more indicators inside `indicators/intraday_indicators.py`
- Add stricter portfolio controls in `agents/risk_agent.py`
- Add smarter order handling in `agents/execution_agent.py`

## Logs

Each run writes logs to:

```text
data/trading_bot.log
```
