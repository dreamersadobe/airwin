"""Unit tests for AirPods BLE beacon parser and data models."""

import unittest
from airwin.core.airpods_parser import AirPodsParser
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode


class TestAirPodsParser(unittest.TestCase):
    def test_parse_airpods_pro_packet(self):
        raw = bytearray([0x07, 0x19, 0x0E, 0x20, 0x00, 0x00, 0x98, 0x07, 0x01] + [0x00] * 18)
        state = AirPodsParser.parse_manufacturer_data(bytes(raw), rssi=-55)

        self.assertIsNotNone(state)
        self.assertEqual(state.model, AirPodsModel.AIRPODS_PRO)
        self.assertEqual(state.left_battery, 80)
        self.assertEqual(state.right_battery, 90)
        self.assertEqual(state.case_battery, 70)
        self.assertTrue(state.left_charging)
        self.assertFalse(state.right_charging)
        self.assertFalse(state.case_charging)
        self.assertEqual(state.rssi, -55)

    def test_parse_flipped_channels(self):
        raw = bytearray([0x07, 0x19, 0x14, 0x20, 0x00, 0x20, 0x59, 0x08, 0x02] + [0x00] * 18)
        state = AirPodsParser.parse_manufacturer_data(bytes(raw), rssi=-60)
        self.assertIsNotNone(state)
        self.assertEqual(state.model, AirPodsModel.AIRPODS_PRO_2)
        self.assertEqual(state.left_battery, 50)
        self.assertEqual(state.right_battery, 90)
        self.assertEqual(state.case_battery, 80)
        self.assertTrue(state.left_charging)

    def test_parse_tlv_wrapped_packet(self):
        # Multi-TLV packet with 0x12 Find My followed by 0x07 Proximity Pairing
        tlv_data = bytes.fromhex("12022e0207110673d9fa77ec5cf40b1ba702b19ac7a605")
        state = AirPodsParser.parse_manufacturer_data(tlv_data, rssi=-48, device_name="utopia")
        self.assertIsNotNone(state)
        self.assertEqual(state.left_battery, 70)
        self.assertEqual(state.right_battery, 70)
        self.assertEqual(state.device_name, "utopia")
        self.assertEqual(state.model, AirPodsModel.AIRPODS_4_ANC)
        self.assertTrue(state.right_in_ear)

    def test_state_merging(self):
        s1 = AirPodsState(
            device_name="utopia",
            left_battery=70,
            right_battery=75,
            case_battery=80,
            case_open=True,
            connected=True,
        )
        # s2 arrives when case is closed (case_battery = -1)
        s2 = AirPodsState(
            device_name="utopia",
            left_battery=69,
            right_battery=74,
            case_battery=-1,
            case_open=False,
            connected=True,
        )
        merged = s1.merge_with(s2)
        # Should keep case battery 80% instead of dropping to -1
        self.assertEqual(merged.case_battery, 80)
        self.assertEqual(merged.left_battery, 69)
        self.assertFalse(merged.case_open)

    def test_invalid_packet(self):
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b""))
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b"\x07\x02"))
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b"\x01\x02\x03\x04\x05\x06\x07\x08"))

    def test_battery_average_calculation(self):
        state = AirPodsState(left_battery=80, right_battery=90)
        self.assertEqual(state.average_earbud_battery, 85)

        single = AirPodsState(left_battery=70, right_battery=-1)
        self.assertEqual(single.average_earbud_battery, 70)


if __name__ == "__main__":
    unittest.main()
