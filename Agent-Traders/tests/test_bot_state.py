from bot.state import BotState
from bot.trading_loop import current_symbol_quantity


def test_bot_state_tracks_trade_limit():
    state = BotState()

    assert state.can_trade(max_trades_per_day=2)
    state.record_trade()
    assert state.can_trade(max_trades_per_day=2)
    state.record_trade()
    assert not state.can_trade(max_trades_per_day=2)


class FakePosition:
    def __init__(self, qty):
        self.qty = qty


def test_current_symbol_quantity_reads_existing_position_quantity():
    positions = {
        "AAPL": FakePosition("2"),
    }

    assert current_symbol_quantity(positions, "AAPL") == 2
    assert current_symbol_quantity(positions, "MSFT") == 0
