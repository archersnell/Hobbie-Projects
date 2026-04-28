class NewsAgent:
    """
    Beginner-friendly market context agent.

    Right now this keeps the project runnable without requiring any extra news
    APIs. Later, this is the natural place to plug in headlines, sentiment
    models, or an LLM-based market summary.
    """

    def get_market_context(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "sentiment": "neutral",
            "summary": f"No live news feed is connected yet for {symbol}, so sentiment is neutral.",
        }
