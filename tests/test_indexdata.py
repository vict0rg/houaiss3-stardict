# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for authoritative index grouping."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.indexdata import (  # noqa: E402
    build_authoritative_groups,
    parse_detailed_index,
    parse_group_index,
    same_group_key,
)
from houaiss3_stardict.model import Entry  # noqa: E402


class IndexDataTests(unittest.TestCase):
    def test_grouped_index_controls_search_headwords(self) -> None:
        entries = [
            Entry("display-alpha"),
            Entry("display-beta"),
            Entry("Display-Beta"),
        ]

        detailed = parse_detailed_index(
            "alpha;1;0;p;\n"
            "beta;2;1;p;\n"
            "Beta;3;2;p;\n"
        )

        grouped = parse_group_index(
            "alpha;1;0;p;\n"
            "beta;2;2;p;\n"
        )

        result = build_authoritative_groups(entries, detailed, grouped)

        self.assertEqual([key for key, _ in result], ["alpha", "beta"])
        self.assertEqual(len(result[1][1]), 2)

    def test_group_validation_accepts_capitalization_variants(self) -> None:
        self.assertTrue(same_group_key("synthetic", "Synthetic"))
        self.assertTrue(same_group_key("Árvore", "árvore"))
        self.assertFalse(same_group_key("synthetic", "synthetics"))


if __name__ == "__main__":
    unittest.main()
