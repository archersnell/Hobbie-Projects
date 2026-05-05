from research import analyzer

def research_portfolio(tickers: list) -> list:
    stock_analysis = []
    for ticker in tickers:
        stock_analysis.append(analyzer.analyse(ticker))

    stock_analysis.sort(key=lambda x: x["score"], reverse=True)

    return stock_analysis


