# CODEX — Stock Tracker Project

---

## ✂️ Codex Prompt — Copy This Into Any AI Assistant To Continue Development

```
You are continuing development on a project called stock-tracker.

Read CODEX.md in the project root before doing anything else. It contains the full project context, coding conventions, file structure, what has been built, and what still needs building.

Rules you must follow throughout this project:
- Before writing any code, explain in 3-5 plain English sentences what you are about to build and why.
- If there are multiple ways to solve a problem, give the top 2 options with a one-line tradeoff, recommend one, and proceed unless told otherwise.
- Never assume the most complex solution is wanted. Default to simple and clean.
- Always write complete, working files. No partial snippets.
- Add a short plain-English comment above every function. No over-commenting inside function bodies.
- If building on an existing file, show the full updated file.
- Use snake_case throughout. This is already established in the codebase.
- If something requires an API key or external setup, stop and say so before writing code.
- If a request is ambiguous, ask the single most important clarifying question before proceeding.
- After each feature delivery, end with a short "What's next" section listing 2-3 logical next steps.
- If a requested change would break something else, flag it before making the change.

The developer is on Windows, uses a venv at venv\ in the project root, and is comfortable with APIs and environment variables. This app runs as a background process and sends push notifications to an iPhone via Pushover.

Start by reading CODEX.md, then ask what to build next or proceed with the first unchecked item in the "What Still Needs Building" section.
```

---

This document gives any AI assistant full context to continue development on this project without re-explaining the setup.

---

## Project Summary

A background Python application that monitors a watchlist of stocks and sends push notifications to the developer's iPhone via Pushover. The initial watchlist is focused on quantum computing stocks (IONQ, QBTS, RGTI) but is fully editable via CLI.

---

## Developer Profile

- **OS:** Windows
- **Technical level:** Advanced (comfortable with servers, APIs, env vars)
- **Language preference:** Python
- **Purpose:** Personal use

---

## Notification Delivery

- **Service:** Pushover (pushover.net) — $5 one-time iOS app purchase
- **Platform:** iPhone (iOS)
- **No native app required** — all notifications sent via Pushover REST API

---

## Alert Tiers

