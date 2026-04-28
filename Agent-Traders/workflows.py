import logging
from datetime import datetime, timedelta, timezone

from alpaca.data.requests import StockSnapshotRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.trading.requests import GetAssetsRequest

from agents.execution_agent import ExecutionAgent
from agents.news_agent import NewsAgent
from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from clients import create_market_data_client, create_trading_client
from config import BotConfig
from reporting import (
    print_research_report,
    print_top_performers_report,
    print_trade_outcome,
)


def chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def analyze_symbol(config: BotConfig, market_data_client) -> dict:
    news_agent = NewsAgent()
    research_agent = ResearchAgent()
    strategy_agent = StrategyAgent()

    news_context = news_agent.get_market_context(symbol=config.symbol)
    strategy_result = strategy_agent.evaluate(
        market_data_client=market_data_client,
        symbol=config.symbol,
        sma_period=config.sma_period,
        data_feed=config.data_feed,
        history_start=datetime.now(timezone.utc) - timedelta(days=60),
    )
    research_result = research_agent.generate_trade_advice(
        symbol=config.symbol,
        strategy_result=strategy_result,
        news_context=news_context,
    )

    return {
        "news_context": news_context,
        "strategy_result": strategy_result,
        "research_result": research_result,
    }


def log_analysis(config: BotConfig, analysis: dict) -> None:
    strategy_result = analysis["strategy_result"]
    research_result = analysis["research_result"]
    news_context = analysis["news_context"]

    logging.info("Current price: $%.2f", strategy_result["current_price"])
    logging.info("%s-day SMA: $%.2f", config.sma_period, strategy_result["sma"])
    logging.info("Price vs SMA: %.2f%%", strategy_result["price_vs_sma_pct"])
    logging.info("Recent price change: %.2f%%", strategy_result["recent_change_pct"])
    logging.info("Strategy decision: %s", strategy_result["decision"])
    logging.info("Strategy reason: %s", strategy_result["reason"])
    logging.info("News context: %s", news_context["summary"])
    logging.info("Research conviction: %s", research_result["conviction"])
    logging.info("Research action: %s", research_result["action"])
    logging.info("Research summary: %s", research_result["summary"])

    for detail in research_result["details"]:
        logging.info("Research detail: %s", detail)


def get_top_performers(config: BotConfig) -> list[dict]:
    trading_client = create_trading_client(config)
    market_data_client = create_market_data_client(config)
    research_agent = ResearchAgent()

    assets = trading_client.get_all_assets(
        GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
    )
    symbols = [asset.symbol for asset in assets if asset.tradable]

    snapshots = {}
    for symbol_chunk in chunk_list(symbols, 200):
        request = StockSnapshotRequest(
            symbol_or_symbols=symbol_chunk,
            feed=config.data_feed,
        )
        snapshots.update(market_data_client.get_stock_snapshot(request))

    return research_agent.rank_top_performers(snapshots=snapshots, top_n=10)


def run_research(config: BotConfig, symbol_override: str | None = None) -> None:
    if symbol_override is None:
        logging.info("Starting leaderboard research workflow")
        top_performers = get_top_performers(config)
        logging.info("Top performers count: %s", len(top_performers))
        print_top_performers_report(top_performers)
        return

    logging.info("Starting research workflow for %s", config.symbol)
    market_data_client = create_market_data_client(config)
    analysis = analyze_symbol(config, market_data_client)

    log_analysis(config, analysis)
    print_research_report(config, analysis)


def run_trade(config: BotConfig) -> None:
    if not config.symbol:
        raise ValueError(
            "Trade command requires a symbol. Use 'python main.py trade SPY'."
        )

    logging.info("Starting trading workflow for %s", config.symbol)
    logging.info("Trading mode: %s", "paper" if config.paper else "live")

    trading_client = create_trading_client(config)
    market_data_client = create_market_data_client(config)
    bot_state = {"trade_placed_this_run": False}

    account = trading_client.get_account()
    buying_power = float(account.buying_power)
    logging.info("Account status: %s", account.status)
    logging.info("Buying power: $%.2f", buying_power)

    analysis = analyze_symbol(config, market_data_client)
    log_analysis(config, analysis)
    print_research_report(config, analysis)

    risk_agent = RiskAgent()
    execution_agent = ExecutionAgent()
    strategy_result = analysis["strategy_result"]
    risk_result = risk_agent.review_trade(
        symbol=config.symbol,
        decision=strategy_result["decision"],
        current_price=strategy_result["current_price"],
        buying_power=buying_power,
        max_trade_value=config.max_trade_value,
        trade_placed_this_run=bot_state["trade_placed_this_run"],
    )

    trading_mode = "paper" if config.paper else "live"

    if not risk_result["approved"]:
        logging.warning(risk_result["message"])
        print_trade_outcome(config, risk_result, trading_mode)
        return

    if risk_result["message"]:
        logging.warning(risk_result["message"])

    order = execution_agent.place_buy_order(
        trading_client=trading_client,
        symbol=config.symbol,
        quantity=risk_result["quantity"],
    )
    bot_state["trade_placed_this_run"] = True

    logging.info("Order submitted successfully.")
    logging.info("Order ID: %s", order.id)
    logging.info("Order side: %s", order.side)
    logging.info("Order quantity: %s", order.qty)
    print_trade_outcome(config, risk_result, trading_mode)
