"""Parser for Apple Continuity Bluetooth LE advertisement packets.

Decodes Apple manufacturer data (0x004C) containing Proximity Pairing (type 0x07)
and Nearby Info (type 0x10) packets for AirPods and Beats devices.
"""

import logging
from typing import List, Optional, Tuple
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode

logger = logging.getLogger(__name__)

# Apple Bluetooth SIG Company ID
APPLE_COMPANY_ID = 0x004C

# Proximity Pairing Model ID mappings (byte 2 and 3)
MODEL_MAP = {
    (0x02, 0x20): AirPodsModel.AIRPODS_1,
    (0x0F, 0x20): AirPodsModel.AIRPODS_2,
    (0x13, 0x20): AirPodsModel.AIRPODS_3,
    (0x1B, 0x20): AirPodsModel.AIRPODS_4_ANC,
    (0x1C, 0x20): AirPodsModel.AIRPODS_4,
    (0x20, 0x1B): AirPodsModel.AIRPODS_4_ANC,
    (0x06, 0x73): AirPodsModel.AIRPODS_4_ANC,  # Modern truncated 17-byte Proximity beacon
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

    Values above 10 (e.g. 0xF=15 or 0xC=12) indicate disconnected/unavailable.
    """
    if 0 <= nibble <= 10:
        return nibble * 10
    return -1


def extract_tlvs(raw_data: bytes) -> List[Tuple[int, bytes]]:
    """Extracts Apple Continuity Type-Length-Value records from manufacturer data.

    Returns a list of (type, chunk_bytes_with_header).
    """
    tlvs = []
    offset = 0
    while offset + 1 < len(raw_data):
        rec_type = raw_data[offset]
        rec_len = raw_data[offset + 1]
        chunk_len = 2 + rec_len
        if offset + chunk_len <= len(raw_data):
            tlvs.append((rec_type, raw_data[offset : offset + chunk_len]))
            offset += chunk_len
        else:
            # Fallback if raw packet is not structured with TLV header but matches direct 0x07
            if rec_type == 0x07 and len(raw_data) >= 9:
                tlvs.append((0x07, raw_data))
            break
    return tlvs


class AirPodsParser:
    """Parses raw manufacturer data bytes from Apple BLE beacons."""

    @staticmethod
    def parse_manufacturer_data(
        raw_data: bytes,
        rssi: int = -100,
        device_name: Optional[str] = None,
        mac_address: Optional[str] = None,
    ) -> Optional[AirPodsState]:
        """Parses Apple BLE manufacturer data into an AirPodsState object.

        Handles multi-TLV payloads containing Proximity Pairing (0x07) or Nearby Info (0x10).
        """
        if not raw_data or len(raw_data) < 7:
            return None

        tlvs = extract_tlvs(raw_data)

        # 1. Look for Proximity Pairing (0x07)
        for rec_type, chunk in tlvs:
            if rec_type == 0x07:
                state = AirPodsParser._parse_proximity_pairing(chunk, rssi, device_name, mac_address)
                if state:
                    return state

        # 2. Direct 0x07 fallback if not caught by TLV loop
        if raw_data[0] == 0x07 and len(raw_data) >= 9:
            state = AirPodsParser._parse_proximity_pairing(raw_data, rssi, device_name, mac_address)
            if state:
                return state

        # 3. Look for Nearby Action / Status packet (0x10)
        for rec_type, chunk in tlvs:
            if rec_type == 0x10 and len(chunk) >= 8:
                state = AirPodsParser._parse_nearby_action(chunk, rssi, device_name, mac_address)
                if state:
                    return state

        if raw_data[0] == 0x10 and len(raw_data) >= 8:
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

        Structure (27 bytes unencrypted, or 19 bytes encrypted/compact):
        [0]: 0x07 (Type)
        [1]: Length (0x19 or 0x11)
        [2..3]: Device Model ID
        [4]: Status flags
        [5]: Flip & in-ear presence
        [6]: Left & Right battery nibbles
        [7]: Case battery nibble & lid status
        [8]: Charging flags
        """
        if len(data) < 9:
            return None

        # 1. Device Model
        model_key = (data[2], data[3])
        model = MODEL_MAP.get(model_key, AirPodsModel.UNKNOWN)

        if model == AirPodsModel.UNKNOWN:
            if device_name:
                name_lower = device_name.lower()
                if "pro 2" in name_lower:
                    model = AirPodsModel.AIRPODS_PRO_2
                elif "pro" in name_lower:
                    model = AirPodsModel.AIRPODS_PRO
                elif "max" in name_lower:
                    model = AirPodsModel.AIRPODS_MAX
                elif "4" in name_lower or "utopia" in name_lower:
                    model = AirPodsModel.AIRPODS_4_ANC
                elif "3" in name_lower:
                    model = AirPodsModel.AIRPODS_3
                elif "beats" in name_lower:
                    model = AirPodsModel.BEATS_FIT_PRO
                else:
                    model = AirPodsModel.AIRPODS_2
            else:
                model = AirPodsModel.AIRPODS_4_ANC

        # 2. Left / Right Flip Bit (Apple swaps earbud channels dynamically)
        flip = bool((data[5] >> 5) & 0x01)

        # 3. Battery Levels (Nibbles)
        raw_b1 = data[6] & 0x0F
        raw_b2 = (data[6] >> 4) & 0x0F
        raw_case = data[7] & 0x0F

        pct_1 = _raw_nibble_to_percent(raw_b1)
        pct_2 = _raw_nibble_to_percent(raw_b2)
        pct_case = _raw_nibble_to_percent(raw_case)

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
        in_ear_1 = bool((data[5] & 0x08) != 0)
        in_ear_2 = bool((data[5] & 0x04) != 0)

        if flip:
            left_in_ear = in_ear_2
            right_in_ear = in_ear_1
        else:
            left_in_ear = in_ear_1
            right_in_ear = in_ear_2

        # Lid status:
        # Case is open if case battery is actively reported, or charging flags are active,
        # or if neither or only one earbud is in-ear while case is reporting.
        case_open = True
        if left_in_ear and right_in_ear and pct_case < 0:
            case_open = False

        # If all battery readings are completely invalid, drop packet
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
        if len(data) < 6:
            return None

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
