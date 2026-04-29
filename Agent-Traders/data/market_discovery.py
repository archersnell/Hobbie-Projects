ETF_NAME_PREFIXES = [
    "DIREXION",
    "INVESCO",
    "ISHARES",
    "PROSHARES",
    "SPDR",
    "VANGUARD",
    "WISDOMTREE",
]


ETF_KEYWORDS = [
    " ETF",
    " ETN",
    " FUND",
    " TRUST",
    " SHARES",
    " PROSHARES",
    " DIREXION",
    " ISHARES",
    " SPDR",
    " VANGUARD",
    " INVESCO",
    " WISDOMTREE",
]


def _asset_name(asset) -> str:
    return (getattr(asset, "name", "") or "").upper()


def is_etf_asset(asset) -> bool:
    name = _asset_name(asset)
    return (
        any(name.startswith(prefix) for prefix in ETF_NAME_PREFIXES)
        or any(keyword in name for keyword in ETF_KEYWORDS)
    )


def filter_assets_by_market_type(assets: list, market_type: str) -> list:
    if market_type == "all":
        return assets
    if market_type == "etfs":
        return [asset for asset in assets if is_etf_asset(asset)]
    if market_type == "stocks":
        return [asset for asset in assets if not is_etf_asset(asset)]
    raise ValueError("--market must be stocks, etfs, or all.")


def rank_assets_by_daily_move(assets: list, snapshots: dict) -> list[dict]:
    movers = []
    asset_by_symbol = {asset.symbol: asset for asset in assets}

    for symbol, snapshot in snapshots.items():
        daily_bar = getattr(snapshot, "daily_bar", None)
        previous_daily_bar = getattr(snapshot, "previous_daily_bar", None)
        if not daily_bar or not previous_daily_bar:
            continue

        current_price = float(daily_bar.close)
        previous_close = float(previous_daily_bar.close)
        volume = int(daily_bar.volume or 0)
        if previous_close <= 0 or current_price <= 0:
            continue

        percent_change = ((current_price - previous_close) / previous_close) * 100
        asset = asset_by_symbol.get(symbol)
        movers.append(
            {
                "symbol": symbol,
                "name": getattr(asset, "name", "") if asset else "",
                "price": current_price,
                "daily_percent_change": percent_change,
                "abs_daily_percent_change": abs(percent_change),
                "volume": volume,
            }
        )

    movers.sort(
        key=lambda mover: (
            mover["abs_daily_percent_change"],
            mover["volume"],
        ),
        reverse=True,
    )
    return movers
