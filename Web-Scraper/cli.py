import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple multi-URL web scraper"
    )

    parser.add_argument(
        "urls",
        nargs="*",
        help="URLs to scrape (space-separated)"
    )

    parser.add_argument(
        "--url-file",
        type=Path,
        help="Path to text file containing URLs (one per line)"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Request timeout in seconds"
    )

    parser.add_argument(
        "--max-headings",
        type=int,
        default=5,
        help="Maximum headings to collect per page"
    )

    parser.add_argument(
        "--max-links",
        type=int,
        default=5,
        help="Maximum links to collect per page"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay between requests (seconds)"
    )

    parser.add_argument(
        "--out-json",
        type=Path,
        help="Write output to JSON file"
    )

    parser.add_argument(
        "--out-csv",
        type=Path,
        help="Write output to CSV file"
    )

    return parser.parse_args()
