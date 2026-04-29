import logging
import re
import time
from datetime import datetime, timedelta, timezone

from alpaca.common.exceptions import APIError
from alpaca.data.requests import StockSnapshotRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.trading.requests import GetAssetsRequest

from agents.execution_agent import ExecutionAgent
from agents.news_agent import NewsAgent
from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from app.config import BotConfig
from app.reporting import (
    print_scan_report,
    print_research_report,
    print_top_performers_report,
    print_trade_outcome,
)
from brokers.alpaca_clients import create_market_data_client, create_trading_client


SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")

VOLATILE_TECH_SYMBOLS = [
    "AI",
    "APP",
    "AMD",
    "ARM",
    "ARQQ",
    "ASTS",
    "BBAI",
    "BITF",
    "BULZ",
    "CIFR",
    "COIN",
    "DDOG",
    "DKNG",
    "GME",
    "HOOD",
    "FNGU",
    "FSLY",
    "HIMS",
    "IONQ",
    "IREN",
    "JOBY",
    "LCID",
    "MARA",
    "MSTU",
    "MSTX",
    "MSTR",
    "MU",
    "NIO",
    "NVDA",
    "OPEN",
    "PATH",
    "PLTR",
    "QBTS",
    "QQQ",
    "RBLX",
    "RIOT",
    "RKLB",
    "RIVN",
    "SMCI",
    "SNAP",
    "SOFI",
    "SOUN",
    "SOXL",
    "TECL",
    "TEM",
    "TQQQ",
    "TSLA",
    "UPST",
    "WOLF",
    "YINN",
    "ZETA",
]


def chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def validate_symbol_format(symbol: str) -> None:
    if not SYMBOL_PATTERN.match(symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Use a stock ticker like AAPL, MSFT, or BRK.B."
        )


def validate_symbol_exists(trading_client, symbol: str) -> None:
    """
    Validate a symbol before requesting market data.

    This turns Alpaca's API errors into beginner-friendly CLI messages.
    """
    validate_symbol_format(symbol)

    try:
        asset = trading_client.get_asset(symbol)
    except APIError as error:
        message = getattr(error, "message", str(error))
        status_code = getattr(error, "status_code", None)

        if status_code == 404 or "not found" in message.lower():
            raise ValueError(
                f"Invalid symbol '{symbol}'. Alpaca could not find a tradable stock with that ticker."
            ) from error

        raise ValueError(f"Could not validate symbol '{symbol}': {message}") from error

    if asset.status != AssetStatus.ACTIVE:
        raise ValueError(f"Invalid symbol '{symbol}'. Alpaca lists this asset as inactive.")

    if not asset.tradable:
        raise ValueError(f"Invalid symbol '{symbol}'. Alpaca lists this asset as not tradable.")


def get_market_status(config: BotConfig) -> dict:
    """
    Read Alpaca's market clock.

    Intraday indicators are much more useful during regular market hours.
    Outside market hours, prices and volume can be stale or thin.
    """
    try:
        trading_client = create_trading_client(config)
        clock = trading_client.get_clock()
    except Exception as error:
        logging.warning("Could not read market clock: %s", error)
        return {
            "is_open": None,
            "message": "Market status unavailable.",
        }

    is_open = bool(getattr(clock, "is_open", False))
    next_open = getattr(clock, "next_open", None)
    next_close = getattr(clock, "next_close", None)

    if is_open:
        return {
            "is_open": True,
            "message": f"Market open. Next close: {next_close}.",
        }

    return {
        "is_open": False,
        "message": f"Market closed. Next open: {next_open}.",
    }


