"""
Master scheduler for the stock tracker background process.
"""

import time

import schedule

from config import get_alert_settings
from notifier import send_digest_alert
from sources.earnings import check_earnings_calendar, check_earnings_results
from sources.insider import check_insider_trades
from sources.legislation import check_legislation_updates
from sources.news import check_breaking_news
from sources.summarizer import generate_weekly_digest
from sources.time_utils import is_market_day, is_within_time_window


# Runs a scheduled job and prevents one failure from stopping the app.
def run_safely(job_name: str, job_func) -> None:
    try:
        print(f"[main] Running {job_name}")
        job_func()
    except Exception as exc:
        print(f"[main] Error in {job_name}: {exc}")


# Generates and sends the Monday weekly outlook digest.
def send_weekly_outlook() -> None:
    digest = generate_weekly_digest("weekly outlook")
    if digest:
        send_digest_alert("Weekly stock outlook", digest)


# Generates and sends the Friday weekly summary digest.
def send_weekly_summary() -> None:
    digest = generate_weekly_digest("weekly summary")
    if digest:
        send_digest_alert("Weekly stock summary", digest)


# Runs the breaking-news check only during the configured weekday alert window.
def check_breaking_news_during_alert_window() -> None:
    settings = get_alert_settings()
    start_time = settings.get("breaking_news_start", "08:00")
    end_time = settings.get("breaking_news_end", "18:00")

    if not is_market_day():
        print("[main] Skipping breaking news outside market days.")
        return

    if not is_within_time_window(start_time, end_time):
        print(f"[main] Skipping breaking news outside {start_time}-{end_time}.")
        return

    check_breaking_news()


# Registers all recurring jobs with the schedule library.
def setup_schedule() -> None:
    settings = get_alert_settings()

    schedule.every(settings["breaking_news_check_interval_minutes"]).minutes.do(
        run_safely,
        "breaking news",
        check_breaking_news_during_alert_window,
    )
    schedule.every(settings["insider_trade_check_interval_minutes"]).minutes.do(
        run_safely,
        "insider trades",
        check_insider_trades,
    )
    schedule.every().day.at("08:00").do(
        run_safely,
        "earnings calendar",
        check_earnings_calendar,
    )
    schedule.every().hour.do(
        run_safely,
        "earnings results",
        check_earnings_results,
    )
    schedule.every().day.at("07:30").do(
        run_safely,
        "legislation updates",
        check_legislation_updates,
    )

    getattr(schedule.every(), settings["weekly_outlook_day"].lower()).at(
        settings["weekly_outlook_time"]
    ).do(run_safely, "weekly outlook", send_weekly_outlook)

    getattr(schedule.every(), settings["weekly_summary_day"].lower()).at(
        settings["weekly_summary_time"]
    ).do(run_safely, "weekly summary", send_weekly_summary)


# Starts the scheduler loop and runs until interrupted.
def main() -> None:
    setup_schedule()
    print("[main] Stock tracker scheduler started.")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
