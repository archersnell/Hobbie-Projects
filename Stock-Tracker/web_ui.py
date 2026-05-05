"""
Runs a small local HTTP UI for viewing and managing the stock tracker.
"""

from datetime import date
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from config import load_config, save_config
from notifier import test_notification
from sources.state import load_seen_items
from sources.time_utils import is_market_day, now_local


HOST = "127.0.0.1"
PORT = 8799


# Masks sensitive values while still showing whether they are configured.
def mask_secret(value: str) -> str:
    if not value:
        return "not set"

    if len(value) <= 8:
        return "set"

    return f"{value[:4]}...{value[-4:]}"


# Normalizes user-submitted ticker symbols.
def clean_ticker(value: str) -> str:
    return "".join(str(value or "").upper().split())


# Builds the shared page wrapper for the UI.
def render_page(title: str, body: str, notice: str = "") -> bytes:
    notice_html = f'<div class="notice">{escape(notice)}</div>' if notice else ""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #637083;
      --line: #d9e0e7;
      --accent: #126b5d;
      --accent-dark: #0d4e44;
      --danger: #a53434;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }}

    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 32px auto;
    }}

    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 20px;
    }}

    h1 {{
      margin: 0;
      font-size: 28px;
      font-weight: 700;
    }}

    h2 {{
      margin: 0 0 14px;
      font-size: 18px;
    }}

    .muted {{
      color: var(--muted);
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 16px;
    }}

    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}

    .wide {{
      grid-column: span 8;
    }}

    .side {{
      grid-column: span 4;
    }}

    .full {{
      grid-column: 1 / -1;
    }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}

    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcfd;
    }}

    .stat strong {{
      display: block;
      margin-bottom: 4px;
      font-size: 22px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    th,
    td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: middle;
    }}

    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}

    form {{
      margin: 0;
    }}

    .form_row {{
      display: grid;
      grid-template-columns: 120px 1fr auto;
      gap: 10px;
      align-items: center;
    }}

    input {{
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
    }}

    button {{
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      padding: 8px 12px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}

    button:hover {{
      background: var(--accent-dark);
    }}

    .danger {{
      background: var(--danger);
    }}

    .notice {{
      margin-bottom: 16px;
      border: 1px solid #bdd7cf;
      border-radius: 8px;
      background: #e8f4f1;
      padding: 12px 14px;
    }}

    .stack {{
      display: grid;
      gap: 12px;
    }}

    @media (max-width: 780px) {{
      header {{
        display: block;
      }}

      .wide,
      .side {{
        grid-column: 1 / -1;
      }}

      .stats,
      .form_row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Stock Tracker</h1>
        <div class="muted">Local control panel for alerts, watchlist, and setup checks.</div>
      </div>
      <div class="muted">Running at {escape(now_local().strftime("%Y-%m-%d %H:%M %Z"))}</div>
    </header>
    {notice_html}
    {body}
  </main>
</body>
</html>"""
    return html.encode("utf-8")


# Builds the current status cards.
def render_status_cards(config: dict) -> str:
    seen_count = len(load_seen_items())
    market_state = "Market day" if is_market_day() else "Closed/weekend"
    alert_settings = config.get("alert_settings", {})
    news_interval = alert_settings.get("breaking_news_check_interval_minutes", "unknown")
    insider_interval = alert_settings.get("insider_trade_check_interval_minutes", "unknown")

    return f"""
<section class="panel full">
  <h2>Status</h2>
  <div class="stats">
    <div class="stat">
      <strong>{len(config.get("watchlist", []))}</strong>
      <span class="muted">Watched stocks</span>
    </div>
    <div class="stat">
      <strong>{seen_count}</strong>
      <span class="muted">Seen alert IDs</span>
    </div>
    <div class="stat">
      <strong>{escape(market_state)}</strong>
      <span class="muted">Current alert window</span>
    </div>
  </div>
  <p class="muted">News checks every {escape(str(news_interval))} minutes. Insider checks every {escape(str(insider_interval))} minutes.</p>
</section>
"""


# Builds the watchlist table and add form.
def render_watchlist(config: dict) -> str:
    rows = []
    for stock in config.get("watchlist", []):
        ticker = escape(stock.get("ticker", ""))
        name = escape(stock.get("name", ""))
        added = escape(stock.get("added", ""))
        rows.append(f"""
<tr>
  <td><strong>{ticker}</strong></td>
  <td>{name}</td>
  <td>{added}</td>
  <td>
    <form method="post" action="/watchlist/remove">
      <input type="hidden" name="ticker" value="{ticker}">
      <button class="danger" type="submit">Remove</button>
    </form>
  </td>
</tr>
""")

    table_rows = "".join(rows) or '<tr><td colspan="4" class="muted">No stocks are being watched yet.</td></tr>'
    return f"""
<section class="panel wide">
  <h2>Watchlist</h2>
  <table>
    <thead>
      <tr>
        <th>Ticker</th>
        <th>Name</th>
        <th>Added</th>
        <th></th>
      </tr>
    </thead>
    <tbody>{table_rows}</tbody>
  </table>
</section>
<section class="panel side">
  <h2>Add Stock</h2>
  <form class="stack" method="post" action="/watchlist/add">
    <input name="ticker" placeholder="Ticker, e.g. NVDA" required>
    <input name="name" placeholder="Company name">
    <button type="submit">Add to watchlist</button>
  </form>
</section>
"""


# Builds setup and action controls.
def render_controls(config: dict) -> str:
    pushover = config.get("pushover", {})
    finnhub = config.get("finnhub", {})
    return f"""
<section class="panel wide">
  <h2>Setup</h2>
  <table>
    <tbody>
      <tr><th>Pushover user</th><td>{escape(mask_secret(pushover.get("user_key", "")))}</td></tr>
      <tr><th>Pushover token</th><td>{escape(mask_secret(pushover.get("api_token", "")))}</td></tr>
      <tr><th>Finnhub key</th><td>{escape(mask_secret(finnhub.get("api_key", "")))}</td></tr>
      <tr><th>Timezone</th><td>{escape(config.get("alert_settings", {}).get("timezone", "not set"))}</td></tr>
    </tbody>
  </table>
</section>
<section class="panel side">
  <h2>Actions</h2>
  <form class="stack" method="post" action="/test-notification">
    <button type="submit">Send test notification</button>
    <span class="muted">Sends one normal Pushover alert to confirm delivery.</span>
  </form>
</section>
"""


# Builds the complete dashboard body.
def render_dashboard(notice: str = "") -> bytes:
    config = load_config()
    body = f"""
<div class="grid">
  {render_status_cards(config)}
  {render_watchlist(config)}
  {render_controls(config)}
</div>
"""
    return render_page("Stock Tracker", body, notice)


# Reads and parses a submitted HTML form.
def read_form(handler: BaseHTTPRequestHandler) -> dict:
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw_body = handler.rfile.read(content_length).decode("utf-8")
    parsed = parse_qs(raw_body)
    return {key: values[0] for key, values in parsed.items()}


# Adds a stock to the watchlist if it is not already present.
def add_stock(ticker: str, name: str) -> str:
    config = load_config()
    clean_symbol = clean_ticker(ticker)
    clean_name = " ".join(str(name or clean_symbol).split())

    if not clean_symbol:
        return "Ticker is required."

    existing = {stock.get("ticker") for stock in config.get("watchlist", [])}
    if clean_symbol in existing:
        return f"{clean_symbol} is already on the watchlist."

    config.setdefault("watchlist", []).append({
        "ticker": clean_symbol,
        "name": clean_name or clean_symbol,
        "added": str(date.today()),
    })
    save_config(config)
    return f"Added {clean_symbol} to the watchlist."


# Removes a stock from the watchlist if it exists.
def remove_stock(ticker: str) -> str:
    config = load_config()
    clean_symbol = clean_ticker(ticker)
    original_count = len(config.get("watchlist", []))

    config["watchlist"] = [
        stock for stock in config.get("watchlist", []) if stock.get("ticker") != clean_symbol
    ]

    if len(config["watchlist"]) == original_count:
        return f"{clean_symbol} was not found on the watchlist."

    save_config(config)
    return f"Removed {clean_symbol} from the watchlist."


# Handles HTTP requests for the local UI.
class stock_tracker_handler(BaseHTTPRequestHandler):
    # Serves the dashboard page.
    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Not found")
            return

        self.respond_html(render_dashboard())

    # Handles form submissions from the dashboard.
    def do_POST(self) -> None:
        form = read_form(self)

        if self.path == "/watchlist/add":
            notice = add_stock(form.get("ticker", ""), form.get("name", ""))
        elif self.path == "/watchlist/remove":
            notice = remove_stock(form.get("ticker", ""))
        elif self.path == "/test-notification":
            notice = "Test notification sent." if test_notification() else "Test notification failed. Check the terminal output."
        else:
            self.send_error(404, "Not found")
            return

        self.respond_html(render_dashboard(notice))

    # Writes an HTML response to the browser.
    def respond_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# Starts the local HTTP server.
def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), stock_tracker_handler)
    print(f"[web_ui] Open http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
