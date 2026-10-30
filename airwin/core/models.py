"""Data models for AirPods devices, battery status, and noise control."""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Optional


class AirPodsModel(Enum):
    AIRPODS_1 = ("AirPods (1-го поколения)", False, "airpods_1")
    AIRPODS_2 = ("AirPods (2-го поколения)", False, "airpods_2")
    AIRPODS_3 = ("AirPods (3-го поколения)", False, "airpods_3")
    AIRPODS_4 = ("AirPods 4", True, "airpods_4")
    AIRPODS_PRO = ("AirPods Pro (1-го поколения)", True, "airpods_pro")
    AIRPODS_PRO_2 = ("AirPods Pro (2-го поколения)", True, "airpods_pro_2")
    AIRPODS_MAX = ("AirPods Max", True, "airpods_max")
    POWERBEATS_PRO = ("Powerbeats Pro", False, "powerbeats_pro")
    BEATS_SOLO_PRO = ("Beats Solo Pro", True, "beats_solo_pro")
    BEATS_STUDIO_BUDS = ("Beats Studio Buds", True, "beats_studio_buds")
    BEATS_FIT_PRO = ("Beats Fit Pro", True, "beats_fit_pro")
    UNKNOWN = ("AirPods", False, "airpods_pro")

    def __init__(self, display_name: str, has_anc: bool, icon_name: str):
        self.display_name = display_name
        self.has_anc = has_anc
        self.icon_name = icon_name


class NoiseControlMode(Enum):
    OFF = "Выкл"
    NOISE_CANCELLATION = "Шумоподавление"
    TRANSPARENCY = "Прозрачность"
    ADAPTIVE = "Адаптивный"


@dataclass
class AirPodsState:
    model: AirPodsModel = AirPodsModel.UNKNOWN
    device_name: str = "AirPods"
    mac_address: Optional[str] = None

    # Battery levels: 0..100, or -1 if unknown / unavailable
    left_battery: int = -1
    right_battery: int = -1
    case_battery: int = -1

    # Charging states
    left_charging: bool = False
    right_charging: bool = False
    case_charging: bool = False

    # Ear presence detection
    left_in_ear: bool = False
    right_in_ear: bool = False

    # Case lid status
    case_open: bool = False

    # Connection state
    connected: bool = False

    # Noise control
    noise_mode: NoiseControlMode = NoiseControlMode.OFF

    # Signal & metadata
    rssi: int = -100
    last_updated: float = field(default_factory=time.time)

    @property
    def is_in_ear(self) -> bool:
        """Returns True if at least one earbud is in ear."""
        return self.left_in_ear or self.right_in_ear

    @property
    def both_in_ear(self) -> bool:
        """Returns True if both earbuds are in ear."""
        return self.left_in_ear and self.right_in_ear

    @property
    def left_available(self) -> bool:
        return self.left_battery >= 0

    @property
    def right_available(self) -> bool:
        return self.right_battery >= 0

    @property
    def case_available(self) -> bool:
        return self.case_battery >= 0

    @property
    def average_earbud_battery(self) -> int:
        levels = [b for b in (self.left_battery, self.right_battery) if b >= 0]
        if not levels:
            return -1
        return round(sum(levels) / len(levels))

    def copy(self) -> "AirPodsState":
        return AirPodsState(
            model=self.model,
            device_name=self.device_name,
            mac_address=self.mac_address,
            left_battery=self.left_battery,
            right_battery=self.right_battery,
            case_battery=self.case_battery,
            left_charging=self.left_charging,
            right_charging=self.right_charging,
            case_charging=self.case_charging,
            left_in_ear=self.left_in_ear,
            right_in_ear=self.right_in_ear,
            case_open=self.case_open,
            connected=self.connected,
            noise_mode=self.noise_mode,
            rssi=self.rssi,
            last_updated=self.last_updated,
        )
