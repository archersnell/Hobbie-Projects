# Bluetooth Scanner

This project scans for nearby Bluetooth devices for 10 seconds using `bleak` and prints any devices it finds.

## Files

- `scan_bluetooth.py`: Bluetooth scanning script
- `requirements.txt`: Python dependencies
- `.venv/`: Local virtual environment

## Setup

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run

Run the scanner:

```powershell
python .\scan_bluetooth.py
```

## Notes

- The script scans for 10 seconds and prints each device as `name [address]`.
- If no devices are found, it prints a message and exits.
- If Bluetooth is turned off, it prints a readable error instead of a traceback.
- This project currently targets Python 3.14 with `bleak` 3.x.
