from strategies.base import Strategy


class SimpleMomentumStrategy(Strategy):
    """Beginner-friendly rules for finding volatile day-trading candidates."""

    def evaluate(self, symbol: str, market_data: dict) -> dict:
        score = 0
        reasons = []

        if market_data["daily_percent_change"] > 2:
            score += 2
            reasons.append("strong daily gain")
        elif market_data["daily_percent_change"] > 0:
            score += 1
            reasons.append("positive daily move")

        if market_data["relative_volume"] >= 1.5:
            score += 2
            reasons.append("high relative volume")
        elif market_data["relative_volume"] >= 1:
            score += 1
            reasons.append("normal-to-high relative volume")

        if market_data["volatility_estimate"] >= 3:
            score += 2
            reasons.append("large recent price swings")
        elif market_data["volatility_estimate"] >= 1.5:
            score += 1
            reasons.append("moderate recent volatility")

        if market_data["current_price"] > market_data["sma_5"] > market_data["sma_20"]:
            score += 2
            reasons.append("price is above short and medium moving averages")

        if 45 <= market_data["rsi_14"] <= 70:
            score += 1
            reasons.append("RSI is constructive without being too extended")
        elif market_data["rsi_14"] > 80:
            score -= 2
            reasons.append("RSI looks very overbought")

        if market_data["bid_ask_spread_percent"] > 1:
            score -= 2
            reasons.append("bid/ask spread is wide")

        if score >= 6:
            label = "possible buy candidate"
        elif score >= 3:
            label = "watch"
        else:
            label = "avoid"

        if not reasons:
            reasons.append("no strong volatility or momentum edge")

        # TODO: Replace or blend this score with model predictions later.
        return {
            "label": label,
            "score": score,
            "reason": "; ".join(reasons),
        }
