from agents.research_agent import ResearchAgent
from broker.alpaca_client import AlpacaClient
from config import AppConfig
from data.market_discovery import filter_assets_by_market_type, rank_assets_by_daily_move
from data.market_data import get_market_snapshot, normalize_symbol


def _print_research_result(result: dict) -> None:
    metrics = result["metrics"]
    recommendation = result["recommendation"]

    print(f"{result['symbol']} research")
    print(f"Recommendation: {recommendation['label']}")
    print(f"Reason: {recommendation['reason']}")
    print(
        f"Price: ${metrics['current_price']:.2f} | "
        f"Day change: {metrics['daily_percent_change']:.2f}% | "
        f"Volume: {metrics['volume']:,}"
    )
    print(
        f"RVOL: {metrics['relative_volume']:.2f} | "
        f"Volatility: {metrics['volatility_estimate']:.2f}% | "
        f"Momentum: {metrics['momentum']:.2f}%"
    )
    print(
        f"SMA 5: ${metrics['sma_5']:.2f} | "
        f"SMA 20: ${metrics['sma_20']:.2f} | "
        f"RSI 14: {metrics['rsi_14']:.2f}"
    )
    print(f"Bid/ask spread: {metrics['bid_ask_spread_percent']:.2f}%")


def research_symbols(symbols: list[str], client: AlpacaClient, research_agent: ResearchAgent) -> list[dict]:
    results = []
    for symbol in symbols:
        clean_symbol = normalize_symbol(symbol)
        try:
            client.validate_symbol(clean_symbol)
            market_data = get_market_snapshot(client, clean_symbol)
        except Exception as error:
            print(f"Skipping {clean_symbol}: {error}")
            continue
        results.append(research_agent.research_symbol(clean_symbol, market_data))
    return results


def print_ranked_results(title: str, results: list[dict]) -> None:
    if not results:
        print("No research results were available.")
        return

    print(title)
    print(
        f"{'#':>2}  {'Symbol':<6} {'Recommendation':<22} {'Score':>5} "
        f"{'Price':>10} {'Change':>8} {'RVOL':>6} {'Vol':>7} {'RSI':>6} {'Spread':>7}"
    )
    print("-" * 93)

    for index, result in enumerate(results, start=1):
        metrics = result["metrics"]
        recommendation = result["recommendation"]
        print(
            f"{index:>2}. {result['symbol']:<6} "
            f"{recommendation['label']:<22} "
            f"{recommendation['score']:>5} "
            f"${metrics['current_price']:>9.2f} "
            f"{metrics['daily_percent_change']:>7.2f}% "
            f"{metrics['relative_volume']:>6.2f} "
            f"{metrics['volatility_estimate']:>6.2f}% "
            f"{metrics['rsi_14']:>6.1f} "
            f"{metrics['bid_ask_spread_percent']:>6.2f}%"
        )


def _print_market_search_summary(market_type: str, assets_found: int, movers: list[dict]) -> None:
    print(f"Market search: {market_type}")
    print(f"Discovered tradable assets in scope: {assets_found}")
    print(f"Daily movers with snapshot data: {len(movers)}")
    if movers:
        top_mover = movers[0]
        print(
            f"Largest daily move before full research: {top_mover['symbol']} "
            f"({top_mover['daily_percent_change']:.2f}%, volume {top_mover['volume']:,})"
        )


def _discover_market_movers(
    client: AlpacaClient,
    market_type: str,
    limit: int,
    top: int,
) -> list[str]:
    if limit < 1:
        raise ValueError("--limit must be at least 1.")
    if top < 1:
        raise ValueError("--top must be at least 1.")

    assets = client.get_tradable_assets()
    filtered_assets = filter_assets_by_market_type(assets, market_type)
    limited_assets = filtered_assets[:limit]
    snapshots = client.get_stock_snapshots([asset.symbol for asset in limited_assets])
    movers = rank_assets_by_daily_move(limited_assets, snapshots)

    _print_market_search_summary(market_type, len(filtered_assets), movers)
    return [mover["symbol"] for mover in movers[:top]]


def run_research(
    symbols: list[str],
    market_type: str,
    limit: int,
    top: int,
    config: AppConfig,
) -> None:
    client = AlpacaClient(config)
    research_agent = ResearchAgent()

    if len(symbols) == 1:
        clean_symbol = normalize_symbol(symbols[0])
        results = research_symbols([clean_symbol], client, research_agent)
        if not results:
            return
        result = results[0]
        _print_research_result(result)
        return

    if len(symbols) > 1:
        print(f"Researching {len(symbols)} symbols...")
        results = research_symbols(symbols, client, research_agent)
        ranked_results = research_agent.rank_results(results)
        print_ranked_results("Ranked research results", ranked_results)
        return

    mover_symbols = _discover_market_movers(
        client=client,
        market_type=market_type,
        limit=limit,
        top=top,
    )
    print()
    print(f"Researching top {len(mover_symbols)} daily mover(s)...")
    results = research_symbols(mover_symbols, client, research_agent)
    ranked_results = research_agent.rank_results(results)
    print_ranked_results("Concise research report", ranked_results)
