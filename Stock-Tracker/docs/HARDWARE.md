# 24/7 Alert Hardware Options

This tracker only sends alerts while its host is powered on, awake, online, and able to reach the APIs.

## Best Choices

| Option | Use It If | Main Tradeoff |
|---|---|---|
| Raspberry Pi 4/5 | You want cheap always-on home alerts | Requires Linux setup |
| Mini PC | You want an easy always-on Windows or Linux box | Costs more than a Pi |
| Old laptop | You already have spare hardware | Higher power use |
| NAS/home server | You already run one 24/7 | Setup varies by device |
| VPS/cloud server | You want alerts even if home power/internet fails | Monthly cost |

## Recommendation
Best home setup: Raspberry Pi 4/5 with Raspberry Pi OS Lite, this project in a Python `venv`, and a `systemd` service for `main.py`. Most reliable setup: a VPS, because it keeps running if home power/internet fails.

## Raspberry Pi Quick Setup

```bash
sudo apt update && sudo apt install python3 python3-venv git
git clone YOUR_REPO_URL stock-tracker
cd stock-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
python main.py
```

## Raspberry Pi Auto-Start

Create `/etc/systemd/system/stock-tracker.service`:

```ini
[Unit]
Description=Stock Tracker Alerts
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=/home/pi/stock-tracker
Environment=OPENAI_API_KEY=YOUR_OPENAI_API_KEY
ExecStart=/home/pi/stock-tracker/venv/bin/python /home/pi/stock-tracker/main.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
```

Enable and inspect it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-tracker
sudo systemctl start stock-tracker
sudo systemctl status stock-tracker
journalctl -u stock-tracker -f
```

## HTTP UI Note

`web_ui.py` binds to `127.0.0.1`, so it is local-only. For Pi access, use SSH port forwarding or add authentication before binding to `0.0.0.0`. Do not expose the current UI publicly.

## Reliability Tips

- Use wired Ethernet if possible.
- Use a reliable power adapter or UPS.
- Configure auto-start on boot.
- Keep API keys private.
- Move `data/seen_items.json` with the app if you migrate machines.
