"""Parser for Apple Continuity Bluetooth LE advertisement packets.

Decodes Apple manufacturer data (0x004C) containing Proximity Pairing (type 0x07)
and Nearby Info (type 0x10) packets for AirPods and Beats devices.
"""

import logging
from typing import Optional, Tuple
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode

logger = logging.getLogger(__name__)

# Apple Bluetooth SIG Company ID
APPLE_COMPANY_ID = 0x004C

# Proximity Pairing Model ID mappings (byte 2 and 3)
MODEL_MAP = {
    (0x02, 0x20): AirPodsModel.AIRPODS_1,
    (0x0F, 0x20): AirPodsModel.AIRPODS_2,
    (0x13, 0x20): AirPodsModel.AIRPODS_3,
    (0x0E, 0x20): AirPodsModel.AIRPODS_PRO,
    (0x14, 0x20): AirPodsModel.AIRPODS_PRO_2,
    (0x24, 0x20): AirPodsModel.AIRPODS_PRO_2,
    (0x0A, 0x20): AirPodsModel.AIRPODS_MAX,
    (0x10, 0x20): AirPodsModel.POWERBEATS_PRO,
    (0x0B, 0x20): AirPodsModel.BEATS_SOLO_PRO,
    (0x11, 0x20): AirPodsModel.BEATS_STUDIO_BUDS,
    (0x17, 0x20): AirPodsModel.BEATS_FIT_PRO,
}


def _raw_nibble_to_percent(nibble: int) -> int:
    """Converts AirPods 4-bit battery nibble (0-10) to percentage (0-100%).

    A value of 15 (0xF) indicates the part is disconnected / not available.
    """
    if 0 <= nibble <= 10:
        # 10 is 100%, 9 is 90%, etc.
        return nibble * 10
    return -1


