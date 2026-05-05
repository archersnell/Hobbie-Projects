"""
Uses the OpenAI API to generate concise stock summaries and digests.
"""

import os

from openai import OpenAI

from config import get_tickers


MODEL_NAME = "gpt-5.4-mini"


# Returns a configured OpenAI client, or None if the API key is missing.
def get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[summarizer] OPENAI_API_KEY is not set; skipping AI summary.")
        return None

    return OpenAI(api_key=api_key)


# Sends a prompt to OpenAI and returns the text response.
def generate_summary(prompt: str, max_tokens: int = 600) -> str | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.responses.create(
            model=MODEL_NAME,
            input=prompt,
            max_output_tokens=max_tokens,
        )
        return response.output_text.strip()
    except Exception as exc:
        print(f"[summarizer] Error generating summary: {exc}")
        return None


# Summarizes an earnings result for a single ticker.
def summarize_earnings(ticker: str, earnings_data: dict) -> str | None:
    prompt = f"""
Write a short phone notification for {ticker} earnings.
Use this exact compact structure:
Category: Earnings results
EPS: actual vs estimate, and whether it beat or missed
Revenue: actual vs estimate, and whether it beat or missed
Takeaway: one short investor-relevant sentence
Watch for: one short follow-up item if available

Keep it under 650 characters. Do not include raw JSON or markdown.

Data:
{earnings_data}
"""
    return generate_summary(prompt)


# Creates a weekly outlook or weekly recap for the current watchlist.
def generate_weekly_digest(kind: str) -> str | None:
    tickers = ", ".join(get_tickers())
    prompt = f"""
Write a concise {kind} phone notification for these watched stocks: {tickers}.
Use this exact compact structure:
Category: {kind.title()}
Focus: one sentence on the most important theme
Watchlist: 2-3 ticker-specific notes in one line
Risks/catalysts: one short line

Keep it under 800 characters. Be specific, plain English, and avoid hype.
"""
    return generate_summary(prompt, max_tokens=800)