def analyze_symbol(
    config: BotConfig,
    market_data_client,
    min_risk_reward: float = 1.5,
    min_volume_for_signal: float = 0.75,
    min_score_gap: int = 2,
    avoid_range_trades: bool = True,
) -> dict:
    news_agent = NewsAgent()
    research_agent = ResearchAgent()
    strategy_agent = StrategyAgent(
        min_risk_reward=min_risk_reward,
        min_volume_for_signal=min_volume_for_signal,
        min_score_gap=min_score_gap,
        avoid_range_trades=avoid_range_trades,
    )

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
    logging.info("Strategy signal: %s", strategy_result["strategy_signal"])
    logging.info("Buy score: %s", strategy_result["buy_score"])
    logging.info("Sell score: %s", strategy_result["sell_score"])
    logging.info("Confidence: %s", strategy_result["confidence"])
    logging.info("Risk/reward ratio: %s", strategy_result["risk_reward_ratio"])
    logging.info("Strategy reason: %s", strategy_result["reason"])
    logging.info("News context: %s", news_context["summary"])
    logging.info("Research conviction: %s", research_result["conviction"])
    logging.info("Research action: %s", research_result["action"])
    logging.info("Research summary: %s", research_result["summary"])

    for detail in research_result["details"]:
        logging.info("Research detail: %s", detail)


def get_top_performers(
    config: BotConfig,
    top_n: int = 10,
    min_price: float = 5.0,
    offset: int = 0,
) -> list[dict]:
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

    return research_agent.rank_top_performers(
        snapshots=snapshots,
        top_n=top_n,
        min_price=min_price,
        offset=offset,
    )


def parse_symbols(symbols: str | None) -> list[str]:
    if not symbols:
        return []

    parsed_symbols = []
    for symbol in symbols.split(","):
        clean_symbol = symbol.strip().upper()
        if clean_symbol:
            validate_symbol_format(clean_symbol)
            parsed_symbols.append(clean_symbol)

    return parsed_symbols


def slice_symbols_with_wrap(all_symbols: list[str], scan_limit: int, scan_offset: int) -> dict:
    offset = scan_offset % len(all_symbols)
    selected_symbols = []

    for index in range(min(scan_limit, len(all_symbols))):
        selected_symbols.append(all_symbols[(offset + index) % len(all_symbols)])

    return {
        "symbols": selected_symbols,
        "total_symbols": len(all_symbols),
        "next_offset": (offset + scan_limit) % len(all_symbols),
    }


def get_scan_symbols(
    config: BotConfig,
    universe: str,
    symbols: str | None,
    scan_limit: int,
    scan_offset: int,
    min_price: float,
) -> dict:
    if universe == "custom":
        custom_symbols = parse_symbols(symbols)
        if not custom_symbols:
            raise ValueError("--universe custom requires --symbols, such as --symbols NVDA,AMD,SOXL.")
        return slice_symbols_with_wrap(custom_symbols, scan_limit, scan_offset)

    if universe == "volatile-tech":
        return slice_symbols_with_wrap(VOLATILE_TECH_SYMBOLS, scan_limit, scan_offset)

    top_performers = get_top_performers(
        config,
        top_n=scan_limit,
        min_price=min_price,
        offset=scan_offset,
    )
    return {
        "symbols": [stock["symbol"] for stock in top_performers],
        "total_symbols": None,
        "next_offset": scan_offset + scan_limit,
    }


def score_scan_candidate(analysis: dict) -> int:
    strategy_result = analysis["strategy_result"]
    return abs(strategy_result["buy_score"] - strategy_result["sell_score"])


def calculate_atr_pct(strategy_result: dict) -> float:
    current_price = strategy_result["current_price"]
    atr = strategy_result["atr_14"]

    if current_price <= 0:
        return 0.0

    return (atr / current_price) * 100


