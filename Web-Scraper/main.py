import json
import csv
from cli import parse_args
from scraper import run_scraper

def main():
    args = parse_args()
    try:
        results = run_scraper(args)
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(results, indent=2),
            encoding="utf-8"
        )
        print(f"\nJSON written to: {args.out_json.resolve()}")

    if args.out_csv:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)
        print(f"CSV written to: {args.out_csv.resolve()}")

if __name__ == "__main__":
    main()
