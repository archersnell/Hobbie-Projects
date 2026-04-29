from broker.alpaca_client import AlpacaClient
from config import AppConfig
from data.market_data import normalize_symbol


def run_sell(symbol: str, config: AppConfig) -> None:
    symbol = normalize_symbol(symbol)
    client = AlpacaClient(config)

    if config.is_live_trading:
        raise ValueError(
            "Live trading is enabled. This beginner CLI blocks live SELL orders by default. "
            "Switch ALPACA_TRADING_MODE back to paper unless you intentionally extend this code."
        )

    client.validate_symbol(symbol)
    position = client.get_position(symbol)
    if position is None:
        raise ValueError(f"No open paper position found for {symbol}.")

    quantity = int(float(position.qty))
    if quantity < 1:
        raise ValueError(f"Position for {symbol} is smaller than one whole share.")

    order = client.place_market_order(symbol=symbol, quantity=quantity, side="sell")

    print(f"SELL submitted in PAPER mode for {symbol}")
    print(f"Quantity: {quantity} share(s)")
    print(f"Order ID: {order.id}")
