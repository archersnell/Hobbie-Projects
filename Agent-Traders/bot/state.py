from dataclasses import dataclass, field
from datetime import date


@dataclass
class BotState:
    trades_today: int = 0
    trade_date: date = field(default_factory=date.today)

    def reset_if_new_day(self) -> None:
        today = date.today()
        if self.trade_date != today:
            self.trade_date = today
            self.trades_today = 0

    def can_trade(self, max_trades_per_day: int) -> bool:
        self.reset_if_new_day()
        return self.trades_today < max_trades_per_day

    def record_trade(self) -> None:
        self.reset_if_new_day()
        self.trades_today += 1
