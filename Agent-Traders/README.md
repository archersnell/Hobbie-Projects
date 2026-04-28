# Alpaca Trading Bot

This project is a beginner-friendly trading bot built with `alpaca-py`. It connects to Alpaca, reads your account, checks the current price of a stock, compares it to a simple moving average, and places a paper trade when the strategy says to buy.

The code is also organized so you can grow it into a multi-agent trading system later. Each agent has one job:

- `news_agent` prepares market context
- `research_agent` turns signals into plain-English trade ideas
- `strategy_agent` decides whether to buy
- `risk_agent` checks whether the trade is safe enough to place
- `execution_agent` sends the order to Alpaca

## Project Structure

```text
Agent-Traders/
|-- agents/
|   |-- __init__.py
|   |-- execution_agent.py
|   |-- news_agent.py
|   |-- research_agent.py
|   |-- risk_agent.py
|   `-- strategy_agent.py
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
5. Calculates a simple moving average from recent daily bars
6. Builds a research summary with trend and momentum context
7. Buys if `current price > SMA`
8. Limits each trade to a maximum dollar amount
9. Prevents more than one trade per run

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
ALPACA_SYMBOL=AAPL
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

## Future AI Agent Ideas

This project is already structured for future upgrades:

- Upgrade `agents/research_agent.py` to compare multiple symbols and rank opportunities
- Add real headline or sentiment data inside `agents/news_agent.py`
- Replace the simple SMA rule in `agents/strategy_agent.py` with AI or ML logic
- Add stricter portfolio controls in `agents/risk_agent.py`
- Add smarter order handling in `agents/execution_agent.py`

## Logs

Each run writes logs to:

```text
data/trading_bot.log
```
