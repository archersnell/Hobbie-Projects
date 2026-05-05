from broker.alpaca_client import AlpacaClient
from config import AppConfig
from data.market_data import normalize_symbol


def run_buy(symbol: str, config: AppConfig) -> None:
    symbol = normalize_symbol(symbol)
    client = AlpacaClient(config)

    if config.is_live_trading:
        raise ValueError(
            "Live trading is enabled. This beginner CLI blocks live BUY orders by default. "
            "Switch ALPACA_TRADING_MODE back to paper unless you intentionally extend this code."
        )

    client.validate_symbol(symbol)
    account = client.get_account()
    buying_power = float(account.buying_power)
    current_price = client.get_latest_price(symbol)
    trade_value = min(config.max_trade_value, buying_power)
    quantity = int(trade_value // current_price)

    if quantity < 1:
        raise ValueError(
            f"Not enough buying power for {symbol}. Price is ${current_price:.2f}, "
            f"buying power is ${buying_power:.2f}."
        )

    order = client.place_market_order(symbol=symbol, quantity=quantity, side="buy")

    print(f"BUY submitted in PAPER mode for {symbol}")
    print(f"Quantity: {quantity} share(s)")
    print(f"Estimated value: ${quantity * current_price:.2f}")
    print(f"Order ID: {order.id}")
