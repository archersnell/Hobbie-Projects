import time
from urllib.parse import urlparse
import requests
import certifi
from bs4 import BeautifulSoup, SoupStrainer

def validate_url(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname:
        return False

    # Treat bare hostnames like "google" as invalid user input.
    return hostname == "localhost" or "." in hostname

def run_scraper(args):
    urls = list(args.urls)

    if args.url_file:
        file_urls = [
            line.strip()
            for line in args.url_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        urls.extend(file_urls)

    if not urls:
        raise SystemExit("No URLs provided.")

    # Normalize URLs
    normalized_urls = []
    for url in urls:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if not validate_url(url):
            raise ValueError(f"Invalid URL provided: {url}")

        normalized_urls.append(url)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    only = SoupStrainer(["title", "h1","h2","h3","h4","h5","h6","a"])
    results = []

    for url in normalized_urls:
        start = time.perf_counter()
        try:
            response = session.get(
                url,
                verify=certifi.where(),
                timeout=args.timeout
            )
        except requests.exceptions.InvalidURL as exc:
            raise ValueError(f"Invalid URL provided: {url}") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ValueError(f"Could not connect to URL: {url}") from exc

        req_time = round(time.perf_counter() - start, 1)

        soup = BeautifulSoup(response.text, "lxml", parse_only=only)

        title = soup.title.get_text(strip=True) if soup.title else "No title found"
        headings = soup.find_all(["h1","h2","h3","h4","h5","h6"])
        links = soup.find_all("a")

        results.append({
            "url": url,
            "status_code": response.status_code,
            "request_seconds": req_time,
            "title": title,
            "heading_count": len(headings),
            "link_count": len(links),
        })

        print(f"\n{url}")
        print(f"Status: {response.status_code}")
        print(f"Title: {title}")
        print(f"Request Time: {req_time}")

        if args.delay > 0:
            time.sleep(args.delay)

    return results
