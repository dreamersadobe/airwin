"""Application configuration and persistent settings."""

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    auto_pause_enabled: bool = True
    popup_on_case_open: bool = True
    popup_duration_sec: int = 5
    tray_show_percentage: bool = True
    low_latency_audio_fix: bool = True
    launch_on_startup: bool = False
    dark_mode: bool = True
    preferred_device_mac: str = ""
    demo_mode: bool = False

    @classmethod
    def get_config_path(cls) -> Path:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", str(Path.home()))
            path = Path(base) / "AirWin"
        else:
            path = Path.home() / ".config" / "airwin"
        path.mkdir(parents=True, exist_ok=True)
        return path / "config.json"

    @classmethod
    def load(cls) -> "AppConfig":
        config_path = cls.get_config_path()
        if not config_path.exists():
            config = cls()
            config.save()
            return config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        except Exception:
            return cls()

    def save(self) -> None:
        config_path = self.get_config_path()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")
