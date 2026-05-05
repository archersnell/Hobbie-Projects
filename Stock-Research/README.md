# Stock Research Tool

Automated stock research and scoring tool built with Python.

## Setup

**Requirements:** Python 3.8+

**1. Clone the repo and navigate to the project folder**
```bash
cd stock_research
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## CLI Commands

**Analyze a single stock**
```bash
python main.py analyze AAPL
```

**Run the automated NASDAQ scanner**
```bash
python main.py scan
```
Runs continuously during market hours (9:30am–4:00pm ET). Prints stocks scoring 75+.

**Research a portfolio or ticker list**
```bash
python main.py portfolio tickers.txt
```
`tickers.txt` should have one ticker symbol per line:
```
AAPL
MSFT
NVDA
```

---

## Scoring System

| Score | Recommendation |
|-------|---------------|
| 75–100 | Buy |
| 50–74 | Watch |
| 25–49 | Hold |
| 0–24 | Sell |

Scores are based on moving averages (30pts), RSI (25pts), volume trends (25pts), and 52-week position (20pts).