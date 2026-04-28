import random
import threading
import time
from dataclasses import dataclass

from pynput import keyboard, mouse


@dataclass
class ClickerConfig:
    cps: float = 10.0                 # clicks per second
    button: str = "left"              # "left" or "right"
    jitter: float = 0.15              # 0.0–0.5 typical; fraction of base delay
    toggle_key: str = "<f6>"          # global hotkey to toggle on/off
    quit_key: str = "<f8>"            # global hotkey to quit
    failsafe_corner_stop: bool = True # move mouse to top-left to stop


class AutoClicker:
    def __init__(self, cfg: ClickerConfig):
        self.cfg = cfg
        self.mouse_ctl = mouse.Controller()
        self.running = False
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)

    def start(self):
        self._thread.start()

    def toggle(self):
        self.running = not self.running
        state = "ON" if self.running else "OFF"
        print(f"[+] Clicker: {state} | cps={self.cfg.cps} | button={self.cfg.button} | jitter={self.cfg.jitter}")

    def stop_forever(self):
        print("[!] Quitting...")
        self.running = False
        self._stop_event.set()

    def _get_button(self):
        return mouse.Button.left if self.cfg.button.lower() == "left" else mouse.Button.right

    def _worker(self):
        while not self._stop_event.is_set():
            if not self.running:
                time.sleep(0.01)
                continue

            # Optional failsafe: moving mouse to (0,0) turns it off
            if self.cfg.failsafe_corner_stop:
                x, y = self.mouse_ctl.position
                if x <= 0 and y <= 0:
                    self.running = False
                    print("[!] Failsafe triggered (mouse at top-left). Clicker OFF.")
                    continue

            # Base delay from CPS
            cps = max(0.1, float(self.cfg.cps))
            base_delay = 1.0 / cps

            # Randomize delay: +/- jitter fraction
            j = max(0.0, float(self.cfg.jitter))
            low = base_delay * (1.0 - j)
            high = base_delay * (1.0 + j)
            delay = random.uniform(low, high)

            # Click
            self.mouse_ctl.click(self._get_button(), 1)

            # Sleep (but allow quick stop)
            end = time.time() + delay
            while time.time() < end and not self._stop_event.is_set():
                if not self.running:
                    break
                time.sleep(0.001)


def main():
    cfg = ClickerConfig(
        cps=12.0,
        button="left",
        jitter=0.20,
        toggle_key="<f6>",
        quit_key="<f8>",
        failsafe_corner_stop=True,
    )
    clicker = AutoClicker(cfg)
    clicker.start()

    print("Smart Auto Clicker")
    print(f"Toggle: {cfg.toggle_key} | Quit: {cfg.quit_key}")
    print("Failsafe: move mouse to top-left corner to stop (if enabled).")

    hotkeys = {
        cfg.toggle_key: clicker.toggle,
        cfg.quit_key: clicker.stop_forever,
    }

    # Global hotkeys listener
    with keyboard.GlobalHotKeys(hotkeys) as h:
        h.join()


if __name__ == "__main__":
    main()
