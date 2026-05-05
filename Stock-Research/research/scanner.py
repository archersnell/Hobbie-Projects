import schedule
import time
import config
from research.data import fetcher
from research import analyzer
from research.utils import market_hours
import pandas as pd

def run_scan():
    if not market_hours.is_market_open():
        print("Market is closed")
        return

    tickers = _get_nasdaq_tickers()
    filtered = _prefilter(tickers)
    
    for ticker in filtered:
        result = analyzer.analyse(ticker)
        if result["score"] >= config.BUY_THRESHOLD:
            print(f"{result['symbol']} | Score: {result['score']} | {result['recommendation']}")

def start():
    interval = _calculate_interval(config.NASDAQ_TICKER_COUNT)  # rough estimate
    schedule.every(interval).minutes.do(run_scan)
    
    while True:
        schedule.run_pending()
        time.sleep(1)


def _get_nasdaq_tickers() -> list:
    url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&exchange=NASDAQ"
    df = pd.read_json(url)
    rows = pd.DataFrame(df["data"]["rows"])
    return rows["symbol"].tolist()


def _prefilter(tickers: list) -> list:
    tickers_data = fetcher.fetch_bulk_data(tickers)

    last_price = tickers_data["Close"].iloc[-1]
    last_volume = tickers_data["Volume"].iloc[-1]

    price_mask = last_price > config.MIN_PRICE
    volume_mask = last_volume > config.MIN_DAILY_VOLUME

    combined_mask = price_mask & volume_mask

    return list(last_price[combined_mask].index)


def _calculate_interval(num_tickers: int) -> int:
    seconds_per_ticker = 1.5
    return int(num_tickers * seconds_per_ticker / 60)  # returns minutes