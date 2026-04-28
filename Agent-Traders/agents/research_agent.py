class ResearchAgent:
    """
    Research agent that turns raw signals into plain-English trade guidance.

    It does not place trades. Its job is to help you understand whether a setup
    looks interesting enough to watch, research further, or act on.
    """

    def generate_trade_advice(self, symbol: str, strategy_result: dict, news_context: dict) -> dict:
        current_price = strategy_result["current_price"]
        sma = strategy_result["sma"]
        price_vs_sma_pct = strategy_result["price_vs_sma_pct"]
        recent_change_pct = strategy_result["recent_change_pct"]
        sentiment = news_context.get("sentiment", "neutral")

        if current_price > sma and recent_change_pct > 1:
            conviction = "strong"
            action = "research for a possible buy"
            summary = (
                f"{symbol} looks constructive: price is above its SMA and short-term momentum is positive."
            )
        elif current_price > sma:
            conviction = "moderate"
            action = "keep on watch"
            summary = (
                f"{symbol} is above its SMA, but momentum is only modest so the setup is less convincing."
            )
        else:
            conviction = "weak"
            action = "wait"
            summary = (
                f"{symbol} is below or near its SMA, so this setup does not look strong enough yet."
            )

        if sentiment != "neutral":
            summary += f" News sentiment is currently {sentiment}."

        return {
            "symbol": symbol,
            "conviction": conviction,
            "action": action,
            "summary": summary,
            "details": [
                f"Current price: ${current_price:.2f}",
                f"SMA: ${sma:.2f}",
                f"Price vs SMA: {price_vs_sma_pct:.2f}%",
                f"Recent price change: {recent_change_pct:.2f}%",
                f"News sentiment: {sentiment}",
            ],
        }

    def rank_top_performers(
        self,
        snapshots: dict,
        top_n: int = 10,
        min_price: float = 5.0,
        min_volume: int = 500_000,
    ) -> list[dict]:
        ranked = []

        for symbol, snapshot in snapshots.items():
            daily_bar = snapshot.daily_bar
            previous_daily_bar = snapshot.previous_daily_bar

            if not daily_bar or not previous_daily_bar:
                continue

            current_price = float(daily_bar.close)
            previous_close = float(previous_daily_bar.close)
            volume = int(daily_bar.volume or 0)

            if previous_close <= 0:
                continue
            if current_price < min_price or volume < min_volume:
                continue

            percent_change = ((current_price - previous_close) / previous_close) * 100
            ranked.append(
                {
                    "symbol": symbol,
                    "price": current_price,
                    "previous_close": previous_close,
                    "percent_change": percent_change,
                    "volume": volume,
                }
            )

        ranked.sort(key=lambda item: item["percent_change"], reverse=True)
        return ranked[:top_n]
