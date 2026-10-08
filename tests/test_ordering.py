# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for StarDict ordering."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.stardict import stardict_sort_key  # noqa: E402


class OrderingTests(unittest.TestCase):
    def test_ascii_case_primary_order_and_exact_tiebreak(self) -> None:
        words = ["b", "aZ", "az", "AZ", "aa", "AA", "Aa"]
        ordered = sorted(words, key=stardict_sort_key)
        self.assertEqual(ordered, ["AA", "Aa", "aa", "AZ", "aZ", "az", "b"])


if __name__ == "__main__":
    unittest.main()
