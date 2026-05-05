import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str) -> dict:
    try:
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.info

        stock = {
            "current_price": data.get("currentPrice"),
            "volume": data.get("volume"),
            "average_volume": data.get("averageVolume"),
            "52_week_high": data.get("fiftyTwoWeekHigh"),
            "52_week_low": data.get("fiftyTwoWeekLow"),
            "history": ticker_obj.history(period="1y"),
            "news": ticker_obj.news,
            "earnings": ticker_obj.calendar
        }
        return stock
    except Exception as e:
        print("Invalid Symbol Input")
        return {}


def fetch_bulk_data(tickers: list) -> pd.DataFrame:
    bulk_data = yf.download(tickers, period="1d")
    return bulk_data
