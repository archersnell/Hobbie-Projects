from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


class ExecutionAgent:
    """
    Execution agent sends approved orders to Alpaca.

    Later, this can be extended for limit orders, bracket orders, retries,
    trade confirmations, or broker-routing logic.
    """

    def place_market_order(self, trading_client, symbol: str, quantity: int, side: OrderSide):
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=side,
            time_in_force=TimeInForce.DAY,
        )
        return trading_client.submit_order(order_data=order_request)

    def place_buy_order(self, trading_client, symbol: str, quantity: int):
        return self.place_market_order(
            trading_client=trading_client,
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
        )

    def place_sell_order(self, trading_client, symbol: str, quantity: int):
        return self.place_market_order(
            trading_client=trading_client,
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
        )
