# Stock Tracker

A small Windows background app that watches stocks, checks news/earnings/insider trades/government updates, and sends useful push alerts to your iPhone through Pushover.

## What You Need

- Windows
- Python 3
- Pushover user key and app token
- Finnhub API key
- Optional: `OPENAI_API_KEY` for AI earnings and weekly summaries

## First-Time Setup

Open PowerShell in the project folder:

```powershell
cd "C:\Users\atsne\Downloads\Professional Dev\GitHubProjects\Stock-Tracker"
```

Create and activate the virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set your API keys:

```powershell
python manage.py set-key pushover_user YOUR_PUSHOVER_USER_KEY
python manage.py set-key pushover_token YOUR_PUSHOVER_APP_TOKEN
python manage.py set-key finnhub YOUR_FINNHUB_API_KEY
```

Send a test notification:

```powershell
python manage.py test-notification
```

## CLI Commands

List watched stocks:

```powershell
python manage.py list
```

Add a stock:

```powershell
python manage.py add NVDA "NVIDIA Corp."
```

Remove a stock:

```powershell
python manage.py remove NVDA
```

Send a test notification:

```powershell
python manage.py test-notification
```

Run the tracker manually:

```powershell
python main.py
```

Stop manual mode with `Ctrl+C`.

## Notification Schedule

- Breaking news: every 15 minutes from 8:00 AM to 6:00 PM ET on market days.
- Earnings reminders: 8:00 AM ET on report days.
- Earnings results: checked hourly on market days.
- Insider trades: every 60 minutes on market days.
- Legislation/funding updates: 7:30 AM ET daily.
- Weekly outlook: Monday at 8:00 AM ET.
- Weekly summary: Friday at 4:00 PM ET.

## Local HTTP UI

Start the UI:

```powershell
python web_ui.py
```

Open this in your browser:

```text
http://127.0.0.1:8799
```

The UI currently supports:

- View tracker status
- View watched stocks
- Add/remove stocks
- Check masked API key status
- Send a test notification

## More Docs

- [24/7 hardware options](HARDWARE.md)

## Install Background Startup Task

Open **PowerShell as Administrator**, then run:

```powershell
cd "C:\Users\atsne\Downloads\Professional Dev\GitHubProjects\Stock-Tracker"
.\setup_task_scheduler.ps1
```

Start the task immediately:

```powershell
Start-ScheduledTask -TaskName "Stock Tracker"
```

Check that it exists:

```powershell
Get-ScheduledTask -TaskName "Stock Tracker"
```

Restart it after code changes:

```powershell
Stop-ScheduledTask -TaskName "Stock Tracker"
Start-ScheduledTask -TaskName "Stock Tracker"
```

## Optional AI Summaries

Set `OPENAI_API_KEY` as a Windows environment variable if you want AI earnings summaries and weekly digests.

PowerShell for the current session only:

```powershell
$env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

For permanent setup, use:

```text
Start menu -> Edit environment variables -> User variables -> New
```

Name:

```text
OPENAI_API_KEY
```

Value:

```text
YOUR_OPENAI_API_KEY
```

## Notes

- `config.json` stores live API keys. Do not commit or share it.
- `data\seen_items.json` prevents duplicate alerts after restarts.
- The background scheduler and the HTTP UI are separate processes.
- The UI is local-only at `127.0.0.1`.

