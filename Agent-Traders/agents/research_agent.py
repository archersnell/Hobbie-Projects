from strategies.simple_momentum import SimpleMomentumStrategy


class ResearchAgent:
    """Turns strategy output into research results and rankings."""

    def __init__(self):
        self.strategy = SimpleMomentumStrategy()

    def research_symbol(self, symbol: str, market_data: dict) -> dict:
        recommendation = self.strategy.evaluate(symbol, market_data)
        return {
            "symbol": symbol,
            "metrics": market_data,
            "recommendation": recommendation,
        }

    def rank_results(self, results: list[dict]) -> list[dict]:
        return sorted(
            results,
            key=lambda result: result["recommendation"]["score"],
            reverse=True,
        )
