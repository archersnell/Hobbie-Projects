from bot.trading_loop import run_trading_loop
from config import AppConfig


def choose_value(value, fallback):
    return fallback if value is None else value


def run_bot_command(
    market_type: str,
    limit: int,
    candidates: int,
    max_symbol_quantity: int | None,
    max_trades_per_day: int | None,
    loss_tolerance_pct: float | None,
    min_buy_score: int | None,
    interval_seconds: int | None,
    sell_on_watch: bool,
    once: bool,
    config: AppConfig,
) -> None:
    run_trading_loop(
        config=config,
        market_type=market_type,
        limit=limit,
        candidates=candidates,
        max_symbol_quantity=choose_value(max_symbol_quantity, config.max_symbol_quantity),
        max_trades_per_day=choose_value(max_trades_per_day, config.max_trades_per_day),
        loss_tolerance_pct=choose_value(loss_tolerance_pct, config.loss_tolerance_pct),
        min_buy_score=choose_value(min_buy_score, config.min_buy_score),
        interval_seconds=choose_value(interval_seconds, config.bot_interval_seconds),
        sell_on_watch=sell_on_watch,
        once=once,
    )
