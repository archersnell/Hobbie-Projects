"""
Sends push notifications to your iPhone via the Pushover API.
All other modules call this; nothing else should send notifications directly.
"""

import requests

from config import get_pushover_credentials


PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

PRIORITY_LOWEST = -2
PRIORITY_LOW = -1
PRIORITY_NORMAL = 0
PRIORITY_HIGH = 1
PRIORITY_URGENT = 2


# Posts to Pushover without inheriting broken system proxy settings.
def post_to_pushover(payload: dict) -> requests.Response:
    session = requests.Session()
    session.trust_env = False
    return session.post(PUSHOVER_API_URL, data=payload, timeout=10)


# Sends a push notification to your iPhone via Pushover.
def send_notification(
    title: str,
    message: str,
    priority: int = PRIORITY_NORMAL,
    url: str = None,
    url_title: str = None,
) -> bool:
    creds = get_pushover_credentials()

    payload = {
        "token": creds["api_token"],
        "user": creds["user_key"],
        "title": title,
        "message": message,
        "priority": priority,
    }

    if url:
        payload["url"] = url
        payload["url_title"] = url_title or "Read more"

    if priority == PRIORITY_URGENT:
        payload["retry"] = 60
        payload["expire"] = 3600

    try:
        response = post_to_pushover(payload)
        result = response.json()

        if result.get("status") == 1:
            print(f"[notifier] Sent: {title}")
            return True

        print(f"[notifier] Pushover error: {result.get('errors')}")
        return False
    except requests.RequestException as exc:
        print(f"[notifier] Network error sending notification: {exc}")
        return False


# Sends a high-priority alert for urgent news.
def send_breaking_alert(title: str, message: str, url: str = None) -> bool:
    return send_notification(title, message, priority=PRIORITY_HIGH, url=url)


# Sends a standard alert for normal notifications.
def send_normal_alert(title: str, message: str, url: str = None) -> bool:
    return send_notification(title, message, priority=PRIORITY_NORMAL, url=url)


# Sends a low-priority alert for weekly digests.
def send_digest_alert(title: str, message: str) -> bool:
    return send_notification(title, message, priority=PRIORITY_LOW)


# Sends a test ping to confirm your Pushover keys are working.
def test_notification() -> bool:
    return send_normal_alert(
        title="Quantum Tracker Connected",
        message="Your stock alert system is set up and running correctly.",
    )
