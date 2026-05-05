"""
Sends push notifications to your iPhone via the Pushover API.
All other modules call this — nothing else should send notifications directly.
"""

import requests
from config import get_pushover_credentials

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

# Pushover priority levels
PRIORITY_LOWEST  = -2   # No sound, no vibration
PRIORITY_LOW     = -1   # No sound
PRIORITY_NORMAL  =  0   # Default
PRIORITY_HIGH    =  1   # Bypasses quiet hours, makes sound
PRIORITY_URGENT  =  2   # Repeats until acknowledged (requires retry + expire)


def send_notification(
    title: str,
    message: str,
    priority: int = PRIORITY_NORMAL,
    url: str = None,
    url_title: str = None,
) -> bool:
    """
    Sends a push notification to your iPhone via Pushover.
    Returns True if successful, False if something went wrong.
    """
    creds = get_pushover_credentials()

    payload = {
        "token":   creds["api_token"],
        "user":    creds["user_key"],
        "title":   title,
        "message": message,
        "priority": priority,
    }

    # Attach a link if provided (e.g. to a news article or SEC filing)
    if url:
        payload["url"] = url
        payload["url_title"] = url_title or "Read more"

    # Urgent priority requires retry/expire so the alert repeats until acknowledged
    if priority == PRIORITY_URGENT:
        payload["retry"]  = 60    # Retry every 60 seconds
        payload["expire"] = 3600  # Stop retrying after 1 hour

    try:
        response = requests.post(PUSHOVER_API_URL, data=payload, timeout=10)
        result = response.json()

        if result.get("status") == 1:
            print(f"[notifier] ✅ Sent: {title}")
            return True
        else:
            print(f"[notifier] ❌ Pushover error: {result.get('errors')}")
            return False

    except requests.RequestException as e:
        print(f"[notifier] ❌ Network error sending notification: {e}")
        return False


# --- Convenience helpers so other modules don't need to know priority levels ---

def send_breaking_alert(title: str, message: str, url: str = None) -> bool:
    """High-priority alert for urgent news — bypasses iPhone quiet hours."""
    return send_notification(title, message, priority=PRIORITY_HIGH, url=url)


def send_normal_alert(title: str, message: str, url: str = None) -> bool:
    """Standard alert for earnings, insider trades, etc."""
    return send_notification(title, message, priority=PRIORITY_NORMAL, url=url)


def send_digest_alert(title: str, message: str) -> bool:
    """Low-priority alert for weekly outlooks and summaries — silent delivery."""
    return send_notification(title, message, priority=PRIORITY_LOW)


def test_notification() -> bool:
    """Sends a test ping to confirm your Pushover keys are working."""
    return send_normal_alert(
        title="✅ Quantum Tracker Connected",
        message="Your stock alert system is set up and running correctly.",
    )
