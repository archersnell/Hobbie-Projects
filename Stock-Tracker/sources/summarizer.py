"""
Uses the Anthropic API to generate concise stock summaries and digests.
"""

import os

from anthropic import Anthropic

from config import get_tickers


MODEL_NAME = "claude-sonnet-4-20250514"


# Returns a configured Anthropic client, or None if the API key is missing.
def get_anthropic_client() -> Anthropic | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[summarizer] ANTHROPIC_API_KEY is not set; skipping AI summary.")
        return None
    return Anthropic(api_key=api_key)


# Sends a prompt to Claude and returns the text response.
def generate_summary(prompt: str, max_tokens: int = 600) -> str | None:
    client = get_anthropic_client()
    if client is None:
        return None

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        print(f"[summarizer] Error generating summary: {exc}")
        return None


# Summarizes an earnings result for a single ticker.
def summarize_earnings(ticker: str, earnings_data: dict) -> str | None:
    prompt = f"""
Summarize this earnings information for {ticker} for an individual investor.
Focus on surprise vs expectations, revenue/EPS direction, guidance if present,
and whether anything looks urgent.

Data:
{earnings_data}
"""
    return generate_summary(prompt)


# Creates a weekly outlook or weekly recap for the current watchlist.
def generate_weekly_digest(kind: str) -> str | None:
    tickers = ", ".join(get_tickers())
    prompt = f"""
Write a concise {kind} for these watched stocks: {tickers}.
Call out major catalysts, earnings, risks, and any quantum-computing sector context.
Keep it short enough for a phone notification.
"""
    return generate_summary(prompt, max_tokens=800)