| Type | Source | Timing |
|---|---|---|
| Breaking news / disaster | Finnhub news feed + keyword scoring | Immediate, high-priority |
| Earnings report due | Finnhub earnings calendar | Morning of report day (08:00 ET) |
| Earnings summary | Finnhub + OpenAI API | Hourly check, sent when epsActual is populated |
| Insider trades (exec buys/sells) | Finnhub insider transactions | Every 60 min on market days |
| Weekly outlook | OpenAI API summary | Monday 08:00 ET |
| Weekly summary | OpenAI API summary | Friday 16:00 ET |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.x |
| Virtual env | `venv` (located at `venv\` in project root) |
| Push notifications | Pushover API |
| Stock/financial data | Finnhub API (`finnhub-python` SDK) |
| AI summaries | OpenAI API (`openai` SDK) |
| Scheduling | `schedule` library |
| Timezone | `zoneinfo` + `tzdata` for Windows IANA timezone data |
| Background runner | Windows Task Scheduler (to be configured) |

---

## Project Structure

```
stock-tracker/
├── venv\                     # Virtual environment (never edit or commit)
├── data\
│   └── seen_items.json       # Restart-safe deduplication log (auto-created)
├── config.json               # Watchlist, API keys, alert settings — single source of truth
├── config.py                 # Loads/saves config.json, exposes helper functions
├── notifier.py               # Pushover wrapper — ALL notifications go through here
├── manage.py                 # CLI tool: add/remove stocks, set API keys, test notifications
├── web_ui.py                 # Local HTTP UI for watchlist/status/test notifications
├── main.py                   # Scheduler — wires all sources together and runs the loop
├── sources\
│   ├── __init__.py
│   ├── news.py               # Breaking news polling + urgency scoring
│   ├── earnings.py           # Earnings calendar reminders + result summaries
│   ├── insider.py            # SEC insider trade alerts (>$100k threshold)
│   ├── legislation.py        # Federal Register + Grants.gov quantum policy/funding alerts
│   ├── summarizer.py         # OpenAI API — earnings summaries + weekly digests
│   ├── state.py              # Seen-items log: load, save, prune, check, mark
│   └── time_utils.py         # Timezone helpers: now_local, is_weekend, is_market_day
├── setup_task_scheduler.ps1  # Installs Windows Task Scheduler login task
├── requirements.txt
├── .gitignore                # Excludes venv, state, secrets, and cache files
└── CODEX.md                  # This file
```

---

## Coding Conventions

- **Naming:** snake_case throughout
- **Functions:** Short plain-English comment above every function. No over-commenting inside function bodies.
- **Files:** Always complete, working files — no partial snippets
- **Simplicity:** Default to simple and clean. Avoid over-engineering.
- **Imports:** All modules import from `config.py` for settings. Never hardcode keys or tickers.
- **Notifications:** All sends go through `notifier.py`. Sources check the bool return value before calling `mark_item_seen`.
- **State:** All deduplication goes through `sources/state.py`. No module maintains its own seen-items file.

---

## Config Structure (config.json)

```json
{
  "watchlist": [
    { "ticker": "IONQ", "name": "IonQ Inc.", "added": "2026-05-04" },
    { "ticker": "QBTS", "name": "D-Wave Quantum Inc.", "added": "2026-05-04" },
    { "ticker": "RGTI", "name": "Rigetti Computing Inc.", "added": "2026-05-04" }
  ],
  "pushover": {
    "user_key": "...",
    "api_token": "..."
  },
  "finnhub": {
    "api_key": "..."
  },
  "alert_settings": {
    "breaking_news_check_interval_minutes": 15,
    "insider_trade_check_interval_minutes": 60,
    "weekly_outlook_day": "Monday",
    "weekly_outlook_time": "08:00",
    "weekly_summary_day": "Friday",
    "weekly_summary_time": "16:00",
    "market_open": "09:30",
    "market_close": "16:00",
    "timezone": "America/New_York"
  },
  "news_urgency": {
    "high_priority_keywords": [
      "bankruptcy", "fraud", "sec investigation", "delisted", "acquisition",
      "merger", "fda approval", "contract awarded", "major contract",
      "government contract", "department of defense", "breakthrough"
    ]
  }
}
```

---

## Key Functions Reference

### config.py
- `load_config()` → full config dict
- `save_config(config)` → writes back to config.json
- `get_tickers()` → `["IONQ", "QBTS", "RGTI"]`
- `get_pushover_credentials()` → `{ user_key, api_token }`
- `get_finnhub_key()` → string
- `get_alert_settings()` → dict
- `get_urgency_keywords()` → list of strings

### notifier.py
- `send_breaking_alert(title, message, url)` → high priority, bypasses quiet hours, returns bool
- `send_normal_alert(title, message, url)` → standard delivery, returns bool
- `send_digest_alert(title, message)` → silent, low priority, returns bool
- `test_notification()` → sends a test ping to iPhone

### sources/state.py
- `load_seen_items()` → full dict of `{item_id: iso_timestamp}`
- `save_seen_items(seen)` → persists to `data/seen_items.json`, creates dir if needed
- `prune_seen_items(seen)` → removes entries older than 30 days
- `has_seen_item(item_id)` → bool
- `mark_item_seen(item_id)` → loads, prunes, adds, saves

### sources/time_utils.py
- `get_timezone()` → `ZoneInfo` from config
- `now_local()` → current datetime in configured timezone
- `is_weekend()` → bool
- `is_market_day()` → bool

### sources/summarizer.py
- `get_openai_client()` → `OpenAI` client or `None` if `OPENAI_API_KEY` unset
- `generate_summary(prompt, max_tokens)` → string or None
- `summarize_earnings(ticker, earnings_data)` → string or None
- `generate_weekly_digest(kind)` → string or None (kind = "weekly outlook" or "weekly summary")

### manage.py (CLI)
```bat
python manage.py list
python manage.py add TSLA "Tesla Inc."
python manage.py remove TSLA
python manage.py set-key pushover_user YOUR_KEY
python manage.py set-key pushover_token YOUR_TOKEN
python manage.py set-key finnhub YOUR_KEY
python manage.py test-notification
python web_ui.py
```

---

## Environment Variables

| Variable | Required | Used by |
|---|---|---|
| `OPENAI_API_KEY` | Yes (for AI summaries) | `sources/summarizer.py` |

Set permanently via Windows: Start → "Edit environment variables" → New → `OPENAI_API_KEY`

If unset, weekly digests and earnings summaries will be skipped gracefully with a log message. All other alerts still work.

---

## Setup Checklist

- [ ] Python 3.x installed and accessible via `python` in terminal
- [ ] `venv` created: `python -m venv venv`
- [ ] `venv` activated: `venv\Scripts\activate` — prompt shows `(venv)`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Pushover user key set: `python manage.py set-key pushover_user YOUR_KEY`
- [ ] Pushover API token set: `python manage.py set-key pushover_token YOUR_TOKEN`
- [ ] Finnhub API key set: `python manage.py set-key finnhub YOUR_KEY`
- [ ] `OPENAI_API_KEY` set as Windows environment variable
- [ ] Test notification received on iPhone: `python manage.py test-notification`
- [ ] Watchlist looks correct: `python manage.py list`
- [ ] App runs without errors: `python main.py`

---

## What Has Been Built

- [x] `config.json` — watchlist + all settings
- [x] `config.py` — config loader/saver
- [x] `notifier.py` — Pushover notification wrapper
- [x] `manage.py` — CLI watchlist manager
- [x] `web_ui.py` — local HTTP UI for watchlist/status/test notifications
- [x] `requirements.txt` — uses stdlib zoneinfo plus tzdata for Windows
- [x] `sources/__init__.py`
- [x] `sources/state.py` — unified seen-items log with 30-day auto-pruning
- [x] `sources/time_utils.py` — timezone-aware market day helpers
- [x] `sources/news.py` — Finnhub news polling + urgency scoring + deduplication
- [x] `sources/earnings.py` — earnings calendar reminders + result detection + OpenAI summaries
- [x] `sources/insider.py` — insider trade alerts with $100k threshold
- [x] `sources/legislation.py` — Federal Register + Grants.gov monitoring for quantum policy/funding
- [x] `sources/summarizer.py` — OpenAI API summaries, graceful degradation if key missing
- [x] `main.py` — master scheduler with safe error isolation, startup check on launch
- [x] `setup_task_scheduler.ps1` — installs a Windows login scheduled task for `main.py`
- [x] `.gitignore` — excludes `venv\`, `data\`, `config.json`, caches, and env files
- [x] `CODEX.md`

## What Still Needs Building

- [ ] Run `setup_task_scheduler.ps1` locally to install the Windows login task
- [ ] Set `OPENAI_API_KEY` as a Windows environment variable if AI summaries are desired
- [ ] Optional: add richer legislation sources beyond Federal Register and Grants.gov

---

## Important Constraints

- Never send weekend notifications except for urgent breaking news (enforced in `news.py` and source modules via `is_market_day()`)
- All notification sends go through `notifier.py` — no module calls Pushover directly
- `mark_item_seen` is only called after a successful send (gated on bool return)
- The app must survive crashes and restarts without resending old alerts
- `data/seen_items.json` is the single deduplication store — no per-module state files
- `config.json` contains live API keys — never commit or share it
