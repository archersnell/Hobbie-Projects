import asyncio

from bleak import BleakScanner
from bleak.exc import BleakBluetoothNotAvailableError


async def main() -> None:
    print("Scanning for nearby Bluetooth devices for 10 seconds...")
    try:
        devices = await BleakScanner.discover(timeout=10.0)
    except BleakBluetoothNotAvailableError as exc:
        print(f"Bluetooth scan failed: {exc}")
        return

    if not devices:
        print("No Bluetooth devices found.")
        return

    print(f"Found {len(devices)} device(s):")
    for device in devices:
        name = device.name or "Unknown"
        print(f"- {name} [{device.address}]")


if __name__ == "__main__":
    asyncio.run(main())
