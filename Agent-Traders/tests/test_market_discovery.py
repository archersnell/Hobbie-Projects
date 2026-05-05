from data.market_discovery import filter_assets_by_market_type, is_etf_asset, rank_assets_by_daily_move


class FakeAsset:
    def __init__(self, symbol, name):
        self.symbol = symbol
        self.name = name


class FakeBar:
    def __init__(self, close, volume):
        self.close = close
        self.volume = volume


class FakeSnapshot:
    def __init__(self, current_close, previous_close, volume):
        self.daily_bar = FakeBar(current_close, volume)
        self.previous_daily_bar = FakeBar(previous_close, volume)


def test_is_etf_asset_uses_name_keywords():
    assert is_etf_asset(FakeAsset("SPY", "SPDR S&P 500 ETF Trust"))
    assert is_etf_asset(FakeAsset("IVV", "iShares Core S&P 500 ETF"))
    assert not is_etf_asset(FakeAsset("AAPL", "Apple Inc. Common Stock"))


def test_filter_assets_by_market_type_splits_stocks_and_etfs():
    assets = [
        FakeAsset("SPY", "SPDR S&P 500 ETF Trust"),
        FakeAsset("AAPL", "Apple Inc. Common Stock"),
    ]

    assert [asset.symbol for asset in filter_assets_by_market_type(assets, "etfs")] == ["SPY"]
    assert [asset.symbol for asset in filter_assets_by_market_type(assets, "stocks")] == ["AAPL"]


def test_rank_assets_by_daily_move_uses_absolute_move():
    assets = [
        FakeAsset("UP", "Up Stock"),
        FakeAsset("DOWN", "Down Stock"),
    ]
    snapshots = {
        "UP": FakeSnapshot(110, 100, 1_000),
        "DOWN": FakeSnapshot(80, 100, 2_000),
    }

    movers = rank_assets_by_daily_move(assets, snapshots)

    assert movers[0]["symbol"] == "DOWN"
    assert movers[0]["daily_percent_change"] == -20
