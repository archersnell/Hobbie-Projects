from research.data import fetcher
from research import scorer

def analyse(ticker: str) -> dict:
    data = fetcher.fetch_stock_data(ticker)
    output_score = scorer.score(data)
    headline = data.get("news", [])[:3]

    return{
        "symbol": ticker,
        "current_price" : data.get("current_price"),
        "score" : output_score["score"],
        "recommendation" : output_score["recommendation"],
        "news_headline" : headline
    }
