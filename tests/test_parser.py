"""Unit tests for AirPods BLE beacon parser and data models."""

import unittest
from airwin.core.airpods_parser import AirPodsParser
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode


class TestAirPodsParser(unittest.TestCase):
    def test_parse_airpods_pro_packet(self):
        # Simulated raw Apple 0x07 proximity pairing packet:
        # byte 0: 0x07 (Type)
        # byte 1: 0x19 (Length)
        # byte 2: 0x0E, byte 3: 0x20 (AirPods Pro 1)
        # byte 4: 0x00
        # byte 5: 0x00 (flip=0)
        # byte 6: 0x98 (low nibble 8 -> 80% left, high nibble 9 -> 90% right)
        # byte 7: 0x07 (case -> 70%)
        # byte 8: 0x01 (left charging)
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
        # byte 5: bit 5 set (0x20) -> flip=1
        # byte 6: 0x59 (low nibble 9 -> right=90%, high nibble 5 -> left=50%)
        # byte 8: 0x02 (b1 charged -> right charging when flip=0, or left when flip=1)
        raw = bytearray([0x07, 0x19, 0x14, 0x20, 0x00, 0x20, 0x59, 0x08, 0x02] + [0x00] * 18)

        state = AirPodsParser.parse_manufacturer_data(bytes(raw), rssi=-60)
        self.assertIsNotNone(state)
        self.assertEqual(state.model, AirPodsModel.AIRPODS_PRO_2)
        self.assertEqual(state.left_battery, 50)
        self.assertEqual(state.right_battery, 90)
        self.assertEqual(state.case_battery, 80)
        self.assertTrue(state.left_charging)

    def test_invalid_packet(self):
        # Empty or too short
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b""))
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b"\x07\x02"))
        # Non-Apple proximity packet
        self.assertIsNone(AirPodsParser.parse_manufacturer_data(b"\x01\x02\x03\x04\x05\x06\x07\x08"))

    def test_battery_average_calculation(self):
        state = AirPodsState(left_battery=80, right_battery=90)
        self.assertEqual(state.average_earbud_battery, 85)

        single = AirPodsState(left_battery=70, right_battery=-1)
        self.assertEqual(single.average_earbud_battery, 70)


if __name__ == "__main__":
    unittest.main()
