# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for morphology and aliases."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.indexdata import (  # noqa: E402
    parse_detailed_index,
    parse_group_index,
)
from houaiss3_stardict.morphology import (  # noqa: E402
    build_conservative_nominal_aliases,
    parse_verbal_aliases,
)


class MorphologyTests(unittest.TestCase):
    def test_verbal_cross_reference_uses_two_indexes(self) -> None:
        detailed = parse_detailed_index(
            "alpha;1;0;p;\n"
            "verb;2;0;p;\n"
        )
        grouped = parse_group_index(
            "alpha;1;0;p;\n"
            "verb;2;0;p;\n"
        )
        mapping, stats = parse_verbal_aliases(
            "inflected;1;2;p;\n",
            detailed,
            grouped,
        )
        self.assertEqual(mapping["verb"], {"inflected"})
        self.assertEqual(stats["crosscheck_mismatch"], 0)

    def test_conservative_plural_mapping_requires_unique_existing_target(self) -> None:
        mapping, stats = build_conservative_nominal_aliases(
            ["systems", "women", "radars"],
            {"system", "radar"},
        )
        self.assertEqual(mapping["system"], {"systems"})
        self.assertEqual(mapping["radar"], {"radars"})
        self.assertGreaterEqual(stats["no_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
