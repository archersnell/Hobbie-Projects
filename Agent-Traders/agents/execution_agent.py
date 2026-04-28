from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


class ExecutionAgent:
    """
    Execution agent sends approved orders to Alpaca.

    Later, this can be extended for limit orders, bracket orders, retries,
    trade confirmations, or broker-routing logic.
    """

    def place_buy_order(self, trading_client, symbol: str, quantity: int):
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        return trading_client.submit_order(order_data=order_request)