def estimate_trade_value(config: BotConfig, strategy_result: dict) -> float:
    current_price = strategy_result["current_price"]
    quantity = int(config.max_trade_value // current_price)
    return quantity * current_price


def estimate_quantity(config: BotConfig, strategy_result: dict) -> int:
    return int(config.max_trade_value // strategy_result["current_price"])


def matches_scan_focus(
    strategy_result: dict,
    min_price: float,
    max_price: float,
    min_atr_pct: float,
    min_rvol: float,
) -> bool:
    current_price = strategy_result["current_price"]
    relative_volume = strategy_result["relative_volume"]
    atr_pct = calculate_atr_pct(strategy_result)

    return (
        min_price <= current_price <= max_price
        and atr_pct >= min_atr_pct
        and relative_volume >= min_rvol
    )


def run_research(config: BotConfig, symbol_override: str | None = None) -> None:
    if symbol_override is None:
        logging.info("Starting leaderboard research workflow")
        top_performers = get_top_performers(config)
        logging.info("Top performers count: %s", len(top_performers))
        print_top_performers_report(top_performers)
        return

    logging.info("Starting research workflow for %s", config.symbol)
    trading_client = create_trading_client(config)
    validate_symbol_exists(trading_client, config.symbol)
    market_data_client = create_market_data_client(config)
    analysis = analyze_symbol(config, market_data_client)

    log_analysis(config, analysis)
    print_research_report(config, analysis)


def run_scan_once(
    config: BotConfig,
    scan_limit: int,
    scan_offset: int,
    universe: str,
    symbols: str | None,
    candidate_count: int,
    min_price: float,
    max_price: float,
    min_atr_pct: float,
    min_rvol: float,
    min_risk_reward: float,
    min_score_gap: int,
    allow_range_trades: bool,
    max_session_trades: int,
    max_session_value: float,
    session_trades_used: int = 0,
    session_value_used: float = 0.0,
    seen_symbols: set[str] | None = None,
    execute_paper: bool = False,
    paper_side: str = "buy",
) -> dict:
    """Run one automated scan and print the best setups."""
    if scan_limit < 1:
        raise ValueError("--limit must be at least 1.")
    if scan_offset < 0:
        raise ValueError("--offset cannot be negative.")
    if candidate_count < 1:
        raise ValueError("--candidates must be at least 1.")
    if min_price <= 0:
        raise ValueError("--min-price must be greater than 0.")
    if max_price < min_price:
        raise ValueError("--max-price must be greater than or equal to --min-price.")
    if min_atr_pct < 0:
        raise ValueError("--min-atr-pct cannot be negative.")
    if min_rvol < 0:
        raise ValueError("--min-rvol cannot be negative.")
    if min_risk_reward <= 0:
        raise ValueError("--min-risk-reward must be greater than 0.")
    if min_score_gap < 1:
        raise ValueError("--min-score-gap must be at least 1.")
    if max_session_trades < 1:
        raise ValueError("--max-session-trades must be at least 1.")
    if max_session_value <= 0:
        raise ValueError("--max-session-value must be greater than 0.")
    if execute_paper and not config.paper:
        raise ValueError("--execute-paper is only allowed when ALPACA_PAPER=true.")
    if paper_side not in {"buy", "sell", "both"}:
        raise ValueError("--paper-side must be buy, sell, or both.")

    logging.info("Starting automated scan workflow")
    if seen_symbols is None:
        seen_symbols = set()

    market_status = get_market_status(config)
    market_data_client = create_market_data_client(config)
    scan_universe = get_scan_symbols(
        config=config,
        universe=universe,
        symbols=symbols,
        scan_limit=scan_limit,
        scan_offset=scan_offset,
        min_price=min_price,
    )
    scan_symbols = scan_universe["symbols"]
    candidates = []
    skipped_counts = {
        "hold_signal": 0,
        "outside_focus": 0,
        "wrong_side": 0,
        "already_seen": 0,
        "no_quantity": 0,
        "session_value": 0,
    }
    allowed_decisions = {"buy", "sell"} if paper_side == "both" else {paper_side}

    for symbol in scan_symbols:
        scan_config = BotConfig(
            api_key=config.api_key,
            secret_key=config.secret_key,
            paper=config.paper,
            symbol=symbol,
            max_trade_value=config.max_trade_value,
            sma_period=config.sma_period,
            data_feed=config.data_feed,
            log_file=config.log_file,
        )

        try:
            analysis = analyze_symbol(
                scan_config,
                market_data_client,
                min_risk_reward=min_risk_reward,
                min_volume_for_signal=min_rvol,
                min_score_gap=min_score_gap,
                avoid_range_trades=not allow_range_trades,
            )
        except ValueError as error:
            logging.warning("Skipping %s during scan: %s", symbol, error)
            continue

        strategy_result = analysis["strategy_result"]
        if strategy_result["strategy_signal"] == "HOLD":
            skipped_counts["hold_signal"] += 1
            continue

        if not matches_scan_focus(
            strategy_result=strategy_result,
            min_price=min_price,
            max_price=max_price,
            min_atr_pct=min_atr_pct,
            min_rvol=min_rvol,
        ):
            skipped_counts["outside_focus"] += 1
            continue

        candidates.append(
            {
                "symbol": symbol,
                "strategy_result": strategy_result,
                "analysis": analysis,
                "estimated_trade_value": estimate_trade_value(config, strategy_result),
                "quantity": estimate_quantity(config, strategy_result),
                "atr_pct": calculate_atr_pct(strategy_result),
                "execution_status": "not submitted",
            }
        )

    candidates.sort(
        key=lambda candidate: (
            candidate["strategy_result"]["decision"] != "hold",
            score_scan_candidate(candidate["analysis"]),
            candidate["strategy_result"]["relative_volume"],
        ),
        reverse=True,
    )

    session_candidates = []
    session_value_added = 0.0
    remaining_trade_slots = max_session_trades - session_trades_used
    remaining_session_value = max_session_value - session_value_used

    max_visible_candidates = min(remaining_trade_slots, candidate_count)

    for candidate in candidates:
        if len(session_candidates) >= max_visible_candidates:
            break

        if execute_paper and candidate["strategy_result"]["decision"] not in allowed_decisions:
            skipped_counts["wrong_side"] += 1
            continue

        if candidate["symbol"] in seen_symbols:
            skipped_counts["already_seen"] += 1
            continue

        estimated_trade_value = candidate["estimated_trade_value"]
        if estimated_trade_value <= 0:
            skipped_counts["no_quantity"] += 1
            continue

        if session_value_added + estimated_trade_value > remaining_session_value:
            skipped_counts["session_value"] += 1
            continue

        session_value_added += estimated_trade_value
        seen_symbols.add(candidate["symbol"])
        session_candidates.append(candidate)

    execution_blocked_by_market = execute_paper and market_status["is_open"] is False

    if execution_blocked_by_market:
        for candidate in session_candidates:
            candidate["execution_status"] = "not submitted: market is closed"
    elif execute_paper:
        trading_client = create_trading_client(config)
        execution_agent = ExecutionAgent()

        for candidate in session_candidates:
            strategy_result = candidate["strategy_result"]

            if strategy_result["decision"] not in allowed_decisions:
                candidate["execution_status"] = f"not submitted: paper side is {paper_side}"
                continue

            if candidate["quantity"] < 1:
                candidate["execution_status"] = "not submitted: quantity below 1"
                continue

            try:
                if strategy_result["decision"] == "buy":
                    order = execution_agent.place_buy_order(
                        trading_client=trading_client,
                        symbol=candidate["symbol"],
                        quantity=candidate["quantity"],
                    )
                else:
                    order = execution_agent.place_sell_order(
                        trading_client=trading_client,
                        symbol=candidate["symbol"],
                        quantity=candidate["quantity"],
                    )
            except APIError as error:
                message = getattr(error, "message", str(error))
                candidate["execution_status"] = f"failed: {message}"
                logging.warning("Paper order failed for %s: %s", candidate["symbol"], message)
                continue

            candidate["execution_status"] = f"submitted: {order.id}"
            logging.info(
                "Paper %s order submitted for %s: %s",
                strategy_result["decision"],
                candidate["symbol"],
                order.id,
            )

    if execution_blocked_by_market:
        total_session_trades = session_trades_used
        total_session_value = session_value_used
    else:
        total_session_trades = session_trades_used + len(session_candidates)
        total_session_value = session_value_used + session_value_added

    print_scan_report(
        candidates=session_candidates,
        scanned_count=len(scan_symbols),
        universe=universe,
        scan_offset=scan_offset,
        next_offset=scan_universe["next_offset"],
        session_trades_used=total_session_trades,
        max_session_trades=max_session_trades,
        max_session_value=max_session_value,
        session_value_used=total_session_value,
        min_price=min_price,
        max_price=max_price,
        min_atr_pct=min_atr_pct,
        min_rvol=min_rvol,
        min_risk_reward=min_risk_reward,
        skipped_counts=skipped_counts,
        execute_paper=execute_paper,
        paper_side=paper_side,
        market_status=market_status,
    )

    return {
        "session_trades_used": total_session_trades,
        "session_value_used": total_session_value,
        "seen_symbols": seen_symbols,
        "next_offset": scan_universe["next_offset"],
        "found_candidates": bool(session_candidates) and not execution_blocked_by_market,
    }


def run_scan(
    config: BotConfig,
    scan_limit: int = 25,
    scan_offset: int = 0,
    universe: str = "movers",
    symbols: str | None = None,
    candidate_count: int = 5,
    watch: bool = False,
    interval_seconds: int = 300,
    min_price: float = 1.0,
    max_price: float = 10.0,
    min_atr_pct: float = 3.0,
    min_rvol: float = 0.75,
    min_risk_reward: float = 1.5,
    min_score_gap: int = 2,
    allow_range_trades: bool = False,
    max_session_trades: int = 3,
    max_session_value: float = 1000.0,
    execute_paper: bool = False,
    paper_side: str = "buy",
) -> None:
    """
    Automatically scan top movers and show the best trade setups.

    This does not place trades. It only finds and prints candidates.
    """
    if interval_seconds < 30:
        raise ValueError("--interval must be at least 30 seconds.")

    if not watch:
        run_scan_once(
            config=config,
            scan_limit=scan_limit,
            scan_offset=scan_offset,
            universe=universe,
            symbols=symbols,
            candidate_count=candidate_count,
            min_price=min_price,
            max_price=max_price,
            min_atr_pct=min_atr_pct,
            min_rvol=min_rvol,
            min_risk_reward=min_risk_reward,
            min_score_gap=min_score_gap,
            allow_range_trades=allow_range_trades,
            max_session_trades=max_session_trades,
            max_session_value=max_session_value,
            execute_paper=execute_paper,
            paper_side=paper_side,
        )
        return

    print(f"Watching for trade setups every {interval_seconds} seconds. Press Ctrl+C to stop.")
    session_state = {
        "session_trades_used": 0,
        "session_value_used": 0.0,
        "seen_symbols": set(),
        "scan_offset": scan_offset,
    }

    try:
        while True:
            session_state = run_scan_once(
                config=config,
                scan_limit=scan_limit,
                scan_offset=session_state["scan_offset"],
                universe=universe,
                symbols=symbols,
                candidate_count=candidate_count,
                min_price=min_price,
                max_price=max_price,
                min_atr_pct=min_atr_pct,
                min_rvol=min_rvol,
                min_risk_reward=min_risk_reward,
                min_score_gap=min_score_gap,
                allow_range_trades=allow_range_trades,
                max_session_trades=max_session_trades,
                max_session_value=max_session_value,
                execute_paper=execute_paper,
                paper_side=paper_side,
                session_trades_used=session_state["session_trades_used"],
                session_value_used=session_state["session_value_used"],
                seen_symbols=session_state["seen_symbols"],
            )
            if not session_state["found_candidates"]:
                print(f"No candidates found. Next scan will start at offset {session_state['next_offset']}.")
                session_state["scan_offset"] = session_state["next_offset"]
            if session_state["session_trades_used"] >= max_session_trades:
                print("Session trade limit reached. Scan stopped.")
                return
            if session_state["session_value_used"] >= max_session_value:
                print("Session dollar limit reached. Scan stopped.")
                return
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Scan stopped.")


def run_trade(config: BotConfig) -> None:
    if not config.symbol:
        raise ValueError(
            "Trade command requires a symbol. Use 'python main.py trade SPY'."
        )

    logging.info("Starting trading workflow for %s", config.symbol)
    logging.info("Trading mode: %s", "paper" if config.paper else "live")

    trading_client = create_trading_client(config)
    validate_symbol_exists(trading_client, config.symbol)
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
