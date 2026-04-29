class Strategy:
    """Simple strategy interface.

    TODO: A future ML model can implement this same evaluate method and return
    the same kind of recommendation dictionary.
    """

    def evaluate(self, symbol: str, market_data: dict) -> dict:
        raise NotImplementedError
