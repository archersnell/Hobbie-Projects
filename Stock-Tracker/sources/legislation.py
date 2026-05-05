"""
Monitors public government sources for quantum funding and export-control alerts.
"""

from datetime import timedelta

import requests

from notifier import send_normal_alert
from sources.state import has_seen_item, mark_item_seen
from sources.time_utils import now_local


FEDERAL_REGISTER_URL = "https://www.federalregister.gov/api/v1/documents.json"
GRANTS_SEARCH_URL = "https://api.grants.gov/v1/api/search2"

FEDERAL_REGISTER_QUERIES = [
    "quantum computing",
    "quantum technology",
    "export controls quantum",
    "CHIPS Act quantum",
]

GRANTS_QUERIES = [
    "quantum computing",
    "quantum information science",
    "quantum technology",
]


# Returns the oldest date to include in government-source searches.
def get_search_start_date() -> str:
    return (now_local().date() - timedelta(days=7)).isoformat()


# Fetches matching Federal Register documents for one search term.
def fetch_federal_register_documents(query: str) -> list[dict]:
    params = [
        ("conditions[term]", query),
        ("conditions[publication_date][gte]", get_search_start_date()),
        ("order", "newest"),
        ("per_page", "10"),
        ("fields[]", "document_number"),
        ("fields[]", "title"),
        ("fields[]", "publication_date"),
        ("fields[]", "type"),
        ("fields[]", "html_url"),
        ("fields[]", "abstract"),
    ]

    try:
        response = requests.get(FEDERAL_REGISTER_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as exc:
        print(f"[legislation] Federal Register error for '{query}': {exc}")
        return []


# Fetches matching Grants.gov opportunities for one search term.
def fetch_grants_opportunities(query: str) -> list[dict]:
    payload = {
        "rows": 10,
        "keyword": query,
        "oppStatuses": "forecasted|posted",
    }

    try:
        response = requests.post(GRANTS_SEARCH_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("oppHits", [])
    except requests.RequestException as exc:
        print(f"[legislation] Grants.gov error for '{query}': {exc}")
        return []


# Converts a Federal Register document into a notification payload.
def format_federal_register_alert(item: dict) -> tuple[str, str, str | None]:
    title = item.get("title", "Federal Register update")
    publication_date = item.get("publication_date", "unknown date")
    document_type = item.get("type", "document")
    abstract = item.get("abstract") or "New matching Federal Register document."
    message = f"{document_type} published {publication_date}\n\n{abstract[:700]}"
    return f"Federal Register: {title[:70]}", message, item.get("html_url")


# Converts a Grants.gov opportunity into a notification payload.
def format_grants_alert(item: dict) -> tuple[str, str, str | None]:
    title = item.get("title", "Grants.gov opportunity")
    agency = item.get("agencyName", "Unknown agency")
    open_date = item.get("openDate", "unknown")
    close_date = item.get("closeDate") or "not listed"
    status = item.get("oppStatus", "unknown")
    opportunity_id = item.get("id")
    url = f"https://www.grants.gov/search-results-detail/{opportunity_id}" if opportunity_id else None
    message = f"{agency}\nStatus: {status}\nOpen: {open_date}\nClose: {close_date}"
    return f"Grant: {title[:85]}", message, url


# Sends one alert if the item has not already been sent.
def send_legislation_item(item_id: str, title: str, message: str, url: str | None) -> None:
    if has_seen_item(item_id):
        return

    if send_normal_alert(title, message, url):
        mark_item_seen(item_id)


# Checks public government sources for quantum policy and funding updates.
def check_legislation_updates() -> None:
    for query in FEDERAL_REGISTER_QUERIES:
        for item in fetch_federal_register_documents(query):
            document_number = item.get("document_number")
            if not document_number:
                continue

            title, message, url = format_federal_register_alert(item)
            send_legislation_item(f"federal-register:{document_number}", title, message, url)

    for query in GRANTS_QUERIES:
        for item in fetch_grants_opportunities(query):
            opportunity_id = item.get("id") or item.get("number")
            if not opportunity_id:
                continue

            title, message, url = format_grants_alert(item)
            send_legislation_item(f"grants:{opportunity_id}", title, message, url)
