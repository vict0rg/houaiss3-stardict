# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests using entirely synthetic byte sequences."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.decoder import decode_bytes  # noqa: E402


class DecoderTests(unittest.TestCase):
    def test_decode_bytes_uses_modular_offset(self) -> None:
        source = bytes([0x00, 0x01, 0xF5, 0xFF])
        expected = bytes([0x0B, 0x0C, 0x00, 0x0A])
        self.assertEqual(decode_bytes(source), expected)


if __name__ == "__main__":
    unittest.main()