class AirPodsParser:
    """Parses raw manufacturer data bytes from Apple BLE beacons."""

    @staticmethod
    def parse_manufacturer_data(
        raw_data: bytes,
        rssi: int = -100,
        device_name: Optional[str] = None,
        mac_address: Optional[str] = None,
    ) -> Optional[AirPodsState]:
        """Parses raw Apple BLE manufacturer specific data into an AirPodsState object.

        Returns None if data is not an AirPods packet.
        """
        if not raw_data or len(raw_data) < 7:
            return None

        # Check packet type
        packet_type = raw_data[0]

        # 0x07 = Proximity Pairing (Most detailed packet: battery L/R/Case, in-ear, model)
        if packet_type == 0x07:
            return AirPodsParser._parse_proximity_pairing(raw_data, rssi, device_name, mac_address)

        # 0x10 = Nearby Action / Status packet
        if packet_type == 0x10 and len(raw_data) >= 8:
            return AirPodsParser._parse_nearby_action(raw_data, rssi, device_name, mac_address)

        return None

    @staticmethod
    def _parse_proximity_pairing(
        data: bytes,
        rssi: int,
        device_name: Optional[str],
        mac_address: Optional[str],
    ) -> Optional[AirPodsState]:
        """Parses Apple Proximity Pairing (type 0x07) beacon.

        Structure (typical 27 bytes):
        [0]: 0x07 (Type)
        [1]: 0x19 (Length, 25 bytes payload)
        [2..3]: Device Model ID (e.g. 0x0e 0x20 -> AirPods Pro)
        [4]: Status flags
        [5]: Flip / Ear status
        [6]: Left & Right battery nibbles
        [7]: Case battery nibble & lid status
        [8]: Charging flags
        """
        if len(data) < 9:
            return None

        # 1. Device Model
        model_key = (data[2], data[3]) if len(data) > 3 else (0x0E, 0x20)
        model = MODEL_MAP.get(model_key, AirPodsModel.UNKNOWN)

        # If unknown, try guessing based on byte 3 or device_name
        if model == AirPodsModel.UNKNOWN:
            if device_name:
                name_lower = device_name.lower()
                if "pro 2" in name_lower:
                    model = AirPodsModel.AIRPODS_PRO_2
                elif "pro" in name_lower:
                    model = AirPodsModel.AIRPODS_PRO
                elif "max" in name_lower:
                    model = AirPodsModel.AIRPODS_MAX
                elif "beats" in name_lower:
                    model = AirPodsModel.BEATS_FIT_PRO
                else:
                    model = AirPodsModel.AIRPODS_2
            else:
                model = AirPodsModel.AIRPODS_PRO

        # 2. Left / Right Flip Bit
        # Apple swaps earbud channels dynamically; bit 5 in byte 5 indicates inversion
        flip = bool((data[5] >> 5) & 0x01) if len(data) > 5 else False

        # 3. Battery Levels (Nibbles)
        # Byte 6 contains earbud 1 and earbud 2
        raw_b1 = data[6] & 0x0F
        raw_b2 = (data[6] >> 4) & 0x0F
        raw_case = data[7] & 0x0F if len(data) > 7 else 0x0F

        pct_1 = _raw_nibble_to_percent(raw_b1)
        pct_2 = _raw_nibble_to_percent(raw_b2)
        pct_case = _raw_nibble_to_percent(raw_case)

        # Assign to Left / Right based on flip flag
        if flip:
            left_battery = pct_2
            right_battery = pct_1
        else:
            left_battery = pct_1
            right_battery = pct_2

        # 4. Charging Flags (Byte 8)
        left_charging = False
        right_charging = False
        case_charging = False

        if len(data) > 8:
            charge_byte = data[8]
            chg_1 = bool(charge_byte & 0x01)
            chg_2 = bool(charge_byte & 0x02)
            case_charging = bool(charge_byte & 0x04)

            if flip:
                left_charging = chg_2
                right_charging = chg_1
            else:
                left_charging = chg_1
                right_charging = chg_2

        # 5. In-Ear Detection (Byte 5 flags)
        left_in_ear = False
        right_in_ear = False
        case_open = True

        if len(data) > 5:
            # When earbuds are in ear, charging is False and battery is valid
            # Status bits in byte 5 / 7 indicate lid and ear presence
            in_ear_1 = bool((data[5] & 0x08) != 0)
            in_ear_2 = bool((data[5] & 0x04) != 0)

            if flip:
                left_in_ear = in_ear_2
                right_in_ear = in_ear_1
            else:
                left_in_ear = in_ear_1
                right_in_ear = in_ear_2

            # If both earbuds are in ear, case is typically closed
            if left_in_ear and right_in_ear:
                case_open = False

        # If battery is unknown for all 3 components, this isn't a valid reading
        if left_battery < 0 and right_battery < 0 and pct_case < 0:
            return None

        clean_name = device_name or model.display_name

        return AirPodsState(
            model=model,
            device_name=clean_name,
            mac_address=mac_address,
            left_battery=left_battery,
            right_battery=right_battery,
            case_battery=pct_case,
            left_charging=left_charging,
            right_charging=right_charging,
            case_charging=case_charging,
            left_in_ear=left_in_ear,
            right_in_ear=right_in_ear,
            case_open=case_open,
            connected=True,
            noise_mode=NoiseControlMode.NOISE_CANCELLATION if model.has_anc else NoiseControlMode.OFF,
            rssi=rssi,
        )

    @staticmethod
    def _parse_nearby_action(
        data: bytes,
        rssi: int,
        device_name: Optional[str],
        mac_address: Optional[str],
    ) -> Optional[AirPodsState]:
        """Parses Apple Nearby Action (type 0x10) packet for supplementary battery/state."""
        # Typically shorter, provides activity state or battery level summary
        if len(data) < 6:
            return None

        # Byte 3 or 4 can contain overall battery level
        raw_bat = (data[4] & 0x7F) if len(data) > 4 else -1
        bat = raw_bat if 0 <= raw_bat <= 100 else -1

        if bat < 0:
            return None

        return AirPodsState(
            model=AirPodsModel.AIRPODS_PRO,
            device_name=device_name or "AirPods",
            mac_address=mac_address,
            left_battery=bat,
            right_battery=bat,
            case_battery=-1,
            connected=True,
            rssi=rssi,
        )
