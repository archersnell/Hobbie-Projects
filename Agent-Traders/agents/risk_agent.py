class RiskAgent:
    """
    Risk checks run after strategy and before execution.

    This is where future portfolio rules, stop-loss logic, and AI safety checks
    can be added without changing the strategy or broker code.
    """

    def review_trade(
        self,
        symbol: str,
        decision: str,
        current_price: float,
        buying_power: float,
        max_trade_value: float,
        trade_placed_this_run: bool,
    ) -> dict:
        if trade_placed_this_run:
            return {
                "approved": False,
                "message": "Risk warning: only one trade is allowed per bot run.",
                "quantity": 0,
            }

        if decision != "buy":
            return {
                "approved": False,
                "message": f"No trade placed for {symbol}: strategy did not return a BUY signal.",
                "quantity": 0,
            }

        allowed_trade_value = min(max_trade_value, buying_power)
        quantity = int(allowed_trade_value // current_price)

        if buying_power < current_price:
            return {
                "approved": False,
                "message": (
                    f"Risk warning: buying power (${buying_power:.2f}) is lower than "
                    f"the current share price (${current_price:.2f})."
                ),
                "quantity": 0,
            }

        if quantity < 1:
            return {
                "approved": False,
                "message": (
                    f"Risk warning: max trade value (${max_trade_value:.2f}) is too small "
                    f"to buy one share of {symbol} at ${current_price:.2f}."
                ),
                "quantity": 0,
            }

        if buying_power < max_trade_value:
            warning = (
                f"Risk warning: buying power is below the $"
                f"{max_trade_value:.2f} limit, so trade size was reduced."
            )
        else:
            warning = ""

        return {
            "approved": True,
            "message": warning,
            "quantity": quantity,
        }
