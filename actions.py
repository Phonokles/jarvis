"""
JARVIS Actions
Handles PC control: open apps, files, websites, volume, setups, smart home, etc.
"""

import subprocess
import webbrowser
import os
import re
import time
import requests
from datetime import datetime
from config import Config


class Actions:
    def __init__(self, config: Config):
        self.config = config

        self.app_map = {
            "firefox": "firefox",
            "browser": "firefox",
            "chrome": "google-chrome",
            "terminal": "kitty",
            "files": "nautilus",
            "file manager": "nautilus",
            "calculator": "gnome-calculator",
            "text editor": "gedit",
            "code": "code",
            "vscode": "code",
            "vs code": "code",
            "spotify": "spotify",
            "discord": "discord",
            "steam": "steam",
            "settings": "gnome-control-center",
        }

        self.setups = {
            "gaming setup": self._setup_gaming,
            "gaming mode": self._setup_gaming,
            "start gaming": self._setup_gaming,
            "code setup": self._setup_coding,
            "coding setup": self._setup_coding,
            "coding mode": self._setup_coding,
            "start coding": self._setup_coding,
            "developer mode": self._setup_coding,
        }

    def handle(self, text: str) -> str | None:
        text_lower = text.lower().strip()

        # --- Setup profiles (check first!) ---
        for keyword, func in self.setups.items():
            if keyword in text_lower:
                return func()

        # --- Time & Date ---
        if any(w in text_lower for w in ["what time", "current time", "what's the time"]):
            return f"It's {datetime.now().strftime('%I:%M %p')}."

        if any(w in text_lower for w in ["what day", "what's today", "today's date", "what date"]):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

        # --- Open Applications ---
        if text_lower.startswith("open ") or "launch " in text_lower:
            app_name = text_lower.replace("open ", "").replace("launch ", "").strip()
            return self._open_app(app_name)

        # --- Open Websites ---
        if "go to " in text_lower or "open website" in text_lower:
            match = re.search(r"go to (.+)", text_lower)
            if match:
                site = match.group(1).strip()
                if not site.startswith("http"):
                    site = f"https://{site}"
                webbrowser.open(site)
                return f"Opening {site}."

        # --- Volume Control ---
        if "volume up" in text_lower or "turn up" in text_lower:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
            return "Volume increased."

        if "volume down" in text_lower or "turn down" in text_lower:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
            return "Volume decreased."

        if "mute" in text_lower:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
            return "Audio muted."

        # --- System Commands ---
        if "lock" in text_lower and "screen" in text_lower:
            subprocess.Popen(["loginctl", "lock-session"])
            return "Locking screen."

        if "screenshot" in text_lower:
            path = f"/home/{os.getenv('USER')}/Pictures/jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            subprocess.Popen(["gnome-screenshot", "-f", path])
            return "Screenshot saved."

        if "shutdown" in text_lower or "shut down" in text_lower:
            return "Shutdown cancelled for safety. Please confirm manually."

        if "clear memory" in text_lower or "forget everything" in text_lower:
            return "__RESET_MEMORY__"

        # --- Smart Home ---
        if any(w in text_lower for w in ["turn on", "turn off", "switch on", "switch off"]):
            return self._handle_smart_home(text_lower)

        return None

    # ─── Setup Profiles ────────────────────────────────────────────────────────

    def _setup_gaming(self) -> str:
        apps = [
            ("spotify", "Spotify"),
            ("discord", "Discord"),
            ("steam", "Steam"),
        ]
        launched = []
        for cmd, name in apps:
            try:
                subprocess.Popen([cmd])
                launched.append(name)
                time.sleep(1)
            except FileNotFoundError:
                pass

        if launched:
            return f"Gaming setup ready! Launched {', '.join(launched)}."
        return "Couldn't find any gaming apps. Make sure Spotify, Discord and Steam are installed."

    def _setup_coding(self) -> str:
        launched = []

        # VSCode
        try:
            subprocess.Popen(["code"])
            launched.append("VSCode")
            time.sleep(0.5)
        except FileNotFoundError:
            pass

        # Terminal with cmatrix — tries kitty, alacritty, xterm
        terminal_launched = False
        for term, args in [
            ("foot", ["foot", "bash", "-c", "cmatrix; exec bash"]),
            ("kitty", ["kitty", "--", "bash", "-c", "cmatrix; exec bash"]),
            ("alacritty", ["alacritty", "-e", "bash", "-c", "cmatrix; exec bash"]),
            ("xterm", ["xterm", "-e", "bash", "-c", "cmatrix; exec bash"]),
        ]:
            try:
                subprocess.Popen(args)
                launched.append("terminal with cmatrix")
                terminal_launched = True
                time.sleep(0.5)
                break
            except FileNotFoundError:
                continue

        if not terminal_launched:
            launched.append("no terminal found — install kitty or alacritty")

        # Spotify
        try:
            subprocess.Popen(["spotify"])
            launched.append("Spotify")
        except FileNotFoundError:
            pass

        if launched:
            return f"Coding setup ready! Launched {', '.join(launched)}."
        return "Couldn't launch coding setup."

    # ─── Helpers ───────────────────────────────────────────────────────────────

    def _open_app(self, app_name: str) -> str:
        for keyword, command in self.app_map.items():
            if keyword in app_name:
                try:
                    subprocess.Popen([command])
                    return f"Opening {keyword}."
                except FileNotFoundError:
                    return f"I couldn't find {keyword} on your system."
        try:
            subprocess.Popen([app_name])
            return f"Opening {app_name}."
        except Exception:
            return f"I couldn't find an app called '{app_name}'."

    def _handle_smart_home(self, text: str) -> str | None:
        token = self.config.HOME_ASSISTANT_TOKEN
        if token == "YOUR_HA_TOKEN_HERE":
            return None

        match = re.search(r"turn (on|off) (.+)", text)
        if not match:
            return None

        action = match.group(1)
        device = match.group(2).strip().replace(" ", "_")
        state = "turn_on" if action == "on" else "turn_off"

        try:
            url = f"{self.config.HOME_ASSISTANT_URL}/api/services/homeassistant/{state}"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            resp = requests.post(url, json={"entity_id": f"switch.{device}"}, headers=headers, timeout=5)
            if resp.status_code == 200:
                return f"Turning {action} {device.replace('_', ' ')}."
            return f"Smart home error: {resp.status_code}"
        except Exception as e:
            return f"Couldn't reach Home Assistant: {e}"
